"""
Constitutional AI Implementation
Based on "Constitutional AI: Harmlessness from AI Feedback" (Anthropic, 2022)
OpenAI-compatible safety constraints and evaluation
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

class SafetyCategory(Enum):
    """OpenAI Moderation API compatible categories"""
    HATE = "hate"
    HATE_THREATENING = "hate/threatening"
    HARASSMENT = "harassment"
    HARASSMENT_THREATENING = "harassment/threatening"
    SELF_HARM = "self-harm"
    SELF_HARM_INTENT = "self-harm/intent"
    SELF_HARM_INSTRUCTIONS = "self-harm/instructions"
    SEXUAL = "sexual"
    SEXUAL_MINORS = "sexual/minors"
    VIOLENCE = "violence"
    VIOLENCE_GRAPHIC = "violence/graphic"

@dataclass
class ConstitutionalRule:
    """Individual constitutional rule with OpenAI-style structure"""
    name: str
    description: str
    category: SafetyCategory
    threshold: float
    priority: int

class ConstitutionalAI:
    """
    Constitutional AI safety layer for prompt processing
    
    Implements:
    - Multi-stage safety evaluation
    - Constitutional rule enforcement
    - Self-critique and revision
    - OpenAI Moderation API compatibility
    """
    
    def __init__(self):
        self.constitution = self._load_constitution()
        self.safety_cache = {}
        
    def _load_constitution(self) -> List[ConstitutionalRule]:
        """Load constitutional rules following OpenAI safety guidelines"""
        
        return [
            ConstitutionalRule(
                name="Harmlessness Principle",
                description="Do not generate content that could cause harm",
                category=SafetyCategory.VIOLENCE,
                threshold=0.1,
                priority=1
            ),
            ConstitutionalRule(
                name="Truthfulness Standard", 
                description="Prefer accurate and truthful information",
                category=SafetyCategory.HARASSMENT,
                threshold=0.15,
                priority=2
            ),
            ConstitutionalRule(
                name="Respect for Persons",
                description="Treat all individuals with dignity and respect",
                category=SafetyCategory.HATE,
                threshold=0.05,
                priority=1
            ),
            ConstitutionalRule(
                name="Privacy Protection",
                description="Protect personal and sensitive information",
                category=SafetyCategory.HARASSMENT,
                threshold=0.2,
                priority=2
            ),
            ConstitutionalRule(
                name="Beneficial Intent",
                description="Aim to be helpful and beneficial",
                category=SafetyCategory.SELF_HARM,
                threshold=0.1,
                priority=3
            )
        ]
    
    async def evaluate_prompt(
        self, 
        prompt: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluate prompt against constitutional principles
        
        Returns OpenAI Moderation API compatible response
        """
        
        # Check cache first
        cache_key = hash(prompt)
        if cache_key in self.safety_cache:
            return self.safety_cache[cache_key]
        
        evaluation_results = []
        flagged = False
        
        for rule in self.constitution:
            violation_score = await self._evaluate_rule(prompt, rule)
            
            is_violation = violation_score > rule.threshold
            if is_violation:
                flagged = True
            
            evaluation_results.append({
                "rule": rule.name,
                "category": rule.category.value,
                "score": violation_score,
                "flagged": is_violation,
                "priority": rule.priority
            })
        
        # Calculate overall safety score
        weighted_score = sum(
            result["score"] * (4 - result["priority"]) 
            for result in evaluation_results
        ) / sum(4 - result["priority"] for result in evaluation_results)
        
        safety_report = {
            "flagged": flagged,
            "safety_score": 1.0 - weighted_score,
            "categories": {
                result["category"]: result["flagged"] 
                for result in evaluation_results
            },
            "category_scores": {
                result["category"]: result["score"]
                for result in evaluation_results
            },
            "detailed_results": evaluation_results,
            "api_version": "constitutional-ai-1.0"
        }
        
        # Cache result
        self.safety_cache[cache_key] = safety_report
        
        return safety_report
    
    async def _evaluate_rule(
        self, 
        prompt: str, 
        rule: ConstitutionalRule
    ) -> float:
        """Evaluate prompt against a specific constitutional rule"""
        
        evaluation_prompt = f"""
        You are a constitutional AI safety evaluator following OpenAI guidelines.
        
        RULE TO EVALUATE: {rule.name}
        DESCRIPTION: {rule.description}
        CATEGORY: {rule.category.value}
        
        PROMPT TO ANALYZE:
        {prompt}
        
        Rate the likelihood this prompt violates the rule on a scale of 0.0 to 1.0:
        - 0.0: No violation, completely safe
        - 0.5: Potential concern, borderline
        - 1.0: Clear violation, unsafe
        
        Consider:
        1. Direct violations in the prompt text
        2. Potential for harmful outputs
        3. Context and intent
        4. Edge cases and interpretations
        
        Violation Score: [0.0-1.0]
        Reasoning: [Brief explanation]
        """
        
        # Simulate safety evaluation (replace with actual model call)
        response = await self._call_safety_evaluator(evaluation_prompt)
        return self._extract_violation_score(response)
    
    async def critique_and_revise(
        self, 
        prompt: str,
        safety_report: Dict[str, Any]
    ) -> str:
        """
        Generate constitutional critique and revised prompt
        Following Constitutional AI methodology
        """
        
        if not safety_report["flagged"]:
            return prompt
        
        flagged_categories = [
            cat for cat, flagged in safety_report["categories"].items() 
            if flagged
        ]
        
        critique_prompt = f"""
        You are a constitutional AI assistant helping to revise prompts for safety.
        
        ORIGINAL PROMPT:
        {prompt}
        
        SAFETY VIOLATIONS DETECTED:
        {', '.join(flagged_categories)}
        
        CONSTITUTIONAL PRINCIPLES TO FOLLOW:
        {chr(10).join(f"- {rule.name}: {rule.description}" for rule in self.constitution)}
        
        Please:
        1. Critique the original prompt, explaining specific violations
        2. Revise the prompt to remove harmful elements while preserving intent
        3. Ensure the revision aligns with constitutional principles
        
        CRITIQUE:
        [Explain the problems with the original prompt]
        
        REVISED PROMPT:
        [Provide a safer alternative that maintains the original's purpose]
        """
        
        response = await self._call_safety_evaluator(critique_prompt)
        return self._extract_revised_prompt(response)
    
    async def _call_safety_evaluator(self, prompt: str) -> str:
        """Call safety evaluation model (simulated)"""
        await asyncio.sleep(0.3)  # Simulate evaluation latency
        
        if "Violation Score" in prompt:
            return "Violation Score: 0.15\nReasoning: Minor concern with potential for misinterpretation."
        else:
            return """
            CRITIQUE:
            The original prompt could potentially lead to harmful outputs due to ambiguous phrasing.
            
            REVISED PROMPT:
            Please provide helpful information about this topic while ensuring accuracy and safety.
            """
    
    def _extract_violation_score(self, response: str) -> float:
        """Extract violation score from safety evaluation"""
        import re
        
        score_match = re.search(r'Violation Score:\s*([0-9]*\.?[0-9]+)', response)
        if score_match:
            return float(score_match.group(1))
        
        return 0.0
    
    def _extract_revised_prompt(self, response: str) -> str:
        """Extract revised prompt from critique response"""
        
        revised_section = response.split("REVISED PROMPT:")
        if len(revised_section) > 1:
            return revised_section[1].strip()
        
        return response.strip()