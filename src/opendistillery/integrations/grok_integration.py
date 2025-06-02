"""
OpenDistillery Grok API Integration
Complete xAI (Grok) API integration with latest models and enterprise features
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Union, AsyncGenerator, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import httpx
from datetime import datetime, timedelta
import os
from urllib.parse import urljoin
import base64
from pathlib import Path

logger = logging.getLogger(__name__)

class GrokModel(Enum):
    """Latest Grok models with comprehensive support"""
    GROK_3 = "grok-3"
    GROK_3_BETA = "grok-3-beta"
    GROK_2 = "grok-2"
    GROK_2_MINI = "grok-2-mini"
    GROK_1_5 = "grok-1.5"
    GROK_1_5_VISION = "grok-1.5-vision"

class GrokCapability(Enum):
    """Grok model capabilities"""
    TEXT_GENERATION = "text_generation"
    REAL_TIME_INFO = "real_time_info"
    IMAGE_ANALYSIS = "image_analysis"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    REASONING = "reasoning"
    MULTIMODAL = "multimodal"

@dataclass
class GrokModelSpec:
    """Detailed Grok model specifications"""
    name: str
    max_tokens: int
    context_window: int
    capabilities: List[GrokCapability]
    cost_per_1k_tokens: float
    rate_limit_rpm: int
    real_time_knowledge: bool = True
    vision_support: bool = False
    function_calling_support: bool = True
    reasoning_optimized: bool = True

# Comprehensive Grok model specifications
GROK_MODEL_SPECS = {
    GrokModel.GROK_3.value: GrokModelSpec(
        name="Grok 3",
        max_tokens=131072,
        context_window=1000000,
        capabilities=[
            GrokCapability.TEXT_GENERATION,
            GrokCapability.REAL_TIME_INFO,
            GrokCapability.FUNCTION_CALLING,
            GrokCapability.STREAMING,
            GrokCapability.REASONING,
            GrokCapability.MULTIMODAL
        ],
        cost_per_1k_tokens=0.05,
        rate_limit_rpm=6000,
        real_time_knowledge=True,
        vision_support=True,
        function_calling_support=True,
        reasoning_optimized=True
    ),
    GrokModel.GROK_3_BETA.value: GrokModelSpec(
        name="Grok 3 Beta",
        max_tokens=131072,
        context_window=1000000,
        capabilities=[
            GrokCapability.TEXT_GENERATION,
            GrokCapability.REAL_TIME_INFO,
            GrokCapability.FUNCTION_CALLING,
            GrokCapability.STREAMING,
            GrokCapability.REASONING,
            GrokCapability.MULTIMODAL
        ],
        cost_per_1k_tokens=0.03,
        rate_limit_rpm=8000,
        real_time_knowledge=True,
        vision_support=True,
        function_calling_support=True,
        reasoning_optimized=True
    ),
    GrokModel.GROK_2.value: GrokModelSpec(
        name="Grok 2",
        max_tokens=65536,
        context_window=128000,
        capabilities=[
            GrokCapability.TEXT_GENERATION,
            GrokCapability.REAL_TIME_INFO,
            GrokCapability.FUNCTION_CALLING,
            GrokCapability.STREAMING,
            GrokCapability.REASONING
        ],
        cost_per_1k_tokens=0.02,
        rate_limit_rpm=10000,
        real_time_knowledge=True,
        function_calling_support=True,
        reasoning_optimized=True
    ),
    GrokModel.GROK_1_5_VISION.value: GrokModelSpec(
        name="Grok 1.5 Vision",
        max_tokens=32768,
        context_window=64000,
        capabilities=[
            GrokCapability.TEXT_GENERATION,
            GrokCapability.IMAGE_ANALYSIS,
            GrokCapability.STREAMING,
            GrokCapability.MULTIMODAL
        ],
        cost_per_1k_tokens=0.015,
        rate_limit_rpm=12000,
        vision_support=True,
        function_calling_support=True
    )
}

@dataclass
class GrokResponse:
    """Standardized Grok API response"""
    content: str
    model: str
    usage: Dict[str, int]
    latency_ms: float
    real_time_info: Optional[Dict[str, Any]] = None
    reasoning_trace: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    function_calls: Optional[List[Dict[str, Any]]] = None

@dataclass
class GrokFunction:
    """Function definition for Grok function calling"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Optional[Callable] = None

class GrokRateLimiter:
    """Advanced rate limiter with burst handling for Grok API"""
    def __init__(self, requests_per_minute: int = 6000, burst_size: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.requests = []
        self.burst_tokens = burst_size
        self.last_refill = datetime.now()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        async with self.lock:
            now = datetime.now()
            
            # Refill burst tokens
            time_since_refill = (now - self.last_refill).total_seconds()
            if time_since_refill >= 60:  # Refill every minute
                self.burst_tokens = min(self.burst_size, self.burst_tokens + 1)
                self.last_refill = now
            
            # Remove old requests
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < timedelta(minutes=1)]
            
            # Check burst tokens first
            if self.burst_tokens > 0:
                self.burst_tokens -= 1
                self.requests.append(now)
                return
            
            # Check regular rate limit
            if len(self.requests) >= self.requests_per_minute:
                sleep_time = 60 - (now - self.requests[0]).total_seconds()
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            self.requests.append(now)

class GrokAPIClient:
    """
    Professional Grok API client with enterprise features
    Supports all Grok models with real-time information, function calling, and vision
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        self.base_url = base_url or "https://api.x.ai/v1"
        
        if not self.api_key:
            raise ValueError("XAI_API_KEY environment variable or api_key parameter required")
        
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        
        self.rate_limiter = GrokRateLimiter()
        self.usage_stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "errors": 0,
            "average_latency": 0.0
        }
        self.functions: Dict[str, GrokFunction] = {}
        
        logger.info("Grok API client initialized")
    
    def register_function(self, function: GrokFunction):
        """Register a function for function calling"""
        self.functions[function.name] = function
        logger.info(f"Registered function: {function.name}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Union[str, GrokModel] = GrokModel.GROK_3,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        functions: Optional[List[GrokFunction]] = None,
        real_time_info: bool = True,
        **kwargs
    ) -> Union[GrokResponse, AsyncGenerator[str, None]]:
        """
        Chat completion with comprehensive Grok features
        """
        start_time = time.time()
        
        # Apply rate limiting
        await self.rate_limiter.acquire()
        
        # Normalize model name
        if isinstance(model, GrokModel):
            model_name = model.value
        else:
            model_name = model
        
        # Get model specifications
        model_spec = GROK_MODEL_SPECS.get(model_name)
        if not model_spec:
            raise ValueError(f"Unsupported Grok model: {model_name}")
        
        # Set default max_tokens based on model
        if max_tokens is None:
            max_tokens = min(model_spec.max_tokens // 4, 4096)
        
        # Prepare request payload
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            **kwargs
        }
        
        # Add real-time information if supported
        if real_time_info and model_spec.real_time_knowledge:
            payload["real_time"] = True
        
        # Add function calling if provided
        if functions and model_spec.function_calling_support:
            payload["functions"] = [
                {
                    "name": func.name,
                    "description": func.description,
                    "parameters": func.parameters
                }
                for func in functions
            ]
            payload["function_call"] = "auto"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OpenDistillery/2.0.0"
        }
        
        try:
            if stream:
                return self._stream_completion(headers, payload, start_time)
            else:
                return await self._complete_request(headers, payload, model_name, start_time)
                
        except Exception as e:
            self.usage_stats["errors"] += 1
            logger.error(f"Grok API request failed: {e}")
            raise
    
    async def _complete_request(
        self, 
        headers: Dict[str, str], 
        payload: Dict[str, Any],
        model_name: str,
        start_time: float
    ) -> GrokResponse:
        """Complete non-streaming request"""
        url = urljoin(self.base_url, "chat/completions")
        
        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        choice = data["choices"][0]
        message = choice["message"]
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Update usage statistics
        usage = data.get("usage", {})
        self.usage_stats["total_requests"] += 1
        self.usage_stats["total_tokens"] += usage.get("total_tokens", 0)
        self.usage_stats["average_latency"] = (
            (self.usage_stats["average_latency"] * (self.usage_stats["total_requests"] - 1) + latency_ms) /
            self.usage_stats["total_requests"]
        )
        
        # Extract content and metadata
        content = message.get("content", "")
        function_calls = []
        
        # Handle function calls
        if "function_call" in message:
            func_call = message["function_call"]
            function_calls.append({
                "name": func_call["name"],
                "arguments": json.loads(func_call["arguments"])
            })
        
        # Extract real-time information if available
        real_time_info = data.get("real_time_info")
        
        # Extract reasoning trace if available
        reasoning_trace = None
        if "reasoning" in data:
            reasoning_trace = data["reasoning"].split("\n") if data["reasoning"] else None
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(choice, data)
        
        return GrokResponse(
            content=content,
            model=model_name,
            usage=usage,
            latency_ms=latency_ms,
            real_time_info=real_time_info,
            reasoning_trace=reasoning_trace,
            confidence_score=confidence_score,
            metadata={
                "finish_reason": choice.get("finish_reason"),
                "timestamp": datetime.now().isoformat(),
                "real_time_enabled": payload.get("real_time", False)
            },
            function_calls=function_calls
        )
    
    async def _stream_completion(
        self, 
        headers: Dict[str, str], 
        payload: Dict[str, Any],
        start_time: float
    ) -> AsyncGenerator[str, None]:
        """Stream completion response"""
        url = urljoin(self.base_url, "chat/completions")
        
        async with self.client.stream("POST", url, headers=headers, json=payload) as response:
            response.raise_for_status()
            
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
    
    async def vision_completion(
        self,
        prompt: str,
        images: List[Union[str, bytes, Path]],
        model: Union[str, GrokModel] = GrokModel.GROK_1_5_VISION,
        **kwargs
    ) -> GrokResponse:
        """
        Vision completion with image analysis
        """
        # Normalize model
        if isinstance(model, GrokModel):
            model_name = model.value
        else:
            model_name = model
        
        # Check vision support
        model_spec = GROK_MODEL_SPECS.get(model_name)
        if not model_spec or not model_spec.vision_support:
            raise ValueError(f"Model {model_name} does not support vision")
        
        # Prepare messages with images
        message_content = [{"type": "text", "text": prompt}]
        
        for image in images:
            if isinstance(image, (str, Path)):
                # File path or URL
                if str(image).startswith(("http://", "https://")):
                    message_content.append({
                        "type": "image_url",
                        "image_url": {"url": str(image)}
                    })
                else:
                    # Local file
                    with open(image, "rb") as f:
                        image_data = base64.b64encode(f.read()).decode()
                    message_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    })
            elif isinstance(image, bytes):
                # Raw image bytes
                image_data = base64.b64encode(image).decode()
                message_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                })
        
        messages = [{"role": "user", "content": message_content}]
        
        return await self.chat_completion(
            messages=messages,
            model=model_name,
            **kwargs
        )
    
    async def function_calling_completion(
        self,
        prompt: str,
        functions: List[GrokFunction],
        model: Union[str, GrokModel] = GrokModel.GROK_3,
        execute_functions: bool = False,
        **kwargs
    ) -> GrokResponse:
        """
        Function calling completion with optional execution
        """
        messages = [{"role": "user", "content": prompt}]
        
        response = await self.chat_completion(
            messages=messages,
            model=model,
            functions=functions,
            **kwargs
        )
        
        # Execute functions if requested
        if execute_functions and response.function_calls:
            for func_call in response.function_calls:
                func_name = func_call["name"]
                func_args = func_call["arguments"]
                
                if func_name in self.functions:
                    function_def = self.functions[func_name]
                    if function_def.handler:
                        try:
                            result = await function_def.handler(**func_args)
                            # Add function result to metadata
                            if "function_results" not in response.metadata:
                                response.metadata["function_results"] = {}
                            response.metadata["function_results"][func_name] = result
                        except Exception as e:
                            logger.error(f"Function execution failed: {func_name} - {e}")
                            response.metadata.setdefault("function_errors", {})[func_name] = str(e)
        
        return response
    
    def _calculate_confidence(self, choice: Dict[str, Any], data: Dict[str, Any]) -> float:
        """Calculate confidence score based on response characteristics"""
        base_confidence = 0.8
        
        # Adjust based on finish reason
        finish_reason = choice.get("finish_reason", "stop")
        if finish_reason == "stop":
            confidence_adj = 0.1
        elif finish_reason == "length":
            confidence_adj = -0.1
        else:
            confidence_adj = -0.2
        
        # Adjust based on response length
        content_length = len(choice.get("message", {}).get("content", ""))
        if content_length > 100:
            length_adj = 0.05
        elif content_length < 20:
            length_adj = -0.1
        else:
            length_adj = 0.0
        
        # Adjust based on real-time information usage
        real_time_adj = 0.05 if data.get("real_time_info") else 0.0
        
        final_confidence = base_confidence + confidence_adj + length_adj + real_time_adj
        return max(0.1, min(1.0, final_confidence))
    
    def get_model_info(self, model: Union[str, GrokModel]) -> GrokModelSpec:
        """Get detailed model information"""
        if isinstance(model, GrokModel):
            model_name = model.value
        else:
            model_name = model
        
        return GROK_MODEL_SPECS.get(model_name)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        return {
            **self.usage_stats,
            "registered_functions": len(self.functions),
            "available_models": list(GROK_MODEL_SPECS.keys()),
            "timestamp": datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of Grok API"""
        try:
            start_time = time.time()
            
            response = await self.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                model=GrokModel.GROK_2_MINI,
                max_tokens=10
            )
            
            latency = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "latency_ms": latency,
                "model_available": True,
                "api_key_valid": True,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_key_valid": bool(self.api_key),
                "timestamp": datetime.now().isoformat()
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

# Convenience functions
async def get_grok_completion(
    prompt: str,
    model: Union[str, GrokModel] = GrokModel.GROK_3,
    **kwargs
) -> GrokResponse:
    """Quick Grok completion"""
    async with GrokAPIClient() as client:
        return await client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            **kwargs
        )

async def get_grok_vision_analysis(
    prompt: str,
    images: List[Union[str, bytes, Path]],
    **kwargs
) -> GrokResponse:
    """Quick Grok vision analysis"""
    async with GrokAPIClient() as client:
        return await client.vision_completion(prompt, images, **kwargs)

# Example function definitions for function calling
def create_search_function() -> GrokFunction:
    """Create a web search function for Grok"""
    return GrokFunction(
        name="web_search",
        description="Search the web for current information",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    )

def create_calculator_function() -> GrokFunction:
    """Create a calculator function for Grok"""
    return GrokFunction(
        name="calculate",
        description="Perform mathematical calculations",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    ) 