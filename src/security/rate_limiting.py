"""
Enterprise Rate Limiting and Throttling
Advanced rate limiting, quotas, and traffic management
"""

import time
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class LimitType(Enum):
    """Rate limit types"""
    REQUESTS_PER_SECOND = "rps"
    REQUESTS_PER_MINUTE = "rpm"
    REQUESTS_PER_HOUR = "rph"
    REQUESTS_PER_DAY = "rpd"

@dataclass
class RateLimit:
    """Rate limit configuration"""
    limit: int
    window: int  # seconds
    limit_type: LimitType

class RateLimiter:
    """Enterprise rate limiter"""
    
    def __init__(self, default_limit: int = 100, window_seconds: int = 60):
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
        self.custom_limits: Dict[str, RateLimit] = {}
    
    def check_limit(self, identifier: str) -> bool:
        """Check if request is within rate limit"""
        current_time = time.time()
        
        # Get limit for this identifier
        limit_config = self.custom_limits.get(identifier)
        if limit_config:
            limit = limit_config.limit
            window = limit_config.window
        else:
            limit = self.default_limit
            window = self.window_seconds
        
        # Initialize request history
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Clean old requests
        cutoff_time = current_time - window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] 
            if req_time > cutoff_time
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= limit:
            return False
        
        # Record request
        self.requests[identifier].append(current_time)
        return True
    
    def set_custom_limit(self, identifier: str, limit: RateLimit):
        """Set custom rate limit for identifier"""
        self.custom_limits[identifier] = limit
        logger.info(f"Set custom limit for {identifier}: {limit.limit}/{limit.limit_type.value}")
    
    def get_remaining_requests(self, identifier: str) -> int:
        """Get remaining requests for identifier"""
        current_time = time.time()
        
        limit_config = self.custom_limits.get(identifier)
        if limit_config:
            limit = limit_config.limit
            window = limit_config.window
        else:
            limit = self.default_limit
            window = self.window_seconds
        
        if identifier not in self.requests:
            return limit
        
        cutoff_time = current_time - window
        valid_requests = [
            req_time for req_time in self.requests[identifier] 
            if req_time > cutoff_time
        ]
        
        return max(0, limit - len(valid_requests))

class ThrottleManager:
    """Advanced throttling manager"""
    
    def __init__(self):
        self.throttle_rules: Dict[str, Dict[str, Any]] = {}
        self.active_throttles: Dict[str, float] = {}
    
    def add_throttle_rule(self, name: str, condition: str, action: str, duration: int = 300):
        """Add throttling rule"""
        self.throttle_rules[name] = {
            "condition": condition,
            "action": action,
            "duration": duration
        }
    
    def should_throttle(self, identifier: str, context: Dict[str, Any] = None) -> bool:
        """Check if identifier should be throttled"""
        current_time = time.time()
        
        # Check active throttles
        if identifier in self.active_throttles:
            if current_time < self.active_throttles[identifier]:
                return True
            else:
                del self.active_throttles[identifier]
        
        # Check throttle rules
        for rule_name, rule in self.throttle_rules.items():
            if self._evaluate_condition(rule["condition"], identifier, context):
                self._apply_throttle(identifier, rule["duration"])
                return True
        
        return False
    
    def _evaluate_condition(self, condition: str, identifier: str, context: Dict[str, Any] = None) -> bool:
        """Evaluate throttle condition"""
        # Simple condition evaluation - could be enhanced
        if "suspicious" in condition.lower() and context:
            return context.get("suspicious_activity", False)
        return False
    
    def _apply_throttle(self, identifier: str, duration: int):
        """Apply throttle to identifier"""
        self.active_throttles[identifier] = time.time() + duration
        logger.warning(f"Applied throttle to {identifier} for {duration} seconds")

class QuotaManager:
    """Quota management for API usage"""
    
    def __init__(self):
        self.quotas: Dict[str, Dict[str, Any]] = {}
        self.usage: Dict[str, Dict[str, int]] = {}
    
    def set_quota(self, user_id: str, resource: str, limit: int, period: str = "daily"):
        """Set quota for user and resource"""
        if user_id not in self.quotas:
            self.quotas[user_id] = {}
        
        self.quotas[user_id][resource] = {
            "limit": limit,
            "period": period,
            "reset_time": self._calculate_reset_time(period)
        }
        
        logger.info(f"Set quota for {user_id}/{resource}: {limit}/{period}")
    
    def check_quota(self, user_id: str, resource: str, amount: int = 1) -> bool:
        """Check if quota allows usage"""
        if user_id not in self.quotas or resource not in self.quotas[user_id]:
            return True  # No quota set
        
        quota = self.quotas[user_id][resource]
        current_time = time.time()
        
        # Reset if period expired
        if current_time >= quota["reset_time"]:
            self._reset_usage(user_id, resource)
            quota["reset_time"] = self._calculate_reset_time(quota["period"])
        
        # Check current usage
        current_usage = self.usage.get(user_id, {}).get(resource, 0)
        
        if current_usage + amount > quota["limit"]:
            return False
        
        # Record usage
        if user_id not in self.usage:
            self.usage[user_id] = {}
        self.usage[user_id][resource] = current_usage + amount
        
        return True
    
    def _calculate_reset_time(self, period: str) -> float:
        """Calculate quota reset time"""
        current_time = time.time()
        if period == "hourly":
            return current_time + 3600
        elif period == "daily":
            return current_time + 86400
        elif period == "weekly":
            return current_time + 604800
        elif period == "monthly":
            return current_time + 2592000
        return current_time + 86400  # Default to daily
    
    def _reset_usage(self, user_id: str, resource: str):
        """Reset usage for user and resource"""
        if user_id in self.usage and resource in self.usage[user_id]:
            self.usage[user_id][resource] = 0
    
    def get_quota_status(self, user_id: str, resource: str) -> Dict[str, Any]:
        """Get quota status for user and resource"""
        if user_id not in self.quotas or resource not in self.quotas[user_id]:
            return {"quota_set": False}
        
        quota = self.quotas[user_id][resource]
        usage = self.usage.get(user_id, {}).get(resource, 0)
        
        return {
            "quota_set": True,
            "limit": quota["limit"],
            "used": usage,
            "remaining": quota["limit"] - usage,
            "period": quota["period"],
            "reset_time": quota["reset_time"]
        } 