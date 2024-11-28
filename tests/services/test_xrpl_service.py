import pytest
from src.services.xrpl_service import XRPLService
from xrpl.clients import JsonRpcClient
from src.services import payment_monitor, rate_service, wallet_service

def test_xrpl_service_initialization():
    """Test XRPL service initialization"""
    service = XRPLService()
    assert isinstance(service.client, JsonRpcClient)
    assert service.client.url.startswith('wss://')

@pytest.mark.asyncio
async def test_get_account_info():
    """Test getting account information"""
    service = XRPLService()
    test_account = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"  # Testnet genesis account
    account_info = await service.get_account_info(test_account)
    assert isinstance(account_info, dict)
    assert "account_data" in account_info 

def test_payment_monitor_exists():
    """Test payment monitor service exists"""
    assert payment_monitor is not None

def test_rate_service_exists():
    """Test rate service exists"""
    assert rate_service is not None

def test_wallet_service_exists():
    """Test wallet service exists"""
    assert wallet_service is not None 