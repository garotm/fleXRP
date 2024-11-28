import os
from src.core.config import Config
from src.core import error_handlers, exceptions, metrics, monitoring

def test_config_loading():
    """Test configuration loading"""
    config = Config()
    assert hasattr(config, 'XRPL_NODE')
    assert isinstance(config.XRPL_NODE, str)

def test_environment_variables():
    """Test environment variable handling"""
    test_node = "wss://s.altnet.rippletest.net:51233"
    os.environ['XRPL_NODE'] = test_node
    config = Config()
    assert config.XRPL_NODE == test_node 

def test_core_modules_exist():
    """Test core modules exist"""
    assert error_handlers is not None
    assert exceptions is not None
    assert metrics is not None
    assert monitoring is not None 