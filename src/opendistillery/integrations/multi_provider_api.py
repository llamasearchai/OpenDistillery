"""
Advanced Multi-Provider AI API Integration
Supports latest models from OpenAI, Anthropic, xAI, Google, and other providers
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Dict, List, Optional, Union, Any, AsyncIterator
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

import httpx
import openai
import anthropic
from anthropic import Anthropic, AsyncAnthropic

logger = logging.getLogger(__name__)

class OpenAIModel(Enum):
    """Latest OpenAI Models (2025)"""
    # GPT-4 Series
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    
    # Latest GPT-4.1 Series (April 2025)
    GPT_4_1 = "gpt-4.1"
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1_NANO = "gpt-4.1-nano"
    
    # o-Series (Reasoning Models)
    O1_PREVIEW = "o1-preview"
    O1_MINI = "o1-mini"
    O3 = "o3"
    O3_MINI = "o3-mini"
    O4_MINI = "o4-mini"
    
    # Legacy
    GPT_3_5_TURBO = "gpt-3.5-turbo"

class AnthropicModel(Enum):
    """Latest Anthropic Claude Models (2025)"""
    # Claude 4 Series (May 2025) - Latest
    CLAUDE_4_OPUS = "claude-opus-4-20250514"
    CLAUDE_4_SONNET = "claude-sonnet-4-20250514"
    
    # Claude 3.7 Series (February 2025) - Extended Thinking
    CLAUDE_3_7_SONNET = "claude-3-7-sonnet-20250219"
    
    # Claude 3.5 Series (2024)
    CLAUDE_3_5_SONNET_V2 = "claude-3-5-sonnet-20241022"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20240620"
    CLAUDE_3_5_HAIKU = "claude-3-5-haiku-20241022"
    
    # Claude 3 Series (Legacy)
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"

class XAIModel(Enum):
    """xAI Grok Models (2025)"""
    GROK_3 = "grok-3"
    GROK_2_BETA = "grok-2-beta"
    GROK_2 = "grok-2"
    GROK_1_5V = "grok-1.5v"  # Vision model

class GoogleModel(Enum):
    """Google Gemini Models"""
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_0_PRO = "gemini-2.0-pro"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"

class AIProvider(Enum):
    """AI Model Providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    XAI = "xai"
    GOOGLE = "google"

@dataclass
class ModelSpec:
    """Model specifications and capabilities"""
    name: str
    provider: AIProvider
    context_window: int
    max_output_tokens: int
    supports_vision: bool = False
    supports_function_calling: bool = False
    supports_streaming: bool = True
    supports_reasoning: bool = False
    supports_real_time: bool = False
    cost_per_million_input: float = 0.0
    cost_per_million_output: float = 0.0
    knowledge_cutoff: str = "2024-04"
    special_features: List[str] = field(default_factory=list)

# Model specifications database
MODEL_SPECS = {
    # OpenAI Models
    OpenAIModel.GPT_4_1.value: ModelSpec(
        name="GPT-4.1",
        provider=AIProvider.OPENAI,
        context_window=1000000,  # 1M tokens
        max_output_tokens=32000,
        supports_vision=True,
        supports_function_calling=True,
        supports_reasoning=True,
        cost_per_million_input=15.0,
        cost_per_million_output=75.0,
        knowledge_cutoff="2024-06",
        special_features=["million_token_context", "advanced_reasoning", "tool_calling"]
    ),
    OpenAIModel.O3.value: ModelSpec(
        name="GPT-o3",
        provider=AIProvider.OPENAI,
        context_window=200000,
        max_output_tokens=64000,
        supports_reasoning=True,
        cost_per_million_input=20.0,
        cost_per_million_output=100.0,
        knowledge_cutoff="2025-01",
        special_features=["advanced_reasoning", "deliberative_alignment", "chain_of_thought"]
    ),
    OpenAIModel.O4_MINI.value: ModelSpec(
        name="GPT-o4-mini",
        provider=AIProvider.OPENAI,
        context_window=128000,
        max_output_tokens=32000,
        supports_reasoning=True,
        cost_per_million_input=10.0,
        cost_per_million_output=40.0,
        knowledge_cutoff="2025-01",
        special_features=["advanced_reasoning", "compact_model", "fast_inference"]
    ),
    OpenAIModel.GPT_4O.value: ModelSpec(
        name="GPT-4o",
        provider=AIProvider.OPENAI,
        context_window=128000,
        max_output_tokens=16384,
        supports_vision=True,
        supports_function_calling=True,
        cost_per_million_input=5.0,
        cost_per_million_output=15.0,
        knowledge_cutoff="2024-04",
        special_features=["multimodal", "real_time_capabilities", "voice_mode"]
    ),
    
    # Anthropic Models
    AnthropicModel.CLAUDE_4_OPUS.value: ModelSpec(
        name="Claude 4 Opus",
        provider=AIProvider.ANTHROPIC,
        context_window=200000,
        max_output_tokens=32000,
        supports_vision=True,
        supports_function_calling=True,
        cost_per_million_input=15.0,
        cost_per_million_output=75.0,
        knowledge_cutoff="2025-03",
        special_features=["superior_reasoning", "enterprise_grade", "extended_thinking"]
    ),
    AnthropicModel.CLAUDE_3_7_SONNET.value: ModelSpec(
        name="Claude 3.7 Sonnet",
        provider=AIProvider.ANTHROPIC,
        context_window=200000,
        max_output_tokens=64000,
        supports_vision=True,
        supports_function_calling=True,
        supports_reasoning=True,
        cost_per_million_input=3.0,
        cost_per_million_output=15.0,
        knowledge_cutoff="2024-11",
        special_features=["extended_thinking", "hybrid_reasoning", "action_scaling"]
    ),
    
    # xAI Models
    XAIModel.GROK_3.value: ModelSpec(
        name="Grok 3",
        provider=AIProvider.XAI,
        context_window=32000,
        max_output_tokens=8192,
        supports_vision=True,
        supports_function_calling=True,
        supports_real_time=True,
        cost_per_million_input=5.0,
        cost_per_million_output=20.0,
        knowledge_cutoff="2025-02",
        special_features=["real_time_info", "think_mode", "big_brain_mode", "x_integration"]
    ),
}

@dataclass
class ChatMessage:
    """Chat message structure"""
    role: str  # "user", "assistant", "system"
    content: str
    images: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ChatResponse:
    """Standardized chat response"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    metadata: Optional[Dict[str, Any]] = None

class RateLimiter:
    """Simple rate limiter for API calls"""
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    async def acquire(self):
        now = time.time()
        # Remove calls older than 1 minute
        self.calls = [call_time for call_time in self.calls if now - call_time < 60]
        
        if len(self.calls) >= self.calls_per_minute:
            wait_time = 60 - (now - self.calls[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        self.calls.append(now)

class MultiProviderAPI:
    """
    Advanced Multi-Provider AI API Client
    Supports OpenAI, Anthropic, xAI, Google and other providers
    """
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 anthropic_api_key: Optional[str] = None,
                 xai_api_key: Optional[str] = None,
                 google_api_key: Optional[str] = None,
                 rate_limit_calls_per_minute: int = 60):
        self.openai_client = None
        self.anthropic_client = None
        self.xai_client = None
        self.google_client = None
        
        # Initialize clients
        if openai_api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        
        if anthropic_api_key:
            self.anthropic_client = AsyncAnthropic(api_key=anthropic_api_key)
        
        # Rate limiter
        self.rate_limiter = RateLimiter(rate_limit_calls_per_minute)
        
        # HTTP client for custom APIs
        self.http_client = httpx.AsyncClient(timeout=120.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()
        if self.openai_client:
            await self.openai_client.close()
        if self.anthropic_client:
            await self.anthropic_client.close()
    
    def _get_provider_from_model(self, model: str) -> AIProvider:
        """Determine provider from model name"""
        if model in [m.value for m in OpenAIModel]:
            return AIProvider.OPENAI
        elif model in [m.value for m in AnthropicModel]:
            return AIProvider.ANTHROPIC
        elif model in [m.value for m in XAIModel]:
            return AIProvider.XAI
        elif model in [m.value for m in GoogleModel]:
            return AIProvider.GOOGLE
        else:
            raise ValueError(f"Unknown model: {model}")
    
    async def chat_completion(self,
                            messages: List[Dict[str, str]],
                            model: str,
                            temperature: float = 0.7,
                            max_tokens: Optional[int] = None,
                            stream: bool = False,
                            tools: Optional[List[Dict]] = None,
                            **kwargs) -> Union[ChatResponse, AsyncIterator[str]]:
        """
        Universal chat completion interface
        """
        await self.rate_limiter.acquire()
        
        provider = self._get_provider_from_model(model)
        
        if provider == AIProvider.OPENAI:
            return await self._openai_chat_completion(
                messages, model, temperature, max_tokens, stream, tools, **kwargs
            )
        elif provider == AIProvider.ANTHROPIC:
            return await self._anthropic_chat_completion(
                messages, model, temperature, max_tokens, stream, tools, **kwargs
            )
        elif provider == AIProvider.XAI:
            return await self._xai_chat_completion(
                messages, model, temperature, max_tokens, stream, tools, **kwargs
            )
        else:
            raise ValueError(f"Provider {provider} not implemented yet")
    
    async def _openai_chat_completion(self, messages, model, temperature, max_tokens, stream, tools, **kwargs):
        """OpenAI chat completion"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        try:
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": stream
            }
            
            if max_tokens:
                request_params["max_tokens"] = max_tokens
            if tools:
                request_params["tools"] = tools
            
            # Add reasoning mode for o-series models
            if model.startswith("o"):
                request_params["reasoning"] = kwargs.get("reasoning", True)
            
            response = await self.openai_client.chat.completions.create(**request_params)
            
            if stream:
                return self._openai_stream_generator(response)
            else:
                return ChatResponse(
                    content=response.choices[0].message.content,
                    model=response.model,
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    finish_reason=response.choices[0].finish_reason
                )
        
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _anthropic_chat_completion(self, messages, model, temperature, max_tokens, stream, tools, **kwargs):
        """Anthropic chat completion"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized")
        
        try:
            # Convert messages format
            system_message = None
            formatted_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    formatted_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            request_params = {
                "model": model,
                "messages": formatted_messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 4096,
                "stream": stream
            }
            
            if system_message:
                request_params["system"] = system_message
            
            if tools:
                request_params["tools"] = tools
            
            # Extended thinking for Claude 3.7
            if "3-7" in model:
                request_params["extended_thinking"] = kwargs.get("extended_thinking", True)
            
            response = await self.anthropic_client.messages.create(**request_params)
            
            if stream:
                return self._anthropic_stream_generator(response)
            else:
                return ChatResponse(
                    content=response.content[0].text,
                    model=response.model,
                    usage={
                        "prompt_tokens": response.usage.input_tokens,
                        "completion_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                    },
                    finish_reason=response.stop_reason
                )
        
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    async def _xai_chat_completion(self, messages, model, temperature, max_tokens, stream, tools, **kwargs):
        """xAI Grok chat completion"""
        try:
            # Grok 3 special modes
            mode = kwargs.get("mode", "fast")  # fast, think, big_brain
            real_time = kwargs.get("real_time_info", False)
            
            request_data = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 4096,
                "stream": stream,
                "mode": mode,
                "real_time_info": real_time
            }
            
            if tools:
                request_data["tools"] = tools
            
            # Mock response for now (actual xAI API integration would go here)
            return ChatResponse(
                content=f"Grok 3 response in {mode} mode (simulated)",
                model=model,
                usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                finish_reason="stop",
                metadata={"mode": mode, "real_time": real_time}
            )
        
        except Exception as e:
            logger.error(f"xAI API error: {e}")
            raise
    
    async def _openai_stream_generator(self, response):
        """Generator for OpenAI streaming responses"""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def _anthropic_stream_generator(self, response):
        """Generator for Anthropic streaming responses"""
        async for chunk in response:
            if chunk.type == "content_block_delta":
                yield chunk.delta.text
    
    def get_model_info(self, model: str) -> ModelSpec:
        """Get detailed information about a model"""
        return MODEL_SPECS.get(model, ModelSpec(
            name=model,
            provider=self._get_provider_from_model(model),
            context_window=128000,
            max_output_tokens=4096,
            cost_per_million_input=5.0,
            cost_per_million_output=15.0
        ))
    
    def list_models(self, provider: Optional[AIProvider] = None) -> List[str]:
        """List available models, optionally filtered by provider"""
        all_models = []
        
        model_enums = [OpenAIModel, AnthropicModel, XAIModel, GoogleModel]
        
        for enum_class in model_enums:
            if provider is None or MODEL_SPECS.get(list(enum_class)[0].value, ModelSpec("", AIProvider.OPENAI, 0, 0)).provider == provider:
                all_models.extend([model.value for model in enum_class])
        
        return sorted(all_models)

# Convenience functions
async def get_completion(prompt: str, 
                        model: str = OpenAIModel.GPT_4O.value,
                        temperature: float = 0.7,
                        max_tokens: Optional[int] = None,
                        **kwargs) -> str:
    """Get a simple completion from any supported model"""
    async with MultiProviderAPI() as api:
        messages = [{"role": "user", "content": prompt}]
        response = await api.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        return response.content

async def get_reasoning_completion(prompt: str,
                                 model: str = OpenAIModel.O3.value,
                                 **kwargs) -> str:
    """Get a reasoning completion from o-series or Claude models"""
    reasoning_models = [
        OpenAIModel.O3.value, OpenAIModel.O3_MINI.value,
        AnthropicModel.CLAUDE_3_7_SONNET.value,
        AnthropicModel.CLAUDE_4_OPUS.value
    ]
    
    if model not in reasoning_models:
        model = OpenAIModel.O3.value
    
    return await get_completion(prompt, model, reasoning=True, **kwargs)

async def get_multimodal_completion(prompt: str,
                                  images: List[str],
                                  model: str = OpenAIModel.GPT_4O.value,
                                  **kwargs) -> str:
    """Get completion with vision capabilities"""
    vision_models = [
        OpenAIModel.GPT_4O.value, OpenAIModel.GPT_4_1.value,
        AnthropicModel.CLAUDE_4_OPUS.value, AnthropicModel.CLAUDE_3_7_SONNET.value,
        XAIModel.GROK_3.value
    ]
    
    if model not in vision_models:
        model = OpenAIModel.GPT_4O.value
    
    async with MultiProviderAPI() as api:
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                *[{"type": "image_url", "image_url": {"url": img}} for img in images]
            ]
        }]
        response = await api.chat_completion(messages=messages, model=model, **kwargs)
        return response.content

# Export all public classes and functions
__all__ = [
    "MultiProviderAPI", "ChatMessage", "ChatResponse",
    "OpenAIModel", "AnthropicModel", "XAIModel", "GoogleModel", "AIProvider",
    "ModelSpec", "MODEL_SPECS",
    "get_completion", "get_reasoning_completion", "get_multimodal_completion"
] 