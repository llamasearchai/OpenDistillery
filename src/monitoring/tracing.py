"""
OpenDistillery Distributed Tracing
Provides distributed tracing capabilities for request tracking and performance monitoring.
"""

import uuid
import time
import contextvars
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import opentelemetry

try:
    from opentelemetry import trace
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    trace = None
    JaegerExporter = None
    Resource = None
    SERVICE_NAME = None
    TracerProvider = None
    BatchSpanProcessor = None
    FastAPIInstrumentor = None

logger = logging.getLogger(__name__)

# Context variable for current trace context
_trace_context: contextvars.ContextVar[Optional['TraceContext']] = contextvars.ContextVar('trace_context', default=None)

class SpanKind(Enum):
    """Span kind enumeration"""
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"
    INTERNAL = "internal"

@dataclass
class TraceContext:
    """Trace context for correlation across services"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def new_trace(cls) -> 'TraceContext':
        """Create a new trace context"""
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        return cls(trace_id=trace_id, span_id=span_id)
    
    def child_span(self) -> 'TraceContext':
        """Create a child span context"""
        new_span_id = str(uuid.uuid4())
        return TraceContext(
            trace_id=self.trace_id,
            span_id=new_span_id,
            parent_span_id=self.span_id,
            baggage=self.baggage.copy()
        )

@dataclass
class Span:
    """Span for tracking operations"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    kind: SpanKind
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "ok"
    error: bool = False
    
    def add_tag(self, key: str, value: Any):
        """Add a tag to the span"""
        self.tags[key] = value
    
    def add_log(self, message: str, **kwargs):
        """Add a log entry to the span"""
        log_entry = {
            'timestamp': time.time(),
            'message': message,
            **kwargs
        }
        self.logs.append(log_entry)
    
    def set_error(self, error: Exception):
        """Mark span as having an error"""
        self.error = True
        self.status = "error"
        self.add_tag("error", True)
        self.add_tag("error.type", type(error).__name__)
        self.add_tag("error.message", str(error))
        self.add_log(f"Error: {error}")
    
    def finish(self):
        """Finish the span"""
        if self.end_time is None:
            self.end_time = time.time()
            self.duration_ms = (self.end_time - self.start_time) * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary"""
        return {
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_span_id': self.parent_span_id,
            'operation_name': self.operation_name,
            'kind': self.kind.value,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_ms': self.duration_ms,
            'tags': self.tags,
            'logs': self.logs,
            'status': self.status,
            'error': self.error
        }

class DistributedTracer:
    """Distributed tracer for managing spans and traces"""
    
    def __init__(self, service_name: str = "opendistillery"):
        self.service_name = service_name
        self.active_spans: Dict[str, Span] = {}
        self.finished_spans: List[Span] = []
    
    def start_span(self, 
                   operation_name: str,
                   kind: SpanKind = SpanKind.INTERNAL,
                   parent_context: Optional[TraceContext] = None,
                   tags: Optional[Dict[str, Any]] = None) -> Span:
        """Start a new span"""
        
        # Get or create trace context
        if parent_context is None:
            parent_context = get_current_trace_context()
        
        if parent_context is None:
            # Create new trace
            context = TraceContext.new_trace()
            parent_span_id = None
        else:
            # Create child span
            context = parent_context.child_span()
            parent_span_id = parent_context.span_id
        
        # Create span
        span = Span(
            trace_id=context.trace_id,
            span_id=context.span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            kind=kind,
            start_time=time.time()
        )
        
        # Add default tags
        span.add_tag("service.name", self.service_name)
        span.add_tag("span.kind", kind.value)
        
        # Add custom tags
        if tags:
            for key, value in tags.items():
                span.add_tag(key, value)
        
        # Store active span
        self.active_spans[span.span_id] = span
        
        # Set trace context
        set_trace_context(context)
        
        logger.debug(f"Started span: {operation_name} (trace_id={context.trace_id}, span_id={context.span_id})")
        
        return span
    
    def finish_span(self, span: Span):
        """Finish a span"""
        span.finish()
        
        # Move from active to finished
        if span.span_id in self.active_spans:
            del self.active_spans[span.span_id]
        
        self.finished_spans.append(span)
        
        logger.debug(f"Finished span: {span.operation_name} (duration={span.duration_ms:.2f}ms)")
        
        # Send to tracing backend (in real implementation)
        self._export_span(span)
    
    def _export_span(self, span: Span):
        """Export span to tracing backend"""
        # In a real implementation, this would send to Jaeger, Zipkin, etc.
        logger.debug(f"Exported span: {span.operation_name}")
    
    def get_active_spans(self) -> List[Span]:
        """Get all active spans"""
        return list(self.active_spans.values())
    
    def get_finished_spans(self, limit: int = 100) -> List[Span]:
        """Get finished spans"""
        return self.finished_spans[-limit:]
    
    def flush(self):
        """Flush all pending spans"""
        for span in list(self.active_spans.values()):
            self.finish_span(span)

class SpanContext:
    """Context manager for spans"""
    
    def __init__(self, tracer: DistributedTracer, operation_name: str, **kwargs):
        self.tracer = tracer
        self.operation_name = operation_name
        self.kwargs = kwargs
        self.span: Optional[Span] = None
    
    def __enter__(self) -> Span:
        self.span = self.tracer.start_span(self.operation_name, **self.kwargs)
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type:
                self.span.set_error(exc_val)
            self.tracer.finish_span(self.span)

# Global tracer instance
_tracer: Optional[DistributedTracer] = None

def get_tracer() -> DistributedTracer:
    """Get the global tracer instance"""
    global _tracer
    if _tracer is None:
        _tracer = DistributedTracer()
    return _tracer

def set_tracer(tracer: DistributedTracer):
    """Set the global tracer instance"""
    global _tracer
    _tracer = tracer

def get_current_trace_context() -> Optional[TraceContext]:
    """Get the current trace context"""
    return _trace_context.get()

def set_trace_context(context: TraceContext):
    """Set the current trace context"""
    _trace_context.set(context)

def trace_operation(operation_name: str, **kwargs):
    """Decorator for tracing operations"""
    def decorator(func):
        def wrapper(*args, **func_kwargs):
            tracer = get_tracer()
            with SpanContext(tracer, operation_name, **kwargs) as span:
                try:
                    result = func(*args, **func_kwargs)
                    span.add_tag("success", True)
                    return result
                except Exception as e:
                    span.set_error(e)
                    raise
        return wrapper
    return decorator

async def trace_async_operation(operation_name: str, **kwargs):
    """Async context manager for tracing operations"""
    tracer = get_tracer()
    return SpanContext(tracer, operation_name, **kwargs)

class TracingManager:
    def __init__(self, service_name: str = "opendistillery", jaeger_host: str = "localhost", jaeger_port: int = 6831):
        self.service_name = service_name
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self.tracer_provider = None
        self.initialized = False
        
        if OPENTELEMETRY_AVAILABLE:
            self._initialize_tracing()
        else:
            logger.warning("OpenTelemetry not available, tracing disabled")

    def _initialize_tracing(self):
        """Initialize distributed tracing"""
        try:
            # Create resource with service name
            resource = Resource(attributes={SERVICE_NAME: self.service_name})
            
            # Create tracer provider
            self.tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(self.tracer_provider)
            
            # Configure Jaeger exporter
            jaeger_exporter = JaegerExporter(
                agent_host_name=self.jaeger_host,
                agent_port=self.jaeger_port,
            )
            
            # Add span processor
            span_processor = BatchSpanProcessor(jaeger_exporter)
            self.tracer_provider.add_span_processor(span_processor)
            
            self.initialized = True
            logger.info(f"Tracing initialized for {self.service_name} with Jaeger at {self.jaeger_host}:{self.jaeger_port}")
        except Exception as e:
            logger.error(f"Failed to initialize tracing: {str(e)}")
            self.initialized = False

    def instrument_fastapi(self, app):
        """Instrument FastAPI application for tracing"""
        if self.initialized and FastAPIInstrumentor:
            try:
                FastAPIInstrumentor.instrument_app(app)
                logger.info("FastAPI application instrumented for tracing")
            except Exception as e:
                logger.error(f"Failed to instrument FastAPI app: {str(e)}")

    def get_tracer(self):
        """Get tracer for creating spans"""
        if self.initialized:
            return trace.get_tracer(self.service_name)
        return None

    def start_span(self, name: str, context: Optional[Dict[str, Any]] = None):
        """Start a new span"""
        if self.initialized:
            tracer = self.get_tracer()
            if tracer:
                return tracer.start_span(name, context=context)
        return None

    def shutdown(self):
        """Shutdown tracing system"""
        if self.initialized and self.tracer_provider:
            try:
                self.tracer_provider.shutdown()
                logger.info("Tracing system shutdown")
            except Exception as e:
                logger.error(f"Error shutting down tracing: {str(e)}")

_tracing_manager = None

def configure_tracing(service_name: str = "opendistillery", jaeger_host: str = "localhost", jaeger_port: int = 6831) -> TracingManager:
    """Configure and get the global tracing manager"""
    global _tracing_manager
    if _tracing_manager is None:
        _tracing_manager = TracingManager(service_name, jaeger_host, jaeger_port)
    return _tracing_manager

def get_tracing_manager() -> Optional[TracingManager]:
    """Get the global tracing manager"""
    return _tracing_manager 