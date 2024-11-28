"""
fleXRP API package.

This package contains all API routes and handlers for the merchant interface.
"""

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

from core.monitoring import AlertManager
from core.metrics import metrics_collector

# Initialize extensions
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def init_app(app: Flask) -> None:
    """Initialize Flask application with all routes and middleware."""
    # Register extensions
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Register blueprints
    from .routes import auth, dashboard, payments, settings
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(payments.bp)
    app.register_blueprint(settings.bp)
    
    # Register error handlers
    from .error_handlers import register_error_handlers
    register_error_handlers(app) 