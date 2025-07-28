"""
Intentional test failures to demonstrate PR reviewer agent capabilities.
"""

import pytest
from src.core.base_agent import BaseAgent


def test_import_error():
    """This test will fail due to import error in base_agent.py"""
    try:
        agent = BaseAgent("test", "test description")
        assert False, "Should have failed due to import error"
    except ImportError as e:
        # This is expected - the import error should occur
        pass


def test_syntax_error():
    """This test will fail due to syntax error in base_agent.py"""
    # This test can't even run due to syntax error during import
    assert True


def test_intentional_assertion_failure():
    """This test will fail with an assertion error"""
    assert 1 == 2, "Intentional assertion failure for demo purposes"


def test_missing_dependency():
    """This test will fail due to missing dependency"""
    from nonexistent_module import FakeClass
    fake = FakeClass()
    assert fake is not None


def test_type_error():
    """This test will fail with a type error"""
    result = "string" + 42  # TypeError: can't concatenate str and int
    assert result is not None