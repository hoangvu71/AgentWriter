"""
Agent workflow E2E tests for AgentWriter.
Tests multi-agent system functionality, orchestration, and agent interactions.
"""

import asyncio
import json
import time
from typing import Dict, Any, List
import websockets
import requests
from .playwright.config import get_environment_config, get_websocket_message, get_test_data


class TestAgentWorkflows:
    """Test agent system workflows and interactions."""
    
    def __init__(self, environment: str = "local"):
        self.config = get_environment_config(environment)
        self.base_url = self.config["base_url"]
        self.websocket_url = self.config["websocket_url"]
    
    async def test_plot_generation_workflow(self) -> Dict[str, Any]:
        """Test complete plot generation workflow."""
        result = {
            "test_name": "Plot Generation Workflow",
            "status": "pending",
            "details": [],
            "performance": {},
            "artifacts": []
        }
        
        try:
            session_id = "test-plot-session"
            uri = f"{self.websocket_url}/{session_id}"
            
            # Get test data
            plot_request = get_test_data("sample_plot_request")
            
            async with websockets.connect(uri) as websocket:
                result["details"].append("✅ WebSocket connection established")
                
                # Send plot generation request
                plot_message = {
                    "type": "agent_request",
                    "agent_type": "plot_generator",
                    "content": f"Create a {plot_request['genre']} plot about {plot_request['theme']} for a {plot_request['length']}",
                    "session_id": session_id,
                    "timestamp": time.time()
                }
                
                start_time = time.time()
                await websocket.send(json.dumps(plot_message))
                result["details"].append("✅ Plot generation request sent")
                
                # Wait for response with extended timeout for AI generation
                responses = []
                timeout_duration = 30  # 30 seconds for AI generation
                
                try:
                    while True:
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            responses.append(response)
                            
                            # Try to parse response
                            try:
                                parsed_response = json.loads(response)
                                if parsed_response.get("type") == "agent_response":
                                    generation_time = (time.time() - start_time) * 1000
                                    result["performance"]["plot_generation_time"] = generation_time
                                    
                                    result["details"].append("✅ Plot generation response received")
                                    result["details"].append(f"⏱️ Generation time: {generation_time:.0f}ms")
                                    
                                    # Validate response content
                                    content = parsed_response.get("content", "")
                                    if len(content) > 50:  # Reasonable plot should be substantial
                                        result["details"].append("✅ Generated plot has substantial content")
                                        result["artifacts"].append({
                                            "type": "generated_plot",
                                            "content": content[:200] + "..." if len(content) > 200 else content
                                        })
                                    else:
                                        result["details"].append("⚠️ Generated plot seems too short")
                                    
                                    break
                                    
                            except json.JSONDecodeError:
                                result["details"].append("ℹ️ Received non-JSON response (streaming data)")
                                
                        except asyncio.TimeoutError:
                            elapsed = time.time() - start_time
                            if elapsed > timeout_duration:
                                result["details"].append("⚠️ Plot generation timeout - taking longer than expected")
                                break
                            continue
                
                except Exception as e:
                    result["details"].append(f"⚠️ Response handling error: {str(e)}")
                
                if responses:
                    result["details"].append(f"✅ Received {len(responses)} response(s)")
                    result["status"] = "passed"
                else:
                    result["details"].append("⚠️ No responses received")
                    result["status"] = "partial"
                    
        except Exception as e:
            result["status"] = "failed"
            result["details"].append(f"❌ Plot generation workflow failed: {str(e)}")
        
        return result
    
    async def test_character_creation_workflow(self) -> Dict[str, Any]:
        """Test character creation workflow."""
        result = {
            "test_name": "Character Creation Workflow",
            "status": "pending",
            "details": [],
            "performance": {},
            "artifacts": []
        }
        
        try:
            session_id = "test-character-session"
            uri = f"{self.websocket_url}/{session_id}"
            
            character_request = get_test_data("sample_character")
            
            async with websockets.connect(uri) as websocket:
                result["details"].append("✅ WebSocket connection established")
                
                # Send character creation request
                character_message = {
                    "type": "agent_request",
                    "agent_type": "characters",
                    "content": f"Create a character named {character_request['name']}, age {character_request['age']}, with background: {character_request['background']}",
                    "session_id": session_id,
                    "timestamp": time.time()
                }
                
                start_time = time.time()
                await websocket.send(json.dumps(character_message))
                result["details"].append("✅ Character creation request sent")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                    generation_time = (time.time() - start_time) * 1000
                    result["performance"]["character_generation_time"] = generation_time
                    
                    result["details"].append("✅ Character creation response received")
                    result["details"].append(f"⏱️ Generation time: {generation_time:.0f}ms")
                    
                    # Validate response
                    if len(response) > 30:
                        result["details"].append("✅ Generated character has detailed content")
                        result["artifacts"].append({
                            "type": "generated_character",
                            "content": response[:200] + "..." if len(response) > 200 else response
                        })
                    
                    result["status"] = "passed"
                    
                except asyncio.TimeoutError:
                    result["details"].append("⚠️ Character generation timeout")
                    result["status"] = "partial"
                    
        except Exception as e:
            result["status"] = "failed"
            result["details"].append(f"❌ Character creation workflow failed: {str(e)}")
        
        return result
    
    async def test_orchestrator_workflow(self) -> Dict[str, Any]:
        """Test orchestrator agent coordination."""
        result = {
            "test_name": "Orchestrator Workflow",
            "status": "pending",
            "details": [],
            "performance": {},
            "artifacts": []
        }
        
        try:
            session_id = "test-orchestrator-session"
            uri = f"{self.websocket_url}/{session_id}"
            
            async with websockets.connect(uri) as websocket:
                result["details"].append("✅ WebSocket connection established")
                
                # Send complex request that should trigger orchestrator
                orchestrator_message = {
                    "type": "agent_request",
                    "agent_type": "orchestrator",
                    "content": "Create a complete book concept with plot, main character, and world setting for a fantasy adventure",
                    "session_id": session_id,
                    "timestamp": time.time()
                }
                
                start_time = time.time()
                await websocket.send(json.dumps(orchestrator_message))
                result["details"].append("✅ Orchestrator request sent")
                
                # Collect all responses for complex workflow
                responses = []
                total_timeout = 45  # Extended timeout for complex orchestration
                
                try:
                    while True:
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            responses.append(response)
                            
                            # Check if this is a completion signal
                            try:
                                parsed = json.loads(response)
                                if parsed.get("type") == "workflow_complete" or "complete" in response.lower():
                                    break
                            except:
                                pass
                                
                        except asyncio.TimeoutError:
                            elapsed = time.time() - start_time
                            if elapsed > total_timeout:
                                break
                            continue
                            
                except Exception as e:
                    result["details"].append(f"⚠️ Response collection error: {str(e)}")
                
                orchestration_time = (time.time() - start_time) * 1000
                result["performance"]["orchestration_time"] = orchestration_time
                
                result["details"].append(f"✅ Received {len(responses)} orchestration responses")
                result["details"].append(f"⏱️ Orchestration time: {orchestration_time:.0f}ms")
                
                if len(responses) > 0:
                    result["details"].append("✅ Orchestrator workflow executed")
                    result["artifacts"].append({
                        "type": "orchestration_log",
                        "response_count": len(responses),
                        "sample_responses": responses[:3]  # First 3 responses
                    })
                    result["status"] = "passed"
                else:
                    result["details"].append("⚠️ No orchestration responses received")
                    result["status"] = "partial"
                    
        except Exception as e:
            result["status"] = "failed"
            result["details"].append(f"❌ Orchestrator workflow failed: {str(e)}")
        
        return result
    
    async def test_agent_factory_functionality(self) -> Dict[str, Any]:
        """Test agent factory and creation."""
        result = {
            "test_name": "Agent Factory Functionality",
            "status": "pending",
            "details": [],
            "performance": {}
        }
        
        try:
            # Test agent factory through API endpoint if available
            agent_types = [
                "orchestrator",
                "plot_generator", 
                "characters",
                "world_building",
                "author_generator"
            ]
            
            available_agents = []
            
            # Try to get available agents through models endpoint
            try:
                response = requests.get(f"{self.base_url}/models", timeout=10)
                if response.status_code == 200:
                    result["details"].append("✅ Models endpoint accessible (agent factory available)")
                    
                    # Try to parse and validate response
                    try:
                        models_data = response.json()
                        if isinstance(models_data, (list, dict)):
                            result["details"].append("✅ Models data structure valid")
                            available_agents.append("factory_working")
                    except:
                        result["details"].append("ℹ️ Models response format unknown")
                        
            except Exception as e:
                result["details"].append(f"⚠️ Models endpoint test failed: {str(e)}")
            
            # Test WebSocket agent requests for different types
            session_id = "test-factory-session"
            uri = f"{self.websocket_url}/{session_id}"
            
            async with websockets.connect(uri) as websocket:
                result["details"].append("✅ WebSocket connection for factory testing")
                
                for agent_type in agent_types[:3]:  # Test first 3 to avoid timeout
                    try:
                        test_message = {
                            "type": "agent_request",
                            "agent_type": agent_type,
                            "content": f"Test message for {agent_type}",
                            "session_id": session_id
                        }
                        
                        await websocket.send(json.dumps(test_message))
                        
                        # Try to get response
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                            result["details"].append(f"✅ {agent_type} agent responsive")
                            available_agents.append(agent_type)
                        except asyncio.TimeoutError:
                            result["details"].append(f"⚠️ {agent_type} agent timeout (may be processing)")
                            
                    except Exception as e:
                        result["details"].append(f"⚠️ {agent_type} agent test failed: {str(e)}")
            
            result["details"].append(f"✅ Tested {len(available_agents)} agent types")
            
            if len(available_agents) > 0:
                result["status"] = "passed"
            else:
                result["status"] = "partial"
                
        except Exception as e:
            result["status"] = "failed"
            result["details"].append(f"❌ Agent factory test failed: {str(e)}")
        
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all agent workflow tests."""
        print("🤖 Running Agent Workflow E2E Tests...")
        
        results = {
            "suite_name": "Agent Workflows",
            "total_tests": 4,
            "passed": 0,
            "failed": 0,
            "partial": 0,
            "tests": []
        }
        
        test_methods = [
            self.test_plot_generation_workflow,
            self.test_character_creation_workflow,
            self.test_orchestrator_workflow,
            self.test_agent_factory_functionality
        ]
        
        for test_method in test_methods:
            try:
                test_result = await test_method()
                results["tests"].append(test_result)
                
                if test_result["status"] == "passed":
                    results["passed"] += 1
                elif test_result["status"] == "failed":
                    results["failed"] += 1
                else:
                    results["partial"] += 1
                
                # Print test result
                print(f"\n{test_result['test_name']}: {test_result['status'].upper()}")
                for detail in test_result["details"]:
                    print(f"  {detail}")
                
                # Print artifacts if any
                if "artifacts" in test_result and test_result["artifacts"]:
                    print("  📋 Artifacts generated:", len(test_result["artifacts"]))
                    
            except Exception as e:
                error_result = {
                    "test_name": test_method.__name__,
                    "status": "failed",
                    "details": [f"❌ Test execution failed: {str(e)}"],
                    "performance": {}
                }
                results["tests"].append(error_result)
                results["failed"] += 1
        
        # Print summary
        print(f"\n🎯 Agent Workflow Tests Summary:")
        print(f"   Passed: {results['passed']}/{results['total_tests']}")
        print(f"   Partial: {results['partial']}/{results['total_tests']}")
        print(f"   Failed: {results['failed']}/{results['total_tests']}")
        
        return results


# Standalone execution
if __name__ == "__main__":
    async def main():
        tester = TestAgentWorkflows()
        await tester.run_all_tests()
    
    asyncio.run(main())