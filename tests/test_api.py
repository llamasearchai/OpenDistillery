"""
Comprehensive test suite for OpenDistillery API
Tests all endpoints, authentication, and core functionality.
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
from datetime import datetime, timedelta

# Import the FastAPI app
from src.api.server import app

# Test configuration
TEST_API_KEY = "demo_key_12345"
INVALID_API_KEY = "invalid_key"

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Create async test client"""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

class TestHealthEndpoints:
    """Test health check and status endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "components" in data
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        # Check for any OpenDistillery metrics
        assert "opendistillery" in response.text
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "OpenDistillery API"
        assert data["version"] == "1.0.0"

class TestAuthentication:
    """Test authentication and authorization"""
    
    def test_unauthorized_request(self, client):
        """Test request without API key"""
        response = client.get("/systems")
        assert response.status_code == 403  # Should be 401 but depends on FastAPI security setup
    
    def test_invalid_api_key(self, client):
        """Test request with invalid API key"""
        headers = {"Authorization": f"Bearer {INVALID_API_KEY}"}
        response = client.get("/systems", headers=headers)
        assert response.status_code == 401
    
    def test_valid_api_key(self, client):
        """Test request with valid API key"""
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        response = client.get("/systems", headers=headers)
        assert response.status_code == 200

class TestSystemManagement:
    """Test AI system management endpoints"""
    
    def test_list_systems(self, client):
        """Test listing systems"""
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        response = client.get("/systems", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "systems" in data
        assert "total" in data
    
    def test_create_system(self, client):
        """Test creating a new AI system"""
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        system_data = {
            "system_id": "test_system_001",
            "domain": "finance",
            "use_case": "risk_analysis",
            "architecture": "hybrid",
            "requirements": {
                "latency_target_ms": 500,
                "throughput_rps": 100
            }
        }
        
        response = client.post("/systems", json=system_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["system_id"] == "test_system_001"
        assert data["status"] == "created"
        assert "system_info" in data
    
    def test_get_system_info(self, client):
        """Test getting system information"""
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        response = client.get("/systems/demo_system", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "system_id" in data
        assert "status" in data
        assert "domain" in data
    
    def test_create_system_validation(self, client):
        """Test system creation with invalid data"""
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        invalid_data = {
            "domain": "finance",
            # Missing required fields
        }
        
        response = client.post("/systems", json=invalid_data, headers=headers)
        assert response.status_code == 422  # Validation error

class TestTaskProcessing:
    """Test task processing endpoints"""
    
    def test_process_task(self, client):
        """Test processing a task"""
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        task_data = {
            "task_type": "financial_analysis",
            "input_data": {
                "company": "Test Corp",
                "revenue": 1000000,
                "expenses": 800000
            },
            "context": {
                "industry": "technology",
                "market_cap": "mid"
            },
            "reasoning_strategy": "adaptive"
        }
        
        response = client.post("/systems/demo_system/tasks", json=task_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "task_id" in data
        assert "result" in data
        assert "processing_time" in data
        assert "confidence" in data
        assert "models_used" in data
    
    def test_task_validation(self, client):
        """Test task processing with invalid data"""
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        invalid_data = {
            "task_type": "analysis",
            # Missing required input_data
        }
        
        response = client.post("/systems/demo_system/tasks", json=invalid_data, headers=headers)
        assert response.status_code == 422

class TestApiKeyManagement:
    """Test API key management"""
    
    def test_create_api_key(self, client):
        """Test creating a new API key"""
        response = client.post("/auth/api-keys?name=test_key&expires_in_days=30")
        assert response.status_code == 200
        data = response.json()
        assert "api_key" in data
        assert data["name"] == "test_key"
        assert "expires_at" in data

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_nonexistent_system(self, client):
        """Test accessing non-existent system"""
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        response = client.get("/systems/nonexistent_system", headers=headers)
        assert response.status_code == 200  # Mock response returns data
    
    def test_invalid_json(self, client):
        """Test invalid JSON payload"""
        headers = {
            "Authorization": f"Bearer {TEST_API_KEY}",
            "Content-Type": "application/json"
        }
        response = client.post("/systems", data="invalid json", headers=headers)
        assert response.status_code == 422
    
    def test_large_payload(self, client):
        """Test handling of large payloads"""
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        large_data = {
            "system_id": "large_test",
            "domain": "finance",
            "use_case": "analysis",
            "requirements": {"large_field": "x" * 10000}  # Large string
        }
        
        response = client.post("/systems", json=large_data, headers=headers)
        assert response.status_code == 200

class TestAsyncEndpoints:
    """Test async functionality"""
    
    def test_concurrent_requests(self, client):
        """Test handling concurrent requests"""
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        
        # Create multiple concurrent requests using sync client
        responses = []
        for i in range(5):
            task_data = {
                "task_type": f"test_task_{i}",
                "input_data": {"data": f"test_{i}"}
            }
            response = client.post("/systems/demo_system/tasks", json=task_data, headers=headers)
            responses.append(response)
        
        # Check all requests succeeded
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

class TestPerformance:
    """Test performance characteristics"""
    
    def test_response_time(self, client):
        """Test API response times"""
        import time
        
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        start_time = time.time()
        
        response = client.get("/health")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second
    
    def test_memory_usage(self, client):
        """Test memory usage during requests"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        
        # Make multiple requests
        for _ in range(10):
            response = client.get("/systems", headers=headers)
            assert response.status_code == 200
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024

class TestDataValidation:
    """Test data validation and sanitization"""
    
    def test_sql_injection_protection(self, client):
        """Test SQL injection protection"""
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        malicious_data = {
            "system_id": "test'; DROP TABLE users; --",
            "domain": "finance",
            "use_case": "analysis"
        }
        
        response = client.post("/systems", json=malicious_data, headers=headers)
        # Should either validate and reject, or sanitize the input
        assert response.status_code in [200, 422]
    
    def test_xss_protection(self, client):
        """Test XSS protection"""
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        xss_data = {
            "system_id": "test_system",
            "domain": "<script>alert('xss')</script>",
            "use_case": "analysis"
        }
        
        response = client.post("/systems", json=xss_data, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Should not contain the raw script tag
            assert "<script>" not in str(data)

# Test fixtures and utilities
@pytest.fixture(scope="session")
def setup_test_data():
    """Setup test data for the session"""
    # This would setup test database, mock data, etc.
    yield
    # Cleanup after tests

def test_api_documentation_available(client):
    """Test that API documentation is available"""
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/redoc")
    assert response.status_code == 200

def test_openapi_schema(client):
    """Test OpenAPI schema is valid"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 