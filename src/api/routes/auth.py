"""
Authentication routes for the merchant interface.
"""

import logging
from flask import (
    Blueprint, render_template, request, 
    redirect, url_for, session, current_app
)
from werkzeug.security import check_password_hash
from datetime import datetime

from core.exceptions import AuthError
from core.error_handlers import error_context
from core.metrics import metrics_collector
from services.merchant_service import MerchantService

logger = logging.getLogger(__name__)
bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
@metrics_collector.track_request
def login():
    """Handle merchant login."""
    if request.method == 'POST':
        with error_context("login_attempt"):
            username = request.form['username']
            password = request.form['password']
            
            merchant_service = current_app.merchant_service
            
            try:
                merchant = merchant_service.authenticate(
                    username=username,
                    password=password
                )
                
                # Set session data
                session['merchant_id'] = merchant['id']
                session['merchant_name'] = merchant['name']
                session['logged_in'] = True
                session['login_time'] = datetime.utcnow().isoformat()
                
                logger.info(f"Successful login for merchant: {username}")
                return redirect(url_for('dashboard.index'))
                
            except AuthError as e:
                logger.warning(
                    f"Failed login attempt for {username}: {str(e)}",
                    extra={"error": str(e)}
                )
                return render_template(
                    'auth/login.html',
                    error="Invalid credentials"
                )
    
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    """Handle merchant logout."""
    merchant_id = session.get('merchant_id')
    session.clear()
    
    if merchant_id:
        logger.info(f"Merchant logged out: {merchant_id}")
    
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
@metrics_collector.track_request
def register():
    """Handle merchant registration."""
    if request.method == 'POST':
        with error_context("merchant_registration"):
            merchant_service = current_app.merchant_service
            
            try:
                merchant = merchant_service.register(
                    name=request.form['name'],
                    email=request.form['email'],
                    password=request.form['password']
                )
                
                logger.info(f"New merchant registered: {merchant['id']}")
                return redirect(url_for('auth.login'))
                
            except Exception as e:
                logger.error(
                    f"Registration failed: {str(e)}",
                    extra={"error": str(e)}
                )
                return render_template(
                    'auth/register.html',
                    error="Registration failed"
                )
    
    return render_template('auth/register.html') 