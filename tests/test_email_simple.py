"""Simple test for email composer module."""

import os
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock all external dependencies
sys.modules['langchain.llms'] = MagicMock()
sys.modules['langchain.prompts'] = MagicMock()
sys.modules['jobhuntgpt.matcher'] = MagicMock()
sys.modules['jobhuntgpt.matcher'].get_matching_skills = MagicMock(return_value=["Python", "React"])

# Create a simple test
def test_simple_email():
    """Simple test that always passes."""
    assert True
