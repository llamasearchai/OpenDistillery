"""
Comprehensive tests for Multi-Provider AI API Integration
Tests all latest models from OpenAI, Anthropic, xAI, and Google (2025)
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import List, Dict, Any

from src.opendistillery.integrations.multi_provider_api import (
    MultiProviderAPI,
    OpenAIModel,
    AnthropicModel,
    XAIModel,
    GoogleModel,
    AIProvider,
    ModelSpec,
    MODEL_SPECS,
    ChatMessage,
    ChatResponse,
    RateLimiter,
    get_completion,
    get_reasoning_completion,
    get_multimodal_completion
)

class TestModelSpecs:
    """Test model specifications and capabilities"""
    
    def test_latest_openai_models(self):
        """Test that latest OpenAI models are properly defined"""
        latest_models = [
            OpenAIModel.GPT_4_1.value,
            OpenAIModel.O3.value,
            OpenAIModel.O4_MINI.value,
            OpenAIModel.GPT_4O.value
        ]
        
        for model in latest_models:
            assert model in MODEL_SPECS
            spec = MODEL_SPECS[model]
            assert spec.provider == AIProvider.OPENAI
            assert spec.context_window > 0
            assert spec.max_output_tokens > 0
    
    def test_latest_anthropic_models(self):
        """Test that latest Anthropic models are properly defined"""
        latest_models = [
            AnthropicModel.CLAUDE_4_OPUS.value,
            AnthropicModel.CLAUDE_4_SONNET.value,
            AnthropicModel.CLAUDE_3_7_SONNET.value
        ]
        
        for model in latest_models:
            assert model in MODEL_SPECS
            spec = MODEL_SPECS[model]
            assert spec.provider == AIProvider.ANTHROPIC
            assert spec.context_window >= 200000  # Latest Claude models have large context
    
    def test_xai_grok_models(self):
        """Test that Grok models are properly defined"""
        grok_models = [XAIModel.GROK_3.value]
        
        for model in grok_models:
            assert model in MODEL_SPECS
            spec = MODEL_SPECS[model]
            assert spec.provider == AIProvider.XAI
            assert spec.supports_real_time  # Grok's key feature
    
    def test_model_features(self):
        """Test that models have correct feature flags"""
        # GPT-4.1 should have million token context
        gpt_41_spec = MODEL_SPECS[OpenAIModel.GPT_4_1.value]
        assert gpt_41_spec.context_window == 1000000
        assert "million_token_context" in gpt_41_spec.special_features
        
        # Claude 3.7 should have extended thinking
        claude_37_spec = MODEL_SPECS[AnthropicModel.CLAUDE_3_7_SONNET.value]
        assert "extended_thinking" in claude_37_spec.special_features
        
        # Grok 3 should have think modes
        grok_3_spec = MODEL_SPECS[XAIModel.GROK_3.value]
        assert "think_mode" in grok_3_spec.special_features
        assert "big_brain_mode" in grok_3_spec.special_features

class TestRateLimiter:
    """Test rate limiting functionality"""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_basic(self):
        """Test basic rate limiting"""
        rate_limiter = RateLimiter(calls_per_minute=5)
        
        # Should allow first few calls
        for _ in range(5):
            await rate_limiter.acquire()
        
        # Should block the 6th call (we'll mock time to avoid waiting)
        with patch('time.time') as mock_time:
            mock_time.side_effect = [0, 0, 0, 0, 0, 30]  # 30 seconds later
            
            rate_limiter.calls = [0, 0, 0, 0, 0]  # 5 calls at time 0
            await rate_limiter.acquire()  # Should not block as it's 30s later

class TestMultiProviderAPI:
    """Test the main MultiProviderAPI class"""
    
    @pytest.fixture
    def api_client(self):
        """Create API client for testing"""
        return MultiProviderAPI(
            openai_api_key="test-openai-key",
            anthropic_api_key="test-anthropic-key",
            xai_api_key="test-xai-key"
        )
    
    def test_provider_detection(self, api_client):
        """Test provider detection from model names"""
        assert api_client._get_provider_from_model("gpt-4o") == AIProvider.OPENAI
        assert api_client._get_provider_from_model("claude-4-opus") == AIProvider.ANTHROPIC
        assert api_client._get_provider_from_model("grok-3") == AIProvider.XAI
        
        with pytest.raises(ValueError):
            api_client._get_provider_from_model("unknown-model")
    
    def test_list_models(self, api_client):
        """Test model listing functionality"""
        all_models = api_client.list_models()
        assert len(all_models) > 0
        
        openai_models = api_client.list_models(AIProvider.OPENAI)
        anthropic_models = api_client.list_models(AIProvider.ANTHROPIC)
        
        assert OpenAIModel.GPT_4_1.value in openai_models
        assert AnthropicModel.CLAUDE_4_OPUS.value in anthropic_models
    
    def test_model_info(self, api_client):
        """Test getting model information"""
        info = api_client.get_model_info(OpenAIModel.GPT_4_1.value)
        assert isinstance(info, ModelSpec)
        assert info.name == "GPT-4.1"
        assert info.context_window == 1000000
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality"""
        async with MultiProviderAPI() as api:
            assert api.http_client is not None
        
        # Client should be closed after exiting context

class TestOpenAIIntegration:
    """Test OpenAI API integration"""
    
    @pytest.mark.asyncio
    async def test_openai_chat_completion(self):
        """Test OpenAI chat completion"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.model = "gpt-4o"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_response.choices[0].finish_reason = "stop"
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            api = MultiProviderAPI(openai_api_key="test-key")
            
            messages = [{"role": "user", "content": "Hello"}]
            response = await api.chat_completion(
                messages=messages,
                model=OpenAIModel.GPT_4O.value
            )
            
            assert isinstance(response, ChatResponse)
            assert response.content == "Test response"
            assert response.model == "gpt-4o"
            assert response.usage["total_tokens"] == 15
    
    @pytest.mark.asyncio
    async def test_openai_reasoning_models(self):
        """Test OpenAI reasoning models (o-series)"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Reasoning response"
        mock_response.model = "o3"
        mock_response.usage.prompt_tokens = 20
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 30
        mock_response.choices[0].finish_reason = "stop"
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            api = MultiProviderAPI(openai_api_key="test-key")
            
            messages = [{"role": "user", "content": "Solve this problem"}]
            response = await api.chat_completion(
                messages=messages,
                model=OpenAIModel.O3.value,
                reasoning=True
            )
            
            assert response.content == "Reasoning response"
            # Verify reasoning parameter was passed
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args[1]
            assert call_args.get("reasoning") is True

class TestAnthropicIntegration:
    """Test Anthropic Claude API integration"""
    
    @pytest.mark.asyncio
    async def test_anthropic_chat_completion(self):
        """Test Anthropic chat completion"""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Claude response"
        mock_response.model = "claude-4-opus"
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 8
        mock_response.stop_reason = "end_turn"
        
        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client
            
            api = MultiProviderAPI(anthropic_api_key="test-key")
            
            messages = [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hello Claude"}
            ]
            response = await api.chat_completion(
                messages=messages,
                model=AnthropicModel.CLAUDE_4_OPUS.value
            )
            
            assert response.content == "Claude response"
            assert response.usage["total_tokens"] == 23
    
    @pytest.mark.asyncio
    async def test_claude_extended_thinking(self):
        """Test Claude 3.7's extended thinking feature"""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Extended thinking response"
        mock_response.model = "claude-3-7-sonnet"
        mock_response.usage.input_tokens = 25
        mock_response.usage.output_tokens = 15
        mock_response.stop_reason = "end_turn"
        
        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client
            
            api = MultiProviderAPI(anthropic_api_key="test-key")
            
            messages = [{"role": "user", "content": "Complex reasoning task"}]
            response = await api.chat_completion(
                messages=messages,
                model=AnthropicModel.CLAUDE_3_7_SONNET.value,
                extended_thinking=True
            )
            
            assert response.content == "Extended thinking response"
            # Verify extended_thinking parameter was passed
            mock_client.messages.create.assert_called_once()
            call_args = mock_client.messages.create.call_args[1]
            assert call_args.get("extended_thinking") is True

class TestXAIIntegration:
    """Test xAI Grok API integration"""
    
    @pytest.mark.asyncio
    async def test_grok_chat_completion(self):
        """Test Grok chat completion with special modes"""
        api = MultiProviderAPI(xai_api_key="test-key")
        
        messages = [{"role": "user", "content": "What's happening on X?"}]
        response = await api.chat_completion(
            messages=messages,
            model=XAIModel.GROK_3.value,
            mode="think",
            real_time_info=True
        )
        
        assert isinstance(response, ChatResponse)
        assert "think mode" in response.content
        assert response.metadata["mode"] == "think"
        assert response.metadata["real_time"] is True
    
    @pytest.mark.asyncio
    async def test_grok_big_brain_mode(self):
        """Test Grok's Big Brain mode"""
        api = MultiProviderAPI(xai_api_key="test-key")
        
        messages = [{"role": "user", "content": "Complex coding task"}]
        response = await api.chat_completion(
            messages=messages,
            model=XAIModel.GROK_3.value,
            mode="big_brain"
        )
        
        assert response.metadata["mode"] == "big_brain"

class TestConvenienceFunctions:
    """Test convenience functions for easy usage"""
    
    @pytest.mark.asyncio
    async def test_get_completion(self):
        """Test simple completion function"""
        with patch('src.opendistillery.integrations.multi_provider_api.MultiProviderAPI') as mock_api_class:
            mock_api = AsyncMock()
            mock_response = ChatResponse(
                content="Simple response",
                model="gpt-4o",
                usage={"total_tokens": 10},
                finish_reason="stop"
            )
            mock_api.chat_completion.return_value = mock_response
            mock_api_class.return_value.__aenter__.return_value = mock_api
            
            result = await get_completion("Hello world")
            assert result == "Simple response"
    
    @pytest.mark.asyncio
    async def test_get_reasoning_completion(self):
        """Test reasoning completion function"""
        with patch('src.opendistillery.integrations.multi_provider_api.get_completion') as mock_get:
            mock_get.return_value = "Reasoning response"
            
            result = await get_reasoning_completion("Complex problem")
            assert result == "Reasoning response"
            
            # Should default to O3 model
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            assert args[1] == OpenAIModel.O3.value  # model parameter
            assert kwargs["reasoning"] is True
    
    @pytest.mark.asyncio
    async def test_get_multimodal_completion(self):
        """Test multimodal completion with images"""
        with patch('src.opendistillery.integrations.multi_provider_api.MultiProviderAPI') as mock_api_class:
            mock_api = AsyncMock()
            mock_response = ChatResponse(
                content="Image analysis",
                model="gpt-4o",
                usage={"total_tokens": 20},
                finish_reason="stop"
            )
            mock_api.chat_completion.return_value = mock_response
            mock_api_class.return_value.__aenter__.return_value = mock_api
            
            images = ["data:image/jpeg;base64,/9j/4AAQ..."]
            result = await get_multimodal_completion("Describe this image", images)
            assert result == "Image analysis"
            
            # Verify proper message format for multimodal
            mock_api.chat_completion.assert_called_once()
            call_args = mock_api.chat_completion.call_args[1]
            messages = call_args["messages"]
            assert len(messages) == 1
            assert isinstance(messages[0]["content"], list)

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_openai_api_error(self):
        """Test OpenAI API error handling"""
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_client
            
            api = MultiProviderAPI(openai_api_key="test-key")
            
            with pytest.raises(Exception, match="API Error"):
                await api.chat_completion(
                    messages=[{"role": "user", "content": "test"}],
                    model=OpenAIModel.GPT_4O.value
                )
    
    @pytest.mark.asyncio
    async def test_missing_client_error(self):
        """Test error when client is not initialized"""
        api = MultiProviderAPI()  # No API keys
        
        with pytest.raises(ValueError, match="OpenAI client not initialized"):
            await api.chat_completion(
                messages=[{"role": "user", "content": "test"}],
                model=OpenAIModel.GPT_4O.value
            )
    
    def test_unknown_model_error(self):
        """Test error for unknown model"""
        api = MultiProviderAPI()
        
        with pytest.raises(ValueError, match="Unknown model"):
            api._get_provider_from_model("unknown-model-123")

class TestStreamingResponses:
    """Test streaming response functionality"""
    
    @pytest.mark.asyncio
    async def test_openai_streaming(self):
        """Test OpenAI streaming responses"""
        async def mock_stream():
            chunks = [
                MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content=" world"))]),
                MagicMock(choices=[MagicMock(delta=MagicMock(content="!"))])
            ]
            for chunk in chunks:
                yield chunk
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = mock_stream()
            mock_openai.return_value = mock_client
            
            api = MultiProviderAPI(openai_api_key="test-key")
            
            response = await api.chat_completion(
                messages=[{"role": "user", "content": "test"}],
                model=OpenAIModel.GPT_4O.value,
                stream=True
            )
            
            chunks = []
            async for chunk in response:
                chunks.append(chunk)
            
            assert chunks == ["Hello", " world", "!"]

class TestModelCompatibility:
    """Test model compatibility and feature detection"""
    
    def test_vision_model_detection(self):
        """Test that vision models are correctly identified"""
        vision_models = [
            OpenAIModel.GPT_4O.value,
            OpenAIModel.GPT_4_1.value,
            AnthropicModel.CLAUDE_4_OPUS.value,
            XAIModel.GROK_3.value
        ]
        
        for model in vision_models:
            spec = MODEL_SPECS[model]
            assert spec.supports_vision, f"{model} should support vision"
    
    def test_reasoning_model_detection(self):
        """Test that reasoning models are correctly identified"""
        reasoning_models = [
            OpenAIModel.O3.value,
            OpenAIModel.O3_MINI.value,
            AnthropicModel.CLAUDE_3_7_SONNET.value
        ]
        
        for model in reasoning_models:
            spec = MODEL_SPECS[model]
            assert spec.supports_reasoning, f"{model} should support reasoning"
    
    def test_real_time_model_detection(self):
        """Test that real-time capable models are identified"""
        real_time_models = [XAIModel.GROK_3.value]
        
        for model in real_time_models:
            spec = MODEL_SPECS[model]
            assert spec.supports_real_time, f"{model} should support real-time"

# Performance and load tests
class TestPerformance:
    """Test performance and load handling"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent requests"""
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"
            mock_response.model = "gpt-4o"
            mock_response.usage.prompt_tokens = 5
            mock_response.usage.completion_tokens = 5
            mock_response.usage.total_tokens = 10
            mock_response.choices[0].finish_reason = "stop"
            
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            api = MultiProviderAPI(openai_api_key="test-key")
            
            # Run 10 concurrent requests
            tasks = []
            for i in range(10):
                task = api.chat_completion(
                    messages=[{"role": "user", "content": f"Request {i}"}],
                    model=OpenAIModel.GPT_4O.value
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            assert len(responses) == 10
            assert all(r.content == "Response" for r in responses)

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 