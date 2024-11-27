"""
Error handling utilities and decorators for fleXRP.

This module provides reusable error handling mechanisms including
retry logic, circuit breakers, and error tracking.
"""

import time
import logging
from typing import Any, Callable, Optional, TypeVar, Dict
from functools import wraps
from datetime import datetime, timedelta
from contextlib import contextmanager

from .exceptions import FleXRPError, XRPLError, APIError
from .metrics import increment_error_counter, record_error_details

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitBreaker:
    """Circuit breaker implementation for handling failing operations."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_timeout: int = 30
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_timeout = half_open_timeout
        self.failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"

    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution."""
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            if (datetime.utcnow() - self.last_failure_time) > timedelta(seconds=self.recovery_timeout):
                self.state = "HALF_OPEN"
                return True
            return False
            
        return True

    def record_success(self) -> None:
        """Record successful execution."""
        self.failures = 0
        self.state = "CLOSED"

    def record_failure(self) -> None:
        """Record failed execution."""
        self.failures += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"


def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential: bool = True,
    exceptions: tuple = (Exception,)
) -> Callable:
    """Retry decorator with exponential backoff."""
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed: {str(e)}"
                    )
                    
                    if attempt + 1 == max_attempts:
                        break
                        
                    time.sleep(delay)
                    if exponential:
                        delay = min(delay * 2, max_delay)
            
            raise last_exception
            
        return wrapper
    return decorator


@contextmanager
def error_context(
    operation: str,
    error_details: Optional[Dict[str, Any]] = None
):
    """Context manager for handling errors with proper logging and metrics."""
    try:
        yield
    except Exception as e:
        details = error_details or {}
        details.update({
            "operation": operation,
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(e).__name__
        })
        
        logger.error(
            f"Error in {operation}: {str(e)}",
            extra={"error_details": details},
            exc_info=True
        )
        
        increment_error_counter(operation)
        record_error_details(operation, details)
        
        if isinstance(e, FleXRPError):
            raise
        raise FleXRPError(str(e), details=details) 