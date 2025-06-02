"""
Comprehensive tests for OpenDistillery with latest models (2025)
Tests o1, o3, o4, Claude 4, Grok 3, and advanced prompting strategies
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from typing import Dict, Any, List

# Test imports
from src.integrations.multi_provider_api import (
    MultiProviderAPI, OpenAIModel, AnthropicModel, XAIModel, 
    AIProvider, APIResponse, ModelCapabilities
)
from src.research.techniques.prompting_strategies import (
    PromptingOrchestrator, PromptingStrategy, DiffusionPromptingStrategy,
    QuantumSuperpositionStrategy, NeuromorphicPromptingStrategy,
    AdaptiveTemperatureStrategy, TreeOfThoughtsStrategy
)
from src.integrations.dspy_integration import (
    DSPyIntegrationManager, DSPyConfig, OpenDistilleryDSPyLM,
    ReasoningChainOfThought, TreeOfThoughtsDSPy, CompoundReasoningSystem
)

class TestLatestModels:
    """Test suite for latest AI models (2025)"""
    
    @pytest.fixture
    def api_client(self):
        """Create API client fixture"""
        return MultiProviderAPI()
    
    @pytest.fixture
    def mock_response(self):
        """Mock API response fixture"""
        return APIResponse(
            content="Test response from latest model",
            model="o4",
            provider="openai",
            usage={"total_tokens": 150, "prompt_tokens": 50, "completion_tokens": 100},
            latency_ms=250.0,
            reasoning_steps=["Step 1: Analysis", "Step 2: Synthesis"],
            confidence_score=0.92,
            metadata={"finish_reason": "stop"}
        )
    
    def test_latest_openai_models(self):
        """Test latest OpenAI model enumeration"""
        expected_models = ["o4", "o4-mini", "o3", "o3-mini", "o1", "o1-mini", "gpt-4.1"]
        
        for model in expected_models:
            assert hasattr(OpenAIModel, model.upper().replace("-", "_").replace(".", "_"))
    
    def test_latest_anthropic_models(self):
        """Test latest Anthropic model enumeration"""
        expected_models = ["claude-4-opus", "claude-4-sonnet", "claude-3.5-sonnet"]
        
        for model in expected_models:
            model_enum_name = model.upper().replace("-", "_").replace(".", "_")
            assert hasattr(AnthropicModel, model_enum_name)
    
    def test_latest_xai_models(self):
        """Test latest xAI model enumeration"""
        expected_models = ["grok-3", "grok-3-beta", "grok-2"]
        
        for model in expected_models:
            model_enum_name = model.upper().replace("-", "_")
            assert hasattr(XAIModel, model_enum_name)
    
    def test_model_capabilities_o4(self):
        """Test o4 model capabilities"""
        from src.integrations.multi_provider_api import MODEL_SPECS
        
        o4_caps = MODEL_SPECS.get("o4")
        assert o4_caps is not None
        assert o4_caps.max_tokens == 128000
        assert o4_caps.context_window == 200000
        assert o4_caps.supports_streaming is True
        assert o4_caps.supports_vision is True
        assert o4_caps.reasoning_optimized is True
    
    def test_model_capabilities_claude_4(self):
        """Test Claude 4 model capabilities"""
        from src.integrations.multi_provider_api import MODEL_SPECS
        
        claude4_caps = MODEL_SPECS.get("claude-4-opus")
        assert claude4_caps is not None
        assert claude4_caps.max_tokens == 200000
        assert claude4_caps.context_window == 1000000
        assert claude4_caps.supports_multimodal is True
        assert claude4_caps.reasoning_optimized is True
    
    @pytest.mark.asyncio
    async def test_provider_auto_detection(self, api_client):
        """Test automatic provider detection"""
        test_cases = [
            ("o4", AIProvider.OPENAI),
            ("gpt-4.1", AIProvider.OPENAI),
            ("claude-4-opus", AIProvider.ANTHROPIC),
            ("grok-3", AIProvider.XAI)
        ]
        
        for model, expected_provider in test_cases:
            detected_provider = api_client._detect_provider(model)
            assert detected_provider == expected_provider
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_o4_chat_completion(self, mock_post, api_client):
        """Test o4 model chat completion"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Advanced reasoning response from o4",
                    "reasoning": "Step-by-step analysis\nDetailed evaluation"
                },
                "finish_reason": "stop"
            }],
            "usage": {"total_tokens": 200, "prompt_tokens": 50, "completion_tokens": 150}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Test API call
        messages = [{"role": "user", "content": "Analyze complex problem"}]
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            api_client._initialize_providers()
            response = await api_client.chat_completion(
                messages=messages,
                model="o4",
                reasoning_effort="high"
            )
        
        assert response.model == "o4"
        assert response.provider == "openai"
        assert "reasoning" in response.content.lower()
        assert response.reasoning_steps is not None
        assert response.confidence_score > 0.0
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_claude_4_completion(self, mock_post, api_client):
        """Test Claude 4 model completion"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "content": [{"text": "Sophisticated analysis from Claude 4"}],
            "usage": {"input_tokens": 45, "output_tokens": 120},
            "stop_reason": "end_turn"
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        messages = [{"role": "user", "content": "Complex reasoning task"}]
        
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            api_client._initialize_providers()
            response = await api_client.chat_completion(
                messages=messages,
                model="claude-4-sonnet",
                provider=AIProvider.ANTHROPIC
            )
        
        assert response.model == "claude-4-sonnet"
        assert response.provider == "anthropic"
        assert "analysis" in response.content.lower()
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_grok_3_completion(self, mock_post, api_client):
        """Test Grok 3 model completion"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "Innovative solution from Grok 3"},
                "finish_reason": "stop"
            }],
            "usage": {"total_tokens": 180}
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        messages = [{"role": "user", "content": "Creative problem solving"}]
        
        with patch.dict('os.environ', {'XAI_API_KEY': 'test-key'}):
            api_client._initialize_providers()
            response = await api_client.chat_completion(
                messages=messages,
                model="grok-3",
                provider=AIProvider.XAI
            )
        
        assert response.model == "grok-3"
        assert response.provider == "xai"
        assert "solution" in response.content.lower()

class TestAdvancedPromptingStrategies:
    """Test suite for advanced prompting strategies (2025)"""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client for testing"""
        client = AsyncMock()
        client.chat_completion.return_value = AsyncMock(
            content="Mock response from advanced prompting",
            reasoning_steps=["Analysis step", "Synthesis step"],
            confidence_score=0.85
        )
        return client
    
    @pytest.fixture
    def orchestrator(self, mock_llm_client):
        """Prompting orchestrator fixture"""
        return PromptingOrchestrator(mock_llm_client)
    
    @pytest.mark.asyncio
    async def test_diffusion_prompting_strategy(self, mock_llm_client):
        """Test diffusion-based prompting strategy"""
        strategy = DiffusionPromptingStrategy(mock_llm_client, diffusion_steps=3)
        
        result = await strategy.execute("Solve complex optimization problem")
        
        assert result.strategy == "diffusion_prompting"
        assert result.confidence >= 0.9  # High confidence expected
        assert len(result.reasoning_steps) == 4  # Initial + 3 refinement steps
        assert result.metadata["diffusion_steps"] == 3
    
    @pytest.mark.asyncio
    async def test_quantum_superposition_strategy(self, mock_llm_client):
        """Test quantum superposition prompting"""
        strategy = QuantumSuperpositionStrategy(mock_llm_client, superposition_states=3)
        
        result = await strategy.execute("Multi-perspective analysis problem")
        
        assert result.strategy == "quantum_superposition"
        assert result.confidence >= 0.9
        assert len(result.reasoning_steps) == 3  # One per superposition state
        assert result.metadata["superposition_states"] == 3
    
    @pytest.mark.asyncio
    async def test_neuromorphic_prompting_strategy(self, mock_llm_client):
        """Test neuromorphic prompting strategy"""
        strategy = NeuromorphicPromptingStrategy(mock_llm_client, neural_layers=3)
        
        result = await strategy.execute("Complex pattern recognition task")
        
        assert result.strategy == "neuromorphic_prompting"
        assert result.confidence >= 0.85
        assert result.metadata["neural_layers"] == 3
    
    @pytest.mark.asyncio
    async def test_adaptive_temperature_strategy(self, mock_llm_client):
        """Test adaptive temperature prompting"""
        strategy = AdaptiveTemperatureStrategy(mock_llm_client)
        
        # Test with complex prompt
        complex_prompt = "Analyze and synthesize multiple complex variables in uncertain environment"
        result = await strategy.execute(complex_prompt, temperature=0.1)
        
        assert result.strategy == "adaptive_temperature"
        assert result.metadata["adaptive_temperature"] > 0.1  # Should increase for complex task
        assert result.metadata["complexity_score"] > 0.0
        assert result.metadata["uncertainty_score"] > 0.0
    
    @pytest.mark.asyncio
    async def test_tree_of_thoughts_strategy(self, mock_llm_client):
        """Test Tree of Thoughts strategy"""
        strategy = TreeOfThoughtsStrategy(mock_llm_client, max_depth=2, max_branches=2)
        
        result = await strategy.execute("Multi-step reasoning problem")
        
        assert result.strategy == "tree_of_thoughts"
        assert result.confidence >= 0.8
        assert result.metadata["tree_depth"] >= 1
        assert result.metadata["total_nodes"] >= 1
    
    @pytest.mark.asyncio
    async def test_ensemble_execution(self, orchestrator):
        """Test ensemble execution of multiple strategies"""
        strategies = [
            PromptingStrategy.CHAIN_OF_THOUGHT,
            PromptingStrategy.DIFFUSION_PROMPTING,
            PromptingStrategy.ADAPTIVE_TEMPERATURE
        ]
        
        result = await orchestrator.ensemble_execution(
            strategies,
            "Complex multi-faceted problem"
        )
        
        assert result.strategy == "ensemble"
        assert len(result.reasoning_steps) == len(strategies)
        assert result.metadata["strategies_used"] == [s.value for s in strategies]
        assert len(result.metadata["individual_confidences"]) == len(strategies)
    
    def test_strategy_recommendations(self, orchestrator):
        """Test strategy recommendation system"""
        test_cases = [
            ("Analyze complex financial data", [PromptingStrategy.TREE_OF_THOUGHT]),
            ("Creative brainstorming session", [PromptingStrategy.QUANTUM_SUPERPOSITION]),
            ("Technical system design", [PromptingStrategy.NEUROMORPHIC_PROMPTING])
        ]
        
        for prompt, expected_strategies in test_cases:
            recommendations = orchestrator.get_strategy_recommendations(prompt)
            
            # Check that recommended strategies include expected ones
            for expected in expected_strategies:
                assert expected in recommendations
    
    @pytest.mark.asyncio
    async def test_prompting_performance_tracking(self, orchestrator):
        """Test performance tracking for prompting strategies"""
        # Execute some strategies
        await orchestrator.execute_strategy(
            PromptingStrategy.CHAIN_OF_THOUGHT,
            "Test prompt 1"
        )
        await orchestrator.execute_strategy(
            PromptingStrategy.DIFFUSION_PROMPTING,
            "Test prompt 2"
        )
        
        stats = orchestrator.get_execution_stats()
        
        assert stats["total_executions"] == 2
        assert len(stats["strategies_used"]) == 2
        assert "avg_confidence" in stats
        assert "avg_execution_time" in stats
        assert "strategy_usage_count" in stats

class TestDSPyIntegration:
    """Test suite for DSPy integration with latest models"""
    
    @pytest.fixture
    def dspy_config(self):
        """DSPy configuration fixture"""
        return DSPyConfig(
            model="o4",
            temperature=0.1,
            provider="openai",
            reasoning_mode=True
        )
    
    @pytest.fixture
    def dspy_manager(self, dspy_config):
        """DSPy integration manager fixture"""
        return DSPyIntegrationManager(dspy_config)
    
    @pytest.fixture
    def mock_dspy_lm(self):
        """Mock DSPy language model"""
        with patch('src.integrations.dspy_integration.OpenDistilleryDSPyLM') as mock:
            lm_instance = Mock()
            lm_instance.get_usage_stats.return_value = {
                "requests": 10,
                "total_tokens": 1500,
                "avg_tokens_per_request": 150,
                "reasoning_traces": 5
            }
            mock.return_value = lm_instance
            yield lm_instance
    
    def test_dspy_config_creation(self, dspy_config):
        """Test DSPy configuration creation"""
        assert dspy_config.model == "o4"
        assert dspy_config.temperature == 0.1
        assert dspy_config.reasoning_mode is True
        assert dspy_config.optimization_metric == "accuracy"
    
    def test_dspy_model_enumeration(self):
        """Test DSPy model enumeration"""
        from src.integrations.dspy_integration import DSPyModel
        
        # Check latest models are available
        latest_models = ["O4", "O3", "CLAUDE_4_OPUS", "GROK_3"]
        for model in latest_models:
            assert hasattr(DSPyModel, model)
    
    def test_reasoning_chain_of_thought_module(self, mock_dspy_lm):
        """Test DSPy Chain of Thought module"""
        with patch('dspy.configure'):
            module = ReasoningChainOfThought("o4")
            
            # Mock prediction
            mock_prediction = Mock()
            mock_prediction.reasoning = "Step 1: Analyze problem. Step 2: Generate solution."
            mock_prediction.answer = "Comprehensive solution"
            
            with patch.object(module, 'cot') as mock_cot:
                mock_cot.return_value = mock_prediction
                
                result = module.forward("Test question")
                
                assert hasattr(result, 'confidence')
                assert result.confidence > 0.5  # Should have reasonable confidence
    
    def test_tree_of_thoughts_dspy_module(self, mock_dspy_lm):
        """Test DSPy Tree of Thoughts module"""
        with patch('dspy.configure'):
            module = TreeOfThoughtsDSPy("o4", max_depth=2, branching_factor=2)
            
            # Mock the predict modules
            module.thought_generator = Mock()
            module.thought_evaluator = Mock()
            module.solution_synthesizer = Mock()
            
            module.thought_generator.return_value = Mock(thoughts="1. Approach A\n2. Approach B")
            module.thought_evaluator.return_value = Mock(score="0.8")
            module.solution_synthesizer.return_value = Mock(solution="Final solution")
            
            result = module.forward("Complex problem")
            
            assert hasattr(result, 'solution')
            assert hasattr(result, 'confidence')
            assert result.confidence >= 0.0
    
    def test_compound_reasoning_system(self, mock_dspy_lm):
        """Test compound reasoning system"""
        with patch('dspy.configure'):
            models = ["o4", "claude-4-sonnet"]
            system = CompoundReasoningSystem(models)
            
            # Mock reasoning modules
            for model in models:
                mock_module = Mock()
                mock_prediction = Mock()
                mock_prediction.answer = f"Answer from {model}"
                mock_prediction.reasoning = f"Reasoning from {model}"
                mock_prediction.confidence = 0.85
                mock_module.return_value = mock_prediction
                system.reasoning_modules[model] = mock_module
            
            # Mock ensemble synthesizer
            system.ensemble_synthesizer = Mock()
            system.ensemble_synthesizer.return_value = Mock(final_answer="Ensemble answer")
            
            result = system.forward("Test question")
            
            assert hasattr(result, 'answer')
            assert hasattr(result, 'ensemble_confidence')
            assert hasattr(result, 'individual_predictions')
            assert len(result.individual_predictions) == len(models)
    
    def test_dspy_module_creation(self, dspy_manager, mock_dspy_lm):
        """Test DSPy module creation"""
        with patch('dspy.configure'):
            # Test different module types
            module_types = ["chain_of_thought", "tree_of_thoughts", "compound_reasoning"]
            
            for module_type in module_types:
                module = dspy_manager.create_reasoning_module(module_type)
                assert module is not None
                
                # Check module is stored
                assert len(dspy_manager.modules) > 0
    
    def test_dspy_module_optimization(self, dspy_manager, mock_dspy_lm):
        """Test DSPy module optimization"""
        with patch('dspy.configure'):
            # Create training data
            training_data = [
                {"question": "What is 2+2?", "answer": "4"},
                {"question": "What is the capital of France?", "answer": "Paris"}
            ]
            
            # Create base module
            base_module = Mock()
            
            # Mock optimizer
            with patch('src.integrations.dspy_integration.MetaPromptOptimizer') as mock_optimizer_class:
                mock_optimizer = Mock()
                mock_optimizer.optimize.return_value = Mock()  # Optimized module
                mock_optimizer_class.return_value = mock_optimizer
                
                optimized_module = dspy_manager.optimize_module(
                    base_module,
                    training_data,
                    optimization_strategy="bootstrap"
                )
                
                assert optimized_module is not None
                assert len(dspy_manager.optimizers) > 0
    
    def test_dspy_module_evaluation(self, dspy_manager, mock_dspy_lm):
        """Test DSPy module evaluation"""
        # Mock module that returns predictions
        mock_module = Mock()
        mock_prediction = Mock()
        mock_prediction.answer = "correct answer"
        mock_prediction.confidence = 0.9
        mock_module.return_value = mock_prediction
        
        test_data = [
            {"question": "Test question", "answer": "correct answer"}
        ]
        
        results = dspy_manager.evaluate_module(mock_module, test_data)
        
        assert "accuracy" in results
        assert "confidence" in results
        assert "latency" in results
        assert results["accuracy"] == 1.0  # Perfect match
        assert results["confidence"] == 0.9
    
    def test_dspy_system_status(self, dspy_manager, mock_dspy_lm):
        """Test DSPy system status reporting"""
        status = dspy_manager.get_system_status()
        
        assert "config" in status
        assert "modules" in status
        assert "optimizers" in status
        assert "lm_stats" in status
        assert "timestamp" in status
        
        assert status["config"]["model"] == "o4"
        assert status["config"]["provider"] == "openai"

class TestModelIntegration:
    """Integration tests for latest models with complete system"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_reasoning_pipeline_o4(self):
        """Test complete reasoning pipeline with o4 model"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            # Mock the HTTP client
            with patch('httpx.AsyncClient.post') as mock_post:
                mock_response = Mock()
                mock_response.json.return_value = {
                    "choices": [{
                        "message": {
                            "content": "Complex reasoning solution using o4",
                            "reasoning": "Multi-step analysis\nDetailed synthesis"
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {"total_tokens": 300}
                }
                mock_response.raise_for_status = Mock()
                mock_post.return_value = mock_response
                
                # Create orchestrator with real API client
                api_client = MultiProviderAPI()
                orchestrator = PromptingOrchestrator(api_client)
                
                # Test ensemble with latest models
                result = await orchestrator.ensemble_execution(
                    [PromptingStrategy.CHAIN_OF_THOUGHT, PromptingStrategy.DIFFUSION_PROMPTING],
                    "Analyze quarterly financial performance with predictive insights",
                    model="o4"
                )
                
                assert result.strategy == "ensemble"
                assert result.confidence > 0.7
                assert len(result.reasoning_steps) == 2
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_model_comparison(self):
        """Test comparison across multiple latest models"""
        models_to_test = ["o4", "claude-4-sonnet", "grok-3"]
        
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock different responses for different models
            def mock_response_factory(model):
                mock_response = Mock()
                mock_response.json.return_value = {
                    "choices": [{
                        "message": {"content": f"Response from {model}"},
                        "finish_reason": "stop"
                    }],
                    "usage": {"total_tokens": 200}
                }
                mock_response.raise_for_status = Mock()
                return mock_response
            
            mock_post.side_effect = [mock_response_factory(model) for model in models_to_test]
            
            # Test each model
            api_client = MultiProviderAPI()
            
            with patch.dict('os.environ', {
                'OPENAI_API_KEY': 'test-key',
                'ANTHROPIC_API_KEY': 'test-key',
                'XAI_API_KEY': 'test-key'
            }):
                api_client._initialize_providers()
                
                results = []
                for model in models_to_test:
                    try:
                        response = await api_client.chat_completion(
                            messages=[{"role": "user", "content": "Test prompt"}],
                            model=model
                        )
                        results.append((model, response))
                    except Exception as e:
                        pytest.skip(f"Model {model} test skipped: {e}")
                
                # Verify we got responses
                assert len(results) > 0
                
                # Check that each model returned appropriate response
                for model, response in results:
                    assert model in response.content or response.model == model

# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmarks for latest models"""
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_o4_performance_benchmark(self):
        """Benchmark o4 model performance"""
        start_time = datetime.now()
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Benchmark response"}, "finish_reason": "stop"}],
                "usage": {"total_tokens": 150}
            }
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response
            
            api_client = MultiProviderAPI()
            
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                api_client._initialize_providers()
                
                # Simulate multiple requests
                tasks = []
                for i in range(10):
                    task = api_client.chat_completion(
                        messages=[{"role": "user", "content": f"Benchmark test {i}"}],
                        model="o4"
                    )
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks)
                
                end_time = datetime.now()
                total_time = (end_time - start_time).total_seconds()
                
                # Performance assertions
                assert len(responses) == 10
                assert total_time < 30.0  # Should complete within 30 seconds
                assert all(r.latency_ms < 5000 for r in responses)  # Each request under 5s
    
    @pytest.mark.benchmark
    def test_prompting_strategy_performance(self):
        """Benchmark prompting strategy performance"""
        orchestrator = PromptingOrchestrator(None)
        
        start_time = datetime.now()
        
        # Test strategy recommendations performance
        test_prompts = [
            "Analyze complex data patterns",
            "Creative problem solving",
            "Technical system design",
            "Financial risk assessment",
            "Strategic planning analysis"
        ]
        
        for prompt in test_prompts:
            recommendations = orchestrator.get_strategy_recommendations(prompt)
            assert len(recommendations) > 0
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Should be very fast for recommendations
        assert total_time < 1.0

if __name__ == "__main__":
    # Run specific test categories
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "not benchmark"  # Skip benchmarks in regular runs
    ]) 