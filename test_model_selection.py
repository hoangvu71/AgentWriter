#!/usr/bin/env python3
"""
Test script for model selection functionality
"""
import asyncio
from fastapi.testclient import TestClient
from main import app
from agent_service import BookWriterAgent

def test_model_endpoints():
    """Test the model selection API endpoints"""
    client = TestClient(app)
    
    print("Testing model selection endpoints...")
    
    # Test list models endpoint
    response = client.get("/models")
    assert response.status_code == 200
    data = response.json()
    assert "current_model" in data
    assert "available_models" in data
    assert len(data["available_models"]) > 0
    print(f"Found {len(data['available_models'])} available models")
    
    # Test get specific model info
    current_model = data["current_model"]
    response = client.get(f"/models/{current_model}")
    assert response.status_code == 200
    model_info = response.json()
    assert "model_id" in model_info
    assert "info" in model_info
    assert model_info["is_current"] == True
    print(f"Current model info retrieved: {current_model}")
    
    # Test switching to a different model
    available_models = list(data["available_models"].keys())
    if len(available_models) > 1:
        new_model = next(m for m in available_models if m != current_model)
        response = client.post(f"/models/{new_model}/switch")
        assert response.status_code == 200
        switch_data = response.json()
        assert switch_data["success"] == True
        assert switch_data["current_model"] == new_model
        print(f"Successfully switched to: {new_model}")
    
    # Test invalid model
    response = client.get("/models/invalid-model")
    assert response.status_code == 200
    error_data = response.json()
    assert "error" in error_data
    print("Invalid model handling works")
    
    print("All model endpoint tests passed!")

def test_agent_model_management():
    """Test the BookWriterAgent model management"""
    print("\nTesting BookWriterAgent model management...")
    
    # Test initialization with different models
    agent = BookWriterAgent(model="gemini-2.0-flash")
    assert agent.get_current_model() == "gemini-2.0-flash"
    print("OK Agent initialized with specified model")
    
    # Test available models
    models = agent.get_available_models()
    assert len(models) > 0
    assert "gemini-2.0-flash" in models
    print(f"OK Available models: {list(models.keys())}")
    
    # Test model info
    info = agent.get_model_info("gemini-2.0-flash")
    assert "name" in info
    assert "description" in info
    assert "capabilities" in info
    print("OK Model info retrieved successfully")
    
    # Test model switching
    available_models = list(models.keys())
    if len(available_models) > 1:
        new_model = next(m for m in available_models if m != "gemini-2.0-flash")
        success = agent.switch_model(new_model)
        assert success == True
        assert agent.get_current_model() == new_model
        print(f"OK Successfully switched from gemini-2.0-flash to {new_model}")
    
    # Test invalid model
    try:
        BookWriterAgent(model="invalid-model")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not supported" in str(e)
        print("OK Invalid model validation works")
    
    print("All agent model management tests passed!")

def test_model_descriptions():
    """Test model descriptions and capabilities"""
    print("\nTesting model descriptions...")
    
    agent = BookWriterAgent()
    models = agent.get_available_models()
    
    for model_id, info in models.items():
        print(f"\n{model_id}:")
        print(f"   Name: {info['name']}")
        print(f"   Description: {info['description']}")
        print(f"   Capabilities: {', '.join(info['capabilities'])}")
        print(f"   Best for: {info['best_for']}")
        
        # Validate required fields
        assert "name" in info
        assert "description" in info
        assert "capabilities" in info
        assert "best_for" in info
        assert isinstance(info["capabilities"], list)
    
    print("\nOK All model descriptions are properly formatted")

def main():
    """Run all model selection tests"""
    print("Running Model Selection Tests\n")
    
    test_model_endpoints()
    test_agent_model_management()
    test_model_descriptions()
    
    print("\nAll model selection tests passed!")
    print("\nAvailable Models Summary:")
    agent = BookWriterAgent()
    models = agent.get_available_models()
    for model_id, info in models.items():
        status = "CURRENT" if model_id == agent.get_current_model() else ""
        print(f"  - {info['name']} ({model_id}) {status}")

if __name__ == "__main__":
    main()