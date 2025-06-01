"""
Advanced Security and Compliance Framework
Enterprise-grade security with zero-trust architecture
"""

import hashlib
import hmac
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import asyncio
import aioredis
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging
from dataclasses import dataclass
from enum import Enum
import re
from fastapi import HTTPException, status
import time

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"

class PermissionType(Enum):
    """Permission types"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    OPTIMIZE = "optimize"
    BATCH_PROCESS = "batch_process"

@dataclass
class SecurityContext:
    """Security context for requests"""
    user_id: str
    organization_id: str
    security_level: SecurityLevel
    permissions: Set[PermissionType]
    ip_address: str
    user_agent: str
    timestamp: datetime

class AdvancedEncryption:
    """Advanced encryption for sensitive data"""
    
    def __init__(self, master_key: Optional[str] = None):
        if master_key:
            self.master_key = master_key.encode()
        else:
            self.master_key = Fernet.generate_key()
        
        self.fernet = Fernet(self.master_key)
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        encrypted = self.fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Invalid encrypted data")
    
    def hash_sensitive_data(self, data: str, salt: Optional[str] = None) -> Dict[str, str]:
        """Hash sensitive data with salt"""
        if not salt:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 for secure hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        
        key = kdf.derive(data.encode())
        hashed = base64.urlsafe_b64encode(key).decode()
        
        return {
            "hash": hashed,
            "salt": salt,
            "algorithm": "PBKDF2-SHA256",
            "iterations": 100000
        }

class ZeroTrustAuthenticator:
    """Zero-trust authentication system"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.jwt_secret = secrets.token_urlsafe(32)
        self.encryption = AdvancedEncryption()
        
        # Security policies
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        self.session_timeout = timedelta(hours=8)
        self.token_refresh_threshold = timedelta(minutes=15)
    
    async def authenticate_user(self, api_key: str, ip_address: str, 
                              user_agent: str) -> SecurityContext:
        """Authenticate user with zero-trust principles"""
        
        # Rate limiting check
        await self._check_rate_limits(ip_address)
        
        # Validate API key format
        if not self._validate_api_key_format(api_key):
            await self._log_security_event("invalid_api_key_format", ip_address)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key format"
            )
        
        # Check if API key is blacklisted
        if await self._is_blacklisted(api_key):
            await self._log_security_event("blacklisted_api_key", ip_address)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has been revoked"
            )
        
        # Verify API key
        user_data = await self._verify_api_key(api_key)
        if not user_data:
            await self._handle_failed_authentication(ip_address)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Check account status
        if user_data.get("status") != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )
        
        # Verify IP address if restricted
        if not await self._verify_ip_address(user_data["user_id"], ip_address):
            await self._log_security_event("unauthorized_ip", ip_address, user_data["user_id"])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access from this IP address is not allowed"
            )
        
        # Create security context
        security_context = SecurityContext(
            user_id=user_data["user_id"],
            organization_id=user_data["organization_id"],
            security_level=SecurityLevel(user_data["security_level"]),
            permissions=set(PermissionType(p) for p in user_data["permissions"]),
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now()
        )
        
        # Log successful authentication
        await self._log_security_event("successful_authentication", ip_address, 
                                     user_data["user_id"])
        
        return security_context
    
    async def _check_rate_limits(self, ip_address: str):
        """Check rate limits for IP address"""
        
        rate_limit_key = f"rate_limit:{ip_address}"
        current_count = await self.redis.get(rate_limit_key)
        
        if current_count and int(current_count) > 100:  # 100 requests per minute
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Increment counter
        pipe = self.redis.pipeline()
        pipe.incr(rate_limit_key)
        pipe.expire(rate_limit_key, 60)  # 1 minute window
        await pipe.execute()
    
    def _validate_api_key_format(self, api_key: str) -> bool:
        """Validate API key format"""
        # Expected format: od_[env]_[32_hex_chars]
        pattern = r'^od_(prod|dev|test)_[a-fA-F0-9]{32}$'
        return bool(re.match(pattern, api_key))
    
    async def _is_blacklisted(self, api_key: str) -> bool:
        """Check if API key is blacklisted"""
        blacklist_key = f"blacklist:{api_key}"
        return await self.redis.exists(blacklist_key)
    
    async def _verify_api_key(self, api_key: str) -> Optional[Dict]:
        """Verify API key against database"""
        
        # In practice, this would query the database
        # For demonstration, we'll simulate user data
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        user_key = f"user:{key_hash}"
        
        user_data_json = await self.redis.get(user_key)
        if user_data_json:
            import json
            return json.loads(user_data_json)
        
        return None
    
    async def _verify_ip_address(self, user_id: str, ip_address: str) -> bool:
        """Verify if IP address is allowed for user"""
        
        # Check if user has IP restrictions
        ip_whitelist_key = f"ip_whitelist:{user_id}"
        allowed_ips = await self.redis.smembers(ip_whitelist_key)
        
        if not allowed_ips:
            return True  # No restrictions
        
        # Check if current IP is in whitelist
        return ip_address.encode() in allowed_ips
    
    async def _handle_failed_authentication(self, ip_address: str):
        """Handle failed authentication attempt"""
        
        failed_attempts_key = f"failed_attempts:{ip_address}"
        current_attempts = await self.redis.get(failed_attempts_key)
        current_attempts = int(current_attempts) if current_attempts else 0
        
        current_attempts += 1
        
        if current_attempts >= self.max_failed_attempts:
            # Lock the IP address
            lockout_key = f"lockout:{ip_address}"
            await self.redis.setex(lockout_key, 
                                 int(self.lockout_duration.total_seconds()), 
                                 "locked")
            
            await self._log_security_event("ip_locked", ip_address)
        else:
            # Update failed attempts counter
            await self.redis.setex(failed_attempts_key, 300, current_attempts)  # 5 minutes
    
    async def _log_security_event(self, event_type: str, ip_address: str, 
                                user_id: Optional[str] = None):
        """Log security events"""
        
        event = {
            "event_type": event_type,
            "ip_address": ip_address,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "severity": self._get_event_severity(event_type)
        }
        
        # Store in Redis for real-time monitoring
        event_key = f"security_events:{datetime.now().strftime('%Y%m%d')}"
        await self.redis.lpush(event_key, str(event))
        await self.redis.expire(event_key, 86400 * 30)  # Keep for 30 days
        
        # Log to application logger
        logger.warning(f"Security event: {event}")
    
    def _get_event_severity(self, event_type: str) -> str:
        """Get severity level for security event"""
        severity_map = {
            "invalid_api_key_format": "low",
            "blacklisted_api_key": "high",
            "unauthorized_ip": "high",
            "successful_authentication": "info",
            "ip_locked": "critical"
        }
        return severity_map.get(event_type, "medium")

class DataClassificationEngine:
    """Engine for classifying and protecting sensitive data"""
    
    def __init__(self):
        self.pii_patterns = {
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": re.compile(r'\b(\+\d{1,2}\s?)?(\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b'),
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "credit_card": re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            "ip_address": re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
        }
        
        self.sensitive_keywords = {
            "password", "secret", "key", "token", "credential", "private",
            "confidential", "classified", "restricted", "proprietary"
        }
    
    def classify_data(self, text: str) -> Dict[str, any]:
        """Classify data sensitivity level"""
        
        classification = {
            "security_level": SecurityLevel.PUBLIC,
            "contains_pii": False,
            "pii_types": [],
            "sensitive_keywords_found": [],
            "risk_score": 0.0
        }
        
        # Check for PII
        for pii_type, pattern in self.pii_patterns.items():
            if pattern.search(text):
                classification["contains_pii"] = True
                classification["pii_types"].append(pii_type)
                classification["risk_score"] += 0.3
        
        # Check for sensitive keywords
        text_lower = text.lower()
        for keyword in self.sensitive_keywords:
            if keyword in text_lower:
                classification["sensitive_keywords_found"].append(keyword)
                classification["risk_score"] += 0.2
        
        # Determine security level based on findings
        if classification["risk_score"] >= 0.8:
            classification["security_level"] = SecurityLevel.RESTRICTED
        elif classification["risk_score"] >= 0.5:
            classification["security_level"] = SecurityLevel.CONFIDENTIAL
        elif classification["risk_score"] >= 0.3:
            classification["security_level"] = SecurityLevel.INTERNAL
        
        return classification
    
    def redact_sensitive_data(self, text: str) -> str:
        """Redact sensitive information from text"""
        
        redacted_text = text
        
        # Redact PII
        for pii_type, pattern in self.pii_patterns.items():
            if pii_type == "email":
                redacted_text = pattern.sub("[EMAIL_REDACTED]", redacted_text)
            elif pii_type == "phone":
                redacted_text = pattern.sub("[PHONE_REDACTED]", redacted_text)
            elif pii_type == "ssn":
                redacted_text = pattern.sub("[SSN_REDACTED]", redacted_text)
            elif pii_type == "credit_card":
                redacted_text = pattern.sub("[CARD_REDACTED]", redacted_text)
            elif pii_type == "ip_address":
                redacted_text = pattern.sub("[IP_REDACTED]", redacted_text)
        
        return redacted_text

class ComplianceFramework:
    """Compliance framework for various regulations"""
    
    def __init__(self):
        self.compliance_rules = {
            "gdpr": {
                "data_retention_days": 365,
                "requires_consent": True,
                "right_to_deletion": True,
                "data_portability": True
            },
            "ccpa": {
                "data_retention_days": 365,
                "requires_opt_out": True,
                "right_to_deletion": True,
                "data_portability": True
            },
            "hipaa": {
                "data_retention_days": 2555,  # 7 years
                "requires_encryption": True,
                "audit_logging": True,
                "access_controls": True
            },
            "sox": {
                "audit_logging": True,
                "data_integrity": True,
                "access_controls": True,
                "change_management": True
            }
        }
    
    def check_compliance(self, data_type: str, regulations: List[str]) -> Dict[str, bool]:
        """Check compliance requirements"""
        
        compliance_status = {}
        
        for regulation in regulations:
            if regulation not in self.compliance_rules:
                continue
            
            rules = self.compliance_rules[regulation]
            compliance_status[regulation] = {
                "compliant": True,
                "requirements": [],
                "violations": []
            }
            
            # Check specific requirements
            for requirement, required in rules.items():
                if required:
                    compliance_status[regulation]["requirements"].append(requirement)
        
        return compliance_status
    
    async def audit_data_access(self, user_id: str, resource: str, 
                              action: str, timestamp: datetime):
        """Audit data access for compliance"""
        
        audit_entry = {
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "timestamp": timestamp.isoformat(),
            "ip_address": "recorded_separately",  # For privacy
            "success": True
        }
        
        # In practice, this would be stored in a secure audit database
        logger.info(f"Audit: {audit_entry}")

class SecurityMonitoringSystem:
    """Real-time security monitoring and alerting"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.alert_thresholds = {
            "failed_logins_per_minute": 10,
            "suspicious_ip_requests": 50,
            "unusual_data_access": 100,
            "privilege_escalation_attempts": 1
        }
    
    async def monitor_security_events(self):
        """Monitor security events in real-time"""
        
        while True:
            try:
                #