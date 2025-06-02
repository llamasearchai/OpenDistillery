"""
Graph of Thoughts Implementation
Advanced reasoning technique using graph structures for multi-perspective analysis.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
import networkx as nx
import numpy as np

import structlog

logger = structlog.get_logger(__name__)

class NodeType(Enum):
    PROBLEM = "problem"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    DECISION = "decision"
    EVIDENCE = "evidence"
    HYPOTHESIS = "hypothesis"

class EdgeType(Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    LEADS_TO = "leads_to"
    DEPENDS_ON = "depends_on"
    RELATES_TO = "relates_to"
    SYNTHESIZES = "synthesizes"

@dataclass
class GraphNode:
    """Represents a node in the graph of thoughts"""
    node_id: str
    content: str
    node_type: NodeType
    confidence: float = 0.0
    importance: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

@dataclass
class GraphEdge:
    """Represents an edge in the graph of thoughts"""
    edge_id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class GraphOfThoughts:
    """
    Graph of Thoughts reasoning implementation
    """
    
    def __init__(self, models: Dict[str, Any], model_router: Any, max_nodes: int = 30):
        self.models = models
        self.model_router = model_router
        self.max_nodes = max_nodes
        
        # Graph structure
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        
        # Analysis tracking
        self.reasoning_paths: List[List[str]] = []
        self.synthesis_nodes: List[str] = []
        
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process problem using Graph of Thoughts"""
        problem = request.get("prompt", "")
        context = request.get("context", {})
        
        logger.info(f"Starting Graph of Thoughts for problem: {problem[:100]}...")
        
        start_time = time.time()
        
        # Initialize graph with problem node
        problem_node_id = await self._create_problem_node(problem, context)
        
        # Build reasoning graph
        await self._build_reasoning_graph(problem_node_id, context)
        
        # Analyze reasoning paths
        self._analyze_reasoning_paths()
        
        # Synthesize insights
        synthesis_result = await self._synthesize_insights()
        
        # Generate final decision
        final_decision = await self._generate_final_decision(synthesis_result)
        
        execution_time = time.time() - start_time
        
        # Build result
        result = {
            "success": True,
            "response": final_decision["content"],
            "confidence": final_decision["confidence"],
            "graph_statistics": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "reasoning_paths": len(self.reasoning_paths),
                "synthesis_nodes": len(self.synthesis_nodes),
                "execution_time": execution_time,
                "graph_density": nx.density(self.graph) if self.graph.number_of_nodes() > 1 else 0
            },
            "reasoning_network": self._extract_reasoning_network(),
            "key_insights": synthesis_result.get("insights", []),
            "alternative_perspectives": self._extract_alternative_perspectives()
        }
        
        return result
    
    async def _create_problem_node(self, problem: str, context: Dict[str, Any]) -> str:
        """Create the initial problem node"""
        node_id = str(uuid.uuid4())
        
        node = GraphNode(
            node_id=node_id,
            content=problem,
            node_type=NodeType.PROBLEM,
            confidence=1.0,
            importance=1.0,
            metadata={"context": context}
        )
        
        self.nodes[node_id] = node
        self.graph.add_node(node_id, **node.__dict__)
        
        return node_id
    
    async def _build_reasoning_graph(self, problem_node_id: str, context: Dict[str, Any]) -> None:
        """Build the reasoning graph through iterative expansion"""
        expansion_queue = [problem_node_id]
        processed_nodes = set()
        
        while expansion_queue and len(self.nodes) < self.max_nodes:
            current_node_id = expansion_queue.pop(0)
            
            if current_node_id in processed_nodes:
                continue
            
            processed_nodes.add(current_node_id)
            current_node = self.nodes[current_node_id]
            
            # Generate analysis nodes
            analysis_nodes = await self._generate_analysis_nodes(current_node_id)
            
            # Generate evidence nodes
            evidence_nodes = await self._generate_evidence_nodes(current_node_id)
            
            # Generate hypothesis nodes
            hypothesis_nodes = await self._generate_hypothesis_nodes(current_node_id)
            
            # Add new nodes to expansion queue
            new_nodes = analysis_nodes + evidence_nodes + hypothesis_nodes
            for node_id in new_nodes:
                if len(self.nodes) < self.max_nodes:
                    expansion_queue.append(node_id)
            
            # Create synthesis opportunities
            if len(new_nodes) >= 2:
                synthesis_node_id = await self._create_synthesis_node(new_nodes)
                if synthesis_node_id:
                    self.synthesis_nodes.append(synthesis_node_id)
    
    async def _generate_analysis_nodes(self, parent_node_id: str) -> List[str]:
        """Generate analysis nodes for a given parent"""
        parent_node = self.nodes[parent_node_id]
        
        analysis_prompt = f"""
Analyze the following from multiple perspectives:

Content: {parent_node.content}
Type: {parent_node.node_type.value}

Generate 3 different analytical perspectives:
1. A logical/rational analysis
2. A creative/innovative analysis  
3. A practical/implementation analysis

Format your response as:
Analysis 1: [logical analysis]
Analysis 2: [creative analysis]
Analysis 3: [practical analysis]
"""
        
        model = self.model_router.route_request({"task_type": "analysis"}, list(self.models.values()))
        response = await self._call_model(model, analysis_prompt)
        
        analyses = self._parse_multiple_responses(response, "Analysis")
        
        analysis_node_ids = []
        for i, analysis in enumerate(analyses):
            node_id = str(uuid.uuid4())
            
            node = GraphNode(
                node_id=node_id,
                content=analysis,
                node_type=NodeType.ANALYSIS,
                confidence=0.7 + i * 0.1,  # Vary confidence slightly
                importance=0.6,
                metadata={"analysis_type": ["logical", "creative", "practical"][i]}
            )
            
            self.nodes[node_id] = node
            self.graph.add_node(node_id, **node.__dict__)
            
            # Create edge from parent to analysis
            edge_id = str(uuid.uuid4())
            edge = GraphEdge(
                edge_id=edge_id,
                source_id=parent_node_id,
                target_id=node_id,
                edge_type=EdgeType.LEADS_TO,
                weight=0.8,
                confidence=0.8
            )
            
            self.edges[edge_id] = edge
            self.graph.add_edge(parent_node_id, node_id, **edge.__dict__)
            
            analysis_node_ids.append(node_id)
        
        return analysis_node_ids
    
    async def _generate_evidence_nodes(self, parent_node_id: str) -> List[str]:
        """Generate evidence nodes for a given parent"""
        parent_node = self.nodes[parent_node_id]
        
        evidence_prompt = f"""
Identify evidence that supports or contradicts the following:

Content: {parent_node.content}

Generate 2 pieces of evidence:
1. Supporting evidence
2. Contradicting evidence or alternative viewpoint

Format your response as:
Evidence 1: [supporting evidence]
Evidence 2: [contradicting evidence]
"""
        
        model = self.model_router.route_request({"task_type": "evidence"}, list(self.models.values()))
        response = await self._call_model(model, evidence_prompt)
        
        evidence_items = self._parse_multiple_responses(response, "Evidence")
        
        evidence_node_ids = []
        for i, evidence in enumerate(evidence_items):
            node_id = str(uuid.uuid4())
            
            node = GraphNode(
                node_id=node_id,
                content=evidence,
                node_type=NodeType.EVIDENCE,
                confidence=0.6 + i * 0.2,
                importance=0.5,
                metadata={"evidence_type": ["supporting", "contradicting"][i]}
            )
            
            self.nodes[node_id] = node
            self.graph.add_node(node_id, **node.__dict__)
            
            # Create edge with appropriate type
            edge_type = EdgeType.SUPPORTS if i == 0 else EdgeType.CONTRADICTS
            edge_id = str(uuid.uuid4())
            edge = GraphEdge(
                edge_id=edge_id,
                source_id=node_id,
                target_id=parent_node_id,
                edge_type=edge_type,
                weight=0.7,
                confidence=0.7
            )
            
            self.edges[edge_id] = edge
            self.graph.add_edge(node_id, parent_node_id, **edge.__dict__)
            
            evidence_node_ids.append(node_id)
        
        return evidence_node_ids
    
    async def _generate_hypothesis_nodes(self, parent_node_id: str) -> List[str]:
        """Generate hypothesis nodes for a given parent"""
        parent_node = self.nodes[parent_node_id]
        
        hypothesis_prompt = f"""
Based on the following, generate hypotheses for further exploration:

Content: {parent_node.content}

Generate 2 hypotheses:
1. A testable hypothesis
2. An exploratory hypothesis

Format your response as:
Hypothesis 1: [testable hypothesis]
Hypothesis 2: [exploratory hypothesis]
"""
        
        model = self.model_router.route_request({"task_type": "hypothesis"}, list(self.models.values()))
        response = await self._call_model(model, hypothesis_prompt)
        
        hypotheses = self._parse_multiple_responses(response, "Hypothesis")
        
        hypothesis_node_ids = []
        for i, hypothesis in enumerate(hypotheses):
            node_id = str(uuid.uuid4())
            
            node = GraphNode(
                node_id=node_id,
                content=hypothesis,
                node_type=NodeType.HYPOTHESIS,
                confidence=0.5 + i * 0.1,
                importance=0.7,
                metadata={"hypothesis_type": ["testable", "exploratory"][i]}
            )
            
            self.nodes[node_id] = node
            self.graph.add_node(node_id, **node.__dict__)
            
            # Create edge from parent to hypothesis
            edge_id = str(uuid.uuid4())
            edge = GraphEdge(
                edge_id=edge_id,
                source_id=parent_node_id,
                target_id=node_id,
                edge_type=EdgeType.LEADS_TO,
                weight=0.6,
                confidence=0.6
            )
            
            self.edges[edge_id] = edge
            self.graph.add_edge(parent_node_id, node_id, **edge.__dict__)
            
            hypothesis_node_ids.append(node_id)
        
        return hypothesis_node_ids
    
    async def _create_synthesis_node(self, source_node_ids: List[str]) -> Optional[str]:
        """Create a synthesis node from multiple source nodes"""
        if len(source_node_ids) < 2:
            return None
        
        # Gather content from source nodes
        source_contents = []
        for node_id in source_node_ids:
            node = self.nodes[node_id]
            source_contents.append(f"{node.node_type.value}: {node.content}")
        
        synthesis_prompt = f"""
Synthesize insights from the following perspectives:

{chr(10).join(source_contents)}

Create a synthesis that:
1. Identifies common themes
2. Resolves contradictions where possible
3. Generates new insights from the combination

Synthesis: [your synthesis]
"""
        
        model = self.model_router.route_request({"task_type": "synthesis"}, list(self.models.values()))
        response = await self._call_model(model, synthesis_prompt)
        
        # Extract synthesis content
        synthesis_content = response.strip()
        if synthesis_content.startswith("Synthesis:"):
            synthesis_content = synthesis_content[10:].strip()
        
        # Create synthesis node
        node_id = str(uuid.uuid4())
        
        node = GraphNode(
            node_id=node_id,
            content=synthesis_content,
            node_type=NodeType.SYNTHESIS,
            confidence=0.8,
            importance=0.9,
            metadata={"source_nodes": source_node_ids}
        )
        
        self.nodes[node_id] = node
        self.graph.add_node(node_id, **node.__dict__)
        
        # Create edges from source nodes to synthesis
        for source_id in source_node_ids:
            edge_id = str(uuid.uuid4())
            edge = GraphEdge(
                edge_id=edge_id,
                source_id=source_id,
                target_id=node_id,
                edge_type=EdgeType.SYNTHESIZES,
                weight=0.8,
                confidence=0.8
            )
            
            self.edges[edge_id] = edge
            self.graph.add_edge(source_id, node_id, **edge.__dict__)
        
        return node_id
    
    def _analyze_reasoning_paths(self) -> None:
        """Analyze paths through the reasoning graph"""
        # Find all paths from problem nodes to synthesis/decision nodes
        problem_nodes = [nid for nid, node in self.nodes.items() if node.node_type == NodeType.PROBLEM]
        terminal_nodes = [nid for nid, node in self.nodes.items() 
                         if node.node_type in [NodeType.SYNTHESIS, NodeType.DECISION]]
        
        self.reasoning_paths = []
        
        for start_node in problem_nodes:
            for end_node in terminal_nodes:
                try:
                    paths = list(nx.all_simple_paths(self.graph, start_node, end_node, cutoff=6))
                    self.reasoning_paths.extend(paths)
                except nx.NetworkXNoPath:
                    continue
        
        # Also find high-importance node paths
        high_importance_nodes = [nid for nid, node in self.nodes.items() if node.importance > 0.8]
        
        for node_id in high_importance_nodes:
            # Find paths to this important node
            for start_node in problem_nodes:
                try:
                    paths = list(nx.all_simple_paths(self.graph, start_node, node_id, cutoff=4))
                    self.reasoning_paths.extend(paths)
                except nx.NetworkXNoPath:
                    continue
    
    async def _synthesize_insights(self) -> Dict[str, Any]:
        """Synthesize insights from the reasoning graph"""
        # Collect all synthesis nodes
        synthesis_contents = []
        for node_id in self.synthesis_nodes:
            if node_id in self.nodes:
                synthesis_contents.append(self.nodes[node_id].content)
        
        # Collect high-confidence analysis nodes
        analysis_contents = []
        for node_id, node in self.nodes.items():
            if node.node_type == NodeType.ANALYSIS and node.confidence > 0.7:
                analysis_contents.append(node.content)
        
        # Create overall synthesis
        all_insights = synthesis_contents + analysis_contents[:3]  # Limit to top 3 analyses
        
        if not all_insights:
            return {"insights": [], "confidence": 0.3}
        
        final_synthesis_prompt = f"""
Synthesize the following insights into key takeaways:

{chr(10).join([f"- {insight}" for insight in all_insights])}

Identify the 3 most important insights and provide an overall confidence assessment.

Format your response as:
Insight 1: [first key insight]
Insight 2: [second key insight]
Insight 3: [third key insight]
Confidence: [confidence level 0-1]
"""
        
        model = self.model_router.route_request({"task_type": "synthesis"}, list(self.models.values()))
        response = await self._call_model(model, final_synthesis_prompt)
        
        # Parse insights
        insights = self._parse_multiple_responses(response, "Insight")
        confidence = self._extract_confidence_from_response(response)
        
        return {
            "insights": insights,
            "confidence": confidence,
            "synthesis_count": len(synthesis_contents),
            "analysis_count": len(analysis_contents)
        }
    
    async def _generate_final_decision(self, synthesis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final decision based on synthesis"""
        insights = synthesis_result.get("insights", [])
        confidence = synthesis_result.get("confidence", 0.5)
        
        decision_prompt = f"""
Based on the following key insights, make a final decision or recommendation:

Key Insights:
{chr(10).join([f"- {insight}" for insight in insights])}

Provide a clear, actionable decision or recommendation.

Decision: [your final decision]
Rationale: [brief rationale]
Confidence: [confidence level 0-1]
"""
        
        model = self.model_router.route_request({"task_type": "decision"}, list(self.models.values()))
        response = await self._call_model(model, decision_prompt)
        
        # Parse decision
        decision_content = ""
        rationale = ""
        decision_confidence = confidence
        
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("Decision:"):
                decision_content = line[9:].strip()
            elif line.startswith("Rationale:"):
                rationale = line[10:].strip()
            elif line.startswith("Confidence:"):
                try:
                    decision_confidence = float(line[11:].strip())
                except ValueError:
                    pass
        
        return {
            "content": decision_content,
            "rationale": rationale,
            "confidence": decision_confidence
        }
    
    def _parse_multiple_responses(self, response: str, prefix: str) -> List[str]:
        """Parse multiple responses with a given prefix"""
        items = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith(f"{prefix} 1:"):
                items.append(line[len(f"{prefix} 1:"):].strip())
            elif line.startswith(f"{prefix} 2:"):
                items.append(line[len(f"{prefix} 2:"):].strip())
            elif line.startswith(f"{prefix} 3:"):
                items.append(line[len(f"{prefix} 3:"):].strip())
        
        return items
    
    def _extract_confidence_from_response(self, response: str) -> float:
        """Extract confidence value from response"""
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip().lower()
            if line.startswith("confidence:"):
                try:
                    return float(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
        return 0.7  # Default confidence
    
    def _extract_reasoning_network(self) -> Dict[str, Any]:
        """Extract reasoning network structure"""
        network = {
            "nodes": [],
            "edges": [],
            "clusters": []
        }
        
        # Add nodes
        for node_id, node in self.nodes.items():
            network["nodes"].append({
                "id": node_id,
                "content": node.content[:100] + "..." if len(node.content) > 100 else node.content,
                "type": node.node_type.value,
                "confidence": node.confidence,
                "importance": node.importance
            })
        
        # Add edges
        for edge_id, edge in self.edges.items():
            network["edges"].append({
                "id": edge_id,
                "source": edge.source_id,
                "target": edge.target_id,
                "type": edge.edge_type.value,
                "weight": edge.weight,
                "confidence": edge.confidence
            })
        
        # Identify clusters (connected components)
        if self.graph.number_of_nodes() > 0:
            undirected_graph = self.graph.to_undirected()
            connected_components = list(nx.connected_components(undirected_graph))
            
            for i, component in enumerate(connected_components):
                if len(component) > 1:
                    network["clusters"].append({
                        "cluster_id": i,
                        "nodes": list(component),
                        "size": len(component)
                    })
        
        return network
    
    def _extract_alternative_perspectives(self) -> List[Dict[str, Any]]:
        """Extract alternative perspectives from the graph"""
        perspectives = []
        
        # Group nodes by type and extract different viewpoints
        analysis_nodes = [node for node in self.nodes.values() if node.node_type == NodeType.ANALYSIS]
        evidence_nodes = [node for node in self.nodes.values() if node.node_type == NodeType.EVIDENCE]
        
        # Contradicting evidence as alternative perspectives
        contradicting_evidence = [
            node for node in evidence_nodes 
            if node.metadata.get("evidence_type") == "contradicting"
        ]
        
        for node in contradicting_evidence:
            perspectives.append({
                "type": "contradicting_evidence",
                "content": node.content,
                "confidence": node.confidence
            })
        
        # Creative analyses as alternative perspectives
        creative_analyses = [
            node for node in analysis_nodes
            if node.metadata.get("analysis_type") == "creative"
        ]
        
        for node in creative_analyses:
            perspectives.append({
                "type": "creative_analysis",
                "content": node.content,
                "confidence": node.confidence
            })
        
        return perspectives[:5]  # Limit to top 5 alternatives
    
    async def _call_model(self, model: Any, prompt: str) -> str:
        """Call the language model"""
        try:
            # This would integrate with the actual model calling logic
            # For now, simulate responses based on prompt type
            if "analysis" in prompt.lower():
                return """
Analysis 1: Logical analysis reveals systematic patterns and clear cause-effect relationships
Analysis 2: Creative analysis suggests innovative approaches and unconventional solutions
Analysis 3: Practical analysis focuses on implementation feasibility and resource requirements
"""
            elif "evidence" in prompt.lower():
                return """
Evidence 1: Supporting data shows positive correlation and validates the hypothesis
Evidence 2: Alternative viewpoint suggests different interpretation of the same data
"""
            elif "hypothesis" in prompt.lower():
                return """
Hypothesis 1: Testable hypothesis that can be validated through controlled experiments
Hypothesis 2: Exploratory hypothesis that opens new avenues for investigation
"""
            elif "synthesis" in prompt.lower():
                return "Synthesis: Integration of multiple perspectives reveals comprehensive understanding and actionable insights"
            elif "decision" in prompt.lower():
                return """
Decision: Proceed with the recommended approach based on comprehensive analysis
Rationale: Evidence strongly supports this direction with manageable risks
Confidence: 0.85
"""
            else:
                return "Analysis complete with positive results"
                
        except Exception as e:
            logger.error(f"Model call failed: {str(e)}")
            return "Error in model response"
    
    def get_graph_metrics(self) -> Dict[str, Any]:
        """Get graph analysis metrics"""
        if self.graph.number_of_nodes() == 0:
            return {}
        
        metrics = {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "average_clustering": nx.average_clustering(self.graph.to_undirected()),
            "reasoning_paths": len(self.reasoning_paths),
            "synthesis_nodes": len(self.synthesis_nodes)
        }
        
        # Node type distribution
        node_types = {}
        for node in self.nodes.values():
            node_type = node.node_type.value
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        metrics["node_type_distribution"] = node_types
        
        # Edge type distribution
        edge_types = {}
        for edge in self.edges.values():
            edge_type = edge.edge_type.value
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        metrics["edge_type_distribution"] = edge_types
        
        # Centrality measures
        if self.graph.number_of_nodes() > 1:
            centrality = nx.degree_centrality(self.graph)
            most_central_node = max(centrality, key=centrality.get)
            metrics["most_central_node"] = {
                "node_id": most_central_node,
                "centrality": centrality[most_central_node],
                "content": self.nodes[most_central_node].content[:100]
            }
        
        return metrics 