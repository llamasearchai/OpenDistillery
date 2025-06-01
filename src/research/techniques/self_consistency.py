"""
Self-Consistency Reasoning Implementation
Advanced reasoning technique that generates multiple reasoning paths and selects the most consistent answer.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
import numpy as np
from collections import Counter, defaultdict

import structlog

logger = structlog.get_logger(__name__)

class ReasoningPath:
    """Represents a single reasoning path"""
    def __init__(self, path_id: str, prompt: str, reasoning: str, answer: str, confidence: float = 0.0):
        self.path_id = path_id
        self.prompt = prompt
        self.reasoning = reasoning
        self.answer = answer
        self.confidence = confidence
        self.metadata: Dict[str, Any] = {}
        self.created_at = time.time()

class ConsistencyMetrics:
    """Metrics for measuring consistency across reasoning paths"""
    def __init__(self):
        self.answer_frequency: Dict[str, int] = defaultdict(int)
        self.confidence_scores: List[float] = []
        self.reasoning_similarity: float = 0.0
        self.consensus_strength: float = 0.0
        self.outlier_paths: List[str] = []

class SelfConsistencyReasoner:
    """
    Self-Consistency reasoning implementation
    """
    
    def __init__(self, models: Dict[str, Any], model_router: Any, num_paths: int = 5, consistency_threshold: float = 0.6):
        self.models = models
        self.model_router = model_router
        self.num_paths = num_paths
        self.consistency_threshold = consistency_threshold
        
        # Reasoning paths
        self.reasoning_paths: List[ReasoningPath] = []
        self.consistency_metrics = ConsistencyMetrics()
        
        # Temperature variations for diversity
        self.temperature_range = (0.3, 0.9)
        
    async def reason_with_consistency(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Perform self-consistency reasoning"""
        problem = request.get("prompt", "")
        context = request.get("context", {})
        
        logger.info(f"Starting Self-Consistency reasoning for: {problem[:100]}...")
        
        start_time = time.time()
        
        # Generate multiple reasoning paths
        await self._generate_reasoning_paths(problem, context)
        
        # Analyze consistency
        self._analyze_consistency()
        
        # Select most consistent answer
        final_answer = self._select_consistent_answer()
        
        execution_time = time.time() - start_time
        
        # Build result
        result = {
            "success": len(self.reasoning_paths) > 0,
            "response": final_answer["answer"],
            "confidence": final_answer["confidence"],
            "consistency_analysis": {
                "num_paths": len(self.reasoning_paths),
                "consensus_strength": self.consistency_metrics.consensus_strength,
                "answer_distribution": dict(self.consistency_metrics.answer_frequency),
                "average_confidence": np.mean(self.consistency_metrics.confidence_scores) if self.consistency_metrics.confidence_scores else 0,
                "outlier_count": len(self.consistency_metrics.outlier_paths),
                "execution_time": execution_time
            },
            "reasoning_paths": [
                {
                    "path_id": path.path_id,
                    "reasoning": path.reasoning,
                    "answer": path.answer,
                    "confidence": path.confidence
                }
                for path in self.reasoning_paths
            ],
            "majority_answer": final_answer["answer"],
            "alternative_answers": self._get_alternative_answers()
        }
        
        return result
    
    async def _generate_reasoning_paths(self, problem: str, context: Dict[str, Any]) -> None:
        """Generate multiple independent reasoning paths"""
        self.reasoning_paths = []
        
        # Generate diverse prompts and temperatures
        path_configs = self._create_path_configurations(problem, context)
        
        # Generate paths concurrently
        tasks = []
        for i, config in enumerate(path_configs):
            task = self._generate_single_path(i, config)
            tasks.append(task)
        
        # Wait for all paths to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, ReasoningPath):
                self.reasoning_paths.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Reasoning path failed: {str(result)}")
    
    def _create_path_configurations(self, problem: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create diverse configurations for reasoning paths"""
        configs = []
        
        # Base configuration
        base_config = {
            "problem": problem,
            "context": context,
            "temperature": 0.7
        }
        
        # Variation 1: Direct reasoning
        configs.append({
            **base_config,
            "prompt_style": "direct",
            "temperature": 0.3,
            "instructions": "Think step by step and provide a clear answer."
        })
        
        # Variation 2: Analytical reasoning
        configs.append({
            **base_config,
            "prompt_style": "analytical",
            "temperature": 0.5,
            "instructions": "Analyze this problem systematically, considering all relevant factors."
        })
        
        # Variation 3: Creative reasoning
        configs.append({
            **base_config,
            "prompt_style": "creative",
            "temperature": 0.8,
            "instructions": "Approach this problem from multiple angles and think creatively."
        })
        
        # Variation 4: Cautious reasoning
        configs.append({
            **base_config,
            "prompt_style": "cautious",
            "temperature": 0.2,
            "instructions": "Carefully consider all aspects and potential pitfalls before answering."
        })
        
        # Variation 5: Intuitive reasoning
        configs.append({
            **base_config,
            "prompt_style": "intuitive",
            "temperature": 0.9,
            "instructions": "Use your intuition and experience to guide your reasoning."
        })
        
        return configs[:self.num_paths]
    
    async def _generate_single_path(self, path_index: int, config: Dict[str, Any]) -> ReasoningPath:
        """Generate a single reasoning path"""
        path_id = f"path_{path_index}_{int(time.time())}"
        
        # Build prompt
        prompt = self._build_reasoning_prompt(config)
        
        # Get model response
        model = self.model_router.route_request(
            {"task_type": "reasoning", "temperature": config["temperature"]}, 
            list(self.models.values())
        )
        
        response = await self._call_model(model, prompt, config["temperature"])
        
        # Parse reasoning and answer
        reasoning, answer = self._parse_reasoning_response(response)
        
        # Calculate confidence
        confidence = self._calculate_path_confidence(reasoning, answer, config)
        
        # Create reasoning path
        path = ReasoningPath(
            path_id=path_id,
            prompt=prompt,
            reasoning=reasoning,
            answer=answer,
            confidence=confidence
        )
        
        path.metadata = {
            "prompt_style": config["prompt_style"],
            "temperature": config["temperature"],
            "instructions": config["instructions"]
        }
        
        return path
    
    def _build_reasoning_prompt(self, config: Dict[str, Any]) -> str:
        """Build reasoning prompt based on configuration"""
        problem = config["problem"]
        context = config["context"]
        instructions = config["instructions"]
        prompt_style = config["prompt_style"]
        
        base_prompt = f"""
Problem: {problem}

Context: {json.dumps(context, indent=2) if context else "No additional context provided"}

Instructions: {instructions}
"""
        
        if prompt_style == "direct":
            return base_prompt + """
Please provide your reasoning and final answer clearly.

Reasoning: [your step-by-step reasoning]
Answer: [your final answer]
"""
        
        elif prompt_style == "analytical":
            return base_prompt + """
Please analyze this problem systematically:

1. Problem Analysis: [break down the problem]
2. Key Factors: [identify important factors]
3. Reasoning Process: [your logical reasoning]
4. Conclusion: [your final answer]

Answer: [your final answer]
"""
        
        elif prompt_style == "creative":
            return base_prompt + """
Think about this problem creatively and consider multiple perspectives:

- What are different ways to approach this?
- Are there any unconventional solutions?
- What insights can you gain from different viewpoints?

Creative Reasoning: [your creative analysis]
Answer: [your final answer]
"""
        
        elif prompt_style == "cautious":
            return base_prompt + """
Please approach this problem carefully and thoroughly:

1. What assumptions am I making?
2. What could go wrong with different approaches?
3. What are the risks and benefits?
4. What is the most reliable answer?

Careful Analysis: [your thorough analysis]
Answer: [your final answer]
"""
        
        elif prompt_style == "intuitive":
            return base_prompt + """
Use your intuition and experience to guide your reasoning:

- What does your experience suggest?
- What patterns do you recognize?
- What feels like the right approach?

Intuitive Reasoning: [your intuitive analysis]
Answer: [your final answer]
"""
        
        else:
            return base_prompt + """
Reasoning: [your reasoning]
Answer: [your final answer]
"""
    
    def _parse_reasoning_response(self, response: str) -> Tuple[str, str]:
        """Parse reasoning and answer from model response"""
        lines = response.strip().split('\n')
        
        reasoning = ""
        answer = ""
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("Reasoning:"):
                current_section = "reasoning"
                reasoning = line[10:].strip()
            elif line.startswith("Answer:"):
                current_section = "answer"
                answer = line[7:].strip()
            elif line.startswith("Conclusion:"):
                current_section = "answer"
                answer = line[11:].strip()
            elif line.startswith("Creative Reasoning:"):
                current_section = "reasoning"
                reasoning = line[18:].strip()
            elif line.startswith("Careful Analysis:"):
                current_section = "reasoning"
                reasoning = line[16:].strip()
            elif line.startswith("Intuitive Reasoning:"):
                current_section = "reasoning"
                reasoning = line[19:].strip()
            elif current_section == "reasoning" and line:
                reasoning += " " + line
            elif current_section == "answer" and line:
                answer += " " + line
        
        # Fallback parsing
        if not reasoning and not answer:
            # Try to extract the last substantial line as answer
            substantial_lines = [line for line in lines if line.strip() and len(line.strip()) > 10]
            if substantial_lines:
                answer = substantial_lines[-1].strip()
                reasoning = " ".join(substantial_lines[:-1])
        
        return reasoning.strip(), answer.strip()
    
    def _calculate_path_confidence(self, reasoning: str, answer: str, config: Dict[str, Any]) -> float:
        """Calculate confidence for a reasoning path"""
        confidence = 0.5  # Base confidence
        
        # Length and detail of reasoning
        if len(reasoning) > 100:
            confidence += 0.1
        if len(reasoning) > 200:
            confidence += 0.1
        
        # Presence of clear answer
        if answer and len(answer) > 5:
            confidence += 0.1
        
        # Temperature adjustment (lower temperature = higher confidence)
        temp = config.get("temperature", 0.7)
        confidence += (1.0 - temp) * 0.2
        
        # Prompt style adjustment
        style_confidence = {
            "direct": 0.8,
            "analytical": 0.9,
            "creative": 0.6,
            "cautious": 0.85,
            "intuitive": 0.7
        }
        
        style = config.get("prompt_style", "direct")
        confidence = confidence * style_confidence.get(style, 0.7)
        
        return min(1.0, max(0.1, confidence))
    
    def _analyze_consistency(self) -> None:
        """Analyze consistency across reasoning paths"""
        if not self.reasoning_paths:
            return
        
        # Reset metrics
        self.consistency_metrics = ConsistencyMetrics()
        
        # Collect answers and confidences
        answers = []
        confidences = []
        
        for path in self.reasoning_paths:
            normalized_answer = self._normalize_answer(path.answer)
            answers.append(normalized_answer)
            confidences.append(path.confidence)
            
            self.consistency_metrics.answer_frequency[normalized_answer] += 1
        
        self.consistency_metrics.confidence_scores = confidences
        
        # Calculate consensus strength
        if answers:
            most_common_answer = max(self.consistency_metrics.answer_frequency, 
                                   key=self.consistency_metrics.answer_frequency.get)
            consensus_count = self.consistency_metrics.answer_frequency[most_common_answer]
            self.consistency_metrics.consensus_strength = consensus_count / len(answers)
        
        # Identify outliers
        self._identify_outliers()
        
        # Calculate reasoning similarity
        self._calculate_reasoning_similarity()
    
    def _normalize_answer(self, answer: str) -> str:
        """Normalize answer for consistency comparison"""
        if not answer:
            return "no_answer"
        
        # Convert to lowercase and remove extra whitespace
        normalized = answer.lower().strip()
        
        # Handle common variations
        if any(word in normalized for word in ["yes", "true", "correct", "agree"]):
            return "positive"
        elif any(word in normalized for word in ["no", "false", "incorrect", "disagree"]):
            return "negative"
        elif any(word in normalized for word in ["maybe", "uncertain", "unclear", "depends"]):
            return "uncertain"
        
        # For numerical answers, try to extract numbers
        import re
        numbers = re.findall(r'-?\d+\.?\d*', normalized)
        if numbers:
            try:
                # Use the first number found
                num = float(numbers[0])
                return f"number_{num}"
            except ValueError:
                pass
        
        # Return first few words for text answers
        words = normalized.split()[:3]
        return "_".join(words)
    
    def _identify_outliers(self) -> None:
        """Identify outlier reasoning paths"""
        if len(self.reasoning_paths) < 3:
            return
        
        # Find the majority answer
        majority_answer = max(self.consistency_metrics.answer_frequency, 
                            key=self.consistency_metrics.answer_frequency.get)
        
        # Identify paths with different answers
        for path in self.reasoning_paths:
            normalized_answer = self._normalize_answer(path.answer)
            if normalized_answer != majority_answer:
                self.consistency_metrics.outlier_paths.append(path.path_id)
    
    def _calculate_reasoning_similarity(self) -> None:
        """Calculate similarity between reasoning processes"""
        if len(self.reasoning_paths) < 2:
            self.consistency_metrics.reasoning_similarity = 1.0
            return
        
        # Simple similarity based on common words
        all_reasoning = [path.reasoning.lower() for path in self.reasoning_paths]
        
        # Calculate pairwise similarities
        similarities = []
        
        for i in range(len(all_reasoning)):
            for j in range(i + 1, len(all_reasoning)):
                similarity = self._calculate_text_similarity(all_reasoning[i], all_reasoning[j])
                similarities.append(similarity)
        
        self.consistency_metrics.reasoning_similarity = np.mean(similarities) if similarities else 0.0
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        
        # Simple word overlap similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _select_consistent_answer(self) -> Dict[str, Any]:
        """Select the most consistent answer"""
        if not self.reasoning_paths:
            return {"answer": "No answer generated", "confidence": 0.0}
        
        # Find majority answer
        majority_answer = max(self.consistency_metrics.answer_frequency, 
                            key=self.consistency_metrics.answer_frequency.get)
        
        # Find paths with majority answer
        majority_paths = [
            path for path in self.reasoning_paths 
            if self._normalize_answer(path.answer) == majority_answer
        ]
        
        if not majority_paths:
            # Fallback to highest confidence path
            best_path = max(self.reasoning_paths, key=lambda p: p.confidence)
            return {
                "answer": best_path.answer,
                "confidence": best_path.confidence * 0.5,  # Reduce confidence due to inconsistency
                "reasoning": best_path.reasoning,
                "consensus_type": "highest_confidence"
            }
        
        # Calculate weighted confidence for majority answer
        total_confidence = sum(path.confidence for path in majority_paths)
        weighted_confidence = total_confidence / len(majority_paths)
        
        # Boost confidence based on consensus strength
        consensus_boost = self.consistency_metrics.consensus_strength * 0.3
        final_confidence = min(1.0, weighted_confidence + consensus_boost)
        
        # Select the best reasoning from majority paths
        best_majority_path = max(majority_paths, key=lambda p: p.confidence)
        
        return {
            "answer": best_majority_path.answer,
            "confidence": final_confidence,
            "reasoning": best_majority_path.reasoning,
            "consensus_type": "majority_vote",
            "supporting_paths": len(majority_paths)
        }
    
    def _get_alternative_answers(self) -> List[Dict[str, Any]]:
        """Get alternative answers with their frequencies"""
        alternatives = []
        
        # Sort answers by frequency
        sorted_answers = sorted(
            self.consistency_metrics.answer_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Skip the majority answer (first one)
        for answer, count in sorted_answers[1:4]:  # Top 3 alternatives
            # Find a representative path for this answer
            representative_path = None
            for path in self.reasoning_paths:
                if self._normalize_answer(path.answer) == answer:
                    if not representative_path or path.confidence > representative_path.confidence:
                        representative_path = path
            
            if representative_path:
                alternatives.append({
                    "answer": representative_path.answer,
                    "frequency": count,
                    "confidence": representative_path.confidence,
                    "reasoning": representative_path.reasoning[:200] + "..." if len(representative_path.reasoning) > 200 else representative_path.reasoning
                })
        
        return alternatives
    
    async def _call_model(self, model: Any, prompt: str, temperature: float = 0.7) -> str:
        """Call the language model"""
        try:
            # This would integrate with the actual model calling logic
            # For now, simulate diverse responses based on temperature and prompt style
            
            if "creative" in prompt.lower():
                return """
Creative Reasoning: Looking at this from multiple angles, I can see several innovative approaches. The unconventional solution might actually be the most effective.
Answer: Creative approach with innovative solution
"""
            elif "cautious" in prompt.lower():
                return """
Careful Analysis: After thoroughly considering all risks and potential issues, I believe the safest approach is to proceed methodically with proper safeguards.
Answer: Cautious approach with risk mitigation
"""
            elif "analytical" in prompt.lower():
                return """
Problem Analysis: Breaking this down systematically reveals clear patterns.
Key Factors: Multiple variables need consideration.
Reasoning Process: Logical analysis leads to a well-supported conclusion.
Answer: Analytical solution based on systematic evaluation
"""
            elif "intuitive" in prompt.lower():
                return """
Intuitive Reasoning: Based on experience and pattern recognition, this feels like the right direction.
Answer: Intuitive solution based on experience
"""
            else:
                return """
Reasoning: Step-by-step analysis shows clear logical progression toward the solution.
Answer: Direct solution based on logical reasoning
"""
                
        except Exception as e:
            logger.error(f"Model call failed: {str(e)}")
            return "Reasoning: Error in processing. Answer: Unable to determine"
    
    def get_consistency_report(self) -> Dict[str, Any]:
        """Get detailed consistency analysis report"""
        return {
            "total_paths": len(self.reasoning_paths),
            "consensus_strength": self.consistency_metrics.consensus_strength,
            "answer_distribution": dict(self.consistency_metrics.answer_frequency),
            "confidence_statistics": {
                "mean": np.mean(self.consistency_metrics.confidence_scores) if self.consistency_metrics.confidence_scores else 0,
                "std": np.std(self.consistency_metrics.confidence_scores) if self.consistency_metrics.confidence_scores else 0,
                "min": min(self.consistency_metrics.confidence_scores) if self.consistency_metrics.confidence_scores else 0,
                "max": max(self.consistency_metrics.confidence_scores) if self.consistency_metrics.confidence_scores else 0
            },
            "reasoning_similarity": self.consistency_metrics.reasoning_similarity,
            "outlier_paths": self.consistency_metrics.outlier_paths,
            "consistency_threshold": self.consistency_threshold,
            "meets_threshold": self.consistency_metrics.consensus_strength >= self.consistency_threshold
        } 