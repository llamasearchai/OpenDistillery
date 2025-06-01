"""
Meta-Prompting Framework v2.3
Inspired by "Meta-Prompting: Enhancing Language Models with Task-Agnostic Scaffolding"
Implementation follows OpenAI GPT-4 Technical Report patterns
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

class PromptType(Enum):
    """OpenAI-style prompt categorization"""
    SYSTEM = "system"
    USER = "user" 
    ASSISTANT = "assistant"
    FUNCTION = "function"

@dataclass
class PromptVariant:
    """Individual prompt variant with OpenAI-compatible scoring"""
    content: str
    temperature: float = 0.7
    top_p: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    score: float = field(default=0.0)
    safety_rating: float = field(default=1.0)
    
class MetaPromptingEngine:
    """
    Advanced meta-prompting system following OpenAI's design principles
    
    Features:
    - Self-improving prompt generation
    - Multi-objective optimization 
    - Safety-constrained evolution
    - Research-backed evaluation metrics
    """
    
    def __init__(self, api_key: str = None):
        self.console = Console()
        self.generation_count = 0
        self.safety_threshold = 0.85
        self.performance_history = []
        
    async def evolve_prompt(
        self, 
        base_prompt: str,
        task_description: str,
        evaluation_criteria: List[str],
        generations: int = 5
    ) -> Dict[str, Any]:
        """
        Evolve prompts using meta-learning principles from GPT-4 research
        
        Args:
            base_prompt: Initial prompt to evolve
            task_description: What the prompt should accomplish
            evaluation_criteria: List of evaluation dimensions
            generations: Number of evolution cycles
            
        Returns:
            OpenAI-compatible response with best prompt and metrics
        """
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            
            evolution_task = progress.add_task(
                "[cyan]Evolving prompts...", 
                total=generations
            )
            
            # Initialize population with base prompt
            current_generation = [
                PromptVariant(content=base_prompt)
            ]
            
            best_prompt = None
            best_score = 0.0
            
            for gen in range(generations):
                # Generate prompt variants
                new_variants = await self._generate_variants(
                    current_generation[0], 
                    task_description
                )
                
                # Evaluate all variants
                evaluated_variants = await self._evaluate_generation(
                    new_variants, 
                    evaluation_criteria
                )
                
                # Select best performing and safe variants
                safe_variants = [
                    v for v in evaluated_variants 
                    if v.safety_rating >= self.safety_threshold
                ]
                
                if safe_variants:
                    generation_best = max(safe_variants, key=lambda x: x.score)
                    
                    if generation_best.score > best_score:
                        best_prompt = generation_best
                        best_score = generation_best.score
                    
                    current_generation = [generation_best]
                
                progress.update(evolution_task, advance=1)
                self.generation_count += 1
        
        return {
            "optimized_prompt": best_prompt.content if best_prompt else base_prompt,
            "performance_score": best_score,
            "safety_rating": best_prompt.safety_rating if best_prompt else 1.0,
            "generations_processed": generations,
            "optimization_history": self.performance_history,
            "api_compatible": True
        }
    
    async def _generate_variants(
        self, 
        parent: PromptVariant, 
        task_description: str
    ) -> List[PromptVariant]:
        """Generate prompt variants using meta-prompting"""
        
        meta_prompt = f"""
        You are PromptGPT-4, an advanced prompt optimization engine.
        
        TASK: Generate 5 improved variants of this prompt for: {task_description}
        
        PARENT PROMPT:
        {parent.content}
        
        OPTIMIZATION OBJECTIVES:
        1. Clarity and specificity
        2. Task-relevant context
        3. Output format specification
        4. Error handling instructions
        5. Safety and ethical considerations
        
        Generate variants using these techniques:
        - Chain-of-Thought scaffolding
        - Few-shot example integration
        - Role-based framing
        - Constraint specification
        - Output format templates
        
        Return as JSON array with structure:
        {{
            "variants": [
                {{
                    "content": "optimized prompt text",
                    "technique": "optimization method used",
                    "rationale": "why this should perform better"
                }}
            ]
        }}
        """
        
        # Simulate advanced LLM call (replace with actual OpenAI API)
        response = await self._call_meta_llm(meta_prompt)
        
        try:
            parsed_response = json.loads(response)
            variants = []
            
            for variant_data in parsed_response.get("variants", []):
                variant = PromptVariant(
                    content=variant_data["content"],
                    temperature=parent.temperature + (0.1 * (len(variants) - 2)),
                    top_p=min(1.0, parent.top_p + 0.05),
                )
                variants.append(variant)
                
            return variants
            
        except json.JSONDecodeError:
            # Fallback to mutation-based generation
            return await self._mutation_fallback(parent)
    
    async def _evaluate_generation(
        self, 
        variants: List[PromptVariant],
        criteria: List[str]
    ) -> List[PromptVariant]:
        """Evaluate prompt variants across multiple dimensions"""
        
        for variant in variants:
            scores = []
            
            # Evaluate against each criterion
            for criterion in criteria:
                evaluation_prompt = f"""
                Rate this prompt on the criterion: {criterion}
                Scale: 0.0 (poor) to 1.0 (excellent)
                
                PROMPT TO EVALUATE:
                {variant.content}
                
                Provide score and brief justification:
                Score: [0.0-1.0]
                Reasoning: [brief explanation]
                """
                
                eval_response = await self._call_meta_llm(evaluation_prompt)
                score = self._extract_score(eval_response)
                scores.append(score)
            
            # Calculate composite score
            variant.score = sum(scores) / len(scores)
            
            # Safety evaluation
            variant.safety_rating = await self._evaluate_safety(variant.content)
            
            self.performance_history.append({
                "generation": self.generation_count,
                "score": variant.score,
                "safety": variant.safety_rating
            })
        
        return variants
    
    async def _evaluate_safety(self, prompt_content: str) -> float:
        """
        Safety evaluation following OpenAI Moderation API patterns
        """
        
        safety_prompt = f"""
        Evaluate this prompt for safety concerns using OpenAI safety guidelines:
        
        PROMPT: {prompt_content}
        
        Check for:
        - Harmful content generation potential
        - Bias amplification risks  
        - Privacy violation risks
        - Misinformation potential
        - Inappropriate content risks
        
        Safety Score: [0.0-1.0] where 1.0 is completely safe
        """
        
        response = await self._call_meta_llm(safety_prompt)
        return self._extract_score(response)
    
    async def _call_meta_llm(self, prompt: str) -> str:
        """Simulate advanced LLM call - replace with actual OpenAI API"""
        # In production, this would be:
        # return await self.openai_client.chat.completions.create(...)
        
        await asyncio.sleep(0.5)  # Simulate API latency
        
        # Mock response for demonstration
        if "JSON array" in prompt:
            return json.dumps({
                "variants": [
                    {
                        "content": "Enhanced prompt with better structure...",
                        "technique": "Chain-of-Thought",
                        "rationale": "Adds reasoning steps"
                    }
                ]
            })
        elif "Safety Score" in prompt:
            return "Safety Score: 0.92\nNo significant safety concerns detected."
        else:
            return "Score: 0.85\nReasoning: Well-structured and clear."
    
    def _extract_score(self, response: str) -> float:
        """Extract numerical score from evaluation response"""
        import re
        
        # Look for score pattern
        score_match = re.search(r'(?:Score|score):\s*([0-9]*\.?[0-9]+)', response)
        if score_match:
            return float(score_match.group(1))
        
        # Fallback scoring
        return 0.75
    
    async def _mutation_fallback(self, parent: PromptVariant) -> List[PromptVariant]:
        """Fallback mutation strategy if meta-generation fails"""
        
        mutations = [
            f"Please think step by step about this problem:\n\n{parent.content}",
            f"As an expert in this domain, {parent.content.lower()}",
            f"{parent.content}\n\nExplain your reasoning clearly.",
            f"Consider multiple perspectives on this:\n{parent.content}",
            f"{parent.content}\n\nProvide specific examples to support your answer."
        ]
        
        return [
            PromptVariant(
                content=mutation,
                temperature=parent.temperature + 0.1 * i,
                top_p=min(1.0, parent.top_p + 0.02 * i)
            )
            for i, mutation in enumerate(mutations)
        ]