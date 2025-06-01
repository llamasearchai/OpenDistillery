"""
OpenDistillery Health Check System
Comprehensive health monitoring for all system components.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict, field
import psutil
import logging
import asyncpg
import redis.asyncio as redis
import threading

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ComponentHealth:
    """Health information for a system component"""
    name: str
    status: HealthStatus
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    last_check: Optional[float] = None
    metadata: Dict[str, Any] = None
    details: Dict[str, Any] = field(default_factory=dict)
    last_checked: float = field(default_factory=lambda: 0.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['status'] = self.status.value
        return result

@dataclass
class SystemHealth:
    """Overall system health information"""
    status: HealthStatus
    components: List[ComponentHealth]
    uptime_seconds: float
    version: str
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'status': self.status.value,
            'components': {comp.name: comp.to_dict() for comp in self.components},
            'uptime_seconds': self.uptime_seconds,
            'version': self.version,
            'timestamp': self.timestamp
        }

class HealthChecker:
    """Performs health checks on system components"""
    
    def __init__(self, db_config: Optional[Dict[str, Any]] = None, redis_config: Optional[Dict[str, Any]] = None):
        self.db_config = db_config or {}
        self.redis_config = redis_config or {}
        self.components: Dict[str, ComponentHealth] = {
            'api': ComponentHealth(name='api', status=HealthStatus.HEALTHY),
            'database': ComponentHealth(name='database', status=HealthStatus.HEALTHY),
            'cache': ComponentHealth(name='cache', status=HealthStatus.HEALTHY),
            'ai_system': ComponentHealth(name='ai_system', status=HealthStatus.HEALTHY)
        }
        self.check_interval = 30.0  # seconds
        self.last_full_check = 0.0
        self._health_checker = None
    
    async def check_all(self) -> SystemHealth:
        """Check health of all system components"""
        tasks = []
        for component_name in self.components:
            tasks.append(self._check_component(component_name))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        components = []
        overall_status = HealthStatus.HEALTHY
        for component_name, result in zip(self.components.keys(), results):
            if isinstance(result, ComponentHealth):
                self.components[component_name] = result
                components.append(result)
                if result.status != HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
            else:
                logger.error(f"Health check failed for {component_name}: {str(result)}")
                self.components[component_name].status = HealthStatus.UNHEALTHY
                components.append(self.components[component_name])
                overall_status = HealthStatus.DEGRADED
        
        self.last_full_check = asyncio.get_event_loop().time()
        return SystemHealth(
            status=overall_status,
            components=components,
            uptime_seconds=time.time() - self.start_time,
            version="1.0.0",
            timestamp=self.last_full_check
        )
    
    async def _check_component(self, component_name: str) -> ComponentHealth:
        """Check health of a specific component"""
        component = self.components[component_name]
        try:
            if component_name == 'api':
                return await self._check_api()
            elif component_name == 'database':
                return await self._check_database()
            elif component_name == 'cache':
                return await self._check_cache()
            elif component_name == 'ai_system':
                return await self._check_ai_system()
            else:
                return ComponentHealth(name=component_name, status=HealthStatus.UNHEALTHY, details={'error': 'Unknown component'})
        except Exception as e:
            logger.error(f"Health check error for {component_name}: {str(e)}")
            return ComponentHealth(name=component_name, status=HealthStatus.UNHEALTHY, details={'error': str(e)})
    
    async def _check_api(self) -> ComponentHealth:
        """Check API health"""
        # Simple check - API is running if we can process this
        return ComponentHealth(name='api', status=HealthStatus.HEALTHY, details={'message': 'API responsive'})
    
    async def _check_database(self) -> ComponentHealth:
        """Check database health"""
        if not self.db_config:
            return ComponentHealth(name='database', status=HealthStatus.UNHEALTHY, details={'error': 'No database configuration'})
        
        try:
            conn = await asyncpg.connect(
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 5432),
                database=self.db_config.get('name', 'opendistillery'),
                user=self.db_config.get('user', 'opendistillery'),
                password=self.db_config.get('password', ''),
                timeout=5
            )
            result = await conn.fetchval('SELECT 1')
            await conn.close()
            return ComponentHealth(name='database', status=HealthStatus.HEALTHY, details={'message': 'Database connection successful', 'test_query_result': result})
        except Exception as e:
            return ComponentHealth(name='database', status=HealthStatus.UNHEALTHY, details={'error': str(e)})
    
    async def _check_cache(self) -> ComponentHealth:
        """Check cache (Redis) health"""
        if not self.redis_config:
            return ComponentHealth(name='cache', status=HealthStatus.UNHEALTHY, details={'error': 'No cache configuration'})
        
        try:
            r = redis.Redis(
                host=self.redis_config.get('host', 'localhost'),
                port=self.redis_config.get('port', 6379),
                password=self.redis_config.get('password'),
                decode_responses=True,
                socket_connect_timeout=5
            )
            pong = await r.ping()
            await r.close()
            return ComponentHealth(name='cache', status=HealthStatus.HEALTHY if pong else HealthStatus.UNHEALTHY, details={'message': 'Cache ping result', 'pong': pong})
        except Exception as e:
            return ComponentHealth(name='cache', status=HealthStatus.UNHEALTHY, details={'error': str(e)})
    
    async def _check_ai_system(self) -> ComponentHealth:
        """Check AI system health"""
        # This would check if AI systems are responsive
        # For now, return healthy as placeholder
        return ComponentHealth(name='ai_system', status=HealthStatus.HEALTHY, details={'message': 'AI system check not implemented'})
    
    def get_component_health(self, component_name: str) -> Optional[ComponentHealth]:
        """Get health status of a specific component"""
        return self.components.get(component_name)

# Global health checker instance
_health_checker = None
_health_lock = threading.Lock()

def get_health_checker(db_config: Optional[Dict[str, Any]] = None, redis_config: Optional[Dict[str, Any]] = None) -> HealthChecker:
    """Get the global health checker instance"""
    global _health_checker
    with _health_lock:
        if _health_checker is None:
            _health_checker = HealthChecker(db_config, redis_config)
        return _health_checker 