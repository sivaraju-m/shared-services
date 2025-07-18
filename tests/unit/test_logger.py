import pytest
from shared_services.utils.logger import get_logger

def test_get_logger():
    logger = get_logger("test_logger")
    assert logger is not None
    assert logger.name == "test_logger"
