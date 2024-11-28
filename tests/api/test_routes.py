from src.api.routes import auth, dashboard, payments, settings

def test_auth_routes_exist():
    """Test auth routes module exists"""
    assert auth is not None

def test_dashboard_routes_exist():
    """Test dashboard routes module exists"""
    assert dashboard is not None

def test_payments_routes_exist():
    """Test payments routes module exists"""
    assert payments is not None

def test_settings_routes_exist():
    """Test settings routes module exists"""
    assert settings is not None 