"""
OpenDistillery Multi-Provider AI API Integration
Supports OpenAI, Anthropic, and xAI with latest models (2025)
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import logging
import httpx
from datetime import datetime, timedelta
import os
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    """Supported AI providers with latest models"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    XAI = "xai"

class OpenAIModel(Enum):
    """Latest OpenAI models (2025)"""
    O4 = "o4"
    O4_MINI = "o4-mini"
    O3 = "o3"
    O3_MINI = "o3-mini"
    O1 = "o1"
    O1_MINI = "o1-mini"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4_1 = "gpt-4.1"
    GPT_4_1_TURBO = "gpt-4.1-turbo"
    CLAUDE_SONNET_4 = "claude-3.5-sonnet"  # Latest Claude model
    
class AnthropicModel(Enum):
    """Latest Anthropic models (2025)"""
    CLAUDE_4_OPUS = "claude-4-opus"
    CLAUDE_4_SONNET = "claude-4-sonnet"
    CLAUDE_4_HAIKU = "claude-4-haiku"
    CLAUDE_3_5_OPUS = "claude-3.5-opus"
    CLAUDE_3_5_SONNET = "claude-3.5-sonnet"

class XAIModel(Enum):
    """Latest xAI models (2025)"""
    GROK_2 = "grok-2"
    GROK_2_MINI = "grok-2-mini"
    GROK_3 = "grok-3"
    GROK_3_BETA = "grok-3-beta"

@dataclass
class ModelCapabilities:
    """Model capabilities and specifications"""
    max_tokens: int
    context_window: int
    supports_streaming: bool = True
    supports_function_calling: bool = True
    supports_vision: bool = False
    supports_multimodal: bool = False
    reasoning_optimized: bool = False
    cost_per_1k_tokens: float = 0.0
    rate_limit_rpm: int = 10000
    
# Latest model specifications (2025)
MODEL_SPECS = {
    # OpenAI Latest Models
    OpenAIModel.O4.value: ModelCapabilities(
        max_tokens=128000,
        context_window=200000,
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_multimodal=True,
        reasoning_optimized=True,
        cost_per_1k_tokens=0.06,
        rate_limit_rpm=10000
    ),
    OpenAIModel.O4_MINI.value: ModelCapabilities(
        max_tokens=64000,
        context_window=128000,
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_multimodal=True,
        reasoning_optimized=True,
        cost_per_1k_tokens=0.015,
        rate_limit_rpm=15000
    ),
    OpenAIModel.O3.value: ModelCapabilities(
        max_tokens=128000,
        context_window=200000,
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_multimodal=True,
        reasoning_optimized=True,
        cost_per_1k_tokens=0.05,
        rate_limit_rpm=8000
    ),
    OpenAIModel.O1.value: ModelCapabilities(
        max_tokens=100000,
        context_window=128000,
        supports_streaming=False,
        supports_function_calling=True,
        supports_vision=False,
        supports_multimodal=False,
        reasoning_optimized=True,
        cost_per_1k_tokens=0.04,
        rate_limit_rpm=5000
    ),
    OpenAIModel.GPT_4_1.value: ModelCapabilities(
        max_tokens=16384,
        context_window=32768,
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_multimodal=True,
        reasoning_optimized=False,
        cost_per_1k_tokens=0.03,
        rate_limit_rpm=12000
    ),
    
    # Anthropic Latest Models
    AnthropicModel.CLAUDE_4_OPUS.value: ModelCapabilities(
        max_tokens=200000,
        context_window=1000000,
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_multimodal=True,
        reasoning_optimized=True,
        cost_per_1k_tokens=0.075,
        rate_limit_rpm=5000
    ),
    AnthropicModel.CLAUDE_4_SONNET.value: ModelCapabilities(
        max_tokens=200000,
        context_window=500000,
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_multimodal=True,
        reasoning_optimized=True,
        cost_per_1k_tokens=0.03,
        rate_limit_rpm=8000
    ),
    
    # xAI Latest Models
    XAIModel.GROK_3.value: ModelCapabilities(
        max_tokens=131072,
        context_window=1000000,
        supports_streaming=True,
        supports_function_calling=True,
        supports_vision=True,
        supports_multimodal=True,
        reasoning_optimized=True,
        cost_per_1k_tokens=0.05,
        rate_limit_rpm=6000
    ),
}

@dataclass
class APIResponse:
    """Standardized API response"""
    content: str
    model: str
    provider: str
    usage: Dict[str, int]
    latency_ms: float
    reasoning_steps: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class RateLimiter:
    """Advanced rate limiter with exponential backoff"""
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        async with self.lock:
            now = datetime.now()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < timedelta(minutes=1)]
            
            if len(self.requests) >= self.max_requests:
                sleep_time = 60 - (now - self.requests[0]).total_seconds()
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            self.requests.append(now)

class MultiProviderAPI:
    """
    Advanced multi-provider AI API client with latest models (2025)
    Supports OpenAI, Anthropic, and xAI with intelligent routing
    """
    
    def __init__(self):
        self.providers = {}
        self.rate_limiters = {}
        self.client = httpx.AsyncClient(timeout=60.0)
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize API providers with latest models"""
        # OpenAI Configuration
        if openai_key := os.getenv("OPENAI_API_KEY"):
            self.providers[AIProvider.OPENAI] = {
                "api_key": openai_key,
                "base_url": "https://api.openai.com/v1",
                "models": [model.value for model in OpenAIModel]
            }
            self.rate_limiters[AIProvider.OPENAI] = RateLimiter(10000)
        
        # Anthropic Configuration
        if anthropic_key := os.getenv("ANTHROPIC_API_KEY"):
            self.providers[AIProvider.ANTHROPIC] = {
                "api_key": anthropic_key,
                "base_url": "https://api.anthropic.com/v1",
                "models": [model.value for model in AnthropicModel]
            }
            self.rate_limiters[AIProvider.ANTHROPIC] = RateLimiter(5000)
        
        # xAI Configuration
        if xai_key := os.getenv("XAI_API_KEY"):
            self.providers[AIProvider.XAI] = {
                "api_key": xai_key,
                "base_url": "https://api.x.ai/v1",
                "models": [model.value for model in XAIModel]
            }
            self.rate_limiters[AIProvider.XAI] = RateLimiter(6000)
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        provider: Optional[AIProvider] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[APIResponse, AsyncGenerator[str, None]]:
        """
        Universal chat completion with latest models
        """
        start_time = time.time()
        
        # Auto-detect provider if not specified
        if not provider:
            provider = self._detect_provider(model)
        
        if provider not in self.providers:
            raise ValueError(f"Provider {provider.value} not configured")
        
        # Apply rate limiting
        await self.rate_limiters[provider].acquire()
        
        # Get model capabilities
        model_caps = MODEL_SPECS.get(model, ModelCapabilities(max_tokens=4096, context_window=8192))
        if max_tokens is None:
            max_tokens = min(model_caps.max_tokens, 4096)
        
        try:
            if provider == AIProvider.OPENAI:
                response = await self._openai_completion(
                    messages, model, temperature, max_tokens, stream, **kwargs
                )
            elif provider == AIProvider.ANTHROPIC:
                response = await self._anthropic_completion(
                    messages, model, temperature, max_tokens, stream, **kwargs
                )
            elif provider == AIProvider.XAI:
                response = await self._xai_completion(
                    messages, model, temperature, max_tokens, stream, **kwargs
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            if stream:
                return response
            
            latency_ms = (time.time() - start_time) * 1000
            
            return APIResponse(
                content=response["content"],
                model=model,
                provider=provider.value,
                usage=response.get("usage", {}),
                latency_ms=latency_ms,
                reasoning_steps=response.get("reasoning_steps"),
                confidence_score=response.get("confidence_score"),
                metadata=response.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"API call failed for {provider.value}/{model}: {e}")
            raise
    
    async def _openai_completion(self, messages, model, temperature, max_tokens, stream, **kwargs):
        """OpenAI API completion with latest models"""
        provider_config = self.providers[AIProvider.OPENAI]
        
        headers = {
            "Authorization": f"Bearer {provider_config['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            **kwargs
        }
        
        # Special handling for reasoning models (o1, o3, o4)
        if any(reasoning_model in model for reasoning_model in ["o1", "o3", "o4"]):
            payload["reasoning_effort"] = kwargs.get("reasoning_effort", "medium")
            if "o1" in model:
                # o1 models don't support streaming
                payload["stream"] = False
        
        url = urljoin(provider_config["base_url"], "chat/completions")
        
        if stream:
            return self._stream_openai_response(url, headers, payload)
        
        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        choice = data["choices"][0]
        
        result = {
            "content": choice["message"]["content"],
            "usage": data.get("usage", {}),
            "metadata": {"finish_reason": choice.get("finish_reason")}
        }
        
        # Extract reasoning steps for reasoning-optimized models
        if any(reasoning_model in model for reasoning_model in ["o1", "o3", "o4"]):
            reasoning_content = choice["message"].get("reasoning", "")
            if reasoning_content:
                result["reasoning_steps"] = reasoning_content.split("\n")
                result["confidence_score"] = self._calculate_confidence(reasoning_content)
        
        return result
    
    async def _anthropic_completion(self, messages, model, temperature, max_tokens, stream, **kwargs):
        """Anthropic API completion with latest Claude models"""
        provider_config = self.providers[AIProvider.ANTHROPIC]
        
        headers = {
            "x-api-key": provider_config['api_key'],
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Convert OpenAI format to Anthropic format
        system_message = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            **kwargs
        }
        
        if system_message:
            payload["system"] = system_message
        
        url = urljoin(provider_config["base_url"], "messages")
        
        if stream:
            return self._stream_anthropic_response(url, headers, payload)
        
        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        result = {
            "content": data["content"][0]["text"],
            "usage": data.get("usage", {}),
            "metadata": {"stop_reason": data.get("stop_reason")}
        }
        
        return result
    
    async def _xai_completion(self, messages, model, temperature, max_tokens, stream, **kwargs):
        """xAI (Grok) API completion with latest models"""
        provider_config = self.providers[AIProvider.XAI]
        
        headers = {
            "Authorization": f"Bearer {provider_config['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            **kwargs
        }
        
        url = urljoin(provider_config["base_url"], "chat/completions")
        
        if stream:
            return self._stream_xai_response(url, headers, payload)
        
        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        choice = data["choices"][0]
        
        result = {
            "content": choice["message"]["content"],
            "usage": data.get("usage", {}),
            "metadata": {"finish_reason": choice.get("finish_reason")}
        }
        
        return result
    
    async def _stream_openai_response(self, url, headers, payload):
        """Stream OpenAI response"""
        async with self.client.stream("POST", url, headers=headers, json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        if chunk["choices"][0]["delta"].get("content"):
                            yield chunk["choices"][0]["delta"]["content"]
                    except json.JSONDecodeError:
                        continue
    
    def _detect_provider(self, model: str) -> AIProvider:
        """Auto-detect provider based on model name"""
        model_lower = model.lower()
        
        if any(openai_model in model_lower for openai_model in ["gpt", "o1", "o3", "o4"]):
            return AIProvider.OPENAI
        elif "claude" in model_lower:
            return AIProvider.ANTHROPIC
        elif "grok" in model_lower:
            return AIProvider.XAI
        else:
            # Default to OpenAI
            return AIProvider.OPENAI
    
    def _calculate_confidence(self, reasoning_content: str) -> float:
        """Calculate confidence score based on reasoning content"""
        if not reasoning_content:
            return 0.5
        
        confidence_indicators = [
            "certain", "confident", "definitely", "clearly", "obviously",
            "undoubtedly", "conclusively", "precisely", "exactly"
        ]
        uncertainty_indicators = [
            "maybe", "perhaps", "possibly", "might", "could", "uncertain",
            "unclear", "ambiguous", "tentative", "speculative"
        ]
        
        content_lower = reasoning_content.lower()
        confidence_count = sum(1 for indicator in confidence_indicators if indicator in content_lower)
        uncertainty_count = sum(1 for indicator in uncertainty_indicators if indicator in content_lower)
        
        # Base confidence score
        base_score = 0.7
        confidence_boost = min(confidence_count * 0.05, 0.3)
        uncertainty_penalty = min(uncertainty_count * 0.1, 0.4)
        
        return max(0.1, min(1.0, base_score + confidence_boost - uncertainty_penalty))
    
    def get_available_models(self, provider: Optional[AIProvider] = None) -> Dict[str, List[str]]:
        """Get available models for providers"""
        if provider:
            return {provider.value: self.providers.get(provider, {}).get("models", [])}
        
        return {
            provider_enum.value: config.get("models", [])
            for provider_enum, config in self.providers.items()
        }
    
    def get_model_capabilities(self, model: str) -> ModelCapabilities:
        """Get capabilities for a specific model"""
        return MODEL_SPECS.get(model, ModelCapabilities(max_tokens=4096, context_window=8192))
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

# Global instance for easy access
api_client = MultiProviderAPI()

async def get_completion(
    prompt: str,
    model: str = "o4",
    provider: Optional[AIProvider] = None,
    **kwargs
) -> APIResponse:
    """
    Convenience function for single prompt completion
    """
    messages = [{"role": "user", "content": prompt}]
    return await api_client.chat_completion(messages, model, provider, **kwargs)

async def get_reasoning_completion(
    prompt: str,
    model: str = "o4",
    reasoning_effort: str = "high",
    **kwargs
) -> APIResponse:
    """
    Specialized function for reasoning-optimized models
    """
    if not any(reasoning_model in model for reasoning_model in ["o1", "o3", "o4"]):
        logger.warning(f"Model {model} is not optimized for reasoning. Consider using o1, o3, or o4.")
    
    messages = [{"role": "user", "content": prompt}]
    return await api_client.chat_completion(
        messages,
        model,
        reasoning_effort=reasoning_effort,
        **kwargs
    ) 