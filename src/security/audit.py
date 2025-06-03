"""
Enterprise Audit and Compliance Logging
Comprehensive audit trails and compliance reporting
"""

import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class AuditEvent:
    """Individual audit event"""
    user_id: str
    action: str
    resource: str
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None

class AuditLogger:
    """Enterprise audit logging system"""
    
    def __init__(self):
        self.events: List[AuditEvent] = []
        self.retention_days = 365
    
    def log_event(self, user_id: str, action: str, resource: str, 
                  success: bool = True, details: Dict[str, Any] = None,
                  ip_address: str = None, user_agent: str = None,
                  session_id: str = None):
        """Log audit event"""
        event = AuditEvent(
            user_id=user_id,
            action=action,
            resource=resource,
            success=success,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )
        self.events.append(event)
        logger.info(f"Audit: {user_id} {action} {resource} - {success}")
    
    def get_events(self, user_id: str = None, action: str = None, 
                   start_time: datetime = None, end_time: datetime = None) -> List[AuditEvent]:
        """Query audit events"""
        filtered_events = self.events
        
        if user_id:
            filtered_events = [e for e in filtered_events if e.user_id == user_id]
        if action:
            filtered_events = [e for e in filtered_events if e.action == action]
        if start_time:
            filtered_events = [e for e in filtered_events if e.timestamp >= start_time]
        if end_time:
            filtered_events = [e for e in filtered_events if e.timestamp <= end_time]
        
        return filtered_events
    
    def export_events(self, format: str = "json") -> str:
        """Export audit events"""
        if format == "json":
            return json.dumps([{
                "user_id": e.user_id,
                "action": e.action,
                "resource": e.resource,
                "timestamp": e.timestamp.isoformat(),
                "success": e.success,
                "details": e.details,
                "ip_address": e.ip_address,
                "user_agent": e.user_agent,
                "session_id": e.session_id
            } for e in self.events], indent=2)
        return ""

class ComplianceReporter:
    """Compliance reporting for various standards"""
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
    
    def generate_sox_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate SOX compliance report"""
        events = self.audit_logger.get_events(start_time=start_date, end_time=end_date)
        
        return {
            "report_type": "SOX_Compliance",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_events": len(events),
            "failed_access_attempts": len([e for e in events if not e.success]),
            "privileged_actions": len([e for e in events if "admin" in e.action.lower()]),
            "data_access_events": len([e for e in events if "data" in e.resource.lower()])
        }
    
    def generate_gdpr_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate GDPR compliance report"""
        events = self.audit_logger.get_events(start_time=start_date, end_time=end_date)
        
        return {
            "report_type": "GDPR_Compliance",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "data_processing_events": len([e for e in events if "process" in e.action.lower()]),
            "data_deletion_events": len([e for e in events if "delete" in e.action.lower()]),
            "consent_changes": len([e for e in events if "consent" in e.action.lower()]),
            "data_export_requests": len([e for e in events if "export" in e.action.lower()])
        }

class SecurityEventTracker:
    """Security event tracking and alerting"""
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
        self.alert_thresholds = {
            "failed_login": 5,
            "privilege_escalation": 1,
            "suspicious_activity": 3
        }
    
    def check_security_alerts(self, time_window_minutes: int = 60) -> List[Dict[str, Any]]:
        """Check for security alerts in recent events"""
        alerts = []
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        recent_events = self.audit_logger.get_events(start_time=cutoff_time)
        
        # Check failed login attempts
        failed_logins = [e for e in recent_events if e.action == "login" and not e.success]
        if len(failed_logins) >= self.alert_thresholds["failed_login"]:
            alerts.append({
                "type": "failed_login_threshold",
                "count": len(failed_logins),
                "severity": "high"
            })
        
        return alerts
    
    def track_anomalous_behavior(self, user_id: str) -> Dict[str, Any]:
        """Track anomalous user behavior"""
        user_events = self.audit_logger.get_events(user_id=user_id)
        
        # Basic anomaly detection
        recent_events = user_events[-50:] if len(user_events) > 50 else user_events
        action_frequency = {}
        for event in recent_events:
            action_frequency[event.action] = action_frequency.get(event.action, 0) + 1
        
        return {
            "user_id": user_id,
            "total_events": len(user_events),
            "recent_activity": action_frequency,
            "risk_score": min(len(action_frequency) / 10, 1.0)  # Simple risk scoring
        } 