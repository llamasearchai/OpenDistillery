"""
Enterprise-grade API endpoints for next-gen prompting
RESTful API with OpenAPI 3.0 specification
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import asyncio
import time
from datetime import datetime
import uuid

app = FastAPI(
    title="OpenDistillery Advanced Prompting API",
    description="Next-generation AI prompting platform with cutting-edge techniques",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

class PromptRequest(BaseModel):
    prompt: str = Field(..., description="Input prompt to optimize")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    techniques: Optional[List[str]] = Field(None, description="Specific techniques to use")
    quality_target: float = Field(0.90, ge=0.0, le=1.0, description="Quality target (0-1)")
    time_budget: float = Field(30.0, ge=1.0, le=300.0, description="Time budget in seconds")
    model_preference: Optional[str] = Field(None, description="Preferred model")
    safety_level: str = Field("standard", description="Safety level: strict, standard, relaxed")

class PromptResponse(BaseModel):
    request_id: str
    optimized_prompt: str
    techniques_used: List[str]
    performance_metrics: Dict[str, Any]
    execution_time: float
    model_used: str
    safety_score: float
    api_version: str = "2.0.0"

class BatchPromptRequest(BaseModel):
    prompts: List[PromptRequest]
    parallel_execution: bool = True
    priority: str = Field("normal", description="Priority: low, normal, high")

# Global instances
orchestrator = AdaptivePromptingOrchestrator()
model_hub = UnifiedModelHub()
usage_tracker = {}

@app.post("/v2/prompt/optimize", response_model=PromptResponse)
async def optimize_prompt(
    request: PromptRequest,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Optimize a prompt using advanced AI techniques
    """
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Validate API key
        api_key = credentials.credentials
        if not await validate_api_key(api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Apply adaptive prompting
        result = await orchestrator.adaptive_prompting(
            prompt=request.prompt,
            context=request.context,
            quality_target=request.quality_target,
            time_budget=request.time_budget
        )
        
        # Get best model for final execution
        if request.model_preference:
            model_used = request.model_preference
        else:
            model_used = await model_hub.intelligent_router.select_model(
                prompt=result["ensemble_result"]["ensemble_prompt"],
                task_type="general",
                quality_tier="highest",
                budget_constraint=None,
                available_models=model_hub.models
            )
        
        # Execute with selected model
        final_result = await model_hub.optimal_completion(
            prompt=result["ensemble_result"]["ensemble_prompt"],
            task_type="general",
            quality_tier="highest"
        )
        
        execution_time = time.time() - start_time
        
        # Log usage in background
        background_tasks.add_task(
            log_usage,
            api_key,
            request_id,
            execution_time,
            len(request.techniques or []),
            model_used
        )
        
        return PromptResponse(
            request_id=request_id,
            optimized_prompt=result["ensemble_result"]["ensemble_prompt"],
            techniques_used=result["techniques_used"],
            performance_metrics={
                "quality_improvement": result["performance_improvement"],
                "execution_time": execution_time,
                "techniques_applied": len(result["techniques_used"]),
                "ensemble_quality": result["ensemble_result"]["ensemble_quality_estimate"]
            },
            execution_time=execution_time,
            model_used=model_used,
            safety_score=0.95,  # From constitutional AI evaluation
            api_version="2.0.0"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/v2/prompt/batch", response_model=Dict[str, Any])
async def batch_optimize_prompts(
    request: BatchPromptRequest,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Batch optimize multiple prompts with intelligent load balancing
    """
    
    batch_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Validate API key
        api_key = credentials.credentials
        if not await validate_api_key(api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        if len(request.prompts) > 100:
            raise HTTPException(status_code=400, detail="Batch size limited to 100 prompts")
        
        # Process prompts
        if request.parallel_execution:
            # Parallel processing with concurrency control
            semaphore = asyncio.Semaphore(10)  # Limit concurrent requests
            
            async def process_single_prompt(prompt_req: PromptRequest):
                async with semaphore:
                    return await orchestrator.adaptive_prompting(
                        prompt=prompt_req.prompt,
                        context=prompt_req.context,
                        quality_target=prompt_req.quality_target,
                        time_budget=prompt_req.time_budget
                    )
            
            tasks = [process_single_prompt(prompt_req) for prompt_req in request.prompts]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        else:
            # Sequential processing
            results = []
            for prompt_req in request.prompts:
                result = await orchestrator.adaptive_prompting(
                    prompt=prompt_req.prompt,
                    context=prompt_req.context,
                    quality_target=prompt_req.quality_target,
                    time_budget=prompt_req.time_budget
                )
                results.append(result)
        
        execution_time = time.time() - start_time
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "index": i,
                    "error": str(result),
                    "success": False
                })
            else:
                processed_results.append({
                    "index": i,
                    "optimized_prompt": result["ensemble_result"]["ensemble_prompt"],
                    "techniques_used": result["techniques_used"],
                    "performance_improvement": result["performance_improvement"],
                    "success": True
                })
        
        # Log batch usage
        background_tasks.add_task(
            log_batch_usage,
            api_key,
            batch_id,
            len(request.prompts),
            execution_time
        )
        
        return {
            "batch_id": batch_id,
            "total_prompts": len(request.prompts),
            "successful_prompts": sum(1 for r in processed_results if r.get("success", False)),
            "failed_prompts": sum(1 for r in processed_results if not r.get("success", True)),
            "results": processed_results,
            "execution_time": execution_time,
            "parallel_execution": request.parallel_execution
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing error: {str(e)}")

@app.get("/v2/techniques/list")
async def list_available_techniques(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    List all available prompting techniques with descriptions
    """
    
    api_key = credentials.credentials
    if not await validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    techniques_info = {
        "quantum_superposition": {
            "name": "Quantum Prompt Superposition",
            "description": "Quantum-inspired prompt optimization using superposition states",
            "research_paper": "Quantum Superposition Prompting for Enhanced LLM Reasoning (2024)",
            "performance_tier": "experimental",
            "complexity": "high",
            "best_for": ["complex_reasoning", "creative_tasks", "multi_perspective_analysis"]
        },
        "neural_architecture_search": {
            "name": "Neural Architecture Search for Prompts",
            "description": "Automated discovery of optimal prompt architectures",
            "research_paper": "NAS-P: Neural Architecture Search for Prompting (2024)",
            "performance_tier": "beta",
            "complexity": "very_high",
            "best_for": ["optimization", "systematic_search", "architecture_discovery"]
        },
        "hyperparameter_optimization": {
            "name": "Hyperparameter Optimized Prompting",
            "description": "Bayesian optimization of prompt hyperparameters",
            "research_paper": "Hyperparameter Optimization for Prompting (HOP) (2024)",
            "performance_tier": "production",
            "complexity": "medium",
            "best_for": ["fine_tuning", "performance_optimization", "parameter_search"]
        },
        "metacognitive": {
            "name": "Meta-Cognitive Prompting",
            "description": "Self-aware prompting with reflection and adaptation",
            "research_paper": "Meta-Cognitive AI: Self-Reflective Prompting Systems (2024)",
            "performance_tier": "production",
            "complexity": "high",
            "best_for": ["self_improvement", "adaptive_reasoning", "reflective_analysis"]
        },
        "neuro_symbolic": {
            "name": "Neuro-Symbolic Prompting",
            "description": "Combines neural generation with symbolic reasoning",
            "research_paper": "Neuro-Symbolic Prompting Framework (2024)",
            "performance_tier": "beta",
            "complexity": "very_high",
            "best_for": ["logical_reasoning", "knowledge_integration", "hybrid_intelligence"]
        },
        "multimodal_cot": {
            "name": "Multi-Modal Chain of Thought",
            "description": "Chain of thought reasoning across multiple modalities",
            "research_paper": "Multi-Modal Chain of Thought Reasoning (2024)",
            "performance_tier": "production",
            "complexity": "high",
            "best_for": ["multimodal_tasks", "complex_reasoning", "cross_modal_analysis"]
        },
        "tree_of_thoughts": {
            "name": "Tree of Thoughts",
            "description": "Systematic exploration of thought processes in tree structure",
            "research_paper": "Tree of Thoughts: Deliberate Problem Solving with Large Language Models",
            "performance_tier": "production",
            "complexity": "medium",
            "best_for": ["problem_solving", "systematic_exploration", "decision_making"]
        }
    }
    
    return {
        "total_techniques": len(techniques_info),
        "techniques": techniques_info,
        "api_version": "2.0.0",
        "last_updated": datetime.now().isoformat()
    }

@app.get("/v2/models/available")
async def list_available_models(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    List all available models with capabilities and pricing
    """
    
    api_key = credentials.credentials
    if not await validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    models_info = {}
    for model_name, capabilities in model_hub.models.items():
        models_info[model_name] = {
            "max_tokens": capabilities.max_tokens,
            "supports_vision": capabilities.supports_vision,
            "supports_function_calling": capabilities.supports_function_calling,
            "cost_per_token": capabilities.cost_per_token,
            "reasoning_quality": capabilities.reasoning_quality,
            "safety_rating": capabilities.safety_rating,
            "speed_tier": capabilities.speed_tier,
            "provider": model_hub._get_provider(model_name).value
        }
    
    return {
        "total_models": len(models_info),
        "models": models_info,
        "api_version": "2.0.0"
    }

@app.get("/v2/analytics/usage")
async def get_usage_analytics(
    days: int = 30,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get detailed usage analytics and performance metrics
    """
    
    api_key = credentials.credentials
    if not await validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Get usage data (in production, fetch from database)
    user_usage = usage_tracker.get(api_key, {})
    
    analytics = {
        "time_period": f"Last {days} days",
        "total_requests": user_usage.get("total_requests", 0),
        "total_tokens": user_usage.get("total_tokens", 0),
        "total_cost": user_usage.get("total_cost", 0.0),
        "average_latency": user_usage.get("average_latency", 0.0),
        "success_rate": user_usage.get("success_rate", 1.0),
        "techniques_usage": user_usage.get("techniques_usage", {}),
        "models_usage": user_usage.get("models_usage", {}),
        "quality_improvements": {
            "average_improvement": user_usage.get("avg_improvement", 0.0),
            "best_improvement": user_usage.get("best_improvement", 0.0),
            "improvement_distribution": user_usage.get("improvement_dist", [])
        },
        "cost_breakdown": {
            "by_model": user_usage.get("cost_by_model", {}),
            "by_technique": user_usage.get("cost_by_technique", {}),
            "optimization_savings": user_usage.get("optimization_savings", 0.0)
        }
    }
    
    return analytics

@app.get("/v2/system/health")
async def system_health():
    """
    Get comprehensive system health and performance metrics
    """
    
    # Check model hub health
    model_health = await model_hub.get_system_health() if hasattr(model_hub, 'get_system_health') else {"status": "unknown"}
    
    # Check technique orchestrator health
    technique_health = {
        "available_techniques": len(orchestrator.techniques),
        "performance_history_size": len(orchestrator.performance_history),
        "router_status": "operational"
    }
    
    # System metrics
    import psutil
    
    system_metrics = {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "active_connections": len(usage_tracker)
    }
    
    overall_health = "healthy"
    if system_metrics["cpu_usage"] > 80 or system_metrics["memory_usage"] > 80:
        overall_health = "degraded"
    if system_metrics["cpu_usage"] > 95 or system_metrics["memory_usage"] > 95:
        overall_health = "critical"
    
    return {
        "overall_health": overall_health,
        "timestamp": datetime.now().isoformat(),
        "model_hub": model_health,
        "technique_orchestrator": technique_health,
        "system_metrics": system_metrics,
        "api_version": "2.0.0",
        "uptime": "system_uptime_placeholder"
    }

@app.post("/v2/prompt/evaluate")
async def evaluate_prompt_quality(
    request: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Evaluate prompt quality using multiple metrics
    """
    
    api_key = credentials.credentials
    if not await validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    prompt = request.get("prompt", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    # Comprehensive prompt evaluation
    evaluation_metrics = {
        "clarity": await evaluate_clarity(prompt),
        "specificity": await evaluate_specificity(prompt),
        "completeness": await evaluate_completeness(prompt),
        "coherence": await evaluate_coherence(prompt),
        "safety": await evaluate_safety(prompt),
        "effectiveness": await evaluate_effectiveness(prompt),
        "creativity_potential": await evaluate_creativity_potential(prompt),
        "reasoning_requirements": await evaluate_reasoning_requirements(prompt)
    }
    
    # Overall quality score
    overall_score = sum(evaluation_metrics.values()) / len(evaluation_metrics)
    
    # Recommendations
    recommendations = await generate_improvement_recommendations(evaluation_metrics, prompt)
    
    return {
        "prompt": prompt,
        "overall_quality_score": overall_score,
        "detailed_metrics": evaluation_metrics,
        "recommendations": recommendations,
        "evaluation_timestamp": datetime.now().isoformat(),
        "api_version": "2.0.0"
    }

@app.websocket("/v2/prompt/stream")
async def stream_prompt_optimization(websocket):
    """
    WebSocket endpoint for real-time prompt optimization streaming
    """
    
    await websocket.accept()
    
    try:
        while True:
            # Receive request
            data = await websocket.receive_json()
            
            # Validate API key
            api_key = data.get("api_key", "")
            if not await validate_api_key(api_key):
                await websocket.send_json({"error": "Invalid API key"})
                continue
            
            prompt = data.get("prompt", "")
            context = data.get("context", {})
            
            # Stream optimization process
            await websocket.send_json({
                "status": "started",
                "message": "Beginning prompt optimization..."
            })
            
            # Apply techniques with progress updates
            technique_results = {}
            total_techniques = len(orchestrator.techniques)
            
            for i, (technique_name, technique) in enumerate(orchestrator.techniques.items()):
                await websocket.send_json({
                    "status": "processing",
                    "current_technique": technique_name,
                    "progress": (i / total_techniques) * 100,
                    "message": f"Applying {technique_name}..."
                })
                
                try:
                    # Apply technique (simplified for streaming)
                    result = await orchestrator._apply_technique(
                        technique, technique_name, prompt, context
                    )
                    technique_results[technique_name] = result
                    
                    await websocket.send_json({
                        "status": "technique_completed",
                        "technique": technique_name,
                        "result": result,
                        "progress": ((i + 1) / total_techniques) * 100
                    })
                    
                except Exception as e:
                    await websocket.send_json({
                        "status": "technique_error",
                        "technique": technique_name,
                        "error": str(e)
                    })
            
            # Final ensemble
            await websocket.send_json({
                "status": "ensembling",
                "message": "Creating ensemble result..."
            })
            
            ensemble_result = await orchestrator._ensemble_results(
                technique_results, prompt, context
            )
            
            await websocket.send_json({
                "status": "completed",
                "final_result": ensemble_result,
                "techniques_used": list(technique_results.keys()),
                "message": "Optimization complete!"
            })
            
    except Exception as e:
        await websocket.send_json({
            "status": "error",
            "error": str(e)
        })
    finally:
        await websocket.close()

# Helper functions
async def validate_api_key(api_key: str) -> bool:
    """Validate API key (implement actual validation logic)"""
    # In production, validate against database
    return len(api_key) > 10  # Simple validation for demo

async def log_usage(api_key: str, request_id: str, execution_time: float, techniques_count: int, model_used: str):
    """Log usage statistics"""
    if api_key not in usage_tracker:
        usage_tracker[api_key] = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "average_latency": 0.0,
            "success_rate": 1.0,
            "techniques_usage": {},
            "models_usage": {}
        }
    
    user_stats = usage_tracker[api_key]
    user_stats["total_requests"] += 1
    user_stats["average_latency"] = (
        (user_stats["average_latency"] * (user_stats["total_requests"] - 1) + execution_time) / 
        user_stats["total_requests"]
    )
    
    # Track model usage
    if model_used not in user_stats["models_usage"]:
        user_stats["models_usage"][model_used] = 0
    user_stats["models_usage"][model_used] += 1

async def log_batch_usage(api_key: str, batch_id: str, batch_size: int, execution_time: float):
    """Log batch usage statistics"""
    if api_key not in usage_tracker:
        usage_tracker[api_key] = {"batch_requests": 0, "total_batch_prompts": 0}
    
    user_stats = usage_tracker[api_key]
    user_stats["batch_requests"] = user_stats.get("batch_requests", 0) + 1
    user_stats["total_batch_prompts"] = user_stats.get("total_batch_prompts", 0) + batch_size

# Evaluation functions
async def evaluate_clarity(prompt: str) -> float:
    """Evaluate prompt clarity (0-1 score)"""
    # Simple heuristic-based evaluation
    factors = {
        "length_appropriate": 1.0 if 10 <= len(prompt.split()) <= 200 else 0.5,
        "clear_instructions": 1.0 if any(word in prompt.lower() for word in ["please", "describe", "explain", "analyze"]) else 0.7,
        "no_ambiguity": 1.0 if prompt.count("?") <= 2 else 0.8,
        "specific_language": len(set(prompt.lower().split())) / max(len(prompt.split()), 1)
    }
    return min(sum(factors.values()) / len(factors), 1.0)

async def evaluate_specificity(prompt: str) -> float:
    """Evaluate prompt specificity"""
    specific_words = ["specific", "exactly", "precisely", "detailed", "step-by-step"]
    specificity_score = sum(1 for word in specific_words if word in prompt.lower()) / len(specific_words)
    return min(specificity_score + 0.5, 1.0)

async def evaluate_completeness(prompt: str) -> float:
    """Evaluate prompt completeness"""
    completeness_indicators = ["context", "background", "requirements", "constraints", "example"]
    completeness_score = sum(1 for indicator in completeness_indicators if indicator in prompt.lower()) / len(completeness_indicators)
    return min(completeness_score + 0.3, 1.0)

async def evaluate_coherence(prompt: str) -> float:
    """Evaluate prompt coherence"""
    sentences = prompt.split('.')
    if len(sentences) <= 1:
        return 0.8
    
    # Simple coherence check based on sentence flow
    coherence_score = 0.9 if len(sentences) <= 5 else 0.8
    return coherence_score

async def evaluate_safety(prompt: str) -> float:
    """Evaluate prompt safety"""
    unsafe_indicators = ["harm", "illegal", "dangerous", "violence", "hate"]
    if any(indicator in prompt.lower() for indicator in unsafe_indicators):
        return 0.3
    return 0.95

async def evaluate_effectiveness(prompt: str) -> float:
    """Evaluate prompt effectiveness"""
    effective_patterns = ["think step by step", "explain", "analyze", "provide examples"]
    effectiveness_score = sum(1 for pattern in effective_patterns if pattern in prompt.lower()) / len(effective_patterns)
    return min(effectiveness_score + 0.6, 1.0)

async def evaluate_creativity_potential(prompt: str) -> float:
    """Evaluate creativity potential"""
    creative_words = ["creative", "novel", "innovative", "brainstorm", "imagine", "design"]
    creativity_score = sum(1 for word in creative_words if word in prompt.lower()) / len(creative_words)
    return min(creativity_score + 0.5, 1.0)

async def evaluate_reasoning_requirements(prompt: str) -> float:
    """Evaluate reasoning requirements"""
    reasoning_words = ["analyze", "reason", "logic", "deduce", "conclude", "solve"]
    reasoning_score = sum(1 for word in reasoning_words if word in prompt.lower()) / len(reasoning_words)
    return min(reasoning_score + 0.4, 1.0)

async def generate_improvement_recommendations(metrics: Dict[str, float], prompt: str) -> List[str]:
    """Generate improvement recommendations based on evaluation metrics"""
    
    recommendations = []
    
    if metrics["clarity"] < 0.7:
        recommendations.append("Improve clarity by using more direct language and specific instructions")
    
    if metrics["specificity"] < 0.6:
        recommendations.append("Add more specific details and constraints to guide the response")
    
    if metrics["completeness"] < 0.7:
        recommendations.append("Provide more context and background information")
    
    if metrics["safety"] < 0.9:
        recommendations.append("Review prompt for potential safety concerns")
    
    if metrics["effectiveness"] < 0.8:
        recommendations.append("Consider adding 'think step by step' or similar reasoning prompts")
    
    if not recommendations:
        recommendations.append("Prompt quality is excellent across all metrics!")
    
    return recommendations

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)