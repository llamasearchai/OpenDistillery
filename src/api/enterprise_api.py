"""
OpenDistillery Enterprise API
Production-ready FastAPI application with comprehensive enterprise features.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# OpenDistillery imports
from ..core.compound_system import SystemBuilder, SystemRequirements, SystemArchitecture, ModelConfiguration
from ..agents.orchestrator import AgentOrchestrator, Task, TaskPriority
from ..security.authentication import AuthenticationManager, UserRole, AuthenticationResult
from ..monitoring.logger import get_logger
from ..config import get_config

# Initialize logger
logger = get_logger(__name__)

# Security
security = HTTPBearer()

# Global instances
system_builder = SystemBuilder()
orchestrator = AgentOrchestrator()
auth_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting OpenDistillery Enterprise API")
    
    # Initialize authentication manager
    global auth_manager
    config = get_config()
    auth_manager = AuthenticationManager(
        secret_key=config.security.secret_key
    )
    
    # Create default admin user if not exists
    try:
        admin_user = auth_manager.create_user(
            username="admin",
            email="nikjois@llamasearch.ai",
            password="admin123",  # Change in production
            role=UserRole.ADMIN
        )
        logger.info("Created default admin user", user_id=admin_user.user_id)
    except Exception as e:
        logger.warning("Admin user may already exist", error=str(e))
    
    # Initialize default system
    try:
        requirements = SystemRequirements(
            domain="general",
            use_case="enterprise_ai_platform",
            latency_target_ms=1000,
            throughput_rps=100
        )
        
        default_system = system_builder.create_system(
            system_id="default_enterprise_system",
            requirements=requirements,
            architecture=SystemArchitecture.HYBRID
        )
        
        logger.info("Initialized default enterprise system")
    except Exception as e:
        logger.error("Failed to initialize default system", error=e)
    
    yield
    
    # Shutdown
    logger.info("Shutting down OpenDistillery Enterprise API")
    await orchestrator.shutdown()

# Create FastAPI app
app = FastAPI(
    title="OpenDistillery Enterprise API",
    description="Advanced Compound AI Systems for Enterprise Workflow Transformation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Request/Response Models
class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    uptime_seconds: float
    metrics: Dict[str, Any]

class AuthRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None
    requires_mfa: bool = False
    error_message: Optional[str] = None

class TaskRequest(BaseModel):
    task_type: str
    description: str
    input_data: Dict[str, Any]
    priority: str = "medium"
    required_capabilities: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class SystemStatusResponse(BaseModel):
    system_id: str
    status: Dict[str, Any]
    health: str
    performance: Dict[str, Any]

# Middleware for request logging and correlation
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests with correlation tracking"""
    start_time = time.time()
    
    # Generate correlation ID
    correlation_id = logger.set_correlation_id()
    
    # Log request
    logger.log_request(
        method=request.method,
        path=str(request.url.path),
        status_code=0,  # Will be updated
        duration_ms=0   # Will be updated
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Log response
    logger.log_request(
        method=request.method,
        path=str(request.url.path),
        status_code=response.status_code,
        duration_ms=duration_ms
    )
    
    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    if not auth_manager:
        raise HTTPException(status_code=500, detail="Authentication not initialized")
    
    token = credentials.credentials
    auth_result = auth_manager.authenticate_token(token)
    
    if not auth_result.success:
        raise HTTPException(status_code=401, detail=auth_result.error_message)
    
    return auth_result.user

# API Routes

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    start_time = time.time()
    
    # Get system metrics
    systems_status = []
    for system_id in system_builder.list_systems():
        system = system_builder.get_system(system_id)
        if system:
            systems_status.append(system.get_system_status())
    
    orchestrator_status = orchestrator.get_orchestration_status()
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        uptime_seconds=time.time() - start_time,
        metrics={
            "systems_count": len(systems_status),
            "agents_count": orchestrator_status["agents"]["total"],
            "active_tasks": orchestrator_status["tasks"]["active"],
            "completed_tasks": orchestrator_status["tasks"]["completed"]
        }
    )

@app.post("/auth/login", response_model=AuthResponse)
async def login(auth_request: AuthRequest):
    """Authenticate user and return token"""
    if not auth_manager:
        raise HTTPException(status_code=500, detail="Authentication not initialized")
    
    auth_result = auth_manager.authenticate_password(
        auth_request.username,
        auth_request.password
    )
    
    logger.log_security_event(
        event_type="login_attempt",
        user_id=auth_result.user.user_id if auth_result.user else "unknown",
        details={
            "username": auth_request.username,
            "success": auth_result.success,
            "requires_mfa": auth_result.requires_mfa
        },
        severity="INFO" if auth_result.success else "WARNING"
    )
    
    return AuthResponse(
        success=auth_result.success,
        token=auth_result.token,
        user_id=auth_result.user.user_id if auth_result.user else None,
        role=auth_result.user.role.value if auth_result.user else None,
        requires_mfa=auth_result.requires_mfa,
        error_message=auth_result.error_message
    )

@app.post("/tasks", response_model=TaskResponse)
async def submit_task(
    task_request: TaskRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Submit a task for processing"""
    try:
        # Convert priority string to enum
        priority_map = {
            "low": TaskPriority.LOW,
            "medium": TaskPriority.MEDIUM,
            "high": TaskPriority.HIGH,
            "critical": TaskPriority.CRITICAL
        }
        priority = priority_map.get(task_request.priority.lower(), TaskPriority.MEDIUM)
        
        # Create task
        task = Task(
            task_id=f"task_{int(time.time())}_{current_user.user_id}",
            task_type=task_request.task_type,
            description=task_request.description,
            input_data=task_request.input_data,
            priority=priority,
            context={
                **task_request.context,
                "user_id": current_user.user_id,
                "submitted_at": datetime.utcnow().isoformat()
            }
        )
        
        # Submit to orchestrator
        task_id = await orchestrator.submit_task(task)
        
        logger.log_task_execution(
            task_id=task_id,
            task_type=task_request.task_type,
            agent_id="orchestrator",
            duration_ms=0,
            success=True
        )
        
        return TaskResponse(
            task_id=task_id,
            status="submitted",
            message="Task submitted successfully"
        )
        
    except Exception as e:
        logger.error("Task submission failed", error=e, user_id=current_user.user_id)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user = Depends(get_current_user)
):
    """Get task status and results"""
    # Check if task exists in completed tasks
    if task_id in orchestrator.completed_tasks:
        result = orchestrator.completed_tasks[task_id]
        return {
            "task_id": task_id,
            "status": "completed" if result.success else "failed",
            "success": result.success,
            "result": result.result_data,
            "execution_time": result.execution_time,
            "completed_at": result.completed_at,
            "error": result.error_message if not result.success else None
        }
    
    # Check if task is active
    if task_id in orchestrator.active_tasks:
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Task is currently being processed"
        }
    
    # Task not found
    raise HTTPException(status_code=404, detail="Task not found")

@app.get("/systems", response_model=List[str])
async def list_systems(current_user = Depends(get_current_user)):
    """List all available systems"""
    return system_builder.list_systems()

@app.get("/systems/{system_id}", response_model=SystemStatusResponse)
async def get_system_status(
    system_id: str,
    current_user = Depends(get_current_user)
):
    """Get detailed system status"""
    system = system_builder.get_system(system_id)
    if not system:
        raise HTTPException(status_code=404, detail="System not found")
    
    status = system.get_system_status()
    
    return SystemStatusResponse(
        system_id=system_id,
        status=status,
        health=status["health"]["overall"],
        performance=status["performance"]
    )

@app.post("/systems")
async def create_system(
    system_config: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Create a new compound AI system"""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.OPERATOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        # Extract configuration
        system_id = system_config.get("system_id")
        domain = system_config.get("domain", "general")
        use_case = system_config.get("use_case", "general_purpose")
        
        if not system_id:
            raise ValueError("system_id is required")
        
        # Create requirements
        requirements = SystemRequirements(
            domain=domain,
            use_case=use_case,
            latency_target_ms=system_config.get("latency_target_ms", 1000),
            throughput_rps=system_config.get("throughput_rps", 100),
            accuracy_threshold=system_config.get("accuracy_threshold", 0.95)
        )
        
        # Create system
        system = system_builder.create_system(
            system_id=system_id,
            requirements=requirements,
            architecture=SystemArchitecture(system_config.get("architecture", "hybrid"))
        )
        
        logger.info("System created", 
                   system_id=system_id, 
                   created_by=current_user.user_id)
        
        return {
            "system_id": system_id,
            "status": "created",
            "message": "System created successfully"
        }
        
    except Exception as e:
        logger.error("System creation failed", error=e, user_id=current_user.user_id)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents")
async def list_agents(current_user = Depends(get_current_user)):
    """List all registered agents"""
    status = orchestrator.get_orchestration_status()
    return {
        "total_agents": status["agents"]["total"],
        "active_agents": status["agents"]["active"],
        "agent_types": status["agents"]["by_type"]
    }

@app.get("/metrics")
async def get_metrics(current_user = Depends(get_current_user)):
    """Get system metrics for monitoring"""
    # Aggregate metrics from all systems
    all_metrics = {}
    
    for system_id in system_builder.list_systems():
        system = system_builder.get_system(system_id)
        if system:
            status = system.get_system_status()
            all_metrics[system_id] = status["performance"]
    
    orchestrator_status = orchestrator.get_orchestration_status()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "systems": all_metrics,
        "orchestrator": orchestrator_status["performance"],
        "overall_health": "healthy"  # Could be computed based on all systems
    }

@app.post("/admin/users")
async def create_user(
    user_data: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Create a new user (admin only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not auth_manager:
        raise HTTPException(status_code=500, detail="Authentication not initialized")
    
    try:
        user = auth_manager.create_user(
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"],
            role=UserRole(user_data.get("role", "viewer"))
        )
        
        logger.log_security_event(
            event_type="user_created",
            user_id=current_user.user_id,
            details={
                "new_user_id": user.user_id,
                "username": user.username,
                "role": user.role.value
            }
        )
        
        return {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "created_at": user.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error("User creation failed", error=e, user_id=current_user.user_id)
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning("HTTP exception", 
                  status_code=exc.status_code, 
                  detail=exc.detail,
                  path=str(request.url.path))
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error("Unhandled exception", 
                error=exc,
                path=str(request.url.path))
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Main entry point
def main():
    """Main entry point for the API server"""
    config = get_config()
    
    uvicorn.run(
        "opendistillery.api.enterprise_api:app",
        host=config.api_host,
        port=config.api_port,
        workers=config.worker_processes,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()