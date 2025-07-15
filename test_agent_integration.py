import pytest
import asyncio
import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.runners import InMemoryRunner
from google.genai import types

# Load environment variables
load_dotenv()


class TestADKAgentIntegration:
    """Integration tests for Google ADK Agent with search capability"""
    
    def test_agent_initialization(self):
        """Test that we can initialize an ADK agent with search tool"""
        # Arrange & Act
        agent = Agent(
            name="search_assistant",
            model="gemini-2.0-flash",
            instruction="You are a helpful assistant. Answer user questions using Google Search when needed.",
            description="An assistant that can search the web.",
            tools=[google_search]
        )
        
        # Assert
        assert agent.name == "search_assistant"
        assert agent.model == "gemini-2.0-flash"
        assert google_search in agent.tools
        assert agent.description == "An assistant that can search the web."
    
    @pytest.mark.asyncio
    async def test_agent_search_functionality(self):
        """Test that agent can perform web search"""
        # Arrange
        agent = Agent(
            name="search_assistant",
            model="gemini-2.0-flash",
            instruction="Search for the requested information and provide a concise answer.",
            tools=[google_search]
        )
        runner = InMemoryRunner(agent, app_name="test_app")
        
        # Create session first
        session = await runner.session_service.create_session(
            app_name="test_app",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Create message
        content = types.Content(role='user', parts=[types.Part(text="What is the capital of France?")])
        
        # Act
        response = ""
        async for event in runner.run_async(
            user_id="test_user",
            session_id="test_session",
            new_message=content
        ):
            if hasattr(event, 'content') and event.content:
                response += str(event.content)
        
        # Assert
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        # Should contain reference to Paris
        assert "Paris" in response or "paris" in response.lower()
    
    @pytest.mark.asyncio
    async def test_agent_with_memory(self):
        """Test that agent can maintain conversation memory"""
        # Arrange
        agent = Agent(
            name="search_assistant",
            model="gemini-2.0-flash",
            instruction="You are a helpful assistant with memory of our conversation.",
            tools=[google_search]
        )
        runner = InMemoryRunner(agent)
        
        # Act - First interaction
        response1 = await runner.run_async("My name is TestUser")
        
        # Act - Second interaction referencing first
        response2 = await runner.run_async("What is my name?")
        
        # Assert
        assert "TestUser" in response2
    
    @pytest.mark.asyncio
    async def test_agent_planning_capability(self):
        """Test that agent can plan multi-step tasks"""
        # Arrange
        agent = Agent(
            name="planning_assistant",
            model="gemini-2.0-flash",
            instruction="""You are a planning assistant. When given a complex task:
            1. Break it down into steps
            2. Execute each step
            3. Provide a structured response""",
            tools=[google_search]
        )
        runner = InMemoryRunner(agent)
        
        # Act
        response = await runner.run_async(
            "Find the population of Tokyo and compare it to New York City"
        )
        
        # Assert
        assert response is not None
        # Should contain information about both cities
        assert "Tokyo" in response
        assert "New York" in response
        # Should contain population numbers
        assert any(char.isdigit() for char in response)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])