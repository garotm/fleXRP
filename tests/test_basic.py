def test_basic():
    """Basic test to verify pytest setup"""
    assert True

def test_project_structure():
    """Test basic project structure exists"""
    from src import app
    assert app is not None

def test_app_initialization():
    """Test that app can be initialized"""
    from src.app import app
    assert app is not None
