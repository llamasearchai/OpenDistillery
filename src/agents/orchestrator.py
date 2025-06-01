"""
OpenDistillery Agent Orchestrator
Advanced multi-agent orchestration system with intelligent task distribution,
collaboration patterns, and enterprise-grade performance optimization.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from datetime import datetime
from collections import defaultdict, deque
import threading
import networkx as nx
import numpy as np

from .base_agent import BaseAgent, AgentState, AgentCapability, CollaborationPattern
import structlog

logger = structlog.get_logger(__name__)

class OrchestrationStrategy(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    DEMOCRATIC = "democratic"
    EXPERT_ROUTING = "expert_routing"
    AUCTION_BASED = "auction_based"
    LOAD_BALANCED = "load_balanced"
    ADAPTIVE = "adaptive"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

@dataclass
class Task:
    """Represents a task in the orchestration system"""
    task_id: str
    task_type: str
    description: str
    input_data: Dict[str, Any]
    priority: TaskPriority = TaskPriority.MEDIUM
    required_capabilities: List[AgentCapability] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    deadline: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    
    def is_overdue(self) -> bool:
        """Check if task is past deadline"""
        return self.deadline is not None and time.time() > self.deadline

@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    agent_id: str
    success: bool
    result_data: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    confidence: float = 0.0
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_at: float = field(default_factory=time.time)

@dataclass
class AgentWorkload:
    """Tracks agent workload and performance"""
    agent_id: str
    current_tasks: List[str] = field(default_factory=list)
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_execution_time: float = 0.0
    success_rate: float = 1.0
    specialization_scores: Dict[str, float] = field(default_factory=dict)
    load_factor: float = 0.0
    last_activity: float = field(default_factory=time.time)

class CollaborationEngine:
    """Engine for managing agent collaboration patterns"""
    
    def __init__(self):
        self.collaboration_history: List[Dict[str, Any]] = []
        self.success_patterns: Dict[str, float] = {}
        
    async def execute_collaboration(self,
                                  task: Task,
                                  participating_agents: List[str],
                                  pattern: CollaborationPattern,
                                  agents: Dict[str, BaseAgent]) -> Dict[str, Any]:
        """Execute collaborative task using specified pattern"""
        collaboration_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Starting collaboration {collaboration_id} with pattern {pattern.value}")
        
        try:
            if pattern == CollaborationPattern.CONSENSUS:
                result = await self._execute_consensus(task, participating_agents, agents)
            elif pattern == CollaborationPattern.HIERARCHICAL:
                result = await self._execute_hierarchical(task, participating_agents, agents)
            elif pattern == CollaborationPattern.DELEGATION:
                result = await self._execute_delegation(task, participating_agents, agents)
            elif pattern == CollaborationPattern.AUCTION:
                result = await self._execute_auction(task, participating_agents, agents)
            else:
                result = await self._execute_peer_to_peer(task, participating_agents, agents)
            
            execution_time = time.time() - start_time
            
            # Record collaboration success
            self.collaboration_history.append({
                "collaboration_id": collaboration_id,
                "pattern": pattern.value,
                "agents": participating_agents,
                "success": result.get("success", False),
                "execution_time": execution_time,
                "task_type": task.task_type
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Collaboration {collaboration_id} failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "collaboration_id": collaboration_id
            }
    
    async def _execute_consensus(self, 
                               task: Task,
                               agents: List[str],
                               agent_instances: Dict[str, BaseAgent]) -> Dict[str, Any]:
        """Execute consensus-based collaboration"""
        # Execute task on all agents
        agent_results = []
        
        tasks = []
        for agent_id in agents:
            if agent_id in agent_instances:
                agent = agent_instances[agent_id]
                task_data = {
                    "type": "consensus_input",
                    "description": task.description,
                    "input_data": task.input_data,
                    "context": task.context
                }
                tasks.append(agent.execute_task(task_data))
        
        # Wait for all agents to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, dict) and result.get("success", False):
                result["agent_id"] = agents[i]
                valid_results.append(result)
        
        if not valid_results:
            return {"success": False, "error": "No valid results from consensus agents"}
        
        # Calculate consensus
        consensus_result = self._calculate_consensus(valid_results)
        
        return {
            "success": True,
            "consensus_result": consensus_result,
            "participating_agents": agents,
            "individual_results": valid_results,
            "consensus_confidence": consensus_result.get("confidence", 0.5)
        }
    
    def _calculate_consensus(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate consensus from multiple agent results"""
        if not results:
            return {}
        
        # Simple majority voting for categorical results
        # Weighted averaging for numerical results
        
        confidences = [r.get("result", {}).get("confidence", 0.5) for r in results]
        avg_confidence = np.mean(confidences)
        
        # For now, select result with highest confidence
        best_result = max(results, key=lambda x: x.get("result", {}).get("confidence", 0))
        
        return {
            "consensus_type": "confidence_weighted",
            "selected_result": best_result.get("result", {}),
            "confidence": avg_confidence,
            "agreement_level": len(results) / len(results),  # Simplified
            "contributing_agents": [r.get("agent_id") for r in results]
        }
    
    async def _execute_hierarchical(self, 
                                  task: Task,
                                  agents: List[str],
                                  agent_instances: Dict[str, BaseAgent]) -> Dict[str, Any]:
        """Execute hierarchical collaboration with leader-follower structure"""
        if not agents:
            return {"success": False, "error": "No agents provided"}
        
        # First agent is the leader
        leader_id = agents[0]
        followers = agents[1:]
        
        # Leader breaks down the task
        leader_agent = agent_instances.get(leader_id)
        if not leader_agent:
            return {"success": False, "error": f"Leader agent {leader_id} not found"}
        
        # Leader analyzes and delegates
        leader_task = {
            "type": "hierarchical_planning",
            "description": f"Plan and delegate: {task.description}",
            "input_data": task.input_data,
            "followers": followers,
            "context": task.context
        }
        
        leader_result = await leader_agent.execute_task(leader_task)
        
        if not leader_result.get("success", False):
            return leader_result
        
        # Execute follower tasks if any
        follower_results = []
        if followers:
            follower_tasks = []
            for follower_id in followers:
                if follower_id in agent_instances:
                    follower_agent = agent_instances[follower_id]
                    follower_task = {
                        "type": "hierarchical_execution",
                        "description": f"Execute as directed by {leader_id}",
                        "input_data": task.input_data,
                        "leader_guidance": leader_result.get("result", {}),
                        "context": task.context
                    }
                    follower_tasks.append(follower_agent.execute_task(follower_task))
            
            if follower_tasks:
                follower_results = await asyncio.gather(*follower_tasks, return_exceptions=True)
        
        return {
            "success": True,
            "hierarchical_result": {
                "leader": leader_id,
                "leader_result": leader_result,
                "followers": followers,
                "follower_results": [r for r in follower_results if isinstance(r, dict)]
            },
            "coordination_pattern": "hierarchical"
        }
    
    async def _execute_delegation(self, 
                                task: Task,
                                agents: List[str],
                                agent_instances: Dict[str, BaseAgent]) -> Dict[str, Any]:
        """Execute delegation-based collaboration"""
        # Divide task into subtasks for each agent
        subtasks = self._create_subtasks(task, len(agents))
        
        delegation_tasks = []
        for i, agent_id in enumerate(agents):
            if i < len(subtasks) and agent_id in agent_instances:
                agent = agent_instances[agent_id]
                subtask_data = {
                    "type": "delegated_subtask",
                    "description": subtasks[i]["description"],
                    "input_data": subtasks[i]["data"],
                    "parent_task": task.task_id,
                    "context": task.context
                }
                delegation_tasks.append(agent.execute_task(subtask_data))
        
        # Wait for all subtasks
        results = await asyncio.gather(*delegation_tasks, return_exceptions=True)
        
        # Aggregate results
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, dict) and result.get("success", False):
                result["agent_id"] = agents[i]
                result["subtask_index"] = i
                successful_results.append(result)
        
        # Combine subtask results
        combined_result = self._combine_subtask_results(successful_results, task)
        
        return {
            "success": len(successful_results) > 0,
            "delegation_result": combined_result,
            "subtasks_completed": len(successful_results),
            "total_subtasks": len(subtasks),
            "individual_results": successful_results
        }
    
    def _create_subtasks(self, task: Task, num_agents: int) -> List[Dict[str, Any]]:
        """Create subtasks for delegation"""
        # Simple subtask creation - could be enhanced with AI
        base_description = task.description
        
        subtasks = []
        for i in range(num_agents):
            subtasks.append({
                "description": f"Subtask {i+1}/{num_agents}: {base_description}",
                "data": task.input_data,
                "index": i
            })
        
        return subtasks
    
    def _combine_subtask_results(self, results: List[Dict[str, Any]], original_task: Task) -> Dict[str, Any]:
        """Combine results from subtasks"""
        if not results:
            return {"error": "No successful subtask results"}
        
        # Simple combination - average numerical results, concatenate text
        combined = {
            "subtask_count": len(results),
            "original_task": original_task.task_id,
            "combination_method": "simple_aggregation"
        }
        
        # Extract and combine result data
        all_result_data = [r.get("result", {}) for r in results]
        
        # Combine text outputs
        text_outputs = []
        for result_data in all_result_data:
            if isinstance(result_data, dict):
                for key, value in result_data.items():
                    if isinstance(value, str):
                        text_outputs.append(f"{key}: {value}")
        
        combined["combined_output"] = " | ".join(text_outputs)
        combined["contributing_agents"] = [r.get("agent_id") for r in results]
        
        return combined
    
    async def _execute_auction(self, 
                             task: Task,
                             agents: List[str],
                             agent_instances: Dict[str, BaseAgent]) -> Dict[str, Any]:
        """Execute auction-based collaboration"""
        # Agents bid on the task
        bids = []
        
        for agent_id in agents:
            if agent_id in agent_instances:
                agent = agent_instances[agent_id]
                
                # Agent evaluates task and provides bid
                bid_task = {
                    "type": "auction_bid",
                    "description": f"Evaluate and bid on: {task.description}",
                    "input_data": task.input_data,
                    "context": task.context
                }
                
                try:
                    bid_result = await agent.execute_task(bid_task)
                    if bid_result.get("success", False):
                        bid_data = bid_result.get("result", {})
                        bids.append({
                            "agent_id": agent_id,
                            "bid_score": bid_data.get("bid_score", 0.5),
                            "estimated_time": bid_data.get("estimated_time", 1.0),
                            "confidence": bid_data.get("confidence", 0.5),
                            "capabilities_match": bid_data.get("capabilities_match", 0.5)
                        })
                except Exception as e:
                    logger.warning(f"Agent {agent_id} failed to bid: {str(e)}")
        
        if not bids:
            return {"success": False, "error": "No valid bids received"}
        
        # Select winning bid (highest score)
        winning_bid = max(bids, key=lambda x: x["bid_score"])
        winner_id = winning_bid["agent_id"]
        
        # Execute task with winning agent
        winner_agent = agent_instances[winner_id]
        execution_result = await winner_agent.execute_task({
            "type": "auction_winner_execution",
            "description": task.description,
            "input_data": task.input_data,
            "context": task.context,
            "winning_bid": winning_bid
        })
        
        return {
            "success": execution_result.get("success", False),
            "auction_result": execution_result.get("result", {}),
            "winning_agent": winner_id,
            "winning_bid": winning_bid,
            "all_bids": bids,
            "auction_type": "highest_score"
        }
    
    async def _execute_peer_to_peer(self, 
                                  task: Task,
                                  agents: List[str],
                                  agent_instances: Dict[str, BaseAgent]) -> Dict[str, Any]:
        """Execute peer-to-peer collaboration"""
        # All agents work on task simultaneously and share results
        peer_tasks = []
        
        for agent_id in agents:
            if agent_id in agent_instances:
                agent = agent_instances[agent_id]
                peer_task = {
                    "type": "peer_collaboration",
                    "description": task.description,
                    "input_data": task.input_data,
                    "context": task.context,
                    "collaborating_peers": [aid for aid in agents if aid != agent_id]
                }
                peer_tasks.append(agent.execute_task(peer_task))
        
        # Execute all peer tasks
        results = await asyncio.gather(*peer_tasks, return_exceptions=True)
        
        # Process peer results
        peer_results = []
        for i, result in enumerate(results):
            if isinstance(result, dict) and result.get("success", False):
                result["agent_id"] = agents[i]
                peer_results.append(result)
        
        # Synthesize peer contributions
        synthesis = self._synthesize_peer_results(peer_results)
        
        return {
            "success": len(peer_results) > 0,
            "peer_results": synthesis,
            "participating_peers": [r.get("agent_id") for r in peer_results],
            "collaboration_type": "peer_to_peer"
        }
    
    def _synthesize_peer_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesize results from peer collaboration"""
        if not results:
            return {}
        
        # Calculate average confidence
        confidences = [r.get("result", {}).get("confidence", 0.5) for r in results]
        avg_confidence = np.mean(confidences)
        
        # Combine insights
        insights = []
        for result in results:
            result_data = result.get("result", {})
            if "insight" in result_data:
                insights.append(result_data["insight"])
            elif "output" in result_data:
                insights.append(result_data["output"])
        
        return {
            "synthesis_method": "peer_aggregation",
            "combined_insights": insights,
            "average_confidence": avg_confidence,
            "peer_count": len(results),
            "consensus_strength": len(results) / max(len(results), 1)
        }

class AgentOrchestrator:
    """
    Advanced orchestrator for managing multi-agent systems
    """
    
    def __init__(self, max_concurrent_tasks: int = 100):
        self.agents: Dict[str, BaseAgent] = {}
        self.task_queue: deque = deque()
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.agent_workloads: Dict[str, AgentWorkload] = {}
        
        # Core components
        self.collaboration_engine = CollaborationEngine()
        self.task_graph = nx.DiGraph()  # For dependency management
        
        # Configuration
        self.max_concurrent_tasks = max_concurrent_tasks
        self.default_strategy = OrchestrationStrategy.ADAPTIVE
        
        # Performance metrics
        self.orchestration_metrics = {
            "tasks_processed": 0,
            "average_task_time": 0.0,
            "success_rate": 1.0,
            "agent_utilization": 0.0,
            "collaboration_efficiency": 0.0
        }
        
        # Threading
        self.orchestration_lock = threading.RLock()
        self.background_tasks: Set[asyncio.Task] = set()
        
        logger.info("Agent orchestrator initialized")
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the orchestrator"""
        with self.orchestration_lock:
            self.agents[agent.agent_id] = agent
            self.agent_workloads[agent.agent_id] = AgentWorkload(agent_id=agent.agent_id)
            
            # Initialize specialization scores
            for capability in agent.capabilities:
                self.agent_workloads[agent.agent_id].specialization_scores[capability.value] = 0.5
        
        logger.info(f"Registered agent: {agent.agent_id}")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent"""
        with self.orchestration_lock:
            if agent_id in self.agents:
                # Reassign active tasks
                self._reassign_agent_tasks(agent_id)
                
                del self.agents[agent_id]
                del self.agent_workloads[agent_id]
        
        logger.info(f"Unregistered agent: {agent_id}")
    
    async def submit_task(self, task: Task) -> str:
        """Submit a task for orchestration"""
        # Add to task graph
        self.task_graph.add_node(task.task_id, task=task)
        
        # Add dependency edges
        for dep_id in task.dependencies:
            if dep_id in self.task_graph:
                self.task_graph.add_edge(dep_id, task.task_id)
        
        # Check if task can be executed immediately
        if self._can_execute_task(task):
            await self._schedule_task(task)
        else:
            self.task_queue.append(task)
            logger.info(f"Task {task.task_id} queued (waiting for dependencies)")
        
        return task.task_id
    
    async def _schedule_task(self, task: Task) -> None:
        """Schedule a task for execution"""
        # Select agents for the task
        selected_agents = self._select_agents_for_task(task)
        
        if not selected_agents:
            logger.error(f"No suitable agents for task {task.task_id}")
            self._mark_task_failed(task, "No suitable agents available")
            return
        
        # Add to active tasks
        self.active_tasks[task.task_id] = task
        
        # Execute task
        if len(selected_agents) == 1:
            await self._execute_single_agent_task(task, selected_agents[0])
        else:
            await self._execute_multi_agent_task(task, selected_agents)
    
    def _select_agents_for_task(self, task: Task) -> List[str]:
        """Select best agents for a task"""
        suitable_agents = []
        
        # Filter by capabilities
        for agent_id, agent in self.agents.items():
            if self._agent_can_handle_task(agent, task):
                suitable_agents.append(agent_id)
        
        if not suitable_agents:
            return []
        
        # Score and rank agents
        agent_scores = {}
        for agent_id in suitable_agents:
            score = self._calculate_agent_suitability_score(agent_id, task)
            agent_scores[agent_id] = score
        
        # Sort by score
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Determine how many agents to select
        if task.constraints.get("require_collaboration", False):
            # Multi-agent task
            return [agent_id for agent_id, _ in sorted_agents[:3]]
        else:
            # Single agent task
            return [sorted_agents[0][0]]
    
    def _agent_can_handle_task(self, agent: BaseAgent, task: Task) -> bool:
        """Check if agent can handle task"""
        # Check capabilities
        if task.required_capabilities:
            if not all(cap in agent.capabilities for cap in task.required_capabilities):
                return False
        
        # Check agent state
        if agent.state not in [AgentState.IDLE, AgentState.BUSY]:
            return False
        
        # Check workload
        workload = self.agent_workloads[agent.agent_id]
        if workload.load_factor > 0.9:  # Overloaded
            return False
        
        return True
    
    def _calculate_agent_suitability_score(self, agent_id: str, task: Task) -> float:
        """Calculate agent suitability score"""
        workload = self.agent_workloads[agent_id]
        agent = self.agents[agent_id]
        
        score = 0.0
        
        # Success rate (30%)
        score += workload.success_rate * 0.3
        
        # Capability match (25%)
        if task.required_capabilities:
            matching_caps = sum(1 for cap in task.required_capabilities if cap in agent.capabilities)
            capability_score = matching_caps / len(task.required_capabilities)
            score += capability_score * 0.25
        else:
            score += 0.25  # Default if no specific requirements
        
        # Specialization score (25%)
        task_type_score = workload.specialization_scores.get(task.task_type, 0.5)
        score += task_type_score * 0.25
        
        # Load factor (inverse - prefer less loaded agents) (20%)
        load_score = (1.0 - workload.load_factor) * 0.2
        score += load_score
        
        return score
    
    async def _execute_single_agent_task(self, task: Task, agent_id: str) -> None:
        """Execute task with single agent"""
        agent = self.agents[agent_id]
        workload = self.agent_workloads[agent_id]
        
        # Update workload
        workload.current_tasks.append(task.task_id)
        workload.load_factor = len(workload.current_tasks) / 5.0  # Assume max 5 concurrent
        workload.last_activity = time.time()
        
        try:
            start_time = time.time()
            
            # Execute task
            task_data = {
                "type": task.task_type,
                "description": task.description,
                "input_data": task.input_data,
                "context": task.context
            }
            
            result = await agent.execute_task(task_data, task.context)
            execution_time = time.time() - start_time
            
            # Create task result
            task_result = TaskResult(
                task_id=task.task_id,
                agent_id=agent_id,
                success=result.get("success", True),
                result_data=result.get("result", {}),
                execution_time=execution_time,
                confidence=result.get("confidence", 0.8)
            )
            
            # Update metrics
            self._update_agent_performance(agent_id, task, task_result)
            self._complete_task(task, task_result)
            
        except Exception as e:
            logger.error(f"Single agent task failed: {str(e)}")
            task_result = TaskResult(
                task_id=task.task_id,
                agent_id=agent_id,
                success=False,
                error_message=str(e),
                execution_time=time.time() - start_time
            )
            self._update_agent_performance(agent_id, task, task_result)
            self._complete_task(task, task_result)
        
        finally:
            # Clean up workload
            workload.current_tasks.remove(task.task_id)
            workload.load_factor = len(workload.current_tasks) / 5.0
    
    async def _execute_multi_agent_task(self, task: Task, agent_ids: List[str]) -> None:
        """Execute task with multiple agents"""
        # Determine collaboration pattern
        pattern = CollaborationPattern.CONSENSUS
        if task.constraints.get("collaboration_pattern"):
            pattern = CollaborationPattern(task.constraints["collaboration_pattern"])
        
        # Execute collaboration
        try:
            result = await self.collaboration_engine.execute_collaboration(
                task, agent_ids, pattern, self.agents
            )
            
            # Create consolidated result
            task_result = TaskResult(
                task_id=task.task_id,
                agent_id=",".join(agent_ids),
                success=result.get("success", False),
                result_data=result,
                confidence=result.get("confidence", 0.5),
                metadata={"collaboration_pattern": pattern.value}
            )
            
            # Update all participating agents
            for agent_id in agent_ids:
                self._update_agent_performance(agent_id, task, task_result)
            
            self._complete_task(task, task_result)
            
        except Exception as e:
            logger.error(f"Multi-agent task failed: {str(e)}")
            task_result = TaskResult(
                task_id=task.task_id,
                agent_id=",".join(agent_ids),
                success=False,
                error_message=str(e)
            )
            self._complete_task(task, task_result)
    
    def _complete_task(self, task: Task, result: TaskResult) -> None:
        """Mark task as completed"""
        # Move from active to completed
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]
        
        self.completed_tasks[task.task_id] = result
        
        # Update orchestration metrics
        self._update_orchestration_metrics(result)
        
        # Check for dependent tasks
        self._check_dependent_tasks(task.task_id)
        
        logger.info(f"Task {task.task_id} completed: {result.success}")
    
    def _update_agent_performance(self, agent_id: str, task: Task, result: TaskResult) -> None:
        """Update agent performance metrics"""
        workload = self.agent_workloads[agent_id]
        
        if result.success:
            workload.completed_tasks += 1
        else:
            workload.failed_tasks += 1
        
        # Update success rate
        total_tasks = workload.completed_tasks + workload.failed_tasks
        workload.success_rate = workload.completed_tasks / total_tasks
        
        # Update average execution time
        current_avg = workload.average_execution_time
        workload.average_execution_time = (
            (current_avg * (total_tasks - 1) + result.execution_time) / total_tasks
        )
        
        # Update specialization scores
        if task.task_type in workload.specialization_scores:
            current_score = workload.specialization_scores[task.task_type]
            adjustment = 0.1 if result.success else -0.05
            workload.specialization_scores[task.task_type] = max(0.0, min(1.0, current_score + adjustment))
    
    def _update_orchestration_metrics(self, result: TaskResult) -> None:
        """Update orchestration metrics"""
        self.orchestration_metrics["tasks_processed"] += 1
        
        # Update success rate
        total_tasks = self.orchestration_metrics["tasks_processed"]
        current_rate = self.orchestration_metrics["success_rate"]
        success_value = 1.0 if result.success else 0.0
        self.orchestration_metrics["success_rate"] = (
            (current_rate * (total_tasks - 1) + success_value) / total_tasks
        )
        
        # Update average task time
        current_avg = self.orchestration_metrics["average_task_time"]
        self.orchestration_metrics["average_task_time"] = (
            (current_avg * (total_tasks - 1) + result.execution_time) / total_tasks
        )
    
    def _check_dependent_tasks(self, completed_task_id: str) -> None:
        """Check and schedule dependent tasks"""
        dependent_tasks = []
        
        for successor in self.task_graph.successors(completed_task_id):
            task = self.task_graph.nodes[successor]["task"]
            if self._can_execute_task(task):
                dependent_tasks.append(task)
        
        # Schedule dependent tasks
        for task in dependent_tasks:
            if task in self.task_queue:
                self.task_queue.remove(task)
            # Schedule asynchronously
            background_task = asyncio.create_task(self._schedule_task(task))
            self.background_tasks.add(background_task)
            background_task.add_done_callback(self.background_tasks.discard)
    
    def _can_execute_task(self, task: Task) -> bool:
        """Check if task dependencies are met"""
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
            # Check if dependency was successful
            dep_result = self.completed_tasks[dep_id]
            if not dep_result.success and task.constraints.get("strict_dependencies", True):
                return False
        return True
    
    def _mark_task_failed(self, task: Task, error_message: str) -> None:
        """Mark task as failed"""
        result = TaskResult(
            task_id=task.task_id,
            agent_id="orchestrator",
            success=False,
            error_message=error_message
        )
        self.completed_tasks[task.task_id] = result
        self._update_orchestration_metrics(result)
    
    def _reassign_agent_tasks(self, agent_id: str) -> None:
        """Reassign tasks from removed agent"""
        workload = self.agent_workloads.get(agent_id)
        if not workload:
            return
        
        tasks_to_reassign = []
        for task_id in workload.current_tasks:
            if task_id in self.active_tasks:
                tasks_to_reassign.append(self.active_tasks[task_id])
        
        for task in tasks_to_reassign:
            del self.active_tasks[task.task_id]
            self.task_queue.append(task)
        
        logger.info(f"Reassigned {len(tasks_to_reassign)} tasks from agent {agent_id}")
    
    def get_orchestration_status(self) -> Dict[str, Any]:
        """Get comprehensive orchestration status"""
        return {
            "agents": {
                "total": len(self.agents),
                "active": len([a for a in self.agents.values() if a.state == AgentState.IDLE or a.state == AgentState.BUSY]),
                "by_type": self._get_agent_type_distribution()
            },
            "tasks": {
                "queued": len(self.task_queue),
                "active": len(self.active_tasks),
                "completed": len(self.completed_tasks)
            },
            "performance": self.orchestration_metrics,
            "workload_distribution": self._get_workload_distribution(),
            "collaboration_stats": self._get_collaboration_stats()
        }
    
    def _get_agent_type_distribution(self) -> Dict[str, int]:
        """Get distribution of agent types"""
        distribution = {}
        for agent in self.agents.values():
            agent_type = agent.agent_type
            distribution[agent_type] = distribution.get(agent_type, 0) + 1
        return distribution
    
    def _get_workload_distribution(self) -> Dict[str, Any]:
        """Get workload distribution across agents"""
        if not self.agent_workloads:
            return {}
        
        loads = [w.load_factor for w in self.agent_workloads.values()]
        success_rates = [w.success_rate for w in self.agent_workloads.values()]
        
        return {
            "average_load": np.mean(loads),
            "max_load": np.max(loads),
            "min_load": np.min(loads),
            "load_std": np.std(loads),
            "average_success_rate": np.mean(success_rates),
            "agent_count": len(self.agent_workloads)
        }
    
    def _get_collaboration_stats(self) -> Dict[str, Any]:
        """Get collaboration statistics"""
        history = self.collaboration_engine.collaboration_history
        
        if not history:
            return {"total_collaborations": 0}
        
        successful = [c for c in history if c.get("success", False)]
        patterns = [c.get("pattern") for c in history]
        
        return {
            "total_collaborations": len(history),
            "successful_collaborations": len(successful),
            "success_rate": len(successful) / len(history),
            "patterns_used": dict([(p, patterns.count(p)) for p in set(patterns)]),
            "average_execution_time": np.mean([c.get("execution_time", 0) for c in history])
        }
    
    async def shutdown(self) -> None:
        """Graceful shutdown of orchestrator"""
        logger.info("Shutting down orchestrator...")
        
        # Cancel background tasks
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
        
        # Shutdown all agents
        for agent in self.agents.values():
            await agent.shutdown()
        
        logger.info("Orchestrator shutdown complete")