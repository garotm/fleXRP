"""
System monitoring and alerting for fleXRP.

This module handles system monitoring, health checks, and alert
generation for system issues and anomalies.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import requests

logger = logging.getLogger(__name__)

@dataclass
class AlertConfig:
    """Alert configuration settings."""
    
    type: str
    threshold: float
    window: int
    severity: str
    channels: List[str]


class AlertManager:
    """Manager for system alerts and notifications."""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.alert_history: Dict[str, List[datetime]] = {}

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load alert configuration from file."""
        with open(config_path, 'r') as f:
            return json.load(f)

    def should_alert(
        self,
        alert_type: str,
        value: float,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Check if an alert should be triggered."""
        if alert_type not in self.config:
            return False

        config = self.config[alert_type]
        timestamp = timestamp or datetime.utcnow()
        
        # Clean old history
        self._clean_history(alert_type, timestamp)
        
        # Check threshold
        if value >= config.threshold:
            self.alert_history.setdefault(alert_type, []).append(timestamp)
            return len(self.alert_history[alert_type]) >= config.threshold
            
        return False

    def _clean_history(
        self,
        alert_type: str,
        current_time: datetime
    ) -> None:
        """Clean old alerts from history."""
        if alert_type not in self.alert_history:
            return

        window = timedelta(seconds=self.config[alert_type].window)
        self.alert_history[alert_type] = [
            t for t in self.alert_history[alert_type]
            if current_time - t <= window
        ]

    def send_alert(
        self,
        alert_type: str,
        details: Dict[str, Any]
    ) -> None:
        """Send alert through configured channels."""
        if alert_type not in self.config:
            return

        config = self.config[alert_type]
        
        for channel in config.channels:
            try:
                self._send_to_channel(
                    channel=channel,
                    severity=config.severity,
                    alert_type=alert_type,
                    details=details
                )
            except Exception as e:
                logger.error(
                    f"Failed to send alert to {channel}: {str(e)}",
                    exc_info=True
                )

    def _send_to_channel(
        self,
        channel: str,
        severity: str,
        alert_type: str,
        details: Dict[str, Any]
    ) -> None:
        """Send alert to specific channel."""
        if channel == "slack":
            self._send_slack_alert(severity, alert_type, details)
        elif channel == "email":
            self._send_email_alert(severity, alert_type, details)
        elif channel == "pagerduty":
            self._send_pagerduty_alert(severity, alert_type, details)

    def _send_slack_alert(
        self,
        severity: str,
        alert_type: str,
        details: Dict[str, Any]
    ) -> None:
        """Send alert to Slack."""
        webhook_url = self.config.get("slack_webhook_url")
        if not webhook_url:
            return

        message = {
            "text": f"*{severity.upper()} ALERT*: {alert_type}",
            "attachments": [{
                "color": "danger" if severity == "critical" else "warning",
                "fields": [
                    {"title": k, "value": str(v), "short": True}
                    for k, v in details.items()
                ]
            }]
        }

        response = requests.post(webhook_url, json=message)
        response.raise_for_status() 