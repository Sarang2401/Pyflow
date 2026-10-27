"""
pytest configuration and shared fixtures.
Ensures log handlers are properly closed after each test to prevent
Windows file-lock errors (PermissionError: [WinError 32]) when
TemporaryDirectory cleanup tries to delete open log files.
"""

import logging
import pytest


@pytest.fixture(autouse=True)
def close_log_handlers_after_test():
    """
    Close and remove all root logging handlers after every test.

    Without this, ETLPipeline.__init__() opens a RotatingFileHandler
    pointing at a temp-dir log file. On Windows, open file handles block
    deletion, causing PermissionError when TemporaryDirectory.__exit__()
    tries to clean up.
    """
    yield  # let the test run

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
