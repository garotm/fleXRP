"""
Main application entry point for fleXRP.

This module initializes and configures the Flask application,
sets up logging, and starts the payment monitoring service.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from flask import Flask
from prometheus_client import start_http_server

from core.monitoring import AlertManager
from core.metrics import metrics_collector
from services.payment_monitor import PaymentMonitor
from services.wallet_service import WalletService
from api.routes import register_routes

logger = logging.getLogger(__name__)

class Config:
    """Application configuration."""
    
    XRPL_NODE_URL = os.getenv('XRPL_NODE_URL', 'wss://s.altnet.rippletest.net:51233')
    MERCHANT_ADDRESS = os.getenv('MERCHANT_ADDRESS')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    METRICS_PORT = int(os.getenv('METRICS_PORT', '9090'))
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.MERCHANT_ADDRESS:
            raise ValueError("MERCHANT_ADDRESS environment variable not set")


def setup_logging() -> None:
    """Configure application logging."""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_handler = RotatingFileHandler(
        log_dir / 'flexrp.log',
        maxBytes=10_485_760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().setLevel(getattr(logging, Config.LOG_LEVEL))


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    # Register routes
    register_routes(app)
    
    # Initialize services
    app.wallet_service = WalletService()
    app.payment_monitor = PaymentMonitor(
        merchant_address=Config.MERCHANT_ADDRESS,
        alert_manager=AlertManager('config/alerts.json')
    )
    
    return app


def main() -> None:
    """Application entry point."""
    try:
        # Validate configuration
        Config.validate()
        
        # Setup logging
        setup_logging()
        logger.info("Starting fleXRP application")
        
        # Start metrics server
        start_http_server(Config.METRICS_PORT)
        logger.info(f"Metrics server started on port {Config.METRICS_PORT}")
        
        # Create and start application
        app = create_app()
        app.payment_monitor.start()
        
        # Start Flask application
        app.run(host='0.0.0.0', port=5000)
        
    except Exception as e:
        logger.error("Failed to start application", exc_info=True)
        raise
    finally:
        logger.info("Shutting down fleXRP application")


if __name__ == '__main__':
    main() 