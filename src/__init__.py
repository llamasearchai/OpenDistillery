"""
OpenDistillery: Advanced Compound AI Systems for Enterprise Workflow Transformation

Latest Models Support (2025):
- OpenAI: o1, o3, o4, GPT-4.1
- Anthropic: Claude 4 Opus, Claude 4 Sonnet, Claude 4 Haiku
- xAI: Grok 3, Grok 3 Beta, Grok 2, Grok 1.5 Vision

Advanced Features:
- Real-time information access with Grok
- Vision and multimodal capabilities
- Function calling with automatic execution
- Advanced prompting techniques
- Enterprise-grade security and monitoring
- Multi-agent orchestration
- Compound AI systems

Prompting Techniques:
- Tree of Thoughts
- Chain of Thought
- Diffusion Prompting
- Quantum Superposition
- Neuromorphic Prompting
- Adaptive Temperature
- DSPy Integration
"""

__version__ = "2.0.0"
__author__ = "Nik Jois"
__email__ = "nikjois@llamasearch.ai"
__description__ = "Advanced Compound AI Systems for Enterprise Workflow Transformation with Latest Models (2025)"

# Core imports
try:
    from .integrations.multi_provider_api import (
        MultiProviderAPI,
        OpenAIModel,
        AnthropicModel, 
        XAIModel,
        AIProvider,
        get_completion,
        get_reasoning_completion
    )
    
    # Grok integration imports
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

# Latest model convenience functions
async def analyze_with_o4(prompt: str, **kwargs):
    """Analyze with latest o4 model"""
    return await get_reasoning_completion(prompt, model="o4", **kwargs)

async def reason_with_claude4(prompt: str, **kwargs):
    """Reason with Claude 4 Opus"""
    return await get_completion(prompt, model="claude-4-opus", **kwargs)

async def create_with_grok3(prompt: str, **kwargs):
    """Create with Grok 3"""
    return await get_grok_completion(prompt, model="grok-3", **kwargs)

async def analyze_image_with_grok(prompt: str, images, **kwargs):
    """Analyze images with Grok Vision"""
    return await get_grok_vision_analysis(prompt, images, **kwargs)

async def get_realtime_info(prompt: str, **kwargs):
    """Get real-time information with Grok"""
    return await get_grok_completion(prompt, model="grok-3", real_time_info=True, **kwargs)

# Multi-provider convenience function
async def get_best_completion(prompt: str, providers=None, **kwargs):
    """Get completion from the best available provider"""
    if providers is None:
        providers = ["grok-3", "o4", "claude-4-opus"]
    
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

# Enterprise workflow functions
async def create_compound_system(*models, **kwargs):
    """Create a compound AI system with multiple models"""
    system = CompoundAISystem()
    for model in models:
        system.add_model(model, **kwargs)
    return system

async def create_grok_agent(capabilities=None, **kwargs):
    """Create a specialized Grok-powered agent"""
    if capabilities is None:
        capabilities = ["real_time_info", "vision", "function_calling"]
    
    async with GrokAPIClient() as client:
        # Register standard functions
        if "search" in capabilities:
            client.register_function(create_search_function())
        if "calculator" in capabilities:
            client.register_function(create_calculator_function())
        
        return client

# Quick access functions
def get_available_models():
    """Get all available models across providers"""
    return {
        "openai": [model.value for model in OpenAIModel],
        "anthropic": [model.value for model in AnthropicModel],
        "xai": [model.value for model in GrokModel if 'GrokModel' in globals()]
    }

def get_model_capabilities(model_name: str):
    """Get capabilities for a specific model"""
    try:
        if 'grok' in model_name.lower():
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
    
    # Grok integration
    "GrokAPIClient",
    "GrokModel",
    "GrokCapability",
    "GrokModelSpec",
    "GrokResponse",
    "GrokFunction",
    
    # Model enums
    "OpenAIModel",
    "AnthropicModel", 
    "XAIModel",
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
    "get_grok_completion",
    "get_grok_vision_analysis",
    "analyze_with_o4",
    "reason_with_claude4", 
    "create_with_grok3",
    "analyze_image_with_grok",
    "get_realtime_info",
    "get_best_completion",
    
    # Enterprise functions
    "create_compound_system",
    "create_grok_agent",
    "create_optimized_reasoning_chain",
    "evaluate_reasoning_performance",
    
    # Grok function builders
    "create_search_function",
    "create_calculator_function",
    
    # Utility functions
    "get_available_models",
    "get_model_capabilities",
    
    # Metadata
    "__version__",
    "__author__",
    "__email__",
    "__description__"
] 