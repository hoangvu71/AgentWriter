"""
Playwright configuration for AgentWriter E2E testing.
Integrates with MCP Playwright for comprehensive browser automation.
"""

import os
from typing import Dict, Any

# Playwright configuration for AgentWriter E2E tests
PLAYWRIGHT_CONFIG: Dict[str, Any] = {
    # Base URL for testing
    "base_url": os.getenv("E2E_BASE_URL", "http://localhost:8000"),
    
    # Browser configuration
    "browsers": ["chromium", "firefox", "webkit"],
    "headless": True,
    "viewport": {"width": 1280, "height": 720},
    
    # Test settings
    "timeout": 30000,  # 30 seconds
    "expect_timeout": 5000,  # 5 seconds
    "action_timeout": 10000,  # 10 seconds
    
    # Screenshots and videos
    "screenshot": "only-on-failure",
    "video": "retain-on-failure",
    "trace": "retain-on-failure",
    
    # Test directories
    "test_dir": "tests/e2e",
    "output_dir": "test-results",
    
    # Parallel execution
    "workers": 2,
    "max_failures": 5,
    
    # Test environments
    "environments": {
        "local": {
            "base_url": "http://localhost:8000",
            "websocket_url": "ws://localhost:8000/ws",
            "openwebui_url": "http://localhost:3000"
        },
        "ci": {
            "base_url": "http://localhost:8000", 
            "websocket_url": "ws://localhost:8000/ws",
            "openwebui_url": "http://localhost:3000"
        }
    }
}

# Test data configurations
TEST_DATA = {
    "sample_book_request": {
        "title": "Test Adventure Novel",
        "genre": "Fantasy",
        "description": "A test book about magical adventures",
        "chapters": 5
    },
    
    "sample_plot_request": {
        "genre": "Science Fiction",
        "theme": "AI and humanity",
        "length": "short story"
    },
    
    "sample_character": {
        "name": "Test Hero",
        "age": 25,
        "background": "A brave adventurer from a small village"
    },
    
    "sample_world": {
        "name": "Test Realm",
        "setting": "Medieval fantasy world with magic",
        "key_locations": ["Castle of Light", "Dark Forest", "Ancient Library"]
    }
}

# Page selectors for UI testing
SELECTORS = {
    # Main application
    "chat_input": "[data-testid='chat-input']",
    "send_button": "[data-testid='send-button']",
    "message_list": "[data-testid='message-list']",
    "loading_indicator": "[data-testid='loading']",
    
    # Navigation
    "nav_plots": "[data-testid='nav-plots']",
    "nav_characters": "[data-testid='nav-characters']", 
    "nav_worlds": "[data-testid='nav-worlds']",
    "nav_books": "[data-testid='nav-books']",
    
    # Forms
    "plot_form": "[data-testid='plot-form']",
    "character_form": "[data-testid='character-form']",
    "world_form": "[data-testid='world-form']",
    
    # Results
    "plot_result": "[data-testid='plot-result']",
    "character_result": "[data-testid='character-result']",
    "world_result": "[data-testid='world-result']",
    
    # Open-WebUI specific
    "openwebui_chat": ".chat-container",
    "openwebui_input": "input[placeholder*='message']",
    "openwebui_send": "button[type='submit']"
}

# WebSocket test messages
WEBSOCKET_MESSAGES = {
    "test_connection": {
        "type": "ping",
        "session_id": "test-session"
    },
    
    "plot_generation": {
        "type": "agent_request",
        "agent_type": "plot_generator",
        "content": "Create a fantasy plot about a magical quest",
        "session_id": "test-session"
    },
    
    "character_creation": {
        "type": "agent_request",
        "agent_type": "characters",
        "content": "Create a brave warrior character",
        "session_id": "test-session"
    }
}

# Expected response patterns
EXPECTED_RESPONSES = {
    "plot_keywords": ["plot", "story", "character", "setting", "conflict"],
    "character_keywords": ["name", "age", "background", "personality", "skills"],
    "world_keywords": ["world", "location", "history", "culture", "geography"]
}

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "page_load_time": 3000,  # 3 seconds
    "api_response_time": 5000,  # 5 seconds
    "websocket_connection_time": 2000,  # 2 seconds
    "agent_response_time": 30000  # 30 seconds for AI generation
}

# Utility functions for test configuration
def get_environment_config(env_name: str = "local") -> Dict[str, Any]:
    """Get configuration for specific environment."""
    return PLAYWRIGHT_CONFIG["environments"].get(env_name, PLAYWRIGHT_CONFIG["environments"]["local"])

def get_test_data(data_type: str) -> Dict[str, Any]:
    """Get test data by type."""
    return TEST_DATA.get(data_type, {})

def get_selector(element: str) -> str:
    """Get CSS selector for UI element."""
    return SELECTORS.get(element, f"[data-testid='{element}']")

def get_websocket_message(message_type: str) -> Dict[str, Any]:
    """Get WebSocket test message by type."""
    return WEBSOCKET_MESSAGES.get(message_type, {})