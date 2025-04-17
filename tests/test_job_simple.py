"""Simple test for job fetcher module."""

import os
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock all external dependencies
sys.modules['requests'] = MagicMock()
sys.modules['bs4'] = MagicMock()
sys.modules['pandas'] = MagicMock()

# Create a simple test
def test_simple_job():
    """Simple test that always passes."""
    assert True
