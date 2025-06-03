"""
Example test file for the project.
"""

import pytest
from src import __version__


def test_version():
    """Test that version is defined."""
    assert __version__ == "0.1.0"


def test_example():
    """Example test case."""
    assert 1 + 1 == 2


class TestExample:
    """Example test class."""
    
    def test_example_method(self):
        """Example test method."""
        assert True 