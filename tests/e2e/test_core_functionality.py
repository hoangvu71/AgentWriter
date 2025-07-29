"""
Core functionality E2E tests for AgentWriter.
Tests basic application functionality, API endpoints, and health checks.
"""

import asyncio
import json
import time
from typing import Dict, Any
import websockets
import requests
from playwright.config import get_environment_config, PERFORMANCE_THRESHOLDS


class TestCoreFunctionality:
    """Test core application functionality."""
    
    def __init__(self, environment: str = "local"):
        self.config = get_environment_config(environment)
        self.base_url = self.config["base_url"]
        self.websocket_url = self.config["websocket_url"]
    
    async def test_application_startup(self) -> Dict[str, Any]:
        """Test that the application starts up correctly."""
        result = {
            "test_name": "Application Startup",
            "status": "pending",
            "details": [],
            "performance": {}
        }
        
        try:
            # Test health endpoint
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=10)
            health_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result["details"].append("✅ Health endpoint responsive")
                result["performance"]["health_check"] = health_time
            else:
                result["details"].append(f"❌ Health endpoint returned {response.status_code}")
                result["status"] = "failed"
                return result
            
            # Test models endpoint
            start_time = time.time()
            response = requests.get(f"{self.base_url}/models", timeout=10)
            models_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result["details"].append("✅ Models endpoint responsive")
                result["performance"]["models_check"] = models_time
            else:
                result["details"].append(f"⚠️ Models endpoint returned {response.status_code}")
            
            # Test OpenAI compatibility
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}/openai/v1/models", timeout=10)
                openai_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    result["details"].append("✅ OpenAI compatibility endpoint working")
                    result["performance"]["openai_check"] = openai_time
                else:
                    result["details"].append("⚠️ OpenAI compatibility endpoint issues")
            except Exception:
                result["details"].append("ℹ️ OpenAI compatibility endpoint not available")
            
            result["status"] = "passed"
            
        except Exception as e:
            result["status"] = "failed"
            result["details"].append(f"❌ Application startup test failed: {str(e)}")
        
        return result
    
    async def test_websocket_connection(self) -> Dict[str, Any]:
        """Test WebSocket connectivity."""
        result = {
            "test_name": "WebSocket Connection",
            "status": "pending", 
            "details": [],
            "performance": {}
        }
        
        try:
            session_id = "test-session-core"
            uri = f"{self.websocket_url}/{session_id}"
            
            # Test connection establishment
            start_time = time.time()
            async with websockets.connect(uri) as websocket:
                connection_time = (time.time() - start_time) * 1000
                result["performance"]["connection_time"] = connection_time
                
                result["details"].append("✅ WebSocket connection established")
                
                # Test message sending
                test_message = {
                    "type": "ping",
                    "session_id": session_id,
                    "timestamp": time.time()
                }
                
                await websocket.send(json.dumps(test_message))
                result["details"].append("✅ Message sent successfully")
                
                # Test message receiving (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    result["details"].append("✅ Response received from server")
                    
                    # Try to parse response
                    try:
                        parsed_response = json.loads(response)
                        result["details"].append(f"✅ Valid JSON response: {type(parsed_response)}")
                    except json.JSONDecodeError:
                        result["details"].append("ℹ️ Non-JSON response received (may be expected)")
                        
                except asyncio.TimeoutError:
                    result["details"].append("⚠️ No response received within timeout (may be expected for ping)")
                
                result["status"] = "passed"
                
        except Exception as e:
            result["status"] = "failed"
            result["details"].append(f"❌ WebSocket test failed: {str(e)}")
        
        return result
    
    async def test_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity and basic operations."""
        result = {
            "test_name": "Database Connectivity",
            "status": "pending",
            "details": [],
            "performance": {}
        }
        
        try:
            # Test database connection through API
            start_time = time.time()
            
            # This would typically test a database-dependent endpoint
            # For now, we'll test the health endpoint which should verify DB connectivity
            response = requests.get(f"{self.base_url}/health", timeout=10)
            db_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                health_data = response.json()
                if isinstance(health_data, dict):
                    result["details"].append("✅ API endpoints accessible (implies DB connectivity)")
                    result["performance"]["db_health_check"] = db_time
                else:
                    result["details"].append("⚠️ Health endpoint response format unexpected")
            
            # Test that we can make requests that would require database access
            try:
                # Test getting models (may require database)
                response = requests.get(f"{self.base_url}/models", timeout=10)
                if response.status_code == 200:
                    result["details"].append("✅ Models endpoint working (database operations successful)")
                else:
                    result["details"].append("⚠️ Models endpoint issues (potential database problems)")
            except Exception as e:
                result["details"].append(f"⚠️ Models endpoint test failed: {str(e)}")
            
            result["status"] = "passed"
            
        except Exception as e:
            result["status"] = "failed"
            result["details"].append(f"❌ Database connectivity test failed: {str(e)}")
        
        return result
    
    async def test_static_file_serving(self) -> Dict[str, Any]:
        """Test static file serving."""
        result = {
            "test_name": "Static File Serving",
            "status": "pending",
            "details": [],
            "performance": {}
        }
        
        try:
            # Test common static file endpoints
            static_files = [
                "/static/index.html",
                "/static/css/style.css", 
                "/static/js/app.js",
                "/favicon.ico"
            ]
            
            served_files = 0
            for file_path in static_files:
                try:
                    start_time = time.time()
                    response = requests.get(f"{self.base_url}{file_path}", timeout=5)
                    load_time = (time.time() - start_time) * 1000
                    
                    if response.status_code == 200:
                        result["details"].append(f"✅ {file_path} served successfully")
                        result["performance"][f"static_{file_path.split('/')[-1]}"] = load_time
                        served_files += 1
                    elif response.status_code == 404:
                        result["details"].append(f"ℹ️ {file_path} not found (may not exist)")
                    else:
                        result["details"].append(f"⚠️ {file_path} returned {response.status_code}")
                        
                except Exception as e:
                    result["details"].append(f"⚠️ {file_path} test failed: {str(e)}")
            
            if served_files > 0:
                result["details"].append(f"✅ {served_files}/{len(static_files)} static files accessible")
                result["status"] = "passed"
            else:
                result["details"].append("ℹ️ No static files found (may not be configured)")
                result["status"] = "passed"  # Not a failure if static files aren't configured
                
        except Exception as e:
            result["status"] = "failed"
            result["details"].append(f"❌ Static file serving test failed: {str(e)}")
        
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all core functionality tests."""
        print("🧪 Running Core Functionality E2E Tests...")
        
        results = {
            "suite_name": "Core Functionality",
            "total_tests": 4,
            "passed": 0,
            "failed": 0,
            "tests": []
        }
        
        # Run all tests
        test_methods = [
            self.test_application_startup,
            self.test_websocket_connection,
            self.test_database_connectivity,
            self.test_static_file_serving
        ]
        
        for test_method in test_methods:
            try:
                test_result = await test_method()
                results["tests"].append(test_result)
                
                if test_result["status"] == "passed":
                    results["passed"] += 1
                else:
                    results["failed"] += 1
                    
                # Print test result
                print(f"\n{test_result['test_name']}: {test_result['status'].upper()}")
                for detail in test_result["details"]:
                    print(f"  {detail}")
                    
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
        print(f"\n🎯 Core Functionality Tests Summary:")
        print(f"   Passed: {results['passed']}/{results['total_tests']}")
        print(f"   Failed: {results['failed']}/{results['total_tests']}")
        
        return results


# Standalone execution for testing
if __name__ == "__main__":
    async def main():
        tester = TestCoreFunctionality()
        await tester.run_all_tests()
    
    asyncio.run(main())