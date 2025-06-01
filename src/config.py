"""
OpenDistillery Configuration Management
Comprehensive configuration system with environment-based settings, security, and validation.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import logging
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "opendistillery"
    username: str = "opendistillery"
    password: str = ""
    ssl_mode: str = "prefer"
    pool_size: int = 10
    max_overflow: int = 20

@dataclass
class RedisConfig:
    """Redis configuration"""
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    password: Optional[str] = None
    ssl: bool = False
    max_connections: int = 10

@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = field(default_factory=lambda: os.getenv("OPENDISTILLERY_SECRET_KEY", "dev-secret-key-change-in-production"))
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    jwt_refresh_expiry_days: int = 30
    max_failed_login_attempts: int = 5
    account_lockout_duration_hours: int = 1
    password_min_length: int = 8
    require_mfa: bool = field(default_factory=lambda: os.getenv("OPENDISTILLERY_REQUIRE_MFA", "false").lower() == "true")
    api_key_expiry_days: int = 90
    session_timeout_minutes: int = 60
    enable_rate_limiting: bool = True
    rate_limit_requests_per_minute: int = 100

@dataclass
class ModelConfig:
    """Model provider configuration"""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    default_model: str = "gpt-4"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout_seconds: int = 30
    retry_attempts: int = 3

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    log_level: str = "INFO"
    structured_logging: bool = True
    metrics_retention_days: int = 30
    alert_webhook_url: str = ""

@dataclass
class IntegrationConfig:
    """Enterprise integration configuration"""
    salesforce_enabled: bool = False
    salesforce_username: str = ""
    salesforce_password: str = ""
    salesforce_security_token: str = ""
    salesforce_domain: str = "login"
    
    microsoft365_enabled: bool = False
    microsoft365_tenant_id: str = ""
    microsoft365_client_id: str = ""
    microsoft365_client_secret: str = ""

@dataclass
class OpenDistilleryConfig:
    """Main OpenDistillery configuration"""
    environment: str = field(default_factory=lambda: os.getenv("OPENDISTILLERY_ENV", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("OPENDISTILLERY_DEBUG", "false").lower() == "true")
    
    # Core settings
    api_host: str = field(default_factory=lambda: os.getenv("OPENDISTILLERY_API_HOST", "0.0.0.0"))
    api_port: int = field(default_factory=lambda: int(os.getenv("OPENDISTILLERY_API_PORT", "8000")))
    worker_processes: int = field(default_factory=lambda: int(os.getenv("OPENDISTILLERY_WORKER_PROCESSES", "4")))
    
    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    models: ModelConfig = field(default_factory=ModelConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    integrations: IntegrationConfig = field(default_factory=IntegrationConfig)
    
    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        "multi_agent_orchestration": True,
        "advanced_reasoning": True,
        "enterprise_integrations": True,
        "research_experiments": True,
        "mlx_acceleration": True,
        "real_time_monitoring": True
    })

class ConfigManager:
    """Configuration manager with environment-based loading and encryption"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.config: Optional[OpenDistilleryConfig] = None
        self.cipher_suite: Optional[Fernet] = None
        
        # Initialize encryption
        self._init_encryption()
    
    def _init_encryption(self):
        """Initialize encryption for sensitive configuration data"""
        key_file = self.config_dir / "encryption.key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Secure the key file
            os.chmod(key_file, 0o600)
        
        self.cipher_suite = Fernet(key)
    
    def load_config(self, environment: str = None) -> OpenDistilleryConfig:
        """Load configuration for specified environment"""
        if environment is None:
            environment = os.getenv("OPENDISTILLERY_ENV", "development")
        
        # Load base configuration
        config = self._load_base_config()
        
        # Load environment-specific overrides
        env_config = self._load_environment_config(environment)
        if env_config:
            config = self._merge_configs(config, env_config)
        
        # Load environment variables
        config = self._load_environment_variables(config)
        
        # Validate configuration
        self._validate_config(config)
        
        # Decrypt sensitive values
        config = self._decrypt_sensitive_values(config)
        
        self.config = config
        logger.info(f"Loaded configuration for environment: {environment}")
        
        return config
    
    def _load_base_config(self) -> Dict[str, Any]:
        """Load base configuration"""
        config_file = self.config_dir / "base.yaml"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        
        # Return default configuration
        return self._config_to_dict(OpenDistilleryConfig())
    
    def _load_environment_config(self, environment: str) -> Optional[Dict[str, Any]]:
        """Load environment-specific configuration"""
        config_file = self.config_dir / f"{environment}.yaml"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        
        return None
    
    def _load_environment_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        env_mappings = {
            "OPENDISTILLERY_DEBUG": ("debug", bool),
            "OPENDISTILLERY_API_HOST": ("api_host", str),
            "OPENDISTILLERY_API_PORT": ("api_port", int),
            "OPENDISTILLERY_WORKER_PROCESSES": ("worker_processes", int),
            
            # Database
            "DATABASE_HOST": ("database.host", str),
            "DATABASE_PORT": ("database.port", int),
            "DATABASE_NAME": ("database.database", str),
            "DATABASE_USER": ("database.username", str),
            "DATABASE_PASSWORD": ("database.password", str),
            
            # Redis
            "REDIS_HOST": ("redis.host", str),
            "REDIS_PORT": ("redis.port", int),
            "REDIS_PASSWORD": ("redis.password", str),
            
            # Security
            "SECRET_KEY": ("security.secret_key", str),
            "JWT_ALGORITHM": ("security.jwt_algorithm", str),
            "JWT_EXPIRATION_HOURS": ("security.jwt_expiration_hours", int),
            
            # Models
            "OPENAI_API_KEY": ("models.openai_api_key", str),
            "ANTHROPIC_API_KEY": ("models.anthropic_api_key", str),
            "GOOGLE_API_KEY": ("models.google_api_key", str),
            "DEFAULT_MODEL": ("models.default_model", str),
            
            # Integrations
            "SALESFORCE_USERNAME": ("integrations.salesforce_username", str),
            "SALESFORCE_PASSWORD": ("integrations.salesforce_password", str),
            "SALESFORCE_SECURITY_TOKEN": ("integrations.salesforce_security_token", str),
        }
        
        for env_var, (config_path, value_type) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert value to appropriate type
                if value_type == bool:
                    env_value = env_value.lower() in ('true', '1', 'yes', 'on')
                elif value_type == int:
                    env_value = int(env_value)
                
                # Set nested configuration value
                self._set_nested_value(config, config_path, env_value)
        
        return config
    
    def _set_nested_value(self, config: Dict[str, Any], path: str, value: Any):
        """Set a nested configuration value using dot notation"""
        keys = path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _validate_config(self, config: Dict[str, Any]):
        """Validate configuration"""
        required_fields = [
            "security.secret_key",
            "models.openai_api_key"
        ]
        
        for field in required_fields:
            if not self._get_nested_value(config, field):
                logger.warning(f"Required configuration field missing: {field}")
    
    def _get_nested_value(self, config: Dict[str, Any], path: str) -> Any:
        """Get a nested configuration value using dot notation"""
        keys = path.split('.')
        current = config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _decrypt_sensitive_values(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive configuration values"""
        sensitive_fields = [
            "database.password",
            "redis.password",
            "security.secret_key",
            "models.openai_api_key",
            "models.anthropic_api_key",
            "models.google_api_key",
            "integrations.salesforce_password",
            "integrations.salesforce_security_token"
        ]
        
        for field in sensitive_fields:
            value = self._get_nested_value(config, field)
            if value and isinstance(value, str) and value.startswith("encrypted:"):
                try:
                    encrypted_data = base64.b64decode(value[10:])
                    decrypted_value = self.cipher_suite.decrypt(encrypted_data).decode()
                    self._set_nested_value(config, field, decrypted_value)
                except Exception as e:
                    logger.error(f"Failed to decrypt {field}: {str(e)}")
        
        return config
    
    def _config_to_dict(self, config: OpenDistilleryConfig) -> Dict[str, Any]:
        """Convert configuration object to dictionary"""
        return {
            "environment": config.environment,
            "debug": config.debug,
            "api_host": config.api_host,
            "api_port": config.api_port,
            "worker_processes": config.worker_processes,
            "database": {
                "host": config.database.host,
                "port": config.database.port,
                "database": config.database.database,
                "username": config.database.username,
                "password": config.database.password,
                "ssl_mode": config.database.ssl_mode,
                "pool_size": config.database.pool_size,
                "max_overflow": config.database.max_overflow
            },
            "redis": {
                "host": config.redis.host,
                "port": config.redis.port,
                "database": config.redis.database,
                "password": config.redis.password,
                "ssl": config.redis.ssl,
                "max_connections": config.redis.max_connections
            },
            "security": {
                "secret_key": config.security.secret_key,
                "jwt_algorithm": config.security.jwt_algorithm,
                "jwt_expiry_hours": config.security.jwt_expiry_hours,
                "jwt_refresh_expiry_days": config.security.jwt_refresh_expiry_days,
                "max_failed_login_attempts": config.security.max_failed_login_attempts,
                "account_lockout_duration_hours": config.security.account_lockout_duration_hours,
                "password_min_length": config.security.password_min_length,
                "require_mfa": config.security.require_mfa,
                "api_key_expiry_days": config.security.api_key_expiry_days,
                "session_timeout_minutes": config.security.session_timeout_minutes,
                "enable_rate_limiting": config.security.enable_rate_limiting,
                "rate_limit_requests_per_minute": config.security.rate_limit_requests_per_minute
            },
            "models": {
                "openai_api_key": config.models.openai_api_key,
                "anthropic_api_key": config.models.anthropic_api_key,
                "google_api_key": config.models.google_api_key,
                "default_model": config.models.default_model,
                "max_tokens": config.models.max_tokens,
                "temperature": config.models.temperature,
                "timeout_seconds": config.models.timeout_seconds,
                "retry_attempts": config.models.retry_attempts
            },
            "monitoring": {
                "prometheus_enabled": config.monitoring.prometheus_enabled,
                "prometheus_port": config.monitoring.prometheus_port,
                "log_level": config.monitoring.log_level,
                "structured_logging": config.monitoring.structured_logging,
                "metrics_retention_days": config.monitoring.metrics_retention_days,
                "alert_webhook_url": config.monitoring.alert_webhook_url
            },
            "integrations": {
                "salesforce_enabled": config.integrations.salesforce_enabled,
                "salesforce_username": config.integrations.salesforce_username,
                "salesforce_password": config.integrations.salesforce_password,
                "salesforce_security_token": config.integrations.salesforce_security_token,
                "salesforce_domain": config.integrations.salesforce_domain,
                "microsoft365_enabled": config.integrations.microsoft365_enabled,
                "microsoft365_tenant_id": config.integrations.microsoft365_tenant_id,
                "microsoft365_client_id": config.integrations.microsoft365_client_id,
                "microsoft365_client_secret": config.integrations.microsoft365_client_secret
            },
            "features": config.features
        }
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> OpenDistilleryConfig:
        """Convert dictionary to configuration object"""
        config = OpenDistilleryConfig()
        
        # Basic settings
        config.environment = config_dict.get("environment", "development")
        config.debug = config_dict.get("debug", False)
        config.api_host = config_dict.get("api_host", "0.0.0.0")
        config.api_port = config_dict.get("api_port", 8000)
        config.worker_processes = config_dict.get("worker_processes", 1)
        
        # Database
        db_config = config_dict.get("database", {})
        config.database = DatabaseConfig(
            host=db_config.get("host", "localhost"),
            port=db_config.get("port", 5432),
            database=db_config.get("database", "opendistillery"),
            username=db_config.get("username", "opendistillery"),
            password=db_config.get("password", ""),
            ssl_mode=db_config.get("ssl_mode", "prefer"),
            pool_size=db_config.get("pool_size", 10),
            max_overflow=db_config.get("max_overflow", 20)
        )
        
        # Redis
        redis_config = config_dict.get("redis", {})
        config.redis = RedisConfig(
            host=redis_config.get("host", "localhost"),
            port=redis_config.get("port", 6379),
            database=redis_config.get("database", 0),
            password=redis_config.get("password"),
            ssl=redis_config.get("ssl", False),
            max_connections=redis_config.get("max_connections", 10)
        )
        
        # Security
        security_config = config_dict.get("security", {})
        config.security = SecurityConfig(
            secret_key=security_config.get("secret_key", ""),
            jwt_algorithm=security_config.get("jwt_algorithm", "HS256"),
            jwt_expiry_hours=security_config.get("jwt_expiry_hours", 24),
            jwt_refresh_expiry_days=security_config.get("jwt_refresh_expiry_days", 30),
            max_failed_login_attempts=security_config.get("max_failed_login_attempts", 5),
            account_lockout_duration_hours=security_config.get("account_lockout_duration_hours", 1),
            password_min_length=security_config.get("password_min_length", 8),
            require_mfa=security_config.get("require_mfa", False),
            api_key_expiry_days=security_config.get("api_key_expiry_days", 90),
            session_timeout_minutes=security_config.get("session_timeout_minutes", 60),
            enable_rate_limiting=security_config.get("enable_rate_limiting", True),
            rate_limit_requests_per_minute=security_config.get("rate_limit_requests_per_minute", 100)
        )
        
        # Models
        models_config = config_dict.get("models", {})
        config.models = ModelConfig(
            openai_api_key=models_config.get("openai_api_key", ""),
            anthropic_api_key=models_config.get("anthropic_api_key", ""),
            google_api_key=models_config.get("google_api_key", ""),
            default_model=models_config.get("default_model", "gpt-4"),
            max_tokens=models_config.get("max_tokens", 4096),
            temperature=models_config.get("temperature", 0.7),
            timeout_seconds=models_config.get("timeout_seconds", 30),
            retry_attempts=models_config.get("retry_attempts", 3)
        )
        
        # Monitoring
        monitoring_config = config_dict.get("monitoring", {})
        config.monitoring = MonitoringConfig(
            prometheus_enabled=monitoring_config.get("prometheus_enabled", True),
            prometheus_port=monitoring_config.get("prometheus_port", 9090),
            log_level=monitoring_config.get("log_level", "INFO"),
            structured_logging=monitoring_config.get("structured_logging", True),
            metrics_retention_days=monitoring_config.get("metrics_retention_days", 30),
            alert_webhook_url=monitoring_config.get("alert_webhook_url", "")
        )
        
        # Integrations
        integrations_config = config_dict.get("integrations", {})
        config.integrations = IntegrationConfig(
            salesforce_enabled=integrations_config.get("salesforce_enabled", False),
            salesforce_username=integrations_config.get("salesforce_username", ""),
            salesforce_password=integrations_config.get("salesforce_password", ""),
            salesforce_security_token=integrations_config.get("salesforce_security_token", ""),
            salesforce_domain=integrations_config.get("salesforce_domain", "login"),
            microsoft365_enabled=integrations_config.get("microsoft365_enabled", False),
            microsoft365_tenant_id=integrations_config.get("microsoft365_tenant_id", ""),
            microsoft365_client_id=integrations_config.get("microsoft365_client_id", ""),
            microsoft365_client_secret=integrations_config.get("microsoft365_client_secret", "")
        )
        
        # Features
        config.features = config_dict.get("features", {
            "multi_agent_orchestration": True,
            "advanced_reasoning": True,
            "enterprise_integrations": True,
            "research_experiments": True,
            "mlx_acceleration": True,
            "real_time_monitoring": True
        })
        
        return config
    
    def save_config(self, config: OpenDistilleryConfig, environment: str = None):
        """Save configuration to file"""
        if environment is None:
            environment = config.environment
        
        config_dict = self._config_to_dict(config)
        
        # Encrypt sensitive values before saving
        config_dict = self._encrypt_sensitive_values(config_dict)
        
        config_file = self.config_dir / f"{environment}.yaml"
        
        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        
        logger.info(f"Saved configuration for environment: {environment}")
    
    def _encrypt_sensitive_values(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive configuration values"""
        sensitive_fields = [
            "database.password",
            "redis.password",
            "security.secret_key",
            "models.openai_api_key",
            "models.anthropic_api_key",
            "models.google_api_key",
            "integrations.salesforce_password",
            "integrations.salesforce_security_token"
        ]
        
        for field in sensitive_fields:
            value = self._get_nested_value(config, field)
            if value and isinstance(value, str) and not value.startswith("encrypted:"):
                try:
                    encrypted_data = self.cipher_suite.encrypt(value.encode())
                    encrypted_value = "encrypted:" + base64.b64encode(encrypted_data).decode()
                    self._set_nested_value(config, field, encrypted_value)
                except Exception as e:
                    logger.error(f"Failed to encrypt {field}: {str(e)}")
        
        return config
    
    def create_default_configs(self):
        """Create default configuration files"""
        environments = ["development", "staging", "production"]
        
        for env in environments:
            config = OpenDistilleryConfig()
            config.environment = env
            
            if env == "production":
                config.debug = False
                config.security.require_https = True
                config.monitoring.log_level = "WARNING"
            elif env == "staging":
                config.debug = False
                config.security.require_https = True
                config.monitoring.log_level = "INFO"
            else:  # development
                config.debug = True
                config.security.require_https = False
                config.monitoring.log_level = "DEBUG"
            
            self.save_config(config, env)
        
        logger.info("Created default configuration files")

# Global configuration manager
config_manager = ConfigManager()

def get_config(environment: str = None) -> OpenDistilleryConfig:
    """Get configuration for specified environment"""
    return config_manager.load_config(environment)

def get_current_config() -> Optional[OpenDistilleryConfig]:
    """Get currently loaded configuration"""
    return config_manager.config 