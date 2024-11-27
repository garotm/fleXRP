"""
Metrics collection and monitoring for fleXRP.

This module handles metrics collection, monitoring, and alerting
for system health and performance tracking.
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# Metrics definitions
METRICS = {
    'errors': Counter(
        'flexrp_errors_total',
        'Total number of errors by type',
        ['error_type', 'operation']
    ),
    'api_latency': Histogram(
        'flexrp_api_latency_seconds',
        'API call latency in seconds',
        ['endpoint']
    ),
    'transaction_processing_time': Histogram(
        'flexrp_transaction_processing_seconds',
        'Transaction processing time in seconds'
    ),
    'active_connections': Gauge(
        'flexrp_active_connections',
        'Number of active connections',
        ['type']
    )
}


class MetricsCollector:
    """Collector for system metrics and performance data."""
    
    def __init__(self):
        self.metrics = METRICS

    def increment_error_counter(
        self,
        error_type: str,
        operation: str
    ) -> None:
        """Increment error counter for specific type and operation."""
        self.metrics['errors'].labels(
            error_type=error_type,
            operation=operation
        ).inc()

    def record_api_latency(
        self,
        endpoint: str,
        duration: float
    ) -> None:
        """Record API call latency."""
        self.metrics['api_latency'].labels(
            endpoint=endpoint
        ).observe(duration)

    def update_connection_count(
        self,
        connection_type: str,
        count: int
    ) -> None:
        """Update active connection count."""
        self.metrics['active_connections'].labels(
            type=connection_type
        ).set(count)

    @contextmanager
    def measure_latency(
        self,
        metric_name: str,
        labels: Optional[Dict[str, str]] = None
    ):
        """Context manager to measure operation latency."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            if labels:
                self.metrics[metric_name].labels(**labels).observe(duration)
            else:
                self.metrics[metric_name].observe(duration)


# Global metrics collector instance
metrics_collector = MetricsCollector()


def increment_error_counter(operation: str, error_type: Optional[str] = None) -> None:
    """Increment error counter with operation context."""
    metrics_collector.increment_error_counter(
        error_type or "unknown",
        operation
    )


def record_error_details(operation: str, details: Dict[str, Any]) -> None:
    """Record detailed error information for analysis."""
    logger.error(
        f"Operation error: {operation}",
        extra={
            "error_details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
    ) 