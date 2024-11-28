"""
Dashboard routes for the merchant interface.

This module handles all dashboard-related routes including the main dashboard view,
analytics, metrics, and real-time transaction monitoring.
"""

import logging
from typing import Dict, Any
from flask import (
    Blueprint, render_template, session,
    current_app, jsonify, Response
)
from datetime import datetime, timedelta

from core.error_handlers import error_context
from core.metrics import metrics_collector
from core.exceptions import DashboardError
from .auth import login_required

logger = logging.getLogger(__name__)
bp = Blueprint('dashboard', __name__)

@bp.route('/')
@login_required
@metrics_collector.track_request
def index() -> str:
    """
    Render merchant dashboard with real-time data.
    
    Returns:
        Rendered dashboard template with merchant data
        
    Raises:
        DashboardError: If data fetching fails
    """
    with error_context("dashboard_view"):
        merchant_id = session.get('merchant_id')
        if not merchant_id:
            return render_template('auth/login.html')
            
        try:
            dashboard_data = _fetch_dashboard_data(merchant_id)
            return render_template('dashboard/index.html', **dashboard_data)
            
        except Exception as e:
            logger.error(
                f"Dashboard error for merchant {merchant_id}: {str(e)}",
                exc_info=True
            )
            metrics_collector.increment_error_counter('dashboard_view')
            return render_template(
                'error.html',
                error="Dashboard temporarily unavailable"
            )

def _fetch_dashboard_data(merchant_id: str) -> Dict[str, Any]:
    """
    Fetch all required data for dashboard display.
    
    Args:
        merchant_id: Unique identifier for the merchant
        
    Returns:
        Dictionary containing all dashboard data
        
    Raises:
        DashboardError: If any data fetch fails
    """
    try:
        # Get required services
        wallet_service = current_app.wallet_service
        payment_monitor = current_app.payment_monitor
        rate_service = current_app.rate_service
        analytics_service = current_app.analytics_service
        
        # Fetch wallet information
        wallet = wallet_service.get_wallet(merchant_id)
        balance_xrp = wallet_service.get_balance(merchant_id)
        
        # Get current exchange rates
        rates = {
            'USD': rate_service.get_rate('USD'),
            'EUR': rate_service.get_rate('EUR'),
            'GBP': rate_service.get_rate('GBP')
        }
        
        # Calculate fiat balances
        balances = {
            currency: balance_xrp * rate
            for currency, rate in rates.items()
        }
        
        # Get recent transactions
        transactions = payment_monitor.get_recent_transactions(
            address=wallet['classic_address'],
            limit=10
        )
        
        # Get analytics data
        analytics = analytics_service.get_merchant_analytics(
            merchant_id=merchant_id,
            timeframe='24h'
        )
        
        return {
            'wallet': wallet,
            'transactions': transactions,
            'balance_xrp': balance_xrp,
            'balances': balances,
            'rates': rates,
            'analytics': analytics
        }
        
    except Exception as e:
        raise DashboardError(
            f"Failed to fetch dashboard data: {str(e)}",
            details={'merchant_id': merchant_id}
        )

@bp.route('/api/metrics')
@login_required
@metrics_collector.track_request
def get_metrics() -> Response:
    """
    Get merchant metrics for dashboard charts.
    
    Returns:
        JSON response containing merchant metrics
        
    Raises:
        DashboardError: If metrics fetch fails
    """
    with error_context("metrics_fetch"):
        merchant_id = session['merchant_id']
        
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
            
            # Fetch metrics
            metrics = current_app.metrics_service.get_merchant_metrics(
                merchant_id=merchant_id,
                start_date=start_date,
                end_date=end_date,
                metrics=[
                    'transaction_volume',
                    'transaction_count',
                    'average_transaction_size',
                    'success_rate',
                    'settlement_time'
                ]
            )
            
            return jsonify({
                'status': 'success',
                'data': metrics,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(
                f"Metrics error for merchant {merchant_id}: {str(e)}",
                exc_info=True
            )
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch metrics',
                'error': str(e)
            }), 500

@bp.route('/api/transactions/live')
@login_required
@metrics_collector.track_request
def live_transactions() -> Response:
    """
    Stream live transaction updates via Server-Sent Events.
    
    Returns:
        SSE stream of transaction updates
    """
    def generate():
        merchant_id = session['merchant_id']
        wallet = current_app.wallet_service.get_wallet(merchant_id)
        
        try:
            for transaction in current_app.payment_monitor.stream_transactions(
                address=wallet['classic_address']
            ):
                yield f"data: {jsonify(transaction).data.decode()}\n\n"
                
        except Exception as e:
            logger.error(f"Live transaction stream error: {str(e)}")
            yield f"data: {jsonify({'error': 'Stream ended'}).data.decode()}\n\n"
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    ) 