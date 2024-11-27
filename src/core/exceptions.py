"""
Core exception handling module for fleXRP.

This module defines the exception hierarchy and provides base exception
classes for different types of errors that can occur in the system.
"""

from typing import Optional, Dict, Any
from datetime import datetime


class FleXRPError(Exception):
    """Base exception for all fleXRP errors."""
    
    def __init__(
        self, 
        message: str, 
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        self.message = message
        self.code = code or "FLEX_ERR"
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class XRPLError(FleXRPError):
    """XRPL-related errors."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            code="XRPL_ERR",
            details=details
        )


class APIError(FleXRPError):
    """External API interaction errors."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            code="API_ERR",
            details=details
        )


class DatabaseError(FleXRPError):
    """Database operation errors."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            code="DB_ERR",
            details=details
        ) 