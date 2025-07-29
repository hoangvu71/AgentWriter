"""
Test for Issue #32: Critical AI orchestrator failure with `__name__` AttributeError

This test reproduces the exact error scenario described in the GitHub issue.
"""

import os
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.core.agent_modules.agent_error_handler import AgentErrorHandler
from src.agents.orchestrator import OrchestratorAgent
from src.core.interfaces import AgentRequest
from src.core.configuration import Configuration


class TestIssue32NameAttributeError:
    """Test suite for Issue #32: `__name__` AttributeError in orchestrator"""
    
    def setup_method(self):
        """Set up test environment"""
        self.agent_name = "test_orchestrator"
        self.error_handler = AgentErrorHandler(self.agent_name)
    
    def test_error_handler_str_conversion_with_malformed_exception(self):
        """Test that error handler can handle exceptions without proper string representation"""
        # Create a malformed exception object that doesn't have proper __name__ or __str__
        class MalformedException(Exception):
            def __str__(self):
                # This simulates an exception where accessing __name__ fails
                return getattr(self, '__name__', 'undefined_attribute')
        
        malformed_error = MalformedException("test error")
        
        # This should not raise an AttributeError for __name__
        result = self.error_handler.handle_vertex_ai_error(malformed_error)
        
        # Should return a proper error message without crashing
        assert "Error generating response:" in result
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_error_handler_with_none_error(self):
        """Test error handler with None error object"""
        result = self.error_handler.handle_vertex_ai_error(None)
        
        assert "Error generating response:" in result
        assert "Unknown error" in result
    
    def test_error_handler_with_object_without_str_method(self):
        """Test error handler with object that has broken __str__ method"""
        class BrokenStrException(Exception):
            def __str__(self):
                raise AttributeError("__name__")
        
        broken_error = BrokenStrException()
        
        # Should handle the broken __str__ gracefully
        result = self.error_handler.handle_vertex_ai_error(broken_error)
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Should not contain "__name__" as the error message
        assert "__name__" not in result
    
    def test_orchestrator_error_handling_integration(self):
        """Test that the orchestrator handles malformed exceptions properly via error handler"""
        
        # This is a simplified integration test focusing on the error handler fix
        error_handler = AgentErrorHandler("orchestrator")
        
        # Simulate the exact error scenario that occurs in the orchestrator
        class ProblematicError:
            def __str__(self):
                raise AttributeError("__name__")
        
        error = ProblematicError()
        
        # This should now work without returning "__name__"
        result = error_handler.handle_vertex_ai_error(error)
        
        # Verify the fix
        assert isinstance(result, str)
        assert len(result) > 0
        assert result != "__name__"
        assert "Error generating response:" in result
        # The message should contain a meaningful fallback, not just "__name__"
        # The error handler may use different fallback strategies
        assert ("ProblematicError error" in result or 
                "Error object could not be converted to string" in result or
                "An error occurred but details could not be extracted safely" in result)
    
    def test_improved_error_handler_str_conversion(self):
        """Test the improved error handler that should fix the __name__ issue"""
        
        # Test various problematic error objects
        test_cases = [
            None,
            Exception("normal exception"),
            ValueError("value error"),
            AttributeError("__name__"),  # This is the specific case causing issues
            RuntimeError(),  # Exception without message
        ]
        
        for error in test_cases:
            result = self.error_handler.handle_vertex_ai_error(error)
            
            # Should always return a valid string
            assert isinstance(result, str)
            assert len(result) > 0
            
            # Should not return just "__name__" 
            assert result != "__name__"
            
            # Should contain meaningful error message
            assert "Error generating response:" in result
    
    def test_error_handler_logging_with_malformed_exception(self):
        """Test that error handler logs properly even with malformed exceptions"""
        
        class MalformedException(Exception):
            def __str__(self):
                raise AttributeError("__name__")
        
        error = MalformedException()
        
        # Mock the logger to capture log calls
        with patch.object(self.error_handler, 'logger') as mock_logger:
            result = self.error_handler.handle_vertex_ai_error(error)
            
            # Should have attempted to log the error
            assert mock_logger.error.called
            
            # Should return a meaningful result
            assert isinstance(result, str)
            assert "__name__" not in result