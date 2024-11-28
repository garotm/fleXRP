"""
Settings routes for the merchant interface.

This module handles merchant settings, preferences, and configuration
management.
"""

import logging
from typing import Dict, Any
from flask import (
    Blueprint, render_template, request, 
    redirect, url_for, current_app, session
)

from core.error_handlers import error_context
from core.metrics import metrics_collector
from core.exceptions import SettingsError
from .auth import login_required

logger = logging.getLogger(__name__)
bp = Blueprint('settings', __name__, url_prefix='/settings')

@bp.route('/', methods=['GET', 'POST'])
@login_required
@metrics_collector.track_request
def index() -> str:
    """
    Manage merchant settings.
    
    Returns:
        Rendered settings template
    """
    merchant_id = session['merchant_id']
    
    if request.method == 'POST':
        with error_context("settings_update"):
            try:
                _update_settings(merchant_id, request.form)
                return redirect(url_for('settings.index'))
                
            except Exception as e:
                logger.error(f"Settings update failed: {str(e)}")
                return render_template(
                    'settings/index.html',
                    error="Failed to update settings",
                    settings=_get_current_settings(merchant_id)
                )
    
    return render_template(
        'settings/index.html',
        settings=_get_current_settings(merchant_id)
    )

def _get_current_settings(merchant_id: str) -> Dict[str, Any]:
    """
    Get current merchant settings.
    
    Args:
        merchant_id: Merchant identifier
        
    Returns:
        Dictionary of current settings
        
    Raises:
        SettingsError: If settings fetch fails
    """
    try:
        return current_app.merchant_service.get_settings(merchant_id)
    except Exception as e:
        raise SettingsError(
            f"Failed to fetch settings: {str(e)}",
            details={'merchant_id': merchant_id}
        )

def _update_settings(merchant_id: str, form_data: Dict[str, Any]) -> None:
    """
    Update merchant settings.
    
    Args:
        merchant_id: Merchant identifier
        form_data: Form data containing new settings
        
    Raises:
        SettingsError: If settings update fails
    """
    try:
        settings = {
            'business_name': form_data.get('business_name'),
            'contact_email': form_data.get('contact_email'),
            'default_currency': form_data.get('default_currency'),
            'notification_preferences': {
                'email': form_data.get('notify_email') == 'on',
                'sms': form_data.get('notify_sms') == 'on',
                'webhook': form_data.get('notify_webhook') == 'on'
            },
            'webhook_url': form_data.get('webhook_url'),
            'settlement_preferences': {
                'auto_convert': form_data.get('auto_convert') == 'on',
                'settlement_currency': form_data.get('settlement_currency'),
                'minimum_settlement': float(form_data.get('minimum_settlement', 0))
            }
        }
        
        current_app.merchant_service.update_settings(
            merchant_id=merchant_id,
            settings=settings
        )
        
        logger.info(f"Settings updated for merchant: {merchant_id}")
        
    except Exception as e:
        raise SettingsError(
            f"Failed to update settings: {str(e)}",
            details={'merchant_id': merchant_id}
        )

@bp.route('/security', methods=['GET', 'POST'])
@login_required
@metrics_collector.track_request
def security_settings() -> str:
    """
    Manage security settings.
    
    Returns:
        Rendered security settings template
    """
    merchant_id = session['merchant_id']
    
    if request.method == 'POST':
        with error_context("security_settings_update"):
            try:
                _update_security_settings(merchant_id, request.form)
                return redirect(url_for('settings.security_settings'))
                
            except Exception as e:
                logger.error(f"Security settings update failed: {str(e)}")
                return render_template(
                    'settings/security.html',
                    error="Failed to update security settings",
                    settings=_get_security_settings(merchant_id)
                )
    
    return render_template(
        'settings/security.html',
        settings=_get_security_settings(merchant_id)
    )

def _get_security_settings(merchant_id: str) -> Dict[str, Any]:
    """Get current security settings."""
    try:
        return current_app.merchant_service.get_security_settings(merchant_id)
    except Exception as e:
        raise SettingsError(
            f"Failed to fetch security settings: {str(e)}",
            details={'merchant_id': merchant_id}
        )

def _update_security_settings(
    merchant_id: str,
    form_data: Dict[str, Any]
) -> None:
    """Update security settings."""
    try:
        settings = {
            'two_factor_enabled': form_data.get('2fa_enabled') == 'on',
            'ip_whitelist': form_data.get('ip_whitelist', '').split(','),
            'api_key_expiry': int(form_data.get('api_key_expiry', 30)),
            'password_expiry': int(form_data.get('password_expiry', 90)),
            'session_timeout': int(form_data.get('session_timeout', 60))
        }
        
        current_app.merchant_service.update_security_settings(
            merchant_id=merchant_id,
            settings=settings
        )
        
        logger.info(f"Security settings updated for merchant: {merchant_id}")
        
    except Exception as e:
        raise SettingsError(
            f"Failed to update security settings: {str(e)}",
            details={'merchant_id': merchant_id}
        ) 