"""
OpenDistillery Advanced Logging System
Enterprise-grade structured logging with correlation tracking and security features.
"""

import logging
import json
import time
import uuid
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import structlog
from pythonjsonlogger import jsonlogger
import contextvars
import sys
import os

# Context variables for correlation tracking
correlation_id_var = contextvars.ContextVar('correlation_id', default=None)
user_id_var = contextvars.ContextVar('user_id', default=None)
session_id_var = contextvars.ContextVar('session_id', default=None)

class CorrelationFilter(logging.Filter):
    """Add correlation ID and context to log records"""
    
    def filter(self, record):
        record.correlation_id = correlation_id_var.get()
        record.user_id = user_id_var.get()
        record.session_id = session_id_var.get()
        record.timestamp = datetime.utcnow().isoformat()
        return True

class SecurityFilter(logging.Filter):
    """Filter sensitive information from logs"""
    
    SENSITIVE_FIELDS = {
        'password', 'token', 'key', 'secret', 'api_key', 
        'authorization', 'credential', 'private_key'
    }
    
    def filter(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, dict):
            record.msg = self._sanitize_dict(record.msg)
        elif hasattr(record, 'args') and record.args:
            record.args = tuple(self._sanitize_value(arg) for arg in record.args)
        return True
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize dictionary by masking sensitive fields"""
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_value(item) for item in value]
            else:
                sanitized[key] = value
        return sanitized
    
    def _sanitize_value(self, value: Any) -> Any:
        """Sanitize individual values"""
        if isinstance(value, dict):
            return self._sanitize_dict(value)
        elif isinstance(value, str) and len(value) > 20:
            # Potentially sensitive long strings
            return value[:10] + "***" + value[-5:]
        return value

class OpenDistilleryLogger:
    """Advanced logger for OpenDistillery with enterprise features"""
    
    def __init__(self, 
                 name: str,
                 log_level: str = "INFO",
                 log_dir: Optional[Path] = None,
                 enable_json: bool = True,
                 enable_correlation: bool = True,
                 enable_security_filter: bool = True):
        
        self.name = name
        self.log_level = getattr(logging, log_level.upper())
        self.log_dir = log_dir or Path("logs")
        self.enable_json = enable_json
        self.enable_correlation = enable_correlation
        self.enable_security_filter = enable_security_filter
        
        # Ensure log directory exists
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.log_level)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
        
        # Setup structured logging
        if enable_json:
            self._setup_structlog()
    
    def _setup_handlers(self):
        """Setup log handlers"""
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        
        # File handler for general logs
        file_handler = logging.FileHandler(
            self.log_dir / f"{self.name}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        
        # Error file handler
        error_handler = logging.FileHandler(
            self.log_dir / f"{self.name}_errors.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # JSON formatter for structured logging
        if self.enable_json:
            json_formatter = jsonlogger.JsonFormatter(
                '%(timestamp)s %(name)s %(levelname)s %(correlation_id)s %(user_id)s %(message)s'
            )
            file_handler.setFormatter(json_formatter)
            error_handler.setFormatter(json_formatter)
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
            )
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
            error_handler.setFormatter(formatter)
        
        # Add filters
        if self.enable_correlation:
            correlation_filter = CorrelationFilter()
            console_handler.addFilter(correlation_filter)
            file_handler.addFilter(correlation_filter)
            error_handler.addFilter(correlation_filter)
        
        if self.enable_security_filter:
            security_filter = SecurityFilter()
            console_handler.addFilter(security_filter)
            file_handler.addFilter(security_filter)
            error_handler.addFilter(security_filter)
        
        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
    
    def _setup_structlog(self):
        """Setup structured logging with structlog"""
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    def set_correlation_id(self, correlation_id: str = None) -> str:
        """Set correlation ID for request tracking"""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        correlation_id_var.set(correlation_id)
        return correlation_id
    
    def set_user_context(self, user_id: str, session_id: str = None):
        """Set user context for audit logging"""
        user_id_var.set(user_id)
        if session_id:
            session_id_var.set(session_id)
    
    def clear_context(self):
        """Clear all context variables"""
        correlation_id_var.set(None)
        user_id_var.set(None)
        session_id_var.set(None)
    
    def log_request(self, method: str, path: str, status_code: int, 
                   duration_ms: float, user_id: str = None):
        """Log HTTP request with standard format"""
        self.logger.info(
            "HTTP Request",
            extra={
                "event_type": "http_request",
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "user_id": user_id or user_id_var.get()
            }
        )
    
    def log_task_execution(self, task_id: str, task_type: str, 
                          agent_id: str, duration_ms: float, 
                          success: bool, error: str = None):
        """Log task execution with standard format"""
        log_data = {
            "event_type": "task_execution",
            "task_id": task_id,
            "task_type": task_type,
            "agent_id": agent_id,
            "duration_ms": duration_ms,
            "success": success
        }
        
        if error:
            log_data["error"] = error
        
        if success:
            self.logger.info("Task Completed", extra=log_data)
        else:
            self.logger.error("Task Failed", extra=log_data)
    
    def log_model_call(self, model_name: str, provider: str, 
                      tokens_used: int, cost: float, duration_ms: float):
        """Log model API call with cost tracking"""
        self.logger.info(
            "Model API Call",
            extra={
                "event_type": "model_call",
                "model_name": model_name,
                "provider": provider,
                "tokens_used": tokens_used,
                "cost": cost,
                "duration_ms": duration_ms
            }
        )
    
    def log_security_event(self, event_type: str, user_id: str, 
                          details: Dict[str, Any], severity: str = "INFO"):
        """Log security events for audit trail"""
        log_level = getattr(logging, severity.upper())
        self.logger.log(
            log_level,
            f"Security Event: {event_type}",
            extra={
                "event_type": "security",
                "security_event_type": event_type,
                "user_id": user_id,
                "details": details,
                "severity": severity
            }
        )
    
    def log_performance_metric(self, metric_name: str, value: float, 
                             unit: str, tags: Dict[str, str] = None):
        """Log performance metrics"""
        log_data = {
            "event_type": "performance_metric",
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "timestamp": time.time()
        }
        
        if tags:
            log_data["tags"] = tags
        
        self.logger.info("Performance Metric", extra=log_data)
    
    def debug(self, message: str, **kwargs):
        """Debug level logging"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Info level logging"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Warning level logging"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, error: Exception = None, **kwargs):
        """Error level logging"""
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)
        self.logger.error(message, extra=kwargs, exc_info=error is not None)
    
    def critical(self, message: str, **kwargs):
        """Critical level logging"""
        self.logger.critical(message, extra=kwargs)

# Global logger instances
_loggers: Dict[str, OpenDistilleryLogger] = {}
_logger_lock = threading.Lock()

def get_logger(name: str, **kwargs) -> OpenDistilleryLogger:
    """Get or create a logger instance"""
    with _logger_lock:
        if name not in _loggers:
            _loggers[name] = OpenDistilleryLogger(name, **kwargs)
        return _loggers[name]

def configure_logging(log_level: str = "INFO", 
                     log_dir: str = "logs",
                     enable_json: bool = True):
    """Configure global logging settings"""
    global _default_config
    _default_config = {
        "log_level": log_level,
        "log_dir": Path(log_dir),
        "enable_json": enable_json
    }

# Default configuration
_default_config = {
    "log_level": "INFO",
    "log_dir": Path("logs"),
    "enable_json": True
}

# Configure standard logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.render_to_log_kwargs,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Add JSON renderer for production
if os.getenv("ENVIRONMENT") == "production":
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ]
    )

class LoggerManager:
    def __init__(self, app_name: str = "opendistillery"):
        self.app_name = app_name
        self.loggers: Dict[str, structlog.BoundLogger] = {}

    def get_logger(self, module_name: str) -> structlog.BoundLogger:
        """Get a logger for a specific module"""
        if module_name not in self.loggers:
            logger = structlog.get_logger(module_name)
            self.loggers[module_name] = logger.bind(app=self.app_name)
        return self.loggers[module_name]

    def set_log_level(self, level: str):
        """Set log level for all loggers"""
        level_value = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger().setLevel(level_value)
        for logger in self.loggers.values():
            logger._logger.setLevel(level_value)

_logger_manager = None

def get_logger(module_name: str) -> structlog.BoundLogger:
    """Get a structured logger for the specified module"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    return _logger_manager.get_logger(module_name)

def configure_logging(level: str = "INFO", environment: str = "development"):
    """Configure logging for the application"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    _logger_manager.set_log_level(level)
    
    # Reconfigure for JSON output in production
    if environment == "production":
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ]
        )
    return _logger_manager 