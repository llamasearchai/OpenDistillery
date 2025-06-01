"""
OpenDistillery Test Configuration
Pytest configuration and fixtures for testing.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

@pytest.fixture(autouse=True)
def setup_demo_api_key():
    """Automatically set up demo API key for all tests"""
    from src.api.server import api_keys
    
    # Demo API key for testing
    demo_key = "demo_key_12345"
    api_keys[demo_key] = {
        "name": "Demo Key",
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(days=365),
        "tier": "enterprise"
    }
    
    yield
    
    # Cleanup
    if demo_key in api_keys:
        del api_keys[demo_key]

@pytest.fixture
def test_client():
    """Create test client for API tests"""
    from src.api.server import app
    return TestClient(app) 