import pytest
import os
import sys

# Add src to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope="session")
def test_config():
    """Fixture for test configuration"""
    return {
        "XRPL_NODE": "wss://s.altnet.rippletest.net:51233",
        "DATABASE_URL": "sqlite:///test.db",
        "SECRET_KEY": "test_secret_key"
    } 