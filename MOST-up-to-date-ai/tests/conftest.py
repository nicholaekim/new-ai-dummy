"""Pytest configuration and fixtures for tests."""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment variables for testing
os.environ['ENV'] = 'test'
os.environ['LOG_LEVEL'] = 'WARNING'


# Add any additional fixtures below this line
