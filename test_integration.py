#!/usr/bin/env python3
"""
OpenDistillery Integration Test
Simple test script to verify the complete system works end-to-end.
"""

import requests
import json
import time

def test_integration():
    """Test complete system integration"""
    
    print(" Starting OpenDistillery Integration Test")
    
    base_url = "http://localhost:8000"
    demo_key = "demo_key_12345"
    headers = {"Authorization": f"Bearer {demo_key}"}
    
    # Test 1: Health Check
    print("\n1. Testing Health Check...")
    try:
        response = requests.get(f"{base_url}/health")
        assert response.status_code == 200
        health_data = response.json()
        print(f"   ✅ Health Status: {health_data['status']}")
        print(f"   ⏱  Uptime: {health_data['uptime_seconds']:.2f} seconds")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return False
    
    # Test 2: Metrics
    print("\n2. Testing Metrics...")
    try:
        response = requests.get(f"{base_url}/metrics")
        assert response.status_code == 200
        assert "opendistillery" in response.text
        print("   ✅ Metrics endpoint working")
    except Exception as e:
        print(f"   ❌ Metrics test failed: {e}")
        return False
    
    # Test 3: Create API Key
    print("\n3. Testing API Key Creation...")
    try:
        response = requests.post(
            f"{base_url}/auth/api-keys?name=test_key&expires_in_days=30"
        )
        assert response.status_code == 200
        key_data = response.json()
        print(f"   ✅ Created API key: {key_data['name']}")
    except Exception as e:
        print(f"   ❌ API key creation failed: {e}")
        return False
    
    # Test 4: List Systems
    print("\n4. Testing System Listing...")
    try:
        response = requests.get(f"{base_url}/systems", headers=headers)
        assert response.status_code == 200
        systems_data = response.json()
        print(f"   ✅ Listed {systems_data['total']} systems")
    except Exception as e:
        print(f"   ❌ System listing failed: {e}")
        return False
    
    # Test 5: Create System
    print("\n5. Testing System Creation...")
    try:
        system_data = {
            "system_id": "integration_test_system",
            "domain": "testing",
            "use_case": "integration_testing",
            "architecture": "hybrid"
        }
        response = requests.post(
            f"{base_url}/systems", 
            json=system_data, 
            headers=headers
        )
        assert response.status_code == 200
        created_system = response.json()
        print(f"   ✅ Created system: {created_system['system_id']}")
    except Exception as e:
        print(f"   ❌ System creation failed: {e}")
        return False
    
    # Test 6: Process Task
    print("\n6. Testing Task Processing...")
    try:
        task_data = {
            "task_type": "integration_test",
            "input_data": {
                "test": "data",
                "timestamp": time.time()
            },
            "context": {
                "test_run": True
            }
        }
        response = requests.post(
            f"{base_url}/systems/integration_test_system/tasks",
            json=task_data,
            headers=headers
        )
        assert response.status_code == 200
        task_result = response.json()
        print(f"   ✅ Processed task: {task_result['task_id']}")
        print(f"   ⏱  Processing time: {task_result['processing_time']:.3f}s")
        print(f"    Confidence: {task_result['confidence']}")
    except Exception as e:
        print(f"   ❌ Task processing failed: {e}")
        return False
    
    print("\n All integration tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = test_integration()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠  Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit(1) 