"""
OpenDistillery Alerting System
Configurable alerting and notification system.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict, field
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

@dataclass
class Alert:
    """Alert data structure"""
    alert_id: str
    severity: str
    component: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['severity'] = self.severity
        result['status'] = self.status
        return result

@dataclass
class AlertRule:
    """Alert rule configuration"""
    id: str
    name: str
    condition: str
    severity: AlertSeverity
    enabled: bool = True
    cooldown_minutes: int = 15
    channels: List[str] = None
    metadata: Dict[str, Any] = None

class AlertChannel:
    """Base class for alert channels"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert through this channel"""
        raise NotImplementedError

class EmailAlertChannel(AlertChannel):
    """Email alert channel"""
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send email alert"""
        try:
            # In a real implementation, this would send an email
            logger.info(f"Email alert sent: {alert.message} to {self.config.get('recipients', [])}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False

class SlackAlertChannel(AlertChannel):
    """Slack alert channel"""
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send Slack alert"""
        try:
            # In a real implementation, this would send to Slack webhook
            logger.info(f"Slack alert sent: {alert.message} to {self.config.get('webhook_url')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False

class WebhookAlertChannel(AlertChannel):
    """Generic webhook alert channel"""
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send webhook alert"""
        try:
            # In a real implementation, this would send HTTP POST to webhook
            logger.info(f"Webhook alert sent: {alert.message} to {self.config.get('url')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, notification_channels: Optional[List[Dict[str, Any]]] = None):
        self.alerts: Dict[str, Alert] = {}
        self.rules: Dict[str, AlertRule] = {}
        self.channels: Dict[str, AlertChannel] = {}
        self.alert_history: List[Alert] = []
        self.max_history = 1000
        self.cooldown_period = timedelta(minutes=5)
        self.last_alert_time: Dict[str, datetime] = {}
        self.notification_channels = notification_channels or []
        self._setup_default_rules()
        self._setup_default_channels()
    
    def _setup_default_rules(self):
        """Setup default alert rules"""
        self.rules['high_cpu'] = AlertRule(
            id='high_cpu',
            name='High CPU Usage',
            condition='cpu_percent > 80',
            severity=AlertSeverity.HIGH,
            cooldown_minutes=10,
            channels=['email', 'slack']
        )
        
        self.rules['high_memory'] = AlertRule(
            id='high_memory',
            name='High Memory Usage',
            condition='memory_percent > 85',
            severity=AlertSeverity.HIGH,
            cooldown_minutes=10,
            channels=['email', 'slack']
        )
        
        self.rules['api_errors'] = AlertRule(
            id='api_errors',
            name='High API Error Rate',
            condition='error_rate > 0.05',
            severity=AlertSeverity.CRITICAL,
            cooldown_minutes=5,
            channels=['email', 'slack', 'webhook']
        )
        
        self.rules['db_connection'] = AlertRule(
            id='db_connection',
            name='Database Connection Failed',
            condition='db_status != "healthy"',
            severity=AlertSeverity.CRITICAL,
            cooldown_minutes=5,
            channels=['email', 'slack']
        )
    
    def _setup_default_channels(self):
        """Setup default alert channels"""
        self.channels['email'] = EmailAlertChannel(
            'email',
            {'recipients': ['nikjois@llamasearch.ai']}
        )
        
        self.channels['slack'] = SlackAlertChannel(
            'slack',
            {'webhook_url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'}
        )
        
        self.channels['webhook'] = WebhookAlertChannel(
            'webhook',
            {'url': 'https://your-webhook-endpoint.com/alerts'}
        )
    
    def add_rule(self, rule: AlertRule):
        """Add alert rule"""
        self.rules[rule.id] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """Remove alert rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")
    
    def add_channel(self, channel: AlertChannel):
        """Add alert channel"""
        self.channels[channel.name] = channel
        logger.info(f"Added alert channel: {channel.name}")
    
    async def raise_alert(self, severity: str, component: str, message: str, details: Dict[str, Any] = None) -> str:
        """Raise a new alert and notify"""
        from uuid import uuid4
        alert_id = str(uuid4())
        details = details or {}
        
        # Check cooldown
        cooldown_key = f"{component}:{severity}:{message}"
        last_alert = self.last_alert_time.get(cooldown_key)
        if last_alert and datetime.now() - last_alert < self.cooldown_period:
            logger.info(f"Alert suppressed due to cooldown: {cooldown_key}")
            return alert_id
        
        self.last_alert_time[cooldown_key] = datetime.now()
        alert = Alert(alert_id=alert_id, severity=severity, component=component, message=message, details=details)
        self.alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)
        
        logger.warning(f"Alert raised: {severity} - {component} - {message}", extra=details)
        await self._notify(alert)
        return alert_id

    async def _notify(self, alert: Alert):
        """Send notifications through configured channels"""
        for channel in self.notification_channels:
            try:
                channel_type = channel.get('type', 'log')
                if channel_type == 'log':
                    logger.info(f"Alert notification: {alert.severity} - {alert.component} - {alert.message}")
                elif channel_type == 'email':
                    # Placeholder for email notification
                    logger.info(f"Email alert would be sent to {channel.get('recipient')}: {alert.message}")
                elif channel_type == 'slack':
                    # Placeholder for Slack notification
                    logger.info(f"Slack alert would be sent to {channel.get('channel')}: {alert.message}")
                elif channel_type == 'pagerduty':
                    # Placeholder for PagerDuty integration
                    logger.info(f"PagerDuty alert would be sent: {alert.message}")
            except Exception as e:
                logger.error(f"Notification failed for channel {channel.get('type')}: {str(e)}")

    async def acknowledge_alert(self, alert_id: str, user: str = "system") -> bool:
        """Acknowledge an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].acknowledged = True
            self.alerts[alert_id].details['acknowledged_by'] = user
            self.alerts[alert_id].details['acknowledged_at'] = datetime.now().isoformat()
            logger.info(f"Alert acknowledged: {alert_id} by {user}")
            return True
        return False

    async def resolve_alert(self, alert_id: str, resolution: str = "", user: str = "system") -> bool:
        """Resolve an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            self.alerts[alert_id].details['resolved_by'] = user
            self.alerts[alert_id].details['resolved_at'] = datetime.now().isoformat()
            self.alerts[alert_id].details['resolution'] = resolution
            logger.info(f"Alert resolved: {alert_id} by {user} - {resolution}")
            return True
        return False

    def get_active_alerts(self) -> List[Alert]:
        """Get list of active (unresolved) alerts"""
        return [alert for alert in self.alerts.values() if not alert.resolved]

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return self.alert_history[-limit:]

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get specific alert by ID"""
        return self.alerts.get(alert_id)

    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        active_alerts = self.get_active_alerts()
        
        severity_counts = {}
        for severity in AlertSeverity:
            severity_counts[severity.value] = sum(
                1 for alert in active_alerts if alert.severity == severity
            )
        
        return {
            'total_active': len(active_alerts),
            'total_rules': len(self.rules),
            'total_channels': len(self.channels),
            'severity_breakdown': severity_counts,
            'total_history': len(self.alert_history)
        }

# Global alert manager instance
_alert_manager = None
_alert_lock = asyncio.Lock()

def get_alert_manager(notification_channels: Optional[List[Dict[str, Any]]] = None) -> AlertManager:
    """Get the global alert manager instance"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager(notification_channels)
    return _alert_manager 