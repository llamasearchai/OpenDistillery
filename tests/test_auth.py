import pytest
import jwt
import datetime
from fastapi.testclient import TestClient
from src.api.server import app
from src.security.auth import create_access_token, verify_password, get_password_hash, SECRET_KEY, ALGORITHM

client = TestClient(app)

@pytest.fixture
async def test_user():
    return {
        "username": "testuser",
        "password": "testpassword"
    }

@pytest.mark.asyncio
async def test_create_access_token():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "testuser"
    assert "exp" in decoded

@pytest.mark.asyncio
async def test_password_hashing_and_verification():
    password = "testpassword"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

@pytest.mark.asyncio
async def test_login_success(test_user):
    response = client.post("/token", data={"username": "johndoe", "password": "secret"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_failure(test_user):
    response = client.post("/token", data={"username": "johndoe", "password": "wrongpassword"})
    assert response.status_code == 401
    assert "detail" in response.json()
    assert response.json()["detail"] == "Incorrect username or password"

@pytest.mark.asyncio
async def test_access_protected_endpoint_without_token():
    response = client.get("/users/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_access_protected_endpoint_with_valid_token():
    token_response = client.post("/token", data={"username": "johndoe", "password": "secret"})
    token = token_response.json()["access_token"]
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "johndoe" 