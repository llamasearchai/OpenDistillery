"""
OpenDistillery Metrics Collection
Prometheus-based metrics collection and monitoring.
"""

import time
from typing import Dict, Any, Optional, List
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST, Summary
import psutil
import logging
import threading

logger = logging.getLogger(__name__)

# Singleton for metrics collector
_metrics_collector = None
_metrics_lock = threading.Lock()

# HTTP request metrics
http_requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status_code'])
http_request_duration_seconds = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])

# AI processing metrics
ai_processing_duration = Histogram('ai_processing_duration_seconds', 'AI processing duration', ['model', 'task_type'])
model_usage_count = Counter('model_usage_total', 'Model usage count', ['model', 'task_type'])
tasks_processed = Counter('tasks_processed_total', 'Total tasks processed', ['system_id', 'task_type', 'status'])

# System health metrics
active_systems = Gauge('active_systems', 'Number of active AI systems')
system_health_status = Gauge('system_health_status', 'System health status (1=healthy, 0=degraded)', ['component'])

# API key metrics
api_key_usage = Counter('api_key_usage_total', 'API key usage', ['key_name'])
api_key_errors = Counter('api_key_errors_total', 'API key errors', ['error_type'])

class MetricsCollector:
    """Collects and manages application metrics"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry
        self._metrics: Dict[str, Any] = {}
        self._initialize_default_metrics()
        self._active_requests = Gauge('active_requests', 'Number of active requests')
        system_health_status.labels(component='api').set(1)
        system_health_status.labels(component='database').set(1)
        system_health_status.labels(component='cache').set(1)
        system_health_status.labels(component='ai_system').set(1)
    
    def _initialize_default_metrics(self):
        """Initialize default application metrics"""
        # Request metrics
        self._metrics['http_requests_total'] = http_requests_total
        
        self._metrics['http_request_duration'] = http_request_duration_seconds
        
        # AI/ML metrics
        self._metrics['ai_processing_duration'] = ai_processing_duration
        
        self._metrics['active_ai_systems'] = active_systems
        
        self._metrics['tasks_processed_total'] = tasks_processed
        
        # System metrics
        self._metrics['system_cpu_usage'] = Gauge(
            'opendistillery_system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self._metrics['system_memory_usage'] = Gauge(
            'opendistillery_system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )
        
        self._metrics['database_connections'] = Gauge(
            'opendistillery_database_connections',
            'Database connection pool size',
            ['pool_name'],
            registry=self.registry
        )
        
        # Application info
        self._metrics['app_info'] = Info(
            'opendistillery_app_info',
            'Application information',
            registry=self.registry
        )
        
        # Set application info
        self._metrics['app_info'].info({
            'version': '1.0.0',
            'environment': 'production'
        })
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_ai_processing(self, model: str, task_type: str, duration: float):
        """Record AI processing metrics"""
        ai_processing_duration.labels(model=model, task_type=task_type).observe(duration)
        model_usage_count.labels(model=model, task_type=task_type).inc()
    
    def record_task_processed(self, system_id: str, task_type: str, status: str):
        """Record task processing metrics"""
        tasks_processed.labels(system_id=system_id, task_type=task_type, status=status).inc()
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self._metrics['system_cpu_usage'].set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self._metrics['system_memory_usage'].set(memory.used)
            
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def set_active_systems(self, count: int):
        """Set the number of active AI systems"""
        active_systems.set(count)
    
    def set_database_connections(self, pool_name: str, count: int):
        """Set database connection count"""
        self._metrics['database_connections'].labels(pool_name=pool_name).set(count)
    
    def set_system_health(self, component: str, healthy: bool):
        system_health_status.labels(component=component).set(1 if healthy else 0)
    
    def record_api_key_usage(self, key_name: str):
        api_key_usage.labels(key_name=key_name).inc()
    
    def record_api_key_error(self, error_type: str):
        api_key_errors.labels(error_type=error_type).inc()
    
    def increment_active_requests(self):
        self._active_requests.inc()
    
    def decrement_active_requests(self):
        self._active_requests.dec()
    
    def get_metric(self, name: str):
        """Get a specific metric"""
        return self._metrics.get(name)

class PrometheusExporter:
    """Exports metrics in Prometheus format"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
    
    def export_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        # Update system metrics before export
        self.collector.update_system_metrics()
        
        # Generate Prometheus format using default registry if none specified
        if self.collector.registry is None:
            return generate_latest()
        else:
            return generate_latest(self.collector.registry)
    
    def get_content_type(self) -> str:
        """Get the content type for Prometheus metrics"""
        return CONTENT_TYPE_LATEST

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    global _metrics_collector
    with _metrics_lock:
        if _metrics_collector is None:
            _metrics_collector = MetricsCollector()
        return _metrics_collector

def get_prometheus_exporter() -> PrometheusExporter:
    """Get Prometheus exporter instance"""
    collector = get_metrics_collector()
    return PrometheusExporter(collector) 