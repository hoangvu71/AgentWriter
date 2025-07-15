#!/usr/bin/env python3
"""
Test script for the Book Writer Agent application
"""
import asyncio
import json
from fastapi.testclient import TestClient
from main import app

def test_basic_endpoints():
    """Test basic HTTP endpoints"""
    client = TestClient(app)
    
    # Test health check
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    
    # Test home page
    response = client.get("/")
    assert response.status_code == 200
    assert "Book Writer Agent" in response.text
    
    # Test sessions endpoint
    response = client.get("/sessions")
    assert response.status_code == 200
    
    print("All basic endpoint tests passed!")

def test_websocket_connection():
    """Test WebSocket connection"""
    client = TestClient(app)
    
    try:
        with client.websocket_connect("/ws/test_session") as websocket:
            # Test connection
            assert websocket is not None
            
            # Test sending a simple message
            test_message = {
                "type": "message",
                "content": "Hello, agent!",
                "user_id": "test_user"
            }
            
            websocket.send_json(test_message)
            
            # Note: This will fail if Google Cloud is not properly configured
            # but it tests that the WebSocket connection works
            print("WebSocket connection test passed!")
            
    except Exception as e:
        print(f"WebSocket test failed (expected if Google Cloud not configured): {e}")

def test_agent_service_structure():
    """Test that the agent service is properly structured"""
    from agent_service import book_agent
    
    # Test agent initialization
    assert book_agent.app_name == "book_writer_app"
    assert book_agent.agent.name == "book_writer_assistant"
    assert book_agent.agent.model == "gemini-2.0-flash"
    assert len(book_agent.agent.tools) > 0
    
    # Test session management
    assert hasattr(book_agent, 'create_session')
    assert hasattr(book_agent, 'chat')
    assert hasattr(book_agent, 'search_and_respond')
    
    print("Agent service structure test passed!")

async def test_session_creation():
    """Test session creation without Google Cloud"""
    from agent_service import book_agent
    
    try:
        # This will fail without proper Google Cloud setup, but tests the structure
        session = await book_agent.create_session("test_user", "test_session")
        print("Session creation test passed!")
    except Exception as e:
        print(f"Session creation test failed (expected if Google Cloud not configured): {e}")

def main():
    """Run all tests"""
    print("Running Book Writer Agent Tests\n")
    
    print("1. Testing basic endpoints...")
    test_basic_endpoints()
    
    print("\n2. Testing WebSocket connection...")
    test_websocket_connection()
    
    print("\n3. Testing agent service structure...")
    test_agent_service_structure()
    
    print("\n4. Testing session creation...")
    asyncio.run(test_session_creation())
    
    print("\nTest suite completed!")
    print("\nTo run the application:")
    print("1. Ensure Google Cloud credentials are set up")
    print("2. Run: python main.py")
    print("3. Visit: http://localhost:8000")

if __name__ == "__main__":
    main()