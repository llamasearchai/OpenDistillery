"""
OpenDistillery DSPy Integration
Advanced integration with DSPy framework for systematic prompt optimization
and compound AI system development with latest models (2025)
"""

import dspy
from typing import Dict, Any, List, Optional, Union, Type
from dataclasses import dataclass, field
import logging
import asyncio
from datetime import datetime
import json
import numpy as np
from enum import Enum

from .multi_provider_api import MultiProviderAPI, OpenAIModel, AnthropicModel, XAIModel

logger = logging.getLogger(__name__)

class DSPyModel(Enum):
    """DSPy compatible models with latest 2025 models"""
    # OpenAI Latest
    O4 = "o4"
    O4_MINI = "o4-mini"
    O3 = "o3"
    O3_MINI = "o3-mini"
    O1 = "o1"
    O1_MINI = "o1-mini"
    GPT_4_1 = "gpt-4.1"
    GPT_4_1_TURBO = "gpt-4.1-turbo"
    
    # Anthropic Latest
    CLAUDE_4_OPUS = "claude-4-opus"
    CLAUDE_4_SONNET = "claude-4-sonnet"
    CLAUDE_3_5_SONNET = "claude-3.5-sonnet"
    
    # xAI Latest
    GROK_3 = "grok-3"
    GROK_3_BETA = "grok-3-beta"

@dataclass
class DSPyConfig:
    """Configuration for DSPy integration"""
    model: str = "o4"
    temperature: float = 0.1
    max_tokens: int = 4096
    provider: str = "openai"
    reasoning_mode: bool = True
    optimization_metric: str = "accuracy"
    cache_enabled: bool = True
    trace_enabled: bool = True

class OpenDistilleryDSPyLM(dspy.LM):
    """
    Custom DSPy Language Model wrapper for OpenDistillery
    Supports latest 2025 models with advanced reasoning capabilities
    """
    
    def __init__(
        self,
        model: str = "o4",
        provider: str = "openai",
        api_key: Optional[str] = None,
        **kwargs
    ):
        self.model = model
        self.provider = provider
        self.api_client = MultiProviderAPI()
        self.kwargs = kwargs
        
        # DSPy configuration
        super().__init__(model, temperature=1.0, max_tokens=20000)
        
        # Performance tracking
        self.request_count = 0
        self.total_tokens = 0
        self.reasoning_traces = []
    
    def __call__(self, prompt: str, **kwargs) -> str:
        """Synchronous interface for DSPy compatibility"""
        return asyncio.run(self.acall(prompt, **kwargs))
    
    async def acall(self, prompt: str, **kwargs) -> str:
        """Async call to the language model"""
        merged_kwargs = {**self.kwargs, **kwargs}
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = await self.api_client.chat_completion(
                messages=messages,
                model=self.model,
                **merged_kwargs
            )
            
            self.request_count += 1
            self.total_tokens += response.usage.get("total_tokens", 0)
            
            # Store reasoning traces for optimization
            if response.reasoning_steps:
                self.reasoning_traces.append({
                    "prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                    "reasoning": response.reasoning_steps,
                    "confidence": response.confidence_score,
                    "model": self.model
                })
            
            return response.content
            
        except Exception as e:
            logger.error(f"DSPy LM call failed: {e}")
            return f"Error: {str(e)}"
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "requests": self.request_count,
            "total_tokens": self.total_tokens,
            "avg_tokens_per_request": self.total_tokens / max(1, self.request_count),
            "reasoning_traces": len(self.reasoning_traces)
        }

class ReasoningChainOfThought(dspy.Module):
    """
    Advanced Chain of Thought module with reasoning optimization
    """
    
    def __init__(self, model: str = "o4"):
        super().__init__()
        self.model = model
        self.cot = dspy.ChainOfThought("question -> reasoning -> answer")
        
    def forward(self, question: str) -> dspy.Prediction:
        """Forward pass with enhanced reasoning"""
        reasoning_prompt = f"""
        Question: {question}
        
        Think through this step by step, showing your reasoning process.
        For complex problems, break them down into smaller components.
        Validate your logic at each step before proceeding.
        
        Provide your reasoning and final answer.
        """
        
        prediction = self.cot(question=reasoning_prompt)
        
        # Enhanced with confidence scoring
        confidence = self._calculate_reasoning_confidence(prediction.reasoning)
        prediction.confidence = confidence
        
        return prediction
    
    def _calculate_reasoning_confidence(self, reasoning: str) -> float:
        """Calculate confidence based on reasoning quality"""
        if not reasoning:
            return 0.3
        
        # Quality indicators
        quality_indicators = [
            len(reasoning.split()) > 50,  # Sufficient detail
            "step" in reasoning.lower(),  # Step-by-step approach
            "because" in reasoning.lower() or "therefore" in reasoning.lower(),  # Causal reasoning
            "consider" in reasoning.lower() or "analyze" in reasoning.lower(),  # Analysis
            reasoning.count(".") > 3  # Multiple sentences
        ]
        
        base_confidence = 0.5
        confidence_boost = sum(quality_indicators) * 0.1
        
        return min(1.0, base_confidence + confidence_boost)

class TreeOfThoughtsDSPy(dspy.Module):
    """
    Tree of Thoughts implementation using DSPy framework
    """
    
    def __init__(self, model: str = "o4", max_depth: int = 3, branching_factor: int = 3):
        super().__init__()
        self.model = model
        self.max_depth = max_depth
        self.branching_factor = branching_factor
        self.thought_generator = dspy.Predict("problem -> thoughts")
        self.thought_evaluator = dspy.Predict("thought -> score")
        self.solution_synthesizer = dspy.Predict("thoughts -> solution")
    
    def forward(self, problem: str) -> dspy.Prediction:
        """Forward pass through tree of thoughts"""
        thought_tree = self._build_thought_tree(problem)
        best_path = self._find_best_path(thought_tree)
        solution = self._synthesize_solution(best_path)
        
        return dspy.Prediction(
            solution=solution,
            thought_tree=thought_tree,
            best_path=best_path,
            confidence=self._calculate_path_confidence(best_path)
        )
    
    def _build_thought_tree(self, problem: str, depth: int = 0) -> Dict:
        """Recursively build tree of thoughts"""
        if depth >= self.max_depth:
            return {"thought": problem, "score": 0.5, "children": []}
        
        # Generate thoughts at current level
        thought_prompt = f"""
        Problem: {problem}
        Generate {self.branching_factor} different approaches or perspectives to solve this.
        Each should explore a distinct angle or methodology.
        """
        
        thoughts_result = self.thought_generator(problem=thought_prompt)
        thoughts = self._parse_thoughts(thoughts_result.thoughts)
        
        # Evaluate and expand each thought
        children = []
        for thought in thoughts:
            score_result = self.thought_evaluator(thought=thought)
            score = self._parse_score(score_result.score)
            
            child_tree = {
                "thought": thought,
                "score": score,
                "children": []
            }
            
            # Recursively expand promising thoughts
            if score > 0.6 and depth < self.max_depth - 1:
                child_tree["children"] = [self._build_thought_tree(thought, depth + 1)]
            
            children.append(child_tree)
        
        return {
            "thought": problem,
            "score": 1.0,
            "children": children
        }
    
    def _parse_thoughts(self, thoughts_text: str) -> List[str]:
        """Parse generated thoughts from text"""
        lines = thoughts_text.strip().split('\n')
        thoughts = []
        for line in lines:
            if line.strip() and (line.strip().startswith(('-', '*', '1.', '2.', '3.'))):
                thought = line.strip().lstrip('-*123. ')
                if thought:
                    thoughts.append(thought)
        return thoughts[:self.branching_factor]
    
    def _parse_score(self, score_text: str) -> float:
        """Parse score from text"""
        try:
            # Extract number from text
            import re
            numbers = re.findall(r'0\.\d+|1\.0|0|1', score_text)
            if numbers:
                return float(numbers[0])
        except:
            pass
        return 0.5
    
    def _find_best_path(self, tree: Dict) -> List[Dict]:
        """Find highest scoring path through tree"""
        def get_path_score(path: List[Dict]) -> float:
            return sum(node["score"] for node in path) / len(path)
        
        def get_all_paths(node: Dict, current_path: List[Dict] = None) -> List[List[Dict]]:
            if current_path is None:
                current_path = []
            
            current_path = current_path + [node]
            
            if not node["children"]:
                return [current_path]
            
            all_paths = []
            for child in node["children"]:
                child_paths = get_all_paths(child, current_path)
                all_paths.extend(child_paths)
            
            return all_paths
        
        all_paths = get_all_paths(tree)
        return max(all_paths, key=get_path_score) if all_paths else [tree]
    
    def _synthesize_solution(self, path: List[Dict]) -> str:
        """Synthesize solution from thought path"""
        path_thoughts = [node["thought"] for node in path]
        synthesis_prompt = f"""
        Thought progression:
        {chr(10).join([f"Level {i}: {thought}" for i, thought in enumerate(path_thoughts)])}
        
        Synthesize these thoughts into a coherent, comprehensive solution.
        """
        
        result = self.solution_synthesizer(thoughts=synthesis_prompt)
        return result.solution
    
    def _calculate_path_confidence(self, path: List[Dict]) -> float:
        """Calculate confidence for the selected path"""
        if not path:
            return 0.0
        
        scores = [node["score"] for node in path]
        return sum(scores) / len(scores)

class MetaPromptOptimizer(dspy.Module):
    """
    Meta-prompt optimization using DSPy's built-in optimizers
    """
    
    def __init__(self, model: str = "o4", optimization_strategy: str = "bootstrap"):
        super().__init__()
        self.model = model
        self.optimization_strategy = optimization_strategy
        self.base_module = ReasoningChainOfThought(model)
        
    def optimize(
        self,
        trainset: List[dspy.Example],
        valset: Optional[List[dspy.Example]] = None,
        metric: Optional[callable] = None
    ) -> dspy.Module:
        """Optimize the module using DSPy optimizers"""
        
        if metric is None:
            metric = self._default_metric
        
        # Configure DSPy with our model
        lm = OpenDistilleryDSPyLM(model=self.model)
        dspy.configure(lm=lm)
        
        # Select optimizer based on strategy
        if self.optimization_strategy == "bootstrap":
            optimizer = dspy.BootstrapFewShot(
                metric=metric,
                max_bootstrapped_demos=8,
                max_labeled_demos=4
            )
        elif self.optimization_strategy == "copro":
            optimizer = dspy.COPRO(
                metric=metric,
                depth=3,
                breadth=10
            )
        elif self.optimization_strategy == "mipro":
            optimizer = dspy.MIPRO(
                metric=metric,
                num_candidates=10,
                init_temperature=1.0
            )
        else:
            raise ValueError(f"Unknown optimization strategy: {self.optimization_strategy}")
        
        # Compile the optimized module
        optimized_module = optimizer.compile(
            self.base_module,
            trainset=trainset,
            valset=valset
        )
        
        return optimized_module
    
    def _default_metric(self, example: dspy.Example, prediction: dspy.Prediction) -> float:
        """Default evaluation metric"""
        try:
            # Simple exact match for demonstration
            if hasattr(example, 'answer') and hasattr(prediction, 'answer'):
                return float(example.answer.lower().strip() == prediction.answer.lower().strip())
            
            # Fallback to confidence if available
            if hasattr(prediction, 'confidence'):
                return prediction.confidence
            
            return 0.5
        except:
            return 0.0

class CompoundReasoningSystem(dspy.Module):
    """
    Compound reasoning system combining multiple DSPy modules
    """
    
    def __init__(self, models: List[str] = None):
        super().__init__()
        
        if models is None:
            models = ["o4", "claude-4-sonnet", "grok-3"]
        
        self.models = models
        self.reasoning_modules = {}
        
        # Initialize reasoning modules for each model
        for model in models:
            self.reasoning_modules[model] = ReasoningChainOfThought(model)
        
        self.ensemble_synthesizer = dspy.Predict("predictions -> final_answer")
    
    def forward(self, question: str) -> dspy.Prediction:
        """Forward pass through compound reasoning system"""
        
        # Get predictions from all models
        predictions = {}
        for model in self.models:
            try:
                pred = self.reasoning_modules[model](question)
                predictions[model] = {
                    "answer": pred.answer,
                    "reasoning": pred.reasoning,
                    "confidence": getattr(pred, 'confidence', 0.7)
                }
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
                predictions[model] = {
                    "answer": "Error in reasoning",
                    "reasoning": f"Model {model} encountered an error",
                    "confidence": 0.1
                }
        
        # Ensemble the predictions
        ensemble_input = self._format_ensemble_input(predictions)
        final_prediction = self.ensemble_synthesizer(predictions=ensemble_input)
        
        # Calculate ensemble confidence
        confidences = [pred["confidence"] for pred in predictions.values()]
        ensemble_confidence = np.mean(confidences) * (1 + 0.1 * len(confidences))  # Bonus for agreement
        
        return dspy.Prediction(
            answer=final_prediction.final_answer,
            individual_predictions=predictions,
            ensemble_confidence=min(1.0, ensemble_confidence),
            models_used=self.models
        )
    
    def _format_ensemble_input(self, predictions: Dict[str, Dict]) -> str:
        """Format predictions for ensemble synthesis"""
        formatted = "Multiple AI models have analyzed the question:\n\n"
        
        for model, pred in predictions.items():
            formatted += f"Model {model} (confidence: {pred['confidence']:.2f}):\n"
            formatted += f"Answer: {pred['answer']}\n"
            formatted += f"Reasoning: {pred['reasoning'][:200]}...\n\n"
        
        formatted += "Synthesize these predictions into the most accurate final answer."
        
        return formatted

class DSPyIntegrationManager:
    """
    Manager for DSPy integration with OpenDistillery
    """
    
    def __init__(self, config: DSPyConfig = None):
        self.config = config or DSPyConfig()
        self.modules = {}
        self.optimizers = {}
        self.performance_metrics = {}
        
        # Initialize DSPy with our custom LM
        self.lm = OpenDistilleryDSPyLM(
            model=self.config.model,
            provider=self.config.provider,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        dspy.configure(lm=self.lm)
    
    def create_reasoning_module(
        self,
        module_type: str = "chain_of_thought",
        **kwargs
    ) -> dspy.Module:
        """Create a reasoning module"""
        
        if module_type == "chain_of_thought":
            module = ReasoningChainOfThought(self.config.model)
        elif module_type == "tree_of_thoughts":
            module = TreeOfThoughtsDSPy(self.config.model, **kwargs)
        elif module_type == "compound_reasoning":
            module = CompoundReasoningSystem(**kwargs)
        else:
            raise ValueError(f"Unknown module type: {module_type}")
        
        module_id = f"{module_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.modules[module_id] = module
        
        return module
    
    def optimize_module(
        self,
        module: dspy.Module,
        training_data: List[Dict],
        validation_data: Optional[List[Dict]] = None,
        optimization_strategy: str = "bootstrap"
    ) -> dspy.Module:
        """Optimize a module using DSPy optimizers"""
        
        # Convert training data to DSPy examples
        trainset = [
            dspy.Example(question=item["question"], answer=item["answer"])
            for item in training_data
        ]
        
        valset = None
        if validation_data:
            valset = [
                dspy.Example(question=item["question"], answer=item["answer"])
                for item in validation_data
            ]
        
        optimizer = MetaPromptOptimizer(
            self.config.model,
            optimization_strategy
        )
        
        optimized_module = optimizer.optimize(trainset, valset)
        
        # Store optimization results
        optimizer_id = f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.optimizers[optimizer_id] = {
            "original_module": module,
            "optimized_module": optimized_module,
            "training_size": len(trainset),
            "validation_size": len(valset) if valset else 0,
            "strategy": optimization_strategy
        }
        
        return optimized_module
    
    def evaluate_module(
        self,
        module: dspy.Module,
        test_data: List[Dict],
        metrics: List[str] = None
    ) -> Dict[str, float]:
        """Evaluate a module's performance"""
        
        if metrics is None:
            metrics = ["accuracy", "confidence"]
        
        results = {"accuracy": 0.0, "confidence": 0.0, "latency": 0.0}
        
        correct_predictions = 0
        total_confidence = 0.0
        total_latency = 0.0
        
        for item in test_data:
            start_time = datetime.now()
            
            try:
                prediction = module(item["question"])
                
                # Calculate latency
                latency = (datetime.now() - start_time).total_seconds()
                total_latency += latency
                
                # Check accuracy
                if hasattr(prediction, 'answer'):
                    predicted_answer = prediction.answer.lower().strip()
                    correct_answer = item["answer"].lower().strip()
                    if predicted_answer == correct_answer:
                        correct_predictions += 1
                
                # Get confidence
                confidence = getattr(prediction, 'confidence', 0.5)
                total_confidence += confidence
                
            except Exception as e:
                logger.error(f"Evaluation error: {e}")
                total_latency += 1.0  # Penalty for errors
        
        # Calculate final metrics
        num_samples = len(test_data)
        results["accuracy"] = correct_predictions / num_samples
        results["confidence"] = total_confidence / num_samples
        results["latency"] = total_latency / num_samples
        
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "config": {
                "model": self.config.model,
                "provider": self.config.provider,
                "temperature": self.config.temperature
            },
            "modules": {
                "count": len(self.modules),
                "types": list(set(mid.split('_')[0] for mid in self.modules.keys()))
            },
            "optimizers": {
                "count": len(self.optimizers),
                "strategies": list(set(opt["strategy"] for opt in self.optimizers.values()))
            },
            "lm_stats": self.lm.get_usage_stats(),
            "timestamp": datetime.now().isoformat()
        }

# Global DSPy integration instance
# Global DSPy integration instance (initialized on first use)
dspy_integration = None

def get_dspy_integration():
    """Get or create global DSPy integration instance"""
    global dspy_integration
    if dspy_integration is None:
        dspy_integration = DSPyIntegrationManager()
    return dspy_integration

# Convenience functions for common operations
async def create_optimized_reasoning_chain(
    training_data: List[Dict],
    model: str = "o4",
    optimization_strategy: str = "bootstrap"
) -> dspy.Module:
    """Create and optimize a reasoning chain"""
    
    # Configure with specific model
    config = DSPyConfig(model=model)
    manager = DSPyIntegrationManager(config)
    
    # Create base module
    base_module = manager.create_reasoning_module("chain_of_thought")
    
    # Optimize with training data
    optimized_module = manager.optimize_module(
        base_module,
        training_data,
        optimization_strategy=optimization_strategy
    )
    
    return optimized_module

async def evaluate_reasoning_performance(
    module: dspy.Module,
    test_data: List[Dict]
) -> Dict[str, float]:
    """Evaluate reasoning module performance"""
    
    manager = DSPyIntegrationManager()
    return manager.evaluate_module(module, test_data) 