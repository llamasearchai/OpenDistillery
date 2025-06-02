"""
OpenDistillery Research Techniques

Advanced prompting and reasoning techniques (2025):
- Tree of Thoughts
- Diffusion Prompting  
- Quantum Superposition
- Neuromorphic Prompting
- Adaptive Temperature
- Chain of Thought
"""

from .prompting_strategies import (
    PromptingOrchestrator,
    PromptingStrategy,
    BasePromptingStrategy,
    ZeroShotStrategy,
    ChainOfThoughtStrategy,
    TreeOfThoughtsStrategy,
    DiffusionPromptingStrategy,
    QuantumSuperpositionStrategy,
    NeuromorphicPromptingStrategy,
    AdaptiveTemperatureStrategy,
    PromptResult,
    ThoughtNode
)

__all__ = [
    "PromptingOrchestrator",
    "PromptingStrategy",
    "BasePromptingStrategy",
    "ZeroShotStrategy",
    "ChainOfThoughtStrategy",
    "TreeOfThoughtsStrategy", 
    "DiffusionPromptingStrategy",
    "QuantumSuperpositionStrategy",
    "NeuromorphicPromptingStrategy",
    "AdaptiveTemperatureStrategy",
    "PromptResult",
    "ThoughtNode"
] 