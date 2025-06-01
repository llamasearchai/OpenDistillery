"""
Tree of Thoughts Implementation
Advanced reasoning technique that explores multiple reasoning paths in a tree structure.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
import heapq
import numpy as np

import structlog

# Import core components
try:
    from ....core.compound_system import ModelConfiguration, ModelRouter
except ImportError:
    from src.core.compound_system import ModelConfiguration, ModelRouter

logger = structlog.get_logger(__name__)

class NodeType(Enum):
    ROOT = "root"
    THOUGHT = "thought"
    EVALUATION = "evaluation"
    SOLUTION = "solution"

class SearchStrategy(Enum):
    BFS = "breadth_first"
    DFS = "depth_first"
    BEST_FIRST = "best_first"
    BEAM_SEARCH = "beam_search"

@dataclass
class ThoughtNode:
    """Represents a node in the tree of thoughts"""
    id: str
    content: str
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    depth: int = 0
    score: float = 0.5
    evaluation: str = ""
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    
    def __lt__(self, other):
        """For priority queue ordering"""
        return self.score > other.score  # Higher score = higher priority

@dataclass
class EvaluationCriteria:
    """Criteria for evaluating thought nodes"""
    relevance_weight: float = 0.3
    feasibility_weight: float = 0.3
    novelty_weight: float = 0.2
    completeness_weight: float = 0.2
    
class TreeOfThoughts:
    """
    Tree of Thoughts reasoning implementation
    """
    
    def __init__(self, models: Dict[str, ModelConfiguration], router: ModelRouter):
        self.models = models
        self.router = router
        self.max_depth = 5
        self.max_branches = 3
        self.nodes: Dict[str, ThoughtNode] = {}
        self.root_id: Optional[str] = None
        self.current_depth = 0
        
        # Search configuration
        self.search_strategy = SearchStrategy.BEST_FIRST
        self.beam_width = 3
        self.evaluation_criteria = EvaluationCriteria()
        
        # Performance tracking
        self.generation_count = 0
        self.evaluation_count = 0
        
    async def solve(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Solve problem using Tree of Thoughts"""
        problem = request.get("prompt", request.get("goal", "Solve the given problem"))
        context = request.get("context", {})
        
        logger.info(f"Starting Tree of Thoughts for problem: {problem[:100]}...")
        
        start_time = time.time()
        
        # Initialize tree
        self.nodes = {}
        self.current_depth = 0
        
        # Create root node
        self.root_id = str(uuid.uuid4())
        root_node = ThoughtNode(
            id=self.root_id,
            content=problem,
            depth=0,
            score=0.8,
            evaluation="Root problem statement"
        )
        self.nodes[self.root_id] = root_node
        
        # Build thought tree
        await self._expand_tree(self.root_id, context)
        
        # Find best solution path
        solution_path = self._find_best_path()
        
        execution_time = time.time() - start_time
        
        # Build result
        result = {
            "success": len(solution_path) > 0,
            "response": solution_path[-1].content if solution_path else "No solution path found",
            "confidence": solution_path[-1].score if solution_path else 0.0,
            "thought_tree": {
                "nodes": len(self.nodes),
                "max_depth": self.current_depth
            },
            "solution_path": [
                {
                    "depth": node.depth,
                    "content": node.content,
                    "score": node.score,
                    "evaluation": node.evaluation
                }
                for node in solution_path
            ],
            "tree_statistics": {
                "total_nodes": len(self.nodes),
                "max_depth_reached": self.current_depth,
                "generation_count": self.generation_count,
                "evaluation_count": self.evaluation_count,
                "execution_time": execution_time
            }
        }
        
        return result
    
    async def _expand_tree(self, parent_id: str, context: Dict[str, Any]):
        """Recursively expand thought tree"""
        if self.current_depth >= self.max_depth:
            logger.info(f"Reached maximum depth {self.max_depth}")
            return
        
        parent_node = self.nodes[parent_id]
        logger.info(f"Expanding node at depth {parent_node.depth}: {parent_node.content[:50]}...")
        
        # Generate branching thoughts
        branches = await self._generate_branches(parent_node, context)
        
        # Add child nodes
        from uuid import uuid4
        self.current_depth = max(self.current_depth, parent_node.depth + 1)
        
        for branch in branches[:self.max_branches]:
            child_id = str(uuid4())
            child_node = ThoughtNode(
                id=child_id,
                content=branch["content"],
                parent_id=parent_id,
                depth=parent_node.depth + 1,
                score=branch["score"],
                evaluation=branch["evaluation"]
            )
            self.nodes[child_id] = child_node
            parent_node.children.append(child_id)
            
            # Recursively expand promising branches
            if child_node.score > 0.6 and child_node.depth < self.max_depth:
                await self._expand_tree(child_id, context)

    async def _generate_branches(self, node: ThoughtNode, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate multiple thought branches from a node"""
        # Build prompt for branching thoughts
        prompt = f"""
        I'm exploring solutions for: {self.nodes[self.root_id].content}
        
        Current thought path:
        {self._get_path_content(node.id)}
        
        Context:
        {json.dumps(context, indent=2)[:500]}...
        
        Generate {self.max_branches} different approaches to explore next.
        For each approach, provide:
        1. A distinct perspective or strategy
        2. A score (0-1) for how promising it seems
        3. A brief evaluation of the approach
        
        Format as:
        Approach 1: [content]
        Score: [0-1]
        Evaluation: [reasoning]
        ---
        Approach 2: [content]
        Score: [0-1]
        Evaluation: [reasoning]
        """
        
        # Route to model
        model = self.router.route_request({"task_type": "exploratory_reasoning"}, list(self.models.values()))
        
        try:
            # Get branches from model
            response = await self._call_model(model, prompt, {})
            
            # Parse response into branches
            branches = self._parse_branches(response)
            logger.info(f"Generated {len(branches)} branches at depth {node.depth + 1}")
            return branches
        except Exception as e:
            logger.error(f"Branch generation failed: {str(e)}")
            return [
                {"content": f"Error generating branch: {str(e)}", "score": 0.1, "evaluation": "Error"}
            ]

    def _parse_branches(self, response: str) -> List[Dict[str, Any]]:
        """Parse model response into thought branches"""
        branches = []
        current_branch = {}
        current_key = None
        
        for line in response.split("\n"):
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("Approach"):
                if current_branch:
                    branches.append(current_branch)
                current_branch = {"content": "", "score": 0.5, "evaluation": ""}
                current_key = "content"
                content = line.split(":", 1)[1].strip() if ":" in line else ""
                current_branch["content"] = content
            elif line.startswith("Score:"):
                current_key = "score"
                try:
                    score = float(line.split(":", 1)[1].strip())
                    current_branch["score"] = max(0.0, min(1.0, score))
                except (ValueError, IndexError):
                    current_branch["score"] = 0.5
            elif line.startswith("Evaluation:"):
                current_key = "evaluation"
                evaluation = line.split(":", 1)[1].strip() if ":" in line else ""
                current_branch["evaluation"] = evaluation
            elif line.startswith("---") or line.startswith("Approach"):
                if current_branch:
                    branches.append(current_branch)
                current_branch = {"content": "", "score": 0.5, "evaluation": ""}
                current_key = None
            elif current_key and current_branch:
                current_branch[current_key] += " " + line
        
        if current_branch and current_branch.get("content"):
            branches.append(current_branch)
        
        # If no branches parsed, create a default one
        if not branches:
            branches.append({
                "content": response[:200] if response else "Generated thought branch",
                "score": 0.6,
                "evaluation": "Default branch from response"
            })
        
        return branches[:self.max_branches]

    def _get_path_content(self, node_id: str) -> str:
        """Get content of path from root to node"""
        if node_id not in self.nodes:
            return ""
        
        node = self.nodes[node_id]
        path_content = [f"Depth {node.depth}: {node.content}"]
        
        if node.parent_id and node.parent_id in self.nodes:
            parent_content = self._get_path_content(node.parent_id)
            if parent_content:
                path_content.insert(0, parent_content)
        
        return " -> ".join(path_content.split("\n"))

    def _find_best_path(self) -> List[ThoughtNode]:
        """Find best path through thought tree based on scores"""
        if not self.nodes or not self.root_id:
            return []
        
        # Find leaf nodes (nodes with no children)
        leaf_nodes = [node for node in self.nodes.values() if not node.children]
        if not leaf_nodes:
            leaf_nodes = list(self.nodes.values())
        
        # Select best leaf based on score and depth
        best_leaf = max(leaf_nodes, key=lambda n: (n.score, n.depth))
        
        # Build path from root to best leaf
        path = []
        current_node = best_leaf
        while current_node is not None:
            path.append(current_node)
            parent_id = current_node.parent_id
            current_node = self.nodes.get(parent_id) if parent_id else None
        
        return list(reversed(path))

    def _format_response(self, solution_path: List[ThoughtNode]) -> Dict[str, Any]:
        """Format final response from Tree of Thoughts"""
        if not solution_path:
            return {
                "success": False,
                "response": "No solution path found",
                "thought_tree": {
                    "nodes": len(self.nodes),
                    "max_depth": self.current_depth
                },
                "solution_path": []
            }
        
        final_answer = solution_path[-1].content
        confidence = solution_path[-1].score
        
        return {
            "success": True,
            "response": final_answer,
            "thought_tree": {
                "nodes": len(self.nodes),
                "max_depth": self.current_depth,
                "branches": sum(len(node.children) for node in self.nodes.values())
            },
            "solution_path": [
                {
                    "depth": node.depth,
                    "content": node.content,
                    "score": node.score,
                    "evaluation": node.evaluation
                }
                for node in solution_path
            ],
            "confidence": confidence
        }

    async def _call_model(self, model: ModelConfiguration, prompt: str, request: Dict[str, Any]) -> str:
        """Call model with error handling"""
        from src.core.compound_system import CompoundAISystem
        
        try:
            if model.provider == "openai":
                response = await CompoundAISystem._call_openai(None, model, prompt, request)
            elif model.provider == "anthropic":
                response = await CompoundAISystem._call_anthropic(None, model, prompt, request)
            elif model.provider == "google":
                response = await CompoundAISystem._call_google(None, model, prompt, request)
            else:
                raise ValueError(f"Unsupported provider: {model.provider}")
            
            return response
        except Exception as e:
            logger.error(f"Model call failed: {str(e)}")
            raise
    
    def get_tree_visualization(self) -> Dict[str, Any]:
        """Get tree structure for visualization"""
        if not self.root_id:
            return {}
        
        def build_tree_dict(node_id: str) -> Dict[str, Any]:
            node = self.nodes[node_id]
            tree_node = {
                "id": node_id,
                "content": node.content[:50] + "..." if len(node.content) > 50 else node.content,
                "score": node.score,
                "evaluation": node.evaluation,
                "depth": node.depth,
                "type": NodeType.THOUGHT.value,
                "children": []
            }
            
            for child_id in node.children:
                tree_node["children"].append(build_tree_dict(child_id))
            
            return tree_node
        
        return build_tree_dict(self.root_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tree statistics"""
        if not self.nodes:
            return {}
        
        depths = [node.depth for node in self.nodes.values()]
        scores = [node.score for node in self.nodes.values()]
        
        return {
            "total_nodes": len(self.nodes),
            "max_depth": max(depths),
            "average_depth": np.mean(depths),
            "average_score": np.mean(scores),
            "best_score": max(scores),
            "generation_count": self.generation_count,
            "evaluation_count": self.evaluation_count,
            "nodes_by_depth": {
                depth: len([n for n in self.nodes.values() if n.depth == depth])
                for depth in range(max(depths) + 1)
            }
        } 