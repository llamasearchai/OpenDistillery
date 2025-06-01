# Reasoning Agent for OpenDistillery
# Specialized agent for complex reasoning tasks

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
import json

# Import base agent and core components
try:
    from ..base_agent import BaseAgent, AgentResponse
    from ...core.compound_system import ModelConfiguration, ModelRouter, CompoundAISystem
    from ...research.techniques.react_engine import ReactEngine
    from ...research.techniques.tree_of_thoughts import TreeOfThoughts
    from ...research.techniques.graph_of_thoughts import GraphOfThoughts
except ImportError:
    from src.agents.base_agent import BaseAgent, AgentResponse
    from src.core.compound_system import ModelConfiguration, ModelRouter, CompoundAISystem
    from src.research.techniques.react_engine import ReactEngine
    from src.research.techniques.tree_of_thoughts import TreeOfThoughts
    from src.research.techniques.graph_of_thoughts import GraphOfThoughts

logger = logging.getLogger(__name__)

class ReasoningAgent(BaseAgent):
    def __init__(self, agent_id: str, models: Dict[str, ModelConfiguration], router: ModelRouter, system: CompoundAISystem):
        super().__init__(agent_id, models, router, system)
        self.capabilities = ["reasoning", "analysis", "problem_solving", "decision_making"]
        self.reasoning_engines = {
            "react": ReactEngine(models, router, system.mlx_processor),
            "tree_of_thoughts": TreeOfThoughts(models, router),
            "graph_of_thoughts": GraphOfThoughts(models, router)
        }
        self.context.state["reasoning_mode"] = "react"

    async def _process_task_internal(self, task: Dict[str, Any]) -> AgentResponse:
        """Process reasoning tasks using appropriate reasoning engine"""
        task_type = task.get("type", "reasoning")
        reasoning_mode = task.get("reasoning_mode", self.context.state.get("reasoning_mode", "react"))
        
        logger.info(f"Reasoning agent {self.agent_id} processing {task_type} task with {reasoning_mode} mode")
        
        try:
            if task_type == "complex_reasoning":
                return await self._handle_complex_reasoning(task, reasoning_mode)
            elif task_type == "decision_making":
                return await self._handle_decision_making(task, reasoning_mode)
            elif task_type == "problem_solving":
                return await self._handle_problem_solving(task, reasoning_mode)
            else:
                return await self._handle_general_reasoning(task, reasoning_mode)
        except Exception as e:
            logger.error(f"Reasoning task failed for agent {self.agent_id}: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Reasoning error: {str(e)}",
                confidence=0.0,
                error=str(e),
                metadata={"task_type": task_type, "reasoning_mode": reasoning_mode}
            )

    async def _handle_complex_reasoning(self, task: Dict[str, Any], reasoning_mode: str) -> AgentResponse:
        """Handle complex reasoning tasks"""
        engine = self.reasoning_engines.get(reasoning_mode)
        if not engine:
            engine = self.reasoning_engines["react"]
            reasoning_mode = "react"
        
        prompt = task.get("prompt", task.get("problem", ""))
        context = task.get("context", {})
        request = {"prompt": prompt, "context": context}
        
        try:
            if reasoning_mode == "react":
                result = await engine.execute(request)
            elif reasoning_mode == "tree_of_thoughts":
                result = await engine.solve(request)
            elif reasoning_mode == "graph_of_thoughts":
                result = await engine.process(request)
            else:
                result = await engine.execute(request)
            
            return AgentResponse(
                success=result.get("success", False),
                content=result.get("response", "No response generated"),
                confidence=result.get("confidence", 0.5),
                metadata={
                    "reasoning_mode": reasoning_mode,
                    "details": {
                        "iterations": result.get("iterations", 0),
                        "thought_process": result.get("history", result.get("thought_tree", result.get("thought_graph", {})))
                    }
                }
            )
        except Exception as e:
            logger.error(f"Complex reasoning failed: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Complex reasoning error: {str(e)}",
                confidence=0.0,
                error=str(e),
                metadata={"reasoning_mode": reasoning_mode}
            )

    async def _handle_decision_making(self, task: Dict[str, Any], reasoning_mode: str) -> AgentResponse:
        """Handle decision making tasks"""
        engine = self.reasoning_engines.get(reasoning_mode, self.reasoning_engines["react"])
        
        options = task.get("options", [])
        criteria = task.get("criteria", [])
        context = task.get("context", {})
        
        prompt = f"""
        I need to make a decision from the following options:
        {json.dumps(options, indent=2)}
        
        Based on these criteria:
        {json.dumps(criteria, indent=2)}
        
        Which option should I choose and why?
        """
        
        request = {"prompt": prompt, "context": context}
        
        try:
            if reasoning_mode == "react":
                result = await engine.execute(request)
            elif reasoning_mode == "tree_of_thoughts":
                result = await engine.solve(request)
            elif reasoning_mode == "graph_of_thoughts":
                result = await engine.process(request)
            else:
                result = await engine.execute(request)
            
            return AgentResponse(
                success=result.get("success", False),
                content=result.get("response", "No decision made"),
                confidence=result.get("confidence", 0.5),
                metadata={
                    "reasoning_mode": reasoning_mode,
                    "options_considered": len(options),
                    "criteria_used": len(criteria)
                }
            )
        except Exception as e:
            logger.error(f"Decision making failed: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Decision making error: {str(e)}",
                confidence=0.0,
                error=str(e),
                metadata={"reasoning_mode": reasoning_mode}
            )

    async def _handle_problem_solving(self, task: Dict[str, Any], reasoning_mode: str) -> AgentResponse:
        """Handle problem solving tasks"""
        engine = self.reasoning_engines.get(reasoning_mode, self.reasoning_engines["react"])
        
        problem = task.get("problem", task.get("prompt", ""))
        constraints = task.get("constraints", [])
        context = task.get("context", {})
        
        prompt = f"""
        I need to solve the following problem:
        {problem}
        
        Subject to these constraints:
        {json.dumps(constraints, indent=2)}
        
        Provide a detailed solution with step-by-step reasoning.
        """
        
        request = {"prompt": prompt, "context": context}
        
        try:
            if reasoning_mode == "react":
                result = await engine.execute(request)
            elif reasoning_mode == "tree_of_thoughts":
                result = await engine.solve(request)
            elif reasoning_mode == "graph_of_thoughts":
                result = await engine.process(request)
            else:
                result = await engine.execute(request)
            
            return AgentResponse(
                success=result.get("success", False),
                content=result.get("response", "No solution found"),
                confidence=result.get("confidence", 0.5),
                metadata={
                    "reasoning_mode": reasoning_mode,
                    "constraints_considered": len(constraints)
                }
            )
        except Exception as e:
            logger.error(f"Problem solving failed: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"Problem solving error: {str(e)}",
                confidence=0.0,
                error=str(e),
                metadata={"reasoning_mode": reasoning_mode}
            )

    async def _handle_general_reasoning(self, task: Dict[str, Any], reasoning_mode: str) -> AgentResponse:
        """Handle general reasoning tasks"""
        engine = self.reasoning_engines.get(reasoning_mode, self.reasoning_engines["react"])
        
        prompt = task.get("prompt", task.get("question", ""))
        context = task.get("context", {})
        
        request = {"prompt": prompt, "context": context}
        
        try:
            if reasoning_mode == "react":
                result = await engine.execute(request)
            elif reasoning_mode == "tree_of_thoughts":
                result = await engine.solve(request)
            elif reasoning_mode == "graph_of_thoughts":
                result = await engine.process(request)
            else:
                result = await engine.execute(request)
            
            return AgentResponse(
                success=result.get("success", False),
                content=result.get("response", "No response generated"),
                confidence=result.get("confidence", 0.5),
                metadata={"reasoning_mode": reasoning_mode}
            )
        except Exception as e:
            logger.error(f"General reasoning failed: {str(e)}")
            return AgentResponse(
                success=False,
                content=f"General reasoning error: {str(e)}",
                confidence=0.0,
                error=str(e),
                metadata={"reasoning_mode": reasoning_mode}
            )

    async def update_reasoning_mode(self, mode: str):
        """Update the reasoning mode to use"""
        if mode in self.reasoning_engines:
            self.context.state["reasoning_mode"] = mode
            logger.info(f"Updated reasoning mode for agent {self.agent_id} to {mode}")
            return True
        else:
            logger.warning(f"Invalid reasoning mode {mode} for agent {self.agent_id}")
            return False 