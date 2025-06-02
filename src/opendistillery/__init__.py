"""
OpenDistillery: Advanced Compound AI Systems for Enterprise Workflow Transformation

Latest Models Support (2025):
- OpenAI: GPT-4, GPT-3.5, and Assistants API
- Anthropic: Claude models
- Advanced features with multi-agent orchestration

Advanced Features:
- Multi-agent orchestration
- Compound AI systems
- Enterprise-grade security and monitoring
- Real-time processing capabilities
- Advanced prompting techniques
"""

__version__ = "2.0.1"
__author__ = "Nik Jois"
__email__ = "nikjois@llamasearch.ai"
__description__ = "Advanced Compound AI Systems for Enterprise Workflow Transformation"

# Core imports
try:
    from .integrations.multi_provider_api import (
        MultiProviderAPI,
        OpenAIModel,
        AnthropicModel, 
        AIProvider,
        get_completion,
        get_reasoning_completion
    )
    
    # Grok integration imports (if available)
    try:
        from .integrations.grok_integration import (
            GrokAPIClient,
            GrokModel,
            GrokCapability,
            GrokModelSpec,
            GrokResponse,
            GrokFunction,
            get_grok_completion,
            get_grok_vision_analysis,
            create_search_function,
            create_calculator_function
        )
        GROK_AVAILABLE = True
    except ImportError:
        GROK_AVAILABLE = False
    
    from .research.techniques.prompting_strategies import (
        PromptingOrchestrator,
        PromptingStrategy,
        TreeOfThoughtsStrategy,
        DiffusionPromptingStrategy,
        QuantumSuperpositionStrategy,
        NeuromorphicPromptingStrategy,
        AdaptiveTemperatureStrategy
    )
    
    from .integrations.dspy_integration import (
        DSPyIntegrationManager,
        DSPyConfig,
        create_optimized_reasoning_chain,
        evaluate_reasoning_performance
    )
    
    # Core system imports
    from .core.compound_system import CompoundAISystem
    from .core.model_hub import ModelHub
    
except ImportError as e:
    # Fallback for development/testing
    import warnings
    warnings.warn(f"Some modules could not be imported: {e}", ImportWarning)
    GROK_AVAILABLE = False

# Multi-provider convenience function
async def get_best_completion(prompt: str, providers=None, **kwargs):
    """Get completion from the best available provider"""
    if providers is None:
        providers = ["gpt-4", "claude-3-opus-20240229"]
    
    try:
        async with MultiProviderAPI() as api:
            for model in providers:
                try:
                    return await api.chat_completion(
                        messages=[{"role": "user", "content": prompt}],
                        model=model,
                        **kwargs
                    )
                except Exception:
                    continue
            
            raise RuntimeError("All providers failed")
    except Exception:
        return {"error": "MultiProviderAPI not available"}

# Enterprise workflow functions
async def create_compound_system(*models, **kwargs):
    """Create a compound AI system with multiple models"""
    try:
        system = CompoundAISystem()
        for model in models:
            system.add_model(model, **kwargs)
        return system
    except Exception:
        return None

# Quick access functions
def get_available_models():
    """Get all available models across providers"""
    try:
        models = {
            "openai": [model.value for model in OpenAIModel],
            "anthropic": [model.value for model in AnthropicModel],
        }
        if GROK_AVAILABLE:
            models["xai"] = [model.value for model in GrokModel]
        return models
    except Exception:
        return {"openai": ["gpt-4", "gpt-3.5-turbo"], "anthropic": ["claude-3-opus-20240229"]}

def get_model_capabilities(model_name: str):
    """Get capabilities for a specific model"""
    try:
        if GROK_AVAILABLE and 'grok' in model_name.lower():
            from .integrations.grok_integration import GROK_MODEL_SPECS
            return GROK_MODEL_SPECS.get(model_name)
        else:
            from .integrations.multi_provider_api import MODEL_SPECS
            return MODEL_SPECS.get(model_name)
    except ImportError:
        return None

# Package metadata and exports
__all__ = [
    # Core classes
    "MultiProviderAPI",
    "PromptingOrchestrator", 
    "DSPyIntegrationManager",
    "CompoundAISystem",
    "ModelHub",
    
    # Model enums
    "OpenAIModel",
    "AnthropicModel", 
    "AIProvider",
    
    # Strategies
    "PromptingStrategy",
    "TreeOfThoughtsStrategy",
    "DiffusionPromptingStrategy",
    "QuantumSuperpositionStrategy",
    "NeuromorphicPromptingStrategy",
    "AdaptiveTemperatureStrategy",
    
    # Configuration
    "DSPyConfig",
    
    # Convenience functions
    "get_completion",
    "get_reasoning_completion",
    "get_best_completion",
    
    # Enterprise functions
    "create_compound_system",
    "create_optimized_reasoning_chain",
    "evaluate_reasoning_performance",
    
    # Utility functions
    "get_available_models",
    "get_model_capabilities",
    
    # Metadata
    "__version__",
    "__author__",
    "__email__",
    "__description__"
]

# Add Grok exports if available
if GROK_AVAILABLE:
    __all__.extend([
        "GrokAPIClient",
        "GrokModel",
        "GrokCapability",
        "GrokModelSpec",
        "GrokResponse",
        "GrokFunction",
        "get_grok_completion",
        "get_grok_vision_analysis",
        "create_search_function",
        "create_calculator_function",
    ]) 