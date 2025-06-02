"""
Example plugin registrations showing proper OpenAI-style implementation
"""

from .registry import PluginMetadata, registry
from .meta_prompting_v2 import MetaPromptingEngine
from .constitutional_ai import ConstitutionalAI
from .gradient_prompt_search import GradientPromptOptimizer

# Register Meta-Prompting Plugin
META_PROMPTING_METADATA = PluginMetadata(
    name="meta-prompting",
    version="2.3.0",
    description="Advanced meta-prompting with self-optimization capabilities",
    author="OpenDistillery Team",
    research_paper="Meta-Prompting: Enhancing Language Models with Task-Agnostic Scaffolding",
    arxiv_link="https://arxiv.org/abs/2401.12954",
    safety_rating=0.95,
    performance_tier="production",
    supported_tasks=["reasoning", "analysis", "optimization", "creative"],
    dependencies=["openai>=1.12.0", "rich>=13.7.0"]
)

# Register Constitutional AI Plugin  
CONSTITUTIONAL_AI_METADATA = PluginMetadata(
    name="constitutional-ai",
    version="1.0.0", 
    description="Safety-first prompting with constitutional constraints",
    author="OpenDistillery Team",
    research_paper="Constitutional AI: Harmlessness from AI Feedback",
    arxiv_link="https://arxiv.org/abs/2212.08073",
    safety_rating=0.99,
    performance_tier="production",
    supported_tasks=["safety", "evaluation", "content-moderation"],
    dependencies=["openai>=1.12.0"]
)

# Register Gradient Search Plugin
GRADIENT_SEARCH_METADATA = PluginMetadata(
    name="gradient-search",
    version="1.1.0",
    description="Differentiable prompt optimization via gradient estimation", 
    author="OpenDistillery Team",
    research_paper="Automatic Prompt Optimization with Gradient Descent and Beam Search",
    arxiv_link="https://arxiv.org/abs/2305.03495",
    safety_rating=0.88,
    performance_tier="beta",
    supported_tasks=["optimization", "search", "tuning"],
    dependencies=["numpy>=1.24.0", "matplotlib>=3.8.0"]
)

async def register_all_plugins():
    """Register all example plugins"""
    
    await registry.register_plugin(MetaPromptingEngine, META_PROMPTING_METADATA)
    await registry.register_plugin(ConstitutionalAI, CONSTITUTIONAL_AI_METADATA) 
    await registry.register_plugin(GradientPromptOptimizer, GRADIENT_SEARCH_METADATA)
    
    print(" All OpenDistillery prompting plugins registered successfully!")