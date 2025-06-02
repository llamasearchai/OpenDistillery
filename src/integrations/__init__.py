"""
OpenDistillery Integrations Module

Latest AI model integrations and advanced frameworks:
- Multi-provider API (OpenAI, Anthropic, xAI)
- Dedicated Grok/xAI integration with full feature support
- DSPy framework integration
- Enterprise system integrations
"""

from .multi_provider_api import (
    MultiProviderAPI,
    OpenAIModel,
    AnthropicModel, 
    XAIModel,
    AIProvider,
    APIResponse,
    ModelCapabilities,
    get_completion,
    get_reasoning_completion
)

from .grok_integration import (
    GrokAPIClient,
    GrokModel,
    GrokCapability,
    GrokModelSpec,
    GrokResponse,
    GrokFunction,
    GrokRateLimiter,
    GROK_MODEL_SPECS,
    get_grok_completion,
    get_grok_vision_analysis,
    create_search_function,
    create_calculator_function
)

from .dspy_integration import (
    DSPyIntegrationManager,
    DSPyConfig,
    DSPyModel,
    OpenDistilleryDSPyLM,
    ReasoningChainOfThought,
    TreeOfThoughtsDSPy,
    CompoundReasoningSystem,
    create_optimized_reasoning_chain,
    evaluate_reasoning_performance
)

__all__ = [
    # Multi-provider API
    "MultiProviderAPI",
    "OpenAIModel",
    "AnthropicModel", 
    "XAIModel",
    "AIProvider",
    "APIResponse",
    "ModelCapabilities",
    "get_completion",
    "get_reasoning_completion",
    
    # Grok/xAI Integration
    "GrokAPIClient",
    "GrokModel",
    "GrokCapability",
    "GrokModelSpec", 
    "GrokResponse",
    "GrokFunction",
    "GrokRateLimiter",
    "GROK_MODEL_SPECS",
    "get_grok_completion",
    "get_grok_vision_analysis",
    "create_search_function",
    "create_calculator_function",
    
    # DSPy Integration
    "DSPyIntegrationManager",
    "DSPyConfig", 
    "DSPyModel",
    "OpenDistilleryDSPyLM",
    "ReasoningChainOfThought",
    "TreeOfThoughtsDSPy",
    "CompoundReasoningSystem",
    "create_optimized_reasoning_chain",
    "evaluate_reasoning_performance"
] 