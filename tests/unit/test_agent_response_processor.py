"""
TDD Test Suite for AgentResponseProcessor class.

This module follows Test-Driven Development methodology:
1. RED: Write failing tests that define requirements
2. GREEN: Implement minimal code to make tests pass  
3. REFACTOR: Improve code while keeping tests green

Test Coverage:
- Response parsing and JSON extraction
- Content type handling
- Response validation
- Error handling for malformed responses
"""

import pytest
import sys
from unittest.mock import MagicMock, patch

# Mock Google dependencies before importing
mock_google_adk = MagicMock()
sys.modules['google.adk'] = mock_google_adk

from src.core.agent_modules.agent_response_processor import AgentResponseProcessor
from src.core.interfaces import ContentType


class TestAgentResponseProcessorInitialization:
    """Test AgentResponseProcessor initialization"""
    
    def test_response_processor_basic_initialization(self):
        """
        RED: Test basic AgentResponseProcessor initialization
        Should initialize with agent name and logger
        """
        # Arrange
        agent_name = "test_agent"
        
        # Act
        processor = AgentResponseProcessor(agent_name)
        
        # Assert
        assert processor.agent_name == agent_name
        assert processor.logger is not None
    
    def test_response_processor_with_different_agent_names(self):
        """
        RED: Test AgentResponseProcessor with different agent names
        Should handle various agent name patterns
        """
        # Arrange & Act
        plot_processor = AgentResponseProcessor("plot_generator")
        author_processor = AgentResponseProcessor("author_generator")
        orchestrator_processor = AgentResponseProcessor("orchestrator")
        
        # Assert
        assert plot_processor.agent_name == "plot_generator"
        assert author_processor.agent_name == "author_generator"
        assert orchestrator_processor.agent_name == "orchestrator"


class TestAgentResponseProcessorJSONParsing:
    """Test JSON parsing functionality"""
    
    def test_parse_response_with_valid_json(self):
        """
        RED: Test response parsing with valid JSON content
        Should extract JSON from agent response
        """
        # Arrange
        processor = AgentResponseProcessor("test_agent")
        content = 'Here is the result: {"title": "Test Plot", "genre": "Fantasy"}'
        
        # Mock JSON parser
        with patch('src.core.agent_modules.agent_response_processor.parse_llm_json') as mock_parser:
            expected_json = {"title": "Test Plot", "genre": "Fantasy"}
            mock_parser.return_value = expected_json
            
            # Act
            result = processor.parse_response(content)
            
            # Assert
            assert result == expected_json
            mock_parser.assert_called_once_with(content)
    
    def test_parse_response_with_no_json(self):
        """
        RED: Test response parsing with no JSON content
        Should return None when no JSON is found
        """
        # Arrange
        processor = AgentResponseProcessor("test_agent")
        content = "Plain text response with no JSON content"
        
        # Mock JSON parser to return None
        with patch('src.core.agent_modules.agent_response_processor.parse_llm_json') as mock_parser:
            mock_parser.return_value = None
            
            # Act
            result = processor.parse_response(content)
            
            # Assert
            assert result is None
            mock_parser.assert_called_once_with(content)
    
    def test_parse_response_with_complex_json(self):
        """
        RED: Test response parsing with complex nested JSON
        Should handle complex JSON structures
        """
        # Arrange
        processor = AgentResponseProcessor("test_agent")
        content = "Complex response with nested data"
        
        # Mock JSON parser with complex structure
        with patch('src.core.agent_modules.agent_response_processor.parse_llm_json') as mock_parser:
            expected_json = {
                "title": "Epic Fantasy",
                "plot": {
                    "beginning": "Hero's journey starts",
                    "middle": "Challenges arise",
                    "end": "Victory achieved"
                },
                "characters": ["Hero", "Villain", "Mentor"],
                "themes": ["heroism", "sacrifice", "redemption"]
            }
            mock_parser.return_value = expected_json
            
            # Act
            result = processor.parse_response(content)
            
            # Assert
            assert result == expected_json
            assert "plot" in result
            assert "characters" in result
            assert len(result["characters"]) == 3
    
    def test_parse_response_with_empty_content(self):
        """
        RED: Test response parsing with empty content
        Should handle empty content gracefully
        """
        # Arrange
        processor = AgentResponseProcessor("test_agent")
        content = ""
        
        # Mock JSON parser
        with patch('src.core.agent_modules.agent_response_processor.parse_llm_json') as mock_parser:
            mock_parser.return_value = None
            
            # Act
            result = processor.parse_response(content)
            
            # Assert
            assert result is None
            mock_parser.assert_called_once_with(content)


class TestAgentResponseProcessorContentType:
    """Test content type handling"""
    
    def test_get_content_type_for_plot_agent(self):
        """
        RED: Test content type for plot generator agent
        Should return PLOT content type for plot agents
        """
        # Arrange
        processor = AgentResponseProcessor("plot_generator")
        
        # Act
        content_type = processor.get_content_type()
        
        # Assert
        assert content_type == ContentType.PLOT
    
    def test_get_content_type_for_author_agent(self):
        """
        RED: Test content type for author generator agent
        Should return AUTHOR content type for author agents
        """
        # Arrange
        processor = AgentResponseProcessor("author_generator")
        
        # Act
        content_type = processor.get_content_type()
        
        # Assert
        assert content_type == ContentType.AUTHOR
    
    def test_get_content_type_for_world_building_agent(self):
        """
        RED: Test content type for world building agent
        Should return WORLD_BUILDING content type for world building agents
        """
        # Arrange
        processor = AgentResponseProcessor("world_building")
        
        # Act
        content_type = processor.get_content_type()
        
        # Assert
        assert content_type == ContentType.WORLD_BUILDING
    
    def test_get_content_type_for_characters_agent(self):
        """
        RED: Test content type for characters agent
        Should return CHARACTERS content type for characters agents
        """
        # Arrange
        processor = AgentResponseProcessor("characters")
        
        # Act
        content_type = processor.get_content_type()
        
        # Assert
        assert content_type == ContentType.CHARACTERS
    
    def test_get_content_type_for_unknown_agent(self):
        """
        RED: Test content type for unknown agent type
        Should return default PLOT content type for unknown agents
        """
        # Arrange
        processor = AgentResponseProcessor("unknown_agent")
        
        # Act
        content_type = processor.get_content_type()
        
        # Assert
        assert content_type == ContentType.PLOT  # Default fallback
    
    def test_get_content_type_for_orchestrator(self):
        """
        RED: Test content type for orchestrator agent
        Should return PLOT content type (default) for orchestrator
        """
        # Arrange
        processor = AgentResponseProcessor("orchestrator")
        
        # Act
        content_type = processor.get_content_type()
        
        # Assert
        assert content_type == ContentType.PLOT  # Default fallback


class TestAgentResponseProcessorValidation:
    """Test response validation functionality"""
    
    def test_validate_response_with_valid_content(self):
        """
        RED: Test response validation with valid content
        Should return True for non-empty content
        """
        # Arrange
        processor = AgentResponseProcessor("test_agent")
        content = "Valid response content"
        
        # Act
        is_valid = processor.validate_response(content)
        
        # Assert
        assert is_valid is True
    
    def test_validate_response_with_empty_content(self):
        """
        RED: Test response validation with empty content
        Should return False for empty content
        """
        # Arrange
        processor = AgentResponseProcessor("test_agent")
        content = ""
        
        # Act
        is_valid = processor.validate_response(content)
        
        # Assert
        assert is_valid is False
    
    def test_validate_response_with_whitespace_only(self):
        """
        RED: Test response validation with whitespace-only content
        Should return False for whitespace-only content
        """
        # Arrange
        processor = AgentResponseProcessor("test_agent")
        content = "   \n\t  "
        
        # Act
        is_valid = processor.validate_response(content)
        
        # Assert
        assert is_valid is False
    
    def test_validate_response_with_none_content(self):
        """
        RED: Test response validation with None content
        Should return False for None content
        """
        # Arrange
        processor = AgentResponseProcessor("test_agent")
        content = None
        
        # Act
        is_valid = processor.validate_response(content)
        
        # Assert
        assert is_valid is False
    
    def test_validate_response_with_minimal_content(self):
        """
        RED: Test response validation with minimal valid content
        Should return True for minimal but valid content
        """
        # Arrange
        processor = AgentResponseProcessor("test_agent")
        content = "ok"
        
        # Act
        is_valid = processor.validate_response(content)
        
        # Assert
        assert is_valid is True


class TestAgentResponseProcessorIntegration:
    """Integration tests for AgentResponseProcessor"""
    
    def test_full_response_processing_workflow(self):
        """
        RED: Test complete response processing workflow
        Should handle parsing, validation, and content type determination
        """
        # Arrange
        processor = AgentResponseProcessor("plot_generator")
        content = 'Plot generated successfully: {"title": "Epic Quest", "genre": "Fantasy", "summary": "A hero\'s journey"}'
        
        # Mock JSON parser
        with patch('src.core.agent_modules.agent_response_processor.parse_llm_json') as mock_parser:
            expected_json = {
                "title": "Epic Quest",
                "genre": "Fantasy", 
                "summary": "A hero's journey"
            }
            mock_parser.return_value = expected_json
            
            # Act
            is_valid = processor.validate_response(content)
            parsed_json = processor.parse_response(content)
            content_type = processor.get_content_type()
            
            # Assert
            assert is_valid is True
            assert parsed_json == expected_json
            assert content_type == ContentType.PLOT
            assert parsed_json["title"] == "Epic Quest"
            assert parsed_json["genre"] == "Fantasy"
    
    def test_error_handling_workflow(self):
        """
        RED: Test error handling in response processing
        Should handle various error conditions gracefully
        """
        # Arrange
        processor = AgentResponseProcessor("test_agent")
        
        # Test invalid content
        assert processor.validate_response("") is False
        assert processor.validate_response(None) is False
        
        # Test failed JSON parsing
        with patch('src.core.agent_modules.agent_response_processor.parse_llm_json') as mock_parser:
            mock_parser.return_value = None
            result = processor.parse_response("Invalid JSON content")
            assert result is None
        
        # Content type should still work
        content_type = processor.get_content_type()
        assert content_type == ContentType.PLOT  # Default fallback
    
    def test_mixed_content_scenarios(self):
        """
        RED: Test processing of mixed content scenarios
        Should handle various real-world response patterns
        """
        # Arrange
        processor = AgentResponseProcessor("author_generator")
        
        # Test scenario 1: Response with explanation and JSON
        content1 = "I've created an author profile for you: {\"name\": \"J.R.R. Tolkien\", \"genre\": \"Fantasy\"}"
        
        # Test scenario 2: Response with only text
        content2 = "Author profile created successfully but no structured data available."
        
        # Test scenario 3: Response with malformed JSON
        content3 = "Here's the author: {name: 'Invalid JSON'}"
        
        with patch('src.core.agent_modules.agent_response_processor.parse_llm_json') as mock_parser:
            # Mock different return values for different content
            mock_parser.side_effect = [
                {"name": "J.R.R. Tolkien", "genre": "Fantasy"},  # Valid JSON
                None,  # No JSON found
                None   # Malformed JSON
            ]
            
            # Act & Assert
            # Scenario 1: Valid content with JSON
            assert processor.validate_response(content1) is True
            result1 = processor.parse_response(content1)
            assert result1 is not None
            assert result1["name"] == "J.R.R. Tolkien"
            
            # Scenario 2: Valid content, no JSON
            assert processor.validate_response(content2) is True
            result2 = processor.parse_response(content2)
            assert result2 is None
            
            # Scenario 3: Valid content, malformed JSON
            assert processor.validate_response(content3) is True
            result3 = processor.parse_response(content3)
            assert result3 is None
            
            # Content type should be consistent
            assert processor.get_content_type() == ContentType.AUTHOR