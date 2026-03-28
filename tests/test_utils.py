"""Tests for utils module."""

import pytest
from src.utils import example_function


def test_example_function():
    """Test example_function."""
    result = example_function()
    assert result == "This is an example utility function"
