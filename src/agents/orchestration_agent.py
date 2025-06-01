# Orchestration Agent for OpenDistillery
# Manages multi-agent workflows and task coordination

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
import json
from dataclasses import dataclass, field

# Import base agent and core components
try:
    from ..base_agent import BaseAgent, AgentResponse
    from ...core.compound_system import ModelConfiguration, ModelRouter, CompoundAISystem
except ImportError:
    from src.agents.base_agent import BaseAgent, AgentResponse
    from src.core.compound_system import ModelConfiguration, ModelRouter, CompoundAISystem

logger = logging.getLogger(__name__)

@dataclass
class WorkflowState:
    workflow_id: str
    status: str = "initialized"
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class OrchestrationAgent(BaseAgent):
    def __init__(self, agent_id: str, models: Dict[str, ModelConfiguration], router: ModelRouter, system: CompoundAISystem):
        super().__init__(agent_id, models, router, system)
        self.capabilities = ["orchestration", "coordination", "workflow_management", "task_delegation"]
        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, WorkflowState] = {}
        self.context.state["active_workflows"] = 0

    async def _process_task_internal(self, task: Dict[str, Any]) -> AgentResponse:
        """Process orchestration tasks"""
        task_type = task.get("type", "workflow")
        
        logger.info(f"Orchestration agent {self.agent_id} processing {task_type} task")
        
        try:
            if task_type == "workflow":
                return await self._handle_workflow(task)
            elif task_type == "agent_registration":
                return await self._handle_agent_registration(task)
            elif task_type == "task_delegation":
                return await self._handle_task_delegation(task)
            elif task_type == "workflow_status":
                return await self._handle_workflow_status(task)
            else:
                return await self._handle_general_orchestration(task)
        except Exception as e:
            logger.error(f"Orchestration task failed for agent {self.agent_id}: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Orchestration error: {str(e)}",
                confidence=0.0,
                error=str(e),
                metadata={"task_type": task_type}
            )

    async def _handle_workflow(self, task: Dict[str, Any]) -> AgentResponse:
        """Handle workflow creation and execution"""
        from uuid import uuid4
        workflow_id = task.get("workflow_id", str(uuid4()))
        tasks = task.get("tasks", [])
        dependencies = task.get("dependencies", {})
        metadata = task.get("metadata", {})
        
        # Initialize workflow state
        workflow = WorkflowState(
            workflow_id=workflow_id,
            tasks=tasks,
            dependencies=dependencies,
            metadata=metadata
        )
        self.workflows[workflow_id] = workflow
        self.context.state["active_workflows"] = len(self.workflows)
        
        logger.info(f"Starting workflow {workflow_id} with {len(tasks)} tasks")
        
        # Execute workflow
        try:
            results = await self._execute_workflow(workflow)
            workflow.results = results
            workflow.status = "completed"
            workflow.progress = 1.0
            
            self.context.state["active_workflows"] = len([w for w in self.workflows.values() if w.status != "completed"])
            
            return AgentResponse(
                success=True,
                content={"workflow_id": workflow_id, "results": results},
                confidence=0.9,
                metadata={"task_count": len(tasks), "workflow_id": workflow_id}
            )
        except Exception as e:
            workflow.status = "failed"
            workflow.metadata["error"] = str(e)
            logger.error(f"Workflow {workflow_id} failed: {str(e)}")
            
            self.context.state["active_workflows"] = len([w for w in self.workflows.values() if w.status != "completed"])
            
            return AgentResponse(
                success=False,
                content=f"Workflow execution error: {str(e)}",
                confidence=0.0,
                error=str(e),
                metadata={"workflow_id": workflow_id}
            )

    async def _execute_workflow(self, workflow: WorkflowState) -> Dict[str, Any]:
        """Execute a workflow by resolving dependencies and delegating tasks"""
        tasks = workflow.tasks
        dependencies = workflow.dependencies
        results = {}
        completed_tasks = set()
        total_tasks = len(tasks)
        completed_count = 0
        
        while completed_count < total_tasks:
            tasks_to_run = []
            
            # Find tasks whose dependencies are all completed
            for i, task in enumerate(tasks):
                task_id = task.get("task_id", f"task_{i}")
                if task_id in completed_tasks:
                    continue
                
                deps = dependencies.get(task_id, [])
                if all(dep in completed_tasks for dep in deps):
                    tasks_to_run.append((task_id, task))
            
            if not tasks_to_run:
                raise Exception("Circular dependency detected or no tasks to run")
            
            # Execute tasks in parallel
            task_coroutines = []
            for task_id, task in tasks_to_run:
                coro = self._delegate_task(task_id, task, results)
                task_coroutines.append(coro)
            
            # Gather results
            task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)
            
            # Process results
            for (task_id, _), result in zip(tasks_to_run, task_results):
                if isinstance(result, Exception):
                    raise Exception(f"Task {task_id} failed: {str(result)}")
                results[task_id] = result.content
                completed_tasks.add(task_id)
                completed_count += 1
                workflow.progress = completed_count / total_tasks
                workflow.status = "running"
                logger.info(f"Task {task_id} completed ({completed_count}/{total_tasks})")
            
            # Update workflow state
            workflow.results = results
        
        return results

    async def _delegate_task(self, task_id: str, task: Dict[str, Any], previous_results: Dict[str, Any]) -> AgentResponse:
        """Delegate task to appropriate agent"""
        task_type = task.get("type", "general")
        required_capabilities = task.get("required_capabilities", [])
        agent_id = task.get("agent_id")
        
        if agent_id and agent_id in self.agents:
            agent = self.agents[agent_id]
        else:
            agent = self._find_suitable_agent(task_type, required_capabilities)
            if not agent:
                raise Exception(f"No suitable agent found for task {task_id} with capabilities {required_capabilities}")
        
        # Enrich task with context from previous results if needed
        if task.get("use_previous_results", False):
            task["context"] = task.get("context", {})
            task["context"]["previous_results"] = previous_results
        
        logger.info(f"Delegating task {task_id} to agent {agent.agent_id}")
        return await agent.process_task(task)

    def _find_suitable_agent(self, task_type: str, required_capabilities: List[str]) -> Optional[BaseAgent]:
        """Find agent suitable for the task based on capabilities"""
        for agent in self.agents.values():
            if not required_capabilities or all(cap in agent.capabilities for cap in required_capabilities):
                return agent
        return None

    async def _handle_agent_registration(self, task: Dict[str, Any]) -> AgentResponse:
        """Handle registration of other agents"""
        agent = task.get("agent")
        if not isinstance(agent, BaseAgent):
            return AgentResponse(
                success=False,
                content="Invalid agent provided for registration",
                confidence=0.0,
                error="Invalid agent type"
            )
        
        self.agents[agent.agent_id] = agent
        logger.info(f"Registered agent {agent.agent_id} with orchestration agent {self.agent_id}")
        return AgentResponse(
            success=True,
            content=f"Agent {agent.agent_id} registered successfully",
            confidence=0.9,
            metadata={"agent_count": len(self.agents)}
        )

    async def _handle_task_delegation(self, task: Dict[str, Any]) -> AgentResponse:
        """Handle direct task delegation to specific agent"""
        agent_id = task.get("agent_id")
        delegated_task = task.get("task", {})
        
        if agent_id not in self.agents:
            return AgentResponse(
                success=False,
                content=f"Agent {agent_id} not found",
                confidence=0.0,
                error="Agent not registered"
            )
        
        agent = self.agents[agent_id]
        logger.info(f"Delegating task directly to agent {agent_id}")
        result = await agent.process_task(delegated_task)
        return AgentResponse(
            success=result.success,
            content=result.content,
            confidence=result.confidence,
            metadata={"delegated_to": agent_id, "task_type": delegated_task.get("type", "unknown")}
        )

    async def _handle_workflow_status(self, task: Dict[str, Any]) -> AgentResponse:
        """Handle request for workflow status"""
        workflow_id = task.get("workflow_id")
        
        if workflow_id not in self.workflows:
            return AgentResponse(
                success=False,
                content=f"Workflow {workflow_id} not found",
                confidence=0.0,
                error="Workflow not found"
            )
        
        workflow = self.workflows[workflow_id]
        return AgentResponse(
            success=True,
            content={
                "workflow_id": workflow_id,
                "status": workflow.status,
                "progress": workflow.progress,
                "task_count": len(workflow.tasks),
                "completed_tasks": len(workflow.results),
                "metadata": workflow.metadata
            },
            confidence=0.9
        )

    async def _handle_general_orchestration(self, task: Dict[str, Any]) -> AgentResponse:
        """Handle general orchestration tasks"""
        action = task.get("action", "status")
        
        if action == "status":
            return AgentResponse(
                success=True,
                content={
                    "active_agents": len(self.agents),
                    "active_workflows": len([w for w in self.workflows.values() if w.status != "completed"]),
                    "total_workflows": len(self.workflows)
                },
                confidence=0.9
            )
        else:
            return AgentResponse(
                success=False,
                content=f"Unsupported orchestration action: {action}",
                confidence=0.0,
                error="Unsupported action"
            )

    async def shutdown(self):
        """Shut down orchestration agent and all managed agents"""
        logger.info(f"Shutting down orchestration agent {self.agent_id} and {len(self.agents)} managed agents")
        
        # Shut down all managed agents
        shutdown_tasks = []
        for agent in self.agents.values():
            shutdown_tasks.append(agent.shutdown())
        
        await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        
        # Shut down self
        await super().shutdown() 