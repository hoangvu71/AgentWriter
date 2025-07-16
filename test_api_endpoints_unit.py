#!/usr/bin/env python3
"""
API Endpoints Unit Tests - CRITICAL TDD COMPLIANCE
These tests should have been written FIRST before any API implementation
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import json

# Import the FastAPI app that should have been test-driven
from main import app

class TestAPIEndpointsTDD:
    """
    Tests that SHOULD have driven the API endpoint design
    These represent CRITICAL TDD violations - all endpoints were written BEFORE tests
    """
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    # RED: These tests should have FAILED first, driving the implementation
    
    class TestHealthAndStatus:
        """Tests that should have driven health check endpoints"""
        
        def test_should_fail_without_health_endpoint(self, client):
            """RED: This test should have failed first"""
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
        
        def test_should_provide_api_version_info(self, client):
            """RED: This test should have driven version endpoint"""
            response = client.get("/version")
            assert response.status_code == 200
            assert "version" in response.json()
        
        def test_should_provide_system_status(self, client):
            """RED: This test should have driven status monitoring"""
            response = client.get("/status")
            assert response.status_code == 200
            data = response.json()
            assert "database" in data
            assert "agents" in data
            assert "uptime" in data
    
    class TestChatWebSocket:
        """Tests that should have driven WebSocket chat functionality"""
        
        def test_should_fail_without_websocket_endpoint(self, client):
            """RED: This test should have failed first"""
            with client.websocket_connect("/ws/chat") as websocket:
                websocket.send_text("test message")
                data = websocket.receive_text()
                assert data is not None
        
        def test_should_validate_websocket_message_format(self, client):
            """RED: This test should have driven message validation"""
            with client.websocket_connect("/ws/chat") as websocket:
                # Send invalid message format
                websocket.send_text("invalid json")
                response = websocket.receive_text()
                error_data = json.loads(response)
                assert error_data["type"] == "error"
                assert "invalid format" in error_data["message"].lower()
        
        def test_should_handle_user_authentication_in_websocket(self, client):
            """RED: This test should have driven WebSocket auth"""
            with client.websocket_connect("/ws/chat?user_id=test_user") as websocket:
                websocket.send_json({
                    "type": "message",
                    "content": "Hello",
                    "user_id": "test_user",
                    "session_id": "test_session"
                })
                response = websocket.receive_json()
                assert response["type"] in ["message", "response"]
        
        def test_should_handle_websocket_disconnection_gracefully(self, client):
            """RED: This test should have driven connection management"""
            with client.websocket_connect("/ws/chat") as websocket:
                websocket.send_text("test")
                websocket.close()
                # Should not raise exceptions on cleanup
    
    class TestPlotEndpoints:
        """Tests that should have driven plot-related API endpoints"""
        
        def test_should_fail_without_plots_list_endpoint(self, client):
            """RED: This test should have failed first"""
            response = client.get("/api/plots")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
        
        def test_should_validate_plot_creation_data(self, client):
            """RED: This test should have driven plot validation"""
            # Test with invalid data
            response = client.post("/api/plots", json={})
            assert response.status_code == 422  # Validation error
            
            # Test with valid data
            valid_plot = {
                "title": "Test Plot",
                "plot_summary": "A test story",
                "genre": "Fantasy",
                "user_id": "test_user"
            }
            response = client.post("/api/plots", json=valid_plot)
            assert response.status_code in [200, 201]
        
        def test_should_handle_plot_retrieval_by_id(self, client):
            """RED: This test should have driven plot retrieval"""
            response = client.get("/api/plots/test-plot-id")
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                plot = response.json()
                assert "id" in plot
                assert "title" in plot
                assert "plot_summary" in plot
        
        def test_should_handle_plot_search_and_filtering(self, client):
            """RED: This test should have driven search functionality"""
            response = client.get("/api/plots?genre=Fantasy&search=dragon")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
    
    class TestAuthorEndpoints:
        """Tests that should have driven author-related API endpoints"""
        
        def test_should_fail_without_authors_list_endpoint(self, client):
            """RED: This test should have failed first"""
            response = client.get("/api/authors")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
        
        def test_should_validate_author_creation_data(self, client):
            """RED: This test should have driven author validation"""
            # Test with invalid data
            response = client.post("/api/authors", json={})
            assert response.status_code == 422
            
            # Test with valid data
            valid_author = {
                "author_name": "Test Author",
                "biography": "A test biography",
                "writing_style": "Descriptive",
                "user_id": "test_user"
            }
            response = client.post("/api/authors", json=valid_author)
            assert response.status_code in [200, 201]
        
        def test_should_handle_author_plot_relationships(self, client):
            """RED: This test should have driven relationship management"""
            response = client.get("/api/authors/test-author-id/plots")
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                plots = response.json()
                assert isinstance(plots, list)
    
    class TestGenreManagement:
        """Tests that should have driven genre management endpoints"""
        
        def test_should_fail_without_genres_endpoint(self, client):
            """RED: This test should have failed first"""
            response = client.get("/api/genres")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
        
        def test_should_validate_genre_creation(self, client):
            """RED: This test should have driven genre validation"""
            # Test invalid genre
            response = client.post("/api/genres", json={"name": ""})
            assert response.status_code == 422
            
            # Test valid genre
            valid_genre = {
                "name": "Test Genre",
                "description": "A test genre description"
            }
            response = client.post("/api/genres", json=valid_genre)
            assert response.status_code in [200, 201]
        
        def test_should_handle_hierarchical_genre_structure(self, client):
            """RED: This test should have driven genre hierarchy"""
            response = client.get("/api/genres/Fantasy/subgenres")
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                subgenres = response.json()
                assert isinstance(subgenres, list)
    
    class TestTargetAudienceEndpoints:
        """Tests that should have driven target audience management"""
        
        def test_should_fail_without_target_audiences_endpoint(self, client):
            """RED: This test should have failed first"""
            response = client.get("/api/target-audiences")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
        
        def test_should_validate_audience_creation(self, client):
            """RED: This test should have driven audience validation"""
            valid_audience = {
                "age_group": "Young Adult",
                "gender": "All",
                "sexual_orientation": "All",
                "interests": ["Adventure", "Romance"],
                "description": "YA adventure romance readers"
            }
            response = client.post("/api/target-audiences", json=valid_audience)
            assert response.status_code in [200, 201]
    
    class TestContentSelection:
        """Tests that should have driven content selection functionality"""
        
        def test_should_fail_without_content_selection_endpoint(self, client):
            """RED: This test should have failed first"""
            response = client.get("/api/content-selection")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            
            # Should contain both plots and authors
            if data:
                item = data[0]
                assert "id" in item
                assert "title" in item
                assert "type" in item
                assert item["type"] in ["plot", "author"]
        
        def test_should_support_content_filtering(self, client):
            """RED: This test should have driven filtering logic"""
            response = client.get("/api/content-selection?type=plot&limit=10")
            assert response.status_code == 200
            data = response.json()
            assert len(data) <= 10
            
            if data:
                assert all(item["type"] == "plot" for item in data)
    
    class TestLibraryInterface:
        """Tests that should have driven library interface endpoints"""
        
        def test_should_fail_without_library_page(self, client):
            """RED: This test should have failed first"""
            response = client.get("/library")
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
        
        def test_should_serve_static_assets(self, client):
            """RED: This test should have driven static file serving"""
            response = client.get("/static/style.css")
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                assert "text/css" in response.headers["content-type"]
    
    class TestErrorHandling:
        """Tests that should have driven API error handling"""
        
        def test_should_handle_404_errors_gracefully(self, client):
            """RED: This test should have driven 404 handling"""
            response = client.get("/api/nonexistent-endpoint")
            assert response.status_code == 404
            assert "error" in response.json() or "detail" in response.json()
        
        def test_should_handle_500_errors_gracefully(self, client):
            """RED: This test should have driven error handling"""
            with patch('main.supabase_service') as mock_service:
                mock_service.get_all_plots.side_effect = Exception("Database error")
                
                response = client.get("/api/plots")
                assert response.status_code == 500
                error_data = response.json()
                assert "error" in error_data or "detail" in error_data
        
        def test_should_validate_request_data_types(self, client):
            """RED: This test should have driven data validation"""
            # Send invalid JSON
            response = client.post(
                "/api/plots",
                data="invalid json",
                headers={"content-type": "application/json"}
            )
            assert response.status_code == 422
        
        def test_should_handle_missing_required_fields(self, client):
            """RED: This test should have driven field validation"""
            response = client.post("/api/plots", json={"title": "Test"})  # Missing required fields
            assert response.status_code == 422
            error_data = response.json()
            assert "detail" in error_data
    
    class TestSecurity:
        """Tests that should have driven API security"""
        
        def test_should_validate_user_authentication(self, client):
            """RED: This test should have driven auth validation"""
            # Test without user authentication
            response = client.post("/api/plots", json={
                "title": "Test Plot",
                "plot_summary": "Test"
            })
            # Should require authentication or user_id
            assert response.status_code in [401, 422]
        
        def test_should_sanitize_user_input(self, client):
            """RED: This test should have driven input sanitization"""
            malicious_input = {
                "title": "<script>alert('xss')</script>",
                "plot_summary": "'; DROP TABLE plots; --",
                "user_id": "test_user"
            }
            response = client.post("/api/plots", json=malicious_input)
            
            if response.status_code in [200, 201]:
                # Input should be sanitized
                plot = response.json()
                assert "<script>" not in plot.get("title", "")
                assert "DROP TABLE" not in plot.get("plot_summary", "")
        
        def test_should_implement_rate_limiting(self, client):
            """RED: This test should have driven rate limiting"""
            # Make multiple rapid requests
            responses = []
            for i in range(100):  # Rapid requests
                response = client.get("/api/plots")
                responses.append(response.status_code)
                if response.status_code == 429:  # Rate limited
                    break
            
            # Should eventually rate limit (or have protection)
            assert any(status == 429 for status in responses) or len(responses) < 100
    
    class TestPerformance:
        """Tests that should have driven API performance requirements"""
        
        def test_should_respond_within_acceptable_time(self, client):
            """RED: This test should have driven performance requirements"""
            import time
            start_time = time.time()
            
            response = client.get("/api/plots")
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response_time < 5.0  # Should respond within 5 seconds
            assert response.status_code == 200
        
        def test_should_handle_concurrent_requests(self, client):
            """RED: This test should have driven concurrency handling"""
            import threading
            
            results = []
            
            def make_request():
                response = client.get("/api/plots")
                results.append(response.status_code)
            
            # Make 10 concurrent requests
            threads = []
            for i in range(10):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            # All requests should succeed
            assert all(status == 200 for status in results)
            assert len(results) == 10

class TestAPIContractValidation:
    """Tests that should have driven API contract design"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_should_follow_rest_conventions(self, client):
        """RED: This test should have driven REST design"""
        # GET should be idempotent
        response1 = client.get("/api/plots")
        response2 = client.get("/api/plots")
        assert response1.status_code == response2.status_code
        
        # POST should create resources
        if hasattr(client, 'post'):
            response = client.post("/api/plots", json={
                "title": "Test",
                "plot_summary": "Test",
                "user_id": "test"
            })
            assert response.status_code in [200, 201, 422]
    
    def test_should_return_consistent_json_structure(self, client):
        """RED: This test should have driven response format"""
        response = client.get("/api/plots")
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            
            if data:
                plot = data[0]
                required_fields = ["id", "title", "plot_summary"]
                for field in required_fields:
                    assert field in plot, f"Missing required field: {field}"
    
    def test_should_handle_content_negotiation(self, client):
        """RED: This test should have driven content type handling"""
        response = client.get("/api/plots", headers={"Accept": "application/json"})
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])