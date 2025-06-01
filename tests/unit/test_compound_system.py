"""
Unit Tests for OpenContext Compound AI System
Comprehensive test suite for core compound AI functionality.
"""

import pytest
import asyncio
import time
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
import numpy as np

from src.core.compound_system import (
    SystemBuilder, CompoundAISystem, SystemRequirements, 
    SystemArchitecture, ModelConfiguration, AgentConfiguration,
    ReasoningStrategy,
    SystemConfiguration,
    CompoundSystem,
    SystemRegistry,
    TaskQueue,
    ResourceManager
)
from src.agents.base_agent import BaseAgent, AgentCapability, AgentState
from src.research.techniques.react_engine import ReactEngine
from src.research.techniques.tree_of_thoughts import TreeOfThoughts
from src.research.techniques.graph_of_thoughts import GraphOfThoughts


class TestSystemBuilder:
    """Test cases for SystemBuilder"""
    
    def setup_method(self):
        """Setup test environment"""
        self.system_builder = SystemBuilder()
        self.test_requirements = SystemRequirements(
            domain="finance",
            use_case="risk_analysis",
            latency_target_ms=500,
            throughput_rps=1000,
            accuracy_threshold=0.95
        )
    
    def test_create_system(self):
        """Test basic system creation"""
        system = self.system_builder.create_system(
            system_id="test_system",
            requirements=self.test_requirements,
            architecture=SystemArchitecture.HYBRID
        )
        
        assert system is not None
        assert system.system_id == "test_system"
        assert system.requirements.domain == "finance"
        assert system.architecture == SystemArchitecture.HYBRID
        assert "test_system" in self.system_builder.systems
    
    def test_build_financial_services_system(self):
        """Test specialized financial services system creation"""
        system = self.system_builder.build_financial_services_system("fin_test")
        
        assert system is not None
        assert system.system_id == "fin_test"
        assert system.requirements.domain == "finance"
        assert len(system.models) >= 2  # Should have financial and risk models
        assert len(system.agents) >= 2  # Should have risk and market agents
    
    def test_build_healthcare_system(self):
        """Test specialized healthcare system creation"""
        system = self.system_builder.build_healthcare_system("health_test")
        
        assert system is not None
        assert system.requirements.domain == "healthcare"
        assert system.requirements.accuracy_threshold >= 0.99  # High accuracy for healthcare
        assert len(system.models) >= 2
        assert len(system.agents) >= 1
    
    def test_build_manufacturing_system(self):
        """Test specialized manufacturing system creation"""
        system = self.system_builder.build_manufacturing_system("mfg_test")
        
        assert system is not None
        assert system.requirements.domain == "manufacturing"
        assert system.requirements.latency_target_ms <= 100  # Real-time requirements
        assert len(system.models) >= 2
        assert len(system.agents) >= 2
    
    def test_get_system(self):
        """Test system retrieval"""
        # Create system
        system = self.system_builder.create_system("retrieve_test", self.test_requirements)
        
        # Retrieve system
        retrieved = self.system_builder.get_system("retrieve_test")
        assert retrieved is not None
        assert retrieved.system_id == "retrieve_test"
        
        # Test non-existent system
        assert self.system_builder.get_system("non_existent") is None
    
    def test_list_systems(self):
        """Test system listing"""
        initial_count = len(self.system_builder.list_systems())
        
        # Create multiple systems
        self.system_builder.create_system("list_test_1", self.test_requirements)
        self.system_builder.create_system("list_test_2", self.test_requirements)
        
        systems = self.system_builder.list_systems()
        assert len(systems) == initial_count + 2
        assert "list_test_1" in systems
        assert "list_test_2" in systems


class TestCompoundAISystem:
    """Test cases for CompoundAISystem"""
    
    def setup_method(self):
        """Setup test environment"""
        self.requirements = SystemRequirements(
            domain="test",
            use_case="testing",
            latency_target_ms=1000,
            throughput_rps=100
        )
        self.system = CompoundAISystem(
            system_id="test_compound_system",
            requirements=self.requirements,
            architecture=SystemArchitecture.HYBRID
        )
    
    def test_system_initialization(self):
        """Test system initialization"""
        assert self.system.system_id == "test_compound_system"
        assert self.system.requirements.domain == "test"
        assert self.system.architecture == SystemArchitecture.HYBRID
        assert len(self.system.models) == 0
        assert len(self.system.agents) == 0
        assert self.system.performance_metrics["requests_processed"] == 0
    
    def test_add_model(self):
        """Test model addition"""
        model_config = ModelConfiguration(
            model_name="test_model",
            model_type="llm",
            provider="openai",
            version="gpt-4",
            cost_per_token=0.00003
        )
        
        self.system.add_model(model_config)
        
        assert "test_model" in self.system.models
        assert self.system.models["test_model"].provider == "openai"
        assert self.system.models["test_model"].cost_per_token == 0.00003
    
    def test_add_agent(self):
        """Test agent addition"""
        agent_config = AgentConfiguration(
            agent_id="test_agent",
            agent_type="analyst",
            primary_model="test_model",
            capabilities=[AgentCapability.ANALYSIS]
        )
        
        agent = self.system.add_agent(agent_config)
        
        assert agent is not None
        assert "test_agent" in self.system.agents
        assert self.system.agents["test_agent"].agent_type == "analyst"
        assert AgentCapability.ANALYSIS in self.system.agents["test_agent"].capabilities
    
    def test_create_reasoning_chain(self):
        """Test reasoning chain creation"""
        from src.core.compound_system import ChainType
        
        steps = [
            {"step": "analyze", "description": "Analyze problem"},
            {"step": "plan", "description": "Plan solution"},
            {"step": "execute", "description": "Execute plan"}
        ]
        
        chain = self.system.create_reasoning_chain(
            chain_id="test_chain",
            chain_type=ChainType.SEQUENTIAL,
            steps=steps
        )
        
        assert chain is not None
        assert "test_chain" in self.system.reasoning_chains
        assert len(chain.steps) == 3
    
    @pytest.mark.asyncio
    async def test_process_request_simple(self):
        """Test simple request processing"""
        # Mock the processing methods
        with patch.object(self.system, '_process_adaptive', new_callable=AsyncMock) as mock_adaptive:
            mock_adaptive.return_value = {
                "success": True,
                "result": "test_result",
                "confidence": 0.85,
                "models_used": ["test_model"]
            }
            
            request = {
                "request_id": "test_request",
                "task_type": "analysis",
                "input_data": {"text": "test input"}
            }
            
            result = await self.system.process_request(request)
            
            assert result["success"] is True
            assert "system_metadata" in result
            assert result["system_metadata"]["strategy_used"] == "adaptive"
            assert "processing_time_ms" in result["system_metadata"]
            
            mock_adaptive.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_request_react(self):
        """Test ReAct strategy processing"""
        with patch.object(self.system, '_process_react', new_callable=AsyncMock) as mock_react:
            mock_react.return_value = {
                "success": True,
                "result": "react_result",
                "confidence": 0.90,
                "reasoning_steps": 5
            }
            
            request = {"task_type": "complex_reasoning"}
            
            result = await self.system.process_request(request, ReasoningStrategy.REACT)
            
            assert result["success"] is True
            assert result["system_metadata"]["strategy_used"] == "react"
            mock_react.assert_called_once_with(request)
    
    def test_performance_metrics_tracking(self):
        """Test performance metrics tracking"""
        initial_requests = self.system.performance_metrics["requests_processed"]
        
        # Simulate metric updates
        self.system._update_metrics("test_request", 0.5, {"success": True, "accuracy": 0.95})
        
        assert self.system.performance_metrics["requests_processed"] == initial_requests + 1
        assert self.system.performance_metrics["average_latency"] > 0
        assert len(self.system.performance_metrics["accuracy_scores"]) == 1
    
    def test_cost_calculation(self):
        """Test cost calculation"""
        result = {
            "models_used": ["test_model"],
            "token_usage": {"test_model": 1000}
        }
        
        # Add a model with known cost
        model_config = ModelConfiguration(
            model_name="test_model",
            model_type="llm",
            provider="openai",
            version="gpt-4",
            cost_per_token=0.00003
        )
        self.system.add_model(model_config)
        
        cost = self.system._calculate_cost(result)
        expected_cost = 1000 * 0.00003  # 0.03
        assert cost == expected_cost
    
    def test_system_status(self):
        """Test system status reporting"""
        status = self.system.get_system_status()
        
        assert "system_id" in status
        assert "architecture" in status
        assert "requirements" in status
        assert "performance_metrics" in status
        assert "health_status" in status
        assert "compliance_status" in status
        assert "cost_efficiency" in status
        
        assert status["system_id"] == "test_compound_system"
        assert status["architecture"] == "hybrid"
    
    def test_health_assessment(self):
        """Test system health assessment"""
        # Simulate some performance data
        self.system.performance_metrics["error_rates"] = [0, 0, 1, 0, 0] * 20  # 20% error rate
        self.system.performance_metrics["average_latency"] = 0.8  # 800ms
        
        health = self.system._assess_health()
        
        assert "overall_health" in health
        assert "error_rate" in health
        assert "latency_sla_met" in health
        assert health["error_rate"] == 0.2
        assert health["latency_sla_met"] is True  # 800ms < 1000ms target
    
    def test_cost_efficiency_calculation(self):
        """Test cost efficiency calculation"""
        # Simulate cost data
        self.system.performance_metrics["cost_tracking"] = [0.05] * 100  # $0.05 per request
        
        efficiency = self.system._calculate_cost_efficiency()
        
        assert "average_cost_per_request" in efficiency
        assert "budget_utilization" in efficiency
        assert "cost_budget_met" in efficiency
        assert efficiency["average_cost_per_request"] == 0.05
    
    def test_experiment_management(self):
        """Test experiment tracking"""
        experiment_id = self.system.start_experiment(
            "test_experiment",
            {"strategy": "react", "temperature": 0.7}
        )
        
        assert experiment_id in self.system.experiment_tracker
        assert self.system.experiment_tracker[experiment_id]["status"] == "running"
        
        # Log metrics
        self.system.log_experiment_metric(experiment_id, "accuracy", 0.95)
        
        metrics = self.system.experiment_tracker[experiment_id]["metrics"]
        assert len(metrics) == 1
        assert metrics[0]["metric_name"] == "accuracy"
        assert metrics[0]["value"] == 0.95
        
        # Complete experiment
        completed = self.system.complete_experiment(experiment_id, ["High accuracy achieved"])
        
        assert completed["status"] == "completed"
        assert len(completed["insights"]) == 1


class TestModelConfiguration:
    """Test cases for ModelConfiguration"""
    
    def test_model_config_creation(self):
        """Test model configuration creation"""
        config = ModelConfiguration(
            model_name="gpt-4",
            model_type="llm",
            provider="openai",
            version="gpt-4-0613",
            parameters={"temperature": 0.7, "max_tokens": 4096},
            cost_per_token=0.00003,
            fallback_models=["gpt-3.5-turbo"]
        )
        
        assert config.model_name == "gpt-4"
        assert config.provider == "openai"
        assert config.parameters["temperature"] == 0.7
        assert config.cost_per_token == 0.00003
        assert "gpt-3.5-turbo" in config.fallback_models


class TestAgentConfiguration:
    """Test cases for AgentConfiguration"""
    
    def test_agent_config_creation(self):
        """Test agent configuration creation"""
        config = AgentConfiguration(
            agent_id="financial_analyst",
            agent_type="specialist",
            primary_model="gpt-4",
            backup_models=["claude-3"],
            capabilities=[AgentCapability.ANALYSIS, AgentCapability.PREDICTION],
            specialization="financial_analysis",
            decision_threshold=0.8
        )
        
        assert config.agent_id == "financial_analyst"
        assert config.agent_type == "specialist"
        assert AgentCapability.ANALYSIS in config.capabilities
        assert config.decision_threshold == 0.8


class TestIntegrationPatterns:
    """Test integration patterns and enterprise features"""
    
    def setup_method(self):
        """Setup test environment"""
        self.requirements = SystemRequirements(
            domain="enterprise",
            use_case="integration_testing",
            compliance_requirements=["SOX", "GDPR"]
        )
        self.system = CompoundAISystem(
            system_id="integration_test",
            requirements=self.requirements
        )
    
    def test_enterprise_integration_setup(self):
        """Test enterprise integration configuration"""
        integration_config = {
            "salesforce": {
                "username": "test@company.com",
                "instance_url": "https://test.salesforce.com"
            },
            "microsoft365": {
                "tenant_id": "test-tenant",
                "client_id": "test-client"
            }
        }
        
        # Mock the integration layer
        with patch('src.core.compound_system.EnterpriseIntegrationLayer') as mock_integration:
            self.system.setup_enterprise_integration(integration_config)
            
            assert self.system.integration_layer is not None
            mock_integration.assert_called_once_with(integration_config)
    
    def test_security_framework_setup(self):
        """Test security framework configuration"""
        security_config = {
            "encryption": "AES-256-GCM",
            "authentication": "OAuth2",
            "audit_logging": True
        }
        
        with patch('src.core.compound_system.SecurityFramework') as mock_security:
            self.system.setup_security_framework(security_config)
            
            assert self.system.security_framework is not None
            mock_security.assert_called_once_with(security_config)
    
    def test_compliance_monitoring_setup(self):
        """Test compliance monitoring configuration"""
        compliance_config = {
            "frameworks": ["SOX", "GDPR"],
            "audit_frequency": "daily",
            "reporting": True
        }
        
        with patch('src.core.compound_system.ComplianceMonitor') as mock_compliance:
            self.system.setup_compliance_monitoring(compliance_config)
            
            assert self.system.compliance_monitor is not None
            mock_compliance.assert_called_once_with(compliance_config)


@pytest.fixture
def sample_system():
    """Fixture providing a sample compound AI system"""
    requirements = SystemRequirements(
        domain="test",
        use_case="testing",
        latency_target_ms=500,
        throughput_rps=100
    )
    
    system = CompoundAISystem(
        system_id="sample_test_system",
        requirements=requirements
    )
    
    # Add sample model
    model_config = ModelConfiguration(
        model_name="test_model",
        model_type="llm",
        provider="test_provider",
        version="1.0"
    )
    system.add_model(model_config)
    
    # Add sample agent
    agent_config = AgentConfiguration(
        agent_id="test_agent",
        agent_type="analyst",
        primary_model="test_model",
        capabilities=[AgentCapability.ANALYSIS]
    )
    system.add_agent(agent_config)
    
    return system


class TestSystemIntegration:
    """Integration tests for compound AI system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_processing(self, sample_system):
        """Test end-to-end request processing"""
        # Mock the underlying processing
        with patch.object(sample_system, '_process_adaptive', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = {
                "success": True,
                "result": {"analysis": "completed", "confidence": 0.95},
                "models_used": ["test_model"],
                "agents_used": ["test_agent"]
            }
            
            request = {
                "task_type": "analysis",
                "input_data": {"text": "analyze this business scenario"},
                "context": {"domain": "business", "urgency": "high"}
            }
            
            result = await sample_system.process_request(request)
            
            assert result["success"] is True
            assert "system_metadata" in result
            assert result["system_metadata"]["models_involved"] == ["test_model"]
            assert result["system_metadata"]["confidence_score"] is not None
    
    def test_performance_under_load(self, sample_system):
        """Test system performance under simulated load"""
        # Simulate multiple requests
        for i in range(100):
            sample_system._update_metrics(
                f"request_{i}", 
                np.random.normal(0.2, 0.05),  # ~200ms with variance
                {"success": True, "accuracy": np.random.normal(0.9, 0.05)}
            )
        
        status = sample_system.get_system_status()
        
        assert status["performance_metrics"]["requests_processed"] == 100
        assert 0.1 <= status["performance_metrics"]["average_latency"] <= 0.3
        assert len(status["performance_metrics"]["accuracy_scores"]) == 100
    
    def test_error_handling_and_recovery(self, sample_system):
        """Test error handling and system recovery"""
        # Simulate errors
        for i in range(20):
            success = i % 5 != 0  # 20% error rate
            sample_system._update_metrics(
                f"request_{i}",
                0.2,
                {"success": success}
            )
        
        health = sample_system._assess_health()
        
        assert health["error_rate"] == 0.2
        assert health["overall_health"] == "degraded"  # Due to high error rate


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"]) 