"""
Payment routes for the merchant interface.

This module handles payment-related operations including payment requests,
QR code generation, and payment status tracking.
"""

import logging
from typing import Dict, Any
from flask import (
    Blueprint, render_template, request, 
    jsonify, current_app, session, Response
)
from datetime import datetime
import qrcode
import io
import base64

from core.error_handlers import error_context
from core.metrics import metrics_collector
from core.exceptions import PaymentError
from .auth import login_required

logger = logging.getLogger(__name__)
bp = Blueprint('payments', __name__, url_prefix='/payments')

@bp.route('/request', methods=['GET', 'POST'])
@login_required
@metrics_collector.track_request
def create_request() -> str:
    """
    Create new payment request with QR code.
    
    Returns:
        Rendered payment request template
        
    Raises:
        PaymentError: If payment request creation fails
    """
    if request.method == 'POST':
        with error_context("payment_request_creation"):
            try:
                payment_data = _create_payment_request(
                    amount=float(request.form['amount']),
                    currency=request.form['currency'],
                    description=request.form.get('description', '')
                )
                
                return render_template(
                    'payments/request.html',
                    payment=payment_data
                )
                
            except Exception as e:
                logger.error(f"Payment request creation failed: {str(e)}")
                return render_template(
                    'error.html',
                    error="Failed to create payment request"
                )
    
    return render_template('payments/create_request.html')

def _create_payment_request(
    amount: float,
    currency: str,
    description: str = ''
) -> Dict[str, Any]:
    """
    Create payment request with QR code.
    
    Args:
        amount: Payment amount
        currency: Currency code (e.g., USD, EUR)
        description: Optional payment description
        
    Returns:
        Dictionary containing payment request data
        
    Raises:
        PaymentError: If request creation fails
    """
    merchant_id = session['merchant_id']
    wallet = current_app.wallet_service.get_wallet(merchant_id)
    
    try:
        # Convert to XRP amount
        rate_service = current_app.rate_service
        xrp_rate = rate_service.get_rate(currency)
        xrp_amount = amount / xrp_rate
        
        # Create payment request
        payment_data = {
            'address': wallet['classic_address'],
            'amount_xrp': xrp_amount,
            'amount_fiat': amount,
            'currency': currency,
            'description': description,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (
                datetime.utcnow() + 
                current_app.config['PAYMENT_REQUEST_EXPIRY']
            ).isoformat()
        }
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payment_data)
        qr.make(fit=True)
        
        # Convert QR code to base64 image
        img_buffer = io.BytesIO()
        qr.make_image().save(img_buffer, format='PNG')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        payment_data['qr_code'] = f"data:image/png;base64,{img_str}"
        
        # Store payment request
        current_app.payment_service.store_request(payment_data)
        
        return payment_data
        
    except Exception as e:
        raise PaymentError(
            f"Failed to create payment request: {str(e)}",
            details={
                'merchant_id': merchant_id,
                'amount': amount,
                'currency': currency
            }
        )

@bp.route('/status/<request_id>')
@login_required
@metrics_collector.track_request
def check_status(request_id: str) -> Response:
    """
    Check payment request status.
    
    Args:
        request_id: Unique payment request identifier
        
    Returns:
        JSON response with payment status
    """
    with error_context("payment_status_check"):
        try:
            status = current_app.payment_service.get_request_status(request_id)
            return jsonify({
                'status': 'success',
                'data': status
            })
            
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to check payment status'
            }), 500

@bp.route('/history')
@login_required
@metrics_collector.track_request
def payment_history() -> str:
    """
    Show merchant's payment history.
    
    Returns:
        Rendered payment history template
    """
    with error_context("payment_history"):
        merchant_id = session['merchant_id']
        
        try:
            # Get payment history
            history = current_app.payment_service.get_merchant_history(
                merchant_id=merchant_id,
                limit=50
            )
            
            return render_template(
                'payments/history.html',
                payments=history
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch payment history: {str(e)}")
            return render_template(
                'error.html',
                error="Failed to load payment history"
            ) 