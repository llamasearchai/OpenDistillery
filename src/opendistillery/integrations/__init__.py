"""
OpenDistillery Integrations Module

Latest AI model integrations and advanced frameworks (2025):
- Multi-provider API (OpenAI, Anthropic, xAI, Google)
- Dedicated Grok/xAI integration with full feature support
- DSPy framework integration
- Enterprise system integrations
"""

from .multi_provider_api import (
    MultiProviderAPI,
    OpenAIModel,
    AnthropicModel, 
    XAIModel,
    GoogleModel,
    AIProvider,
    ChatResponse,
    ChatMessage,
    ModelSpec,
    MODEL_SPECS,
    get_completion,
    get_reasoning_completion,
    get_multimodal_completion
)

try:
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
    GROK_AVAILABLE = True
except ImportError:
    GROK_AVAILABLE = False

try:
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
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False

# Base exports (always available)
__all__ = [
    # Multi-provider API
    "MultiProviderAPI",
    "OpenAIModel",
    "AnthropicModel", 
    "XAIModel",
    "GoogleModel",
    "AIProvider",
    "ChatResponse",
    "ChatMessage",
    "ModelSpec",
    "MODEL_SPECS",
    "get_completion",
    "get_reasoning_completion",
    "get_multimodal_completion",
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
        "GrokRateLimiter",
        "GROK_MODEL_SPECS",
        "get_grok_completion",
        "get_grok_vision_analysis",
        "create_search_function",
        "create_calculator_function",
    ])

# Add DSPy exports if available
if DSPY_AVAILABLE:
    __all__.extend([
        "DSPyIntegrationManager",
        "DSPyConfig", 
        "DSPyModel",
        "OpenDistilleryDSPyLM",
        "ReasoningChainOfThought",
        "TreeOfThoughtsDSPy",
        "CompoundReasoningSystem",
        "create_optimized_reasoning_chain",
        "evaluate_reasoning_performance"
    ]) 