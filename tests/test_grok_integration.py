"""
Comprehensive test suite for Grok API integration
Tests all Grok models, features, and enterprise functionality
"""

import asyncio
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from pathlib import Path
import base64
import os

from src.integrations.grok_integration import (
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

class TestGrokModels:
    """Test Grok model definitions and specifications"""
    
    def test_grok_model_enumeration(self):
        """Test all Grok models are properly defined"""
        expected_models = [
            "grok-3", "grok-3-beta", "grok-2", 
            "grok-2-mini", "grok-1.5", "grok-1.5-vision"
        ]
        
        for model in expected_models:
            assert any(gm.value == model for gm in GrokModel)
    
    def test_grok_model_specifications(self):
        """Test Grok model specifications are complete"""
        for model_name, spec in GROK_MODEL_SPECS.items():
            assert isinstance(spec, GrokModelSpec)
            assert spec.max_tokens > 0
            assert spec.context_window > 0
            assert spec.cost_per_1k_tokens >= 0
            assert spec.rate_limit_rpm > 0
            assert len(spec.capabilities) > 0
    
    def test_grok_3_specifications(self):
        """Test Grok 3 model specifications"""
        spec = GROK_MODEL_SPECS[GrokModel.GROK_3.value]
        
        assert spec.name == "Grok 3"
        assert spec.max_tokens == 131072
        assert spec.context_window == 1000000
        assert spec.real_time_knowledge is True
        assert spec.vision_support is True
        assert spec.function_calling_support is True
        assert spec.reasoning_optimized is True
        
        # Check capabilities
        expected_capabilities = [
            GrokCapability.TEXT_GENERATION,
            GrokCapability.REAL_TIME_INFO,
            GrokCapability.FUNCTION_CALLING,
            GrokCapability.STREAMING,
            GrokCapability.REASONING,
            GrokCapability.MULTIMODAL
        ]
        
        for cap in expected_capabilities:
            assert cap in spec.capabilities
    
    def test_vision_model_specifications(self):
        """Test vision-specific model specifications"""
        vision_spec = GROK_MODEL_SPECS[GrokModel.GROK_1_5_VISION.value]
        
        assert vision_spec.vision_support is True
        assert GrokCapability.IMAGE_ANALYSIS in vision_spec.capabilities
        assert GrokCapability.MULTIMODAL in vision_spec.capabilities

class TestGrokRateLimiter:
    """Test Grok rate limiting functionality"""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_basic(self):
        """Test basic rate limiting functionality"""
        limiter = GrokRateLimiter(requests_per_minute=5, burst_size=2)
        
        # Should allow initial requests
        for i in range(3):
            await limiter.acquire()
        
        assert len(limiter.requests) == 3
        assert limiter.burst_tokens <= 0
    
    @pytest.mark.asyncio
    async def test_rate_limiter_burst_handling(self):
        """Test burst token handling"""
        limiter = GrokRateLimiter(requests_per_minute=60, burst_size=3)
        
        # Use up burst tokens
        for i in range(3):
            await limiter.acquire()
        
        assert limiter.burst_tokens == 0
        
        # Should still work with regular limit
        await limiter.acquire()
        assert len(limiter.requests) == 4
    
    @pytest.mark.asyncio
    async def test_rate_limiter_time_window(self):
        """Test rate limiter time window behavior"""
        limiter = GrokRateLimiter(requests_per_minute=2, burst_size=0)
        
        # Fill up the limit
        await limiter.acquire()
        await limiter.acquire()
        
        # Simulate old requests
        old_time = datetime.now() - timedelta(minutes=2)
        limiter.requests = [old_time, old_time]
        
        # Should allow new request after cleanup
        await limiter.acquire()
        assert len([r for r in limiter.requests if r > datetime.now() - timedelta(minutes=1)]) == 1

class TestGrokAPIClient:
    """Test Grok API client functionality"""
    
    @pytest.fixture
    def mock_api_key(self):
        """Mock API key for testing"""
        return "test-xai-api-key"
    
    @pytest.fixture
    def grok_client(self, mock_api_key):
        """Grok client fixture"""
        with patch.dict('os.environ', {'XAI_API_KEY': mock_api_key}):
            return GrokAPIClient()
    
    @pytest.fixture
    def mock_httpx_response(self):
        """Mock httpx response"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Test response from Grok",
                    "role": "assistant"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 50,
                "total_tokens": 70
            },
            "model": "grok-3",
            "real_time_info": {
                "sources": ["Current web data"],
                "timestamp": "2025-01-01T12:00:00Z"
            }
        }
        mock_response.raise_for_status = Mock()
        return mock_response
    
    def test_client_initialization(self, mock_api_key):
        """Test client initialization"""
        with patch.dict('os.environ', {'XAI_API_KEY': mock_api_key}):
            client = GrokAPIClient()
            
            assert client.api_key == mock_api_key
            assert client.base_url == "https://api.x.ai/v1"
            assert isinstance(client.usage_stats, dict)
            assert len(client.functions) == 0
    
    def test_client_initialization_no_api_key(self):
        """Test client initialization without API key"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="XAI_API_KEY"):
                GrokAPIClient()
    
    def test_function_registration(self, grok_client):
        """Test function registration"""
        test_function = GrokFunction(
            name="test_function",
            description="Test function",
            parameters={"type": "object", "properties": {}}
        )
        
        grok_client.register_function(test_function)
        
        assert "test_function" in grok_client.functions
        assert grok_client.functions["test_function"] == test_function
    
    @pytest.mark.asyncio
    async def test_chat_completion_basic(self, grok_client, mock_httpx_response):
        """Test basic chat completion"""
        with patch.object(grok_client.client, 'post', return_value=mock_httpx_response):
            messages = [{"role": "user", "content": "Hello Grok"}]
            
            response = await grok_client.chat_completion(
                messages=messages,
                model=GrokModel.GROK_3
            )
            
            assert isinstance(response, GrokResponse)
            assert response.content == "Test response from Grok"
            assert response.model == "grok-3"
            assert response.usage["total_tokens"] == 70
            assert response.real_time_info is not None
            assert response.confidence_score > 0
    
    @pytest.mark.asyncio
    async def test_chat_completion_with_functions(self, grok_client, mock_httpx_response):
        """Test chat completion with function calling"""
        # Modify mock response for function calling
        mock_httpx_response.json.return_value["choices"][0]["message"]["function_call"] = {
            "name": "search_web",
            "arguments": '{"query": "latest AI news"}'
        }
        
        test_function = GrokFunction(
            name="search_web",
            description="Search the web",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                }
            }
        )
        
        with patch.object(grok_client.client, 'post', return_value=mock_httpx_response):
            messages = [{"role": "user", "content": "Search for latest AI news"}]
            
            response = await grok_client.chat_completion(
                messages=messages,
                model=GrokModel.GROK_3,
                functions=[test_function]
            )
            
            assert len(response.function_calls) == 1
            assert response.function_calls[0]["name"] == "search_web"
            assert response.function_calls[0]["arguments"]["query"] == "latest AI news"
    
    @pytest.mark.asyncio
    async def test_streaming_completion(self, grok_client):
        """Test streaming completion"""
        mock_stream_response = Mock()
        mock_stream_response.aiter_lines = AsyncMock(return_value=[
            "data: " + json.dumps({
                "choices": [{"delta": {"content": "Hello"}}]
            }),
            "data: " + json.dumps({
                "choices": [{"delta": {"content": " world"}}]
            }),
            "data: [DONE]"
        ])
        mock_stream_response.raise_for_status = Mock()
        
        with patch.object(grok_client.client, 'stream') as mock_stream:
            mock_stream.return_value.__aenter__.return_value = mock_stream_response
            
            messages = [{"role": "user", "content": "Hello"}]
            stream = await grok_client.chat_completion(
                messages=messages,
                model=GrokModel.GROK_3,
                stream=True
            )
            
            content_chunks = []
            async for chunk in stream:
                content_chunks.append(chunk)
            
            assert content_chunks == ["Hello", " world"]
    
    @pytest.mark.asyncio
    async def test_vision_completion(self, grok_client, mock_httpx_response):
        """Test vision completion with images"""
        # Create a test image (1x1 pixel PNG)
        test_image_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )
        
        with patch.object(grok_client.client, 'post', return_value=mock_httpx_response):
            response = await grok_client.vision_completion(
                prompt="Describe this image",
                images=[test_image_bytes],
                model=GrokModel.GROK_1_5_VISION
            )
            
            assert isinstance(response, GrokResponse)
            assert response.content == "Test response from Grok"
    
    @pytest.mark.asyncio
    async def test_vision_completion_unsupported_model(self, grok_client):
        """Test vision completion with unsupported model"""
        with pytest.raises(ValueError, match="does not support vision"):
            await grok_client.vision_completion(
                prompt="Describe this image",
                images=[b"test"],
                model=GrokModel.GROK_2  # Doesn't support vision
            )
    
    @pytest.mark.asyncio
    async def test_function_calling_with_execution(self, grok_client, mock_httpx_response):
        """Test function calling with execution"""
        # Mock function handler
        async def mock_search_handler(query: str):
            return f"Search results for: {query}"
        
        test_function = GrokFunction(
            name="search_web",
            description="Search the web",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                }
            },
            handler=mock_search_handler
        )
        
        grok_client.register_function(test_function)
        
        # Mock response with function call
        mock_httpx_response.json.return_value["choices"][0]["message"]["function_call"] = {
            "name": "search_web",
            "arguments": '{"query": "AI news"}'
        }
        
        with patch.object(grok_client.client, 'post', return_value=mock_httpx_response):
            response = await grok_client.function_calling_completion(
                prompt="Search for AI news",
                functions=[test_function],
                execute_functions=True
            )
            
            assert "function_results" in response.metadata
            assert "search_web" in response.metadata["function_results"]
            assert response.metadata["function_results"]["search_web"] == "Search results for: AI news"
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, grok_client, mock_httpx_response):
        """Test health check when API is healthy"""
        with patch.object(grok_client.client, 'post', return_value=mock_httpx_response):
            health = await grok_client.health_check()
            
            assert health["status"] == "healthy"
            assert "latency_ms" in health
            assert health["model_available"] is True
            assert health["api_key_valid"] is True
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, grok_client):
        """Test health check when API is unhealthy"""
        with patch.object(grok_client.client, 'post', side_effect=Exception("API Error")):
            health = await grok_client.health_check()
            
            assert health["status"] == "unhealthy"
            assert "error" in health
            assert health["api_key_valid"] is True
    
    def test_get_model_info(self, grok_client):
        """Test getting model information"""
        info = grok_client.get_model_info(GrokModel.GROK_3)
        
        assert isinstance(info, GrokModelSpec)
        assert info.name == "Grok 3"
        assert info.max_tokens == 131072
    
    def test_get_usage_stats(self, grok_client):
        """Test getting usage statistics"""
        stats = grok_client.get_usage_stats()
        
        assert "total_requests" in stats
        assert "total_tokens" in stats
        assert "errors" in stats
        assert "average_latency" in stats
        assert "registered_functions" in stats
        assert "available_models" in stats
        assert "timestamp" in stats
    
    @pytest.mark.asyncio
    async def test_client_context_manager(self, mock_api_key):
        """Test client as context manager"""
        with patch.dict('os.environ', {'XAI_API_KEY': mock_api_key}):
            async with GrokAPIClient() as client:
                assert client.api_key == mock_api_key
            
            # Client should be closed after context exit
            assert client.client.is_closed

class TestGrokConvenienceFunctions:
    """Test convenience functions for Grok integration"""
    
    @pytest.mark.asyncio
    async def test_get_grok_completion(self):
        """Test convenience completion function"""
        mock_response = GrokResponse(
            content="Test completion",
            model="grok-3",
            usage={"total_tokens": 50},
            latency_ms=500.0
        )
        
        with patch('src.integrations.grok_integration.GrokAPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat_completion.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            result = await get_grok_completion("Test prompt")
            
            assert result == mock_response
            mock_client.chat_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_grok_vision_analysis(self):
        """Test convenience vision analysis function"""
        mock_response = GrokResponse(
            content="Vision analysis result",
            model="grok-1.5-vision",
            usage={"total_tokens": 75},
            latency_ms=750.0
        )
        
        with patch('src.integrations.grok_integration.GrokAPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.vision_completion.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            result = await get_grok_vision_analysis("Analyze this", [b"test_image"])
            
            assert result == mock_response
            mock_client.vision_completion.assert_called_once()

class TestGrokFunctionDefinitions:
    """Test predefined Grok function definitions"""
    
    def test_create_search_function(self):
        """Test search function creation"""
        search_func = create_search_function()
        
        assert search_func.name == "web_search"
        assert "Search the web" in search_func.description
        assert "query" in search_func.parameters["properties"]
        assert search_func.parameters["required"] == ["query"]
    
    def test_create_calculator_function(self):
        """Test calculator function creation"""
        calc_func = create_calculator_function()
        
        assert calc_func.name == "calculate"
        assert "mathematical" in calc_func.description.lower()
        assert "expression" in calc_func.parameters["properties"]
        assert calc_func.parameters["required"] == ["expression"]

class TestGrokErrorHandling:
    """Test error handling in Grok integration"""
    
    @pytest.fixture
    def grok_client(self):
        """Grok client fixture with mock API key"""
        with patch.dict('os.environ', {'XAI_API_KEY': 'test-key'}):
            return GrokAPIClient()
    
    @pytest.mark.asyncio
    async def test_invalid_model_error(self, grok_client):
        """Test error handling for invalid models"""
        with pytest.raises(ValueError, match="Unsupported Grok model"):
            await grok_client.chat_completion(
                messages=[{"role": "user", "content": "test"}],
                model="invalid-model"
            )
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, grok_client):
        """Test API error handling"""
        with patch.object(grok_client.client, 'post', side_effect=Exception("API Error")):
            with pytest.raises(Exception, match="API Error"):
                await grok_client.chat_completion(
                    messages=[{"role": "user", "content": "test"}],
                    model=GrokModel.GROK_3
                )
            
            # Check error stats were updated
            stats = grok_client.get_usage_stats()
            assert stats["errors"] == 1
    
    @pytest.mark.asyncio
    async def test_function_execution_error(self, grok_client):
        """Test function execution error handling"""
        async def failing_handler(**kwargs):
            raise Exception("Function failed")
        
        test_function = GrokFunction(
            name="failing_func",
            description="A failing function",
            parameters={"type": "object", "properties": {}},
            handler=failing_handler
        )
        
        grok_client.register_function(test_function)
        
        # Mock response with function call
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Function call result",
                    "function_call": {
                        "name": "failing_func",
                        "arguments": "{}"
                    }
                },
                "finish_reason": "function_call"
            }],
            "usage": {"total_tokens": 30}
        }
        mock_response.raise_for_status = Mock()
        
        with patch.object(grok_client.client, 'post', return_value=mock_response):
            response = await grok_client.function_calling_completion(
                prompt="Test",
                functions=[test_function],
                execute_functions=True
            )
            
            assert "function_errors" in response.metadata
            assert "failing_func" in response.metadata["function_errors"]

class TestGrokPerformance:
    """Test Grok integration performance characteristics"""
    
    @pytest.fixture
    def grok_client(self):
        """Grok client fixture"""
        with patch.dict('os.environ', {'XAI_API_KEY': 'test-key'}):
            return GrokAPIClient()
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, grok_client):
        """Test handling of concurrent requests"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}, "finish_reason": "stop"}],
            "usage": {"total_tokens": 20}
        }
        mock_response.raise_for_status = Mock()
        
        async def make_request(i):
            with patch.object(grok_client.client, 'post', return_value=mock_response):
                return await grok_client.chat_completion(
                    messages=[{"role": "user", "content": f"Request {i}"}],
                    model=GrokModel.GROK_3
                )
        
        # Test 5 concurrent requests
        tasks = [make_request(i) for i in range(5)]
        responses = await asyncio.gather(*tasks)
        
        assert len(responses) == 5
        assert all(isinstance(r, GrokResponse) for r in responses)
    
    @pytest.mark.asyncio
    async def test_rate_limiting_under_load(self, grok_client):
        """Test rate limiting behavior under load"""
        # Set a very low rate limit for testing
        grok_client.rate_limiter = GrokRateLimiter(requests_per_minute=2, burst_size=1)
        
        start_time = asyncio.get_event_loop().time()
        
        # Make requests that should trigger rate limiting
        for i in range(4):
            await grok_client.rate_limiter.acquire()
        
        end_time = asyncio.get_event_loop().time()
        
        # Should take some time due to rate limiting
        assert end_time - start_time > 0  # Basic sanity check
    
    def test_usage_stats_tracking(self, grok_client):
        """Test usage statistics tracking"""
        initial_stats = grok_client.get_usage_stats()
        
        # Simulate some usage
        grok_client.usage_stats["total_requests"] = 10
        grok_client.usage_stats["total_tokens"] = 1000
        grok_client.usage_stats["average_latency"] = 500.0
        
        updated_stats = grok_client.get_usage_stats()
        
        assert updated_stats["total_requests"] == 10
        assert updated_stats["total_tokens"] == 1000
        assert updated_stats["average_latency"] == 500.0

# Integration test markers
@pytest.mark.integration
class TestGrokIntegration:
    """Integration tests for Grok API (requires actual API key)"""
    
    @pytest.mark.skipif(
        not os.getenv("XAI_API_KEY"),
        reason="XAI_API_KEY not set"
    )
    @pytest.mark.asyncio
    async def test_real_grok_completion(self):
        """Test real Grok API completion (integration test)"""
        async with GrokAPIClient() as client:
            response = await client.chat_completion(
                messages=[{"role": "user", "content": "Hello, how are you?"}],
                model=GrokModel.GROK_2_MINI,
                max_tokens=50
            )
            
            assert isinstance(response, GrokResponse)
            assert len(response.content) > 0
            assert response.model == "grok-2-mini"
            assert response.usage["total_tokens"] > 0
    
    @pytest.mark.skipif(
        not os.getenv("XAI_API_KEY"),
        reason="XAI_API_KEY not set"
    )
    @pytest.mark.asyncio
    async def test_real_grok_health_check(self):
        """Test real Grok API health check (integration test)"""
        async with GrokAPIClient() as client:
            health = await client.health_check()
            
            assert health["status"] == "healthy"
            assert health["model_available"] is True
            assert health["api_key_valid"] is True
            assert health["latency_ms"] > 0 