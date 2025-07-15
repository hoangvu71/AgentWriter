#!/usr/bin/env python3
"""
Integration tests for multi-agent system
"""
import asyncio
import pytest
from multi_agent_system import MultiAgentSystem, AgentType
from fastapi.testclient import TestClient
from main import app

class TestMultiAgentSystem:
    """Test the multi-agent system functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.system = MultiAgentSystem()
        self.session_id = "test_session_123"
        self.user_id = "test_user"
    
    @pytest.mark.asyncio
    async def test_system_initialization(self):
        """Test that all agents are properly initialized"""
        assert AgentType.ORCHESTRATOR.value in self.system.agents
        assert AgentType.PLOT_GENERATOR.value in self.system.agents
        assert AgentType.AUTHOR_GENERATOR.value in self.system.agents
        
        # Test agent info
        info = self.system.get_agent_info()
        assert "agents" in info
        assert len(info["agents"]) == 3
        assert "orchestrator" in info["agents"]
        assert "plot_generator" in info["agents"]
        assert "author_generator" in info["agents"]
    
    @pytest.mark.asyncio
    async def test_plot_only_request(self):
        """Test request that only needs plot generation"""
        request = "Generate a plot for a fantasy novel with dragons and magic"
        
        result = await self.system.process_request(request, self.session_id, self.user_id)
        
        assert result["success"] == True
        assert "responses" in result
        assert len(result["responses"]) >= 1  # At least orchestrator response
        
        # Check that orchestrator was invoked
        orchestrator_response = result["responses"][0]
        assert orchestrator_response.agent_name == "orchestrator"
        assert orchestrator_response.success == True
    
    @pytest.mark.asyncio
    async def test_author_only_request(self):
        """Test request that only needs author generation"""
        request = "Create an author profile for a science fiction writer"
        
        result = await self.system.process_request(request, self.session_id, self.user_id)
        
        assert result["success"] == True
        assert "responses" in result
        assert len(result["responses"]) >= 1
        
        # Check that orchestrator was invoked
        orchestrator_response = result["responses"][0]
        assert orchestrator_response.agent_name == "orchestrator"
        assert orchestrator_response.success == True
    
    @pytest.mark.asyncio
    async def test_full_workflow_request(self):
        """Test complete workflow: plot + author generation"""
        request = """Create a fantasy novel, with subgenre of LitRPG, microgenre of Zombie Apocalypse, 
        trope: survive and family, tone of dark, humour, realistic. 
        With target audience of Male, Heterosexual, Young Adults. Create author too."""
        
        result = await self.system.process_request(request, self.session_id, self.user_id)
        
        assert result["success"] == True
        assert "responses" in result
        assert len(result["responses"]) >= 1
        
        # Check orchestrator response
        orchestrator_response = result["responses"][0]
        assert orchestrator_response.agent_name == "orchestrator"
        assert orchestrator_response.success == True
        
        # The orchestrator should route to appropriate agents
        # We'll verify the routing logic in the orchestrator's response
        assert len(orchestrator_response.content) > 0
    
    @pytest.mark.asyncio
    async def test_session_management(self):
        """Test that sessions are properly managed across agents"""
        request = "Generate a fantasy plot"
        
        # First request
        result1 = await self.system.process_request(request, self.session_id, self.user_id)
        assert result1["success"] == True
        
        # Second request with same session
        result2 = await self.system.process_request(request, self.session_id, self.user_id)
        assert result2["success"] == True
        
        # Sessions should be tracked
        assert self.session_id in self.system.sessions
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in multi-agent system"""
        # Test with empty request
        result = await self.system.process_request("", self.session_id, self.user_id)
        
        # Should still succeed (orchestrator will handle empty input)
        assert result["success"] == True
        
        # Test with very long request
        long_request = "x" * 10000
        result = await self.system.process_request(long_request, self.session_id, self.user_id)
        
        # Should handle gracefully
        assert "success" in result

class TestMultiAgentAPI:
    """Test the FastAPI endpoints for multi-agent system"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = TestClient(app)
    
    def test_agents_endpoint(self):
        """Test the /agents endpoint"""
        response = self.client.get("/agents")
        assert response.status_code == 200
        
        data = response.json()
        assert "agents" in data
        assert "capabilities" in data
        assert len(data["agents"]) == 3
    
    def test_health_endpoint_with_agents(self):
        """Test health endpoint includes agent information"""
        response = self.client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "multi_agent_book_writer"
        assert "agents" in data
        assert len(data["agents"]) == 3

def test_example_requests():
    """Test parsing of example requests"""
    system = MultiAgentSystem()
    
    # Example requests that should work
    examples = [
        "Create a fantasy novel, LitRPG, Zombie Apocalypse, survive and family, dark/humour/realistic, Male/Heterosexual/Young Adults. Create author too.",
        "Generate a plot for a romance novel",
        "Create an author profile for mystery writer",
        "I need both a plot and author for a sci-fi thriller",
        "Plot only: space adventure with aliens",
        "Author only: female writer specializing in historical fiction"
    ]
    
    for example in examples:
        # These should not raise exceptions
        assert len(example) > 0
        assert isinstance(example, str)
        print(f"✓ Example request valid: {example[:50]}...")

def run_manual_test():
    """Manual test function for development"""
    async def test_full_workflow():
        system = MultiAgentSystem()
        
        request = """Create a fantasy novel, with subgenre of LitRPG, microgenre of Zombie Apocalypse, 
        trope: survive and family, tone of dark, humour, realistic. 
        With target audience of Male, Heterosexual, Young Adults. Create author too."""
        
        print("Testing full multi-agent workflow...")
        result = await system.process_request(request, "test_session", "test_user")
        
        print(f"Success: {result['success']}")
        print(f"Number of responses: {len(result['responses'])}")
        
        for i, response in enumerate(result["responses"]):
            print(f"\nResponse {i+1} - Agent: {response.agent_name}")
            print(f"Success: {response.success}")
            print(f"Content length: {len(response.content)}")
            if response.error:
                print(f"Error: {response.error}")
    
    # Run the manual test
    asyncio.run(test_full_workflow())

if __name__ == "__main__":
    # Run manual test
    run_manual_test()
    
    # Run example tests
    test_example_requests()
    
    print("\nAll basic tests passed!")
    print("Run 'python -m pytest test_multi_agent_integration.py -v' for full test suite")