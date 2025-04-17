"""Configuration for pytest."""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow imports from the jobhuntgpt package
sys.path.insert(0, str(Path(__file__).parent.parent))
