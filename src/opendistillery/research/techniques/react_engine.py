"""
ReAct (Reasoning + Acting) Engine
Implementation of the ReAct paradigm for combining reasoning and acting in AI systems.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import re

import structlog

# Import core components
try:
    from ....core.compound_system import ModelConfiguration, ModelRouter, MLXProcessor, ReasoningStrategy
except ImportError:
    from src.core.compound_system import ModelConfiguration, ModelRouter, MLXProcessor, ReasoningStrategy

logger = structlog.get_logger(__name__)

class ActionType(Enum):
    SEARCH = "search"
    CALCULATE = "calculate"
    ANALYZE = "analyze"
    SYNTHESIZE = "synthesize"
    VALIDATE = "validate"
    EXECUTE = "execute"
    OBSERVE = "observe"

@dataclass
class Thought:
    content: str
    reasoning: str = ""
    confidence: float = 0.5
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    source: str = "system"

@dataclass
class Action:
    action_type: str
    description: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    success: bool = False
    error: Optional[str] = None
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())

@dataclass
class Observation:
    content: str
    source: str
    relevance: float = 0.5
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    metadata: Dict[str, Any] = field(default_factory=dict)

class ReactEngine:
    """
    ReAct (Reasoning + Acting) Engine for intelligent problem solving
    """
    
    def __init__(self, models: Dict[str, ModelConfiguration], router: ModelRouter, mlx_processor: MLXProcessor):
        self.models = models
        self.router = router
        self.mlx_processor = mlx_processor
        self.max_iterations = 10
        self.thoughts: List[Thought] = []
        self.actions: List[Action] = []
        self.observations: List[Observation] = []
        self.state = "initial"
        
    async def execute(self, request: Dict[str, Any], max_iterations: Optional[int] = None) -> Dict[str, Any]:
        """Execute ReAct loop for request processing"""
        if max_iterations is not None:
            self.max_iterations = max_iterations
        
        # Initialize state
        self.thoughts = []
        self.actions = []
        self.observations = []
        self.state = "thinking"
        iteration = 0
        goal = request.get("prompt", request.get("goal", "Solve the given problem"))
        
        logger.info(f"Starting ReAct execution for goal: {goal}")
        
        # Initial thought
        initial_thought = Thought(
            content=f"I need to address: {goal}",
            reasoning="Initial problem statement",
            confidence=0.8
        )
        self.thoughts.append(initial_thought)
        
        # Add initial observation from request
        if "context" in request or "data" in request:
            content = json.dumps(request.get("context", request.get("data", {})))
            self.observations.append(Observation(
                content=content,
                source="user_input",
                relevance=0.9,
                metadata={"type": "initial_context"}
            ))
        
        # Main ReAct loop
        while iteration < self.max_iterations and self.state != "complete":
            iteration += 1
            logger.info(f"ReAct iteration {iteration}/{self.max_iterations}, state: {self.state}")
            
            if self.state == "thinking":
                await self._think(goal)
            elif self.state == "acting":
                await self._act()
            elif self.state == "observing":
                await self._observe()
            
            # Check for completion
            if self._check_completion(goal):
                self.state = "complete"
                logger.info("ReAct goal completed")
                break
        
        # Generate final response
        return self._format_response()

    async def _think(self, goal: str):
        """Generate thoughts and reasoning about current state"""
        # Build context from history
        context = self._build_context()
        
        # Formulate prompt for reasoning
        prompt = f"""
        I am solving: {goal}
        
        Current context and history:
        {context}
        
        What should be my next step? Think through this logically.
        1. Review what I know
        2. Identify gaps in my knowledge
        3. Determine if I need to take an action
        4. Decide on the best approach
        
        My reasoning:
        """
        
        # Route to appropriate model
        model = self.router.route_request({"task_type": "reasoning", "goal": goal}, list(self.models.values()))
        
        try:
            # Call model for reasoning
            response = await self._call_model(model, prompt, {})
            
            # Parse response into thought
            thought = Thought(
                content=response,
                reasoning="Model-generated reasoning",
                confidence=0.7,
                source=model.model_name
            )
            self.thoughts.append(thought)
            logger.info(f"Generated thought: {response[:100]}...")
            
            # Decide next state based on thought content
            if "action" in response.lower() or "need to" in response.lower():
                self.state = "acting"
            else:
                self.state = "observing"
        except Exception as e:
            logger.error(f"Thinking failed: {str(e)}")
            self.thoughts.append(Thought(
                content=f"Error in reasoning: {str(e)}",
                reasoning="Error",
                confidence=0.1
            ))
            self.state = "observing"

    async def _act(self):
        """Take an action based on current thought"""
        # Get latest thought
        if not self.thoughts:
            self.state = "thinking"
            return
        
        latest_thought = self.thoughts[-1].content
        
        # Build context
        context = self._build_context()
        
        # Formulate prompt for action
        prompt = f"""
        Based on my reasoning: {latest_thought}
        
        Current context:
        {context}
        
        I need to take an action. What specific action should I take?
        Describe the action and required inputs.
        """
        
        # Route to model
        model = self.router.route_request({"task_type": "action_planning"}, list(self.models.values()))
        
        try:
            # Get action plan from model
            response = await self._call_model(model, prompt, {})
            
            # Parse response - in a real system, this would extract structured action
            action = Action(
                action_type="analyze",
                description=response,
                input_data={"thought": latest_thought},
                success=False
            )
            
            # Execute action - in a real system, this would call tools/APIs
            action.result = {"output": f"Executed: {response[:50]}..."}
            action.success = True
            
            self.actions.append(action)
            logger.info(f"Executed action: {action.description[:100]}...")
            
            self.state = "observing"
        except Exception as e:
            logger.error(f"Action failed: {str(e)}")
            self.actions.append(Action(
                action_type="error",
                description="Failed to execute action",
                error=str(e)
            ))
            self.state = "thinking"

    async def _observe(self):
        """Observe results of actions and update knowledge"""
        # Build context
        context = self._build_context()
        
        # Get latest action result if available
        action_result = ""
        if self.actions:
            last_action = self.actions[-1]
            action_result = f"Last action: {last_action.description}\nResult: {last_action.result if last_action.result else 'pending'}"
        
        # Formulate observation prompt
        prompt = f"""
        Current context:
        {context}
        
        {action_result}
        
        What can I observe from the current state? What new information do I have?
        What is still missing to complete my goal?
        """
        
        # Route to model
        model = self.router.route_request({"task_type": "observation"}, list(self.models.values()))
        
        try:
            # Get observation from model
            response = await self._call_model(model, prompt, {})
            
            # Record observation
            observation = Observation(
                content=response,
                source=model.model_name,
                relevance=0.7,
                metadata={"iteration": len(self.thoughts)}
            )
            self.observations.append(observation)
            logger.info(f"Recorded observation: {response[:100]}...")
            
            self.state = "thinking"
        except Exception as e:
            logger.error(f"Observation failed: {str(e)}")
            self.observations.append(Observation(
                content=f"Error observing: {str(e)}",
                source="error",
                relevance=0.1
            ))
            self.state = "thinking"

    def _build_context(self) -> str:
        """Build context string from history"""
        context_parts = []
        
        # Add recent thoughts
        for i, thought in enumerate(self.thoughts[-3:]):
            context_parts.append(f"Thought {i+1}: {thought.content}")
        
        # Add recent actions
        for i, action in enumerate(self.actions[-2:]):
            context_parts.append(f"Action {i+1}: {action.description}")
            if action.result:
                context_parts.append(f"Result: {json.dumps(action.result)[:200]}...")
        
        # Add recent observations
        for i, obs in enumerate(self.observations[-3:]):
            context_parts.append(f"Observation {i+1}: {obs.content}")
        
        return "\n".join(context_parts) if context_parts else "No history yet"

    def _check_completion(self, goal: str) -> bool:
        """Check if goal is completed based on current state"""
        if not self.thoughts or not self.observations:
            return False
        
        latest_thought = self.thoughts[-1].content.lower()
        latest_observation = self.observations[-1].content.lower()
        
        completion_indicators = [
            "completed", "solved", "finished", "done", "resolved",
            "goal achieved", "problem solved", "task complete"
        ]
        
        for indicator in completion_indicators:
            if indicator in latest_thought or indicator in latest_observation:
                return True
        
        return False

    def _format_response(self) -> Dict[str, Any]:
        """Format final response from ReAct process"""
        summary = "Goal processing completed"
        if self.thoughts:
            summary = self.thoughts[-1].content[:200] + ("..." if len(self.thoughts[-1].content) > 200 else "")
        
        return {
            "success": self.state == "complete",
            "response": summary,
            "history": {
                "thoughts": [t.content for t in self.thoughts],
                "actions": [a.description for a in self.actions],
                "observations": [o.content for o in self.observations]
            },
            "state": self.state,
            "iterations": len(self.thoughts),
            "confidence": self.thoughts[-1].confidence if self.thoughts else 0.5
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
            elif model.provider == "local_mlx":
                result = await self.mlx_processor.process_local(model.model_name, {"prompt": prompt})
                response = result.get("response", "")
            else:
                raise ValueError(f"Unsupported provider: {model.provider}")
            
            return response
        except Exception as e:
            logger.error(f"Model call failed: {str(e)}")
            raise 