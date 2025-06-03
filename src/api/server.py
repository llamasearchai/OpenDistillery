"""
OpenDistillery FastAPI Server
Main production-ready API server with comprehensive enterprise features.
"""

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
import uvicorn
import structlog

# Import monitoring components
from src.monitoring.metrics import get_metrics_collector, get_prometheus_exporter
from src.monitoring.health_check import HealthChecker, get_health_checker
from src.monitoring.alerting import AlertManager
from src.monitoring.tracing import configure_tracing
from src.monitoring.logger import get_logger
from src.security.auth import create_access_token, verify_password, get_password_hash, get_current_user

# Configure structured logging
logger = get_logger(__name__)

# Security
security = HTTPBearer()

# Global state
api_keys: Dict[str, Dict[str, Any]] = {}
app_start_time = time.time()

# Mock user database - replace with actual database in production
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # 'secret'
        "disabled": False,
    }
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting OpenDistillery API Server")
    
    # Initialize components
    await initialize_system()
    
    yield
    
    # Cleanup
    logger.info("Shutting down OpenDistillery API Server")
    await cleanup_system()

# Create FastAPI app
app = FastAPI(
    title="OpenDistillery API",
    description="Advanced Compound AI Systems for Enterprise Workflow Transformation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    uptime_seconds: float
    components: Dict[str, str]

class SystemCreateRequest(BaseModel):
    system_id: str = Field(..., description="Unique system identifier")
    domain: str = Field(..., description="Domain (finance, healthcare, etc.)")
    use_case: str = Field(..., description="Specific use case")
    architecture: str = Field(default="hybrid", description="System architecture")
    requirements: Dict[str, Any] = Field(default_factory=dict)

class SystemResponse(BaseModel):
    success: bool
    system_id: str
    status: str
    message: str
    system_info: Optional[Dict[str, Any]] = None

class TaskRequest(BaseModel):
    task_type: str = Field(..., description="Type of task to process")
    input_data: Dict[str, Any] = Field(..., description="Input data for processing")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    reasoning_strategy: Optional[str] = Field(None, description="Reasoning strategy to use")
    requirements: Optional[Dict[str, Any]] = Field(default_factory=dict)

class TaskResponse(BaseModel):
    success: bool
    task_id: str
    result: Dict[str, Any]
    processing_time: float
    confidence: Optional[float] = None
    models_used: Optional[List[str]] = None

class OptimizationRequest(BaseModel):
    target: str = Field(..., description="Optimization target")
    constraints: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)

class QueryRequest(BaseModel):
    query: str = Field(..., description="Query string")
    context: Dict[str, Any] = Field(default_factory=dict)
    filters: Dict[str, Any] = Field(default_factory=dict)

class TrainingRequest(BaseModel):
    model_type: str = Field(..., description="Type of model to train")
    training_data: Dict[str, Any] = Field(..., description="Training data")
    parameters: Dict[str, Any] = Field(default_factory=dict)

# Authentication
async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Validate API key and return user info"""
    token = credentials.credentials
    
    if token not in api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    user_info = api_keys[token]
    
    # Check if key is expired
    if datetime.now() > user_info["expires_at"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key expired"
        )
    
    return user_info

# Middleware for monitoring
@app.middleware("http")
async def monitor_requests(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # Record metrics using centralized collector
    metrics_collector = get_metrics_collector()
    metrics_collector.record_http_request(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
        duration=duration
    )
    
    response.headers["X-Processing-Time"] = str(duration)
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    
    return response

# Core endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - app_start_time
    
    # Get detailed health status
    health_checker = get_health_checker()
    system_health = await health_checker.check_all()
    
    return HealthResponse(
        status=system_health.status.value,
        version="1.0.0",
        timestamp=datetime.now(),
        uptime_seconds=uptime,
        components={comp.name: comp.status.value for comp in system_health.components}
    )

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    exporter = get_prometheus_exporter()
    return Response(exporter.export_metrics(), media_type=exporter.get_content_type())

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OpenDistillery API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# System management endpoints
@app.post("/systems", response_model=SystemResponse)
async def create_system(
    request: SystemCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new AI system"""
    try:
        logger.info("Creating system", system_id=request.system_id, domain=request.domain)
        
        # Mock system creation for now
        system_info = {
            "system_id": request.system_id,
            "domain": request.domain,
            "use_case": request.use_case,
            "architecture": request.architecture,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "models": ["gpt-4", "claude-3"],
            "capabilities": ["reasoning", "analysis", "synthesis"]
        }
        
        # Update metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.set_active_systems(1)  # In real implementation, this would be dynamic
        
        return SystemResponse(
            success=True,
            system_id=request.system_id,
            status="created",
            message=f"System created successfully for {request.domain}",
            system_info=system_info
        )
    
    except Exception as e:
        logger.error("Failed to create system", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/systems")
async def list_systems(user: Dict[str, Any] = Depends(get_current_user)):
    """List all systems"""
    # Mock response for now
    systems = [
        {
            "system_id": "demo_system",
            "domain": "finance",
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
    ]
    
    return {"systems": systems, "total": len(systems)}

@app.post("/systems/{system_id}/tasks", response_model=TaskResponse)
async def process_task(
    system_id: str,
    request: TaskRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Process a task through the AI system"""
    try:
        start_time = time.time()
        task_id = str(uuid.uuid4())
        
        logger.info("Processing task", task_id=task_id, system_id=system_id, task_type=request.task_type)
        
        # Mock task processing
        await asyncio.sleep(0.1)  # Simulate processing
        
        result = {
            "task_id": task_id,
            "system_id": system_id,
            "result": "Task processed successfully",
            "analysis": f"Processed {request.task_type} task with high confidence",
            "recommendations": ["Consider automation", "Review results"]
        }
        
        processing_time = time.time() - start_time
        
        # Record AI processing metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.record_ai_processing("gpt-4", request.task_type, processing_time)
        metrics_collector.record_task_processed(system_id, request.task_type, "completed")
        
        return TaskResponse(
            success=True,
            task_id=task_id,
            result=result,
            processing_time=processing_time,
            confidence=0.95,
            models_used=["gpt-4", "claude-3"]
        )
    
    except Exception as e:
        logger.error("Task processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/systems/{system_id}")
async def get_system(
    system_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get system information"""
    # Mock system info
    system_info = {
        "system_id": system_id,
        "status": "active",
        "domain": "finance",
        "models": ["gpt-4", "claude-3"],
        "performance": {
            "avg_processing_time": 0.25,
            "success_rate": 0.98,
            "confidence_score": 0.92
        }
    }
    
    return system_info

# API key management
@app.post("/auth/api-keys")
async def create_api_key(
    name: str,
    expires_in_days: int = 30,
    user: Optional[Dict[str, Any]] = None
):
    """Create a new API key"""
    import secrets
    
    api_key = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=expires_in_days)
    
    api_keys[api_key] = {
        "name": name,
        "created_at": datetime.now(),
        "expires_at": expires_at,
        "tier": "enterprise"
    }
    
    return {
        "api_key": api_key,
        "name": name,
        "expires_at": expires_at.isoformat()
    }

# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error("Unhandled exception", error=str(exc), path=str(request.url.path))
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

# Utility functions
async def initialize_system():
    """Initialize system components"""
    # Create demo API key
    demo_key = "demo_key_12345"
    api_keys[demo_key] = {
        "name": "Demo Key",
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(days=365),
        "tier": "enterprise"
    }
    
    logger.info("System initialized")

async def cleanup_system():
    """Cleanup system resources"""
    logger.info("System cleanup completed")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict or not verify_password(form_data.password, user_dict["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user_dict["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: str = Depends(get_current_user)):
    return {"username": current_user}

# Secure the endpoints with dependency injection
@app.post("/api/v1/optimize")
async def optimize_endpoint(request: OptimizationRequest, current_user: str = Depends(get_current_user)):
    return await handle_optimization(request)

@app.post("/api/v1/query")
async def query_endpoint(request: QueryRequest, current_user: str = Depends(get_current_user)):
    return await handle_query(request)

@app.post("/api/v1/train")
async def train_endpoint(request: TrainingRequest, current_user: str = Depends(get_current_user)):
    return await handle_training(request)

@app.get("/api/v1/models")
async def list_models_endpoint(current_user: str = Depends(get_current_user)):
    return await handle_list_models()

@app.get("/api/v1/health")
async def health_check(current_user: str = Depends(get_current_user)):
    return {"status": "healthy"}

# Handler functions now that models are defined above

# Define handler functions
async def handle_optimization(request: OptimizationRequest) -> Dict[str, Any]:
    return {"status": "optimized", "target": request.target}

async def handle_query(request: QueryRequest) -> Dict[str, Any]:
    return {"status": "queried", "results": []}

async def handle_training(request: TrainingRequest) -> Dict[str, Any]:
    return {"status": "training_started", "model_type": request.model_type}

async def handle_list_models() -> Dict[str, Any]:
    return {"models": ["gpt-4", "claude-3", "local-llm"]}

def main():
    """Main entry point"""
    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main() 