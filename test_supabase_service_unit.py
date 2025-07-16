#!/usr/bin/env python3
"""
Unit tests for Supabase Service - RETROACTIVE TDD COMPLIANCE
These tests should have been written FIRST before any implementation
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import json

# Import the service we need to test
from supabase_service import SupabaseService

class TestSupabaseServiceTDD:
    """
    Unit tests that SHOULD have been written BEFORE implementation
    Following TDD RED-GREEN-REFACTOR cycle retroactively
    """
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for isolated testing"""
        mock_client = Mock()
        mock_client.table.return_value = Mock()
        return mock_client
    
    @pytest.fixture
    def supabase_service(self, mock_supabase_client):
        """Create service with mocked client"""
        service = SupabaseService()
        service.client = mock_supabase_client
        return service
    
    # RED: These tests should have FAILED first, driving the implementation
    
    class TestCreateImprovementSession:
        """Tests that should have driven create_improvement_session design"""
        
        @pytest.mark.asyncio
        async def test_should_fail_without_user_id(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="user_id is required"):
                await supabase_service.create_improvement_session(
                    user_id="",  # Empty user_id should fail
                    session_id="test_session",
                    original_content="test content",
                    content_type="plot"
                )
        
        @pytest.mark.asyncio
        async def test_should_fail_without_session_id(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="session_id is required"):
                await supabase_service.create_improvement_session(
                    user_id="test_user",
                    session_id="",  # Empty session_id should fail
                    original_content="test content",
                    content_type="plot"
                )
        
        @pytest.mark.asyncio
        async def test_should_fail_without_original_content(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="original_content is required"):
                await supabase_service.create_improvement_session(
                    user_id="test_user",
                    session_id="test_session",
                    original_content="",  # Empty content should fail
                    content_type="plot"
                )
        
        @pytest.mark.asyncio
        async def test_should_fail_with_invalid_content_type(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="Invalid content_type"):
                await supabase_service.create_improvement_session(
                    user_id="test_user",
                    session_id="test_session",
                    original_content="test content",
                    content_type="invalid_type"  # Invalid type should fail
                )
        
        @pytest.mark.asyncio
        async def test_should_create_valid_session_record(self, supabase_service, mock_supabase_client):
            """GREEN: This test should pass after proper implementation"""
            # Mock successful database response
            mock_response = Mock()
            mock_response.data = [{"id": "test-session-uuid"}]
            mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response
            
            session_id = await supabase_service.create_improvement_session(
                user_id="test_user",
                session_id="test_session",
                original_content="test content",
                content_type="plot",
                target_score=9.5,
                max_iterations=4
            )
            
            assert session_id == "test-session-uuid"
            mock_supabase_client.table.assert_called_with("improvement_sessions")
        
        @pytest.mark.asyncio
        async def test_should_handle_database_errors(self, supabase_service, mock_supabase_client):
            """RED: This test should have driven error handling"""
            # Mock database failure
            mock_supabase_client.table.return_value.insert.return_value.execute.side_effect = Exception("DB Error")
            
            with pytest.raises(Exception, match="Failed to create improvement session"):
                await supabase_service.create_improvement_session(
                    user_id="test_user",
                    session_id="test_session",
                    original_content="test content",
                    content_type="plot"
                )
    
    class TestCreateIterationRecord:
        """Tests that should have driven create_iteration_record design"""
        
        @pytest.mark.asyncio
        async def test_should_fail_without_improvement_session_id(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="improvement_session_id is required"):
                await supabase_service.create_iteration_record(
                    improvement_session_id="",  # Empty ID should fail
                    iteration_number=1,
                    content="test content"
                )
        
        @pytest.mark.asyncio
        async def test_should_fail_with_invalid_iteration_number(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="iteration_number must be positive"):
                await supabase_service.create_iteration_record(
                    improvement_session_id="test-session-id",
                    iteration_number=0,  # Zero or negative should fail
                    content="test content"
                )
        
        @pytest.mark.asyncio
        async def test_should_fail_with_empty_content(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="content is required"):
                await supabase_service.create_iteration_record(
                    improvement_session_id="test-session-id",
                    iteration_number=1,
                    content=""  # Empty content should fail
                )
        
        @pytest.mark.asyncio
        async def test_should_create_valid_iteration_record(self, supabase_service, mock_supabase_client):
            """GREEN: This test should pass after proper implementation"""
            # Mock successful database response
            mock_response = Mock()
            mock_response.data = [{"id": "test-iteration-uuid"}]
            mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response
            
            iteration_id = await supabase_service.create_iteration_record(
                improvement_session_id="test-session-id",
                iteration_number=1,
                content="test content"
            )
            
            assert iteration_id == "test-iteration-uuid"
            mock_supabase_client.table.assert_called_with("iterations")
    
    class TestSaveCritiqueData:
        """Tests that should have driven save_critique_data design"""
        
        @pytest.mark.asyncio
        async def test_should_fail_without_iteration_id(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="iteration_id is required"):
                await supabase_service.save_critique_data(
                    iteration_id="",  # Empty ID should fail
                    critique_json={"rating": "8/10"},
                    agent_response="Good work"
                )
        
        @pytest.mark.asyncio
        async def test_should_fail_with_invalid_critique_json(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="critique_json must be a dictionary"):
                await supabase_service.save_critique_data(
                    iteration_id="test-iteration-id",
                    critique_json="not a dict",  # Invalid JSON should fail
                    agent_response="Good work"
                )
        
        @pytest.mark.asyncio
        async def test_should_fail_without_agent_response(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="agent_response is required"):
                await supabase_service.save_critique_data(
                    iteration_id="test-iteration-id",
                    critique_json={"rating": "8/10"},
                    agent_response=""  # Empty response should fail
                )
        
        @pytest.mark.asyncio
        async def test_should_save_valid_critique_data(self, supabase_service, mock_supabase_client):
            """GREEN: This test should pass after proper implementation"""
            # Mock successful database response
            mock_response = Mock()
            mock_response.data = [{"id": "test-critique-uuid"}]
            mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response
            
            await supabase_service.save_critique_data(
                iteration_id="test-iteration-id",
                critique_json={"rating": "8/10", "strengths": ["good plot"]},
                agent_response="Detailed critique response"
            )
            
            mock_supabase_client.table.assert_called_with("critiques")
    
    class TestSaveEnhancementData:
        """Tests that should have driven save_enhancement_data design"""
        
        @pytest.mark.asyncio
        async def test_should_fail_without_iteration_id(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="iteration_id is required"):
                await supabase_service.save_enhancement_data(
                    iteration_id="",  # Empty ID should fail
                    enhanced_content="Enhanced content",
                    changes_made={"improved": True},
                    rationale="Made improvements",
                    confidence_score=8
                )
        
        @pytest.mark.asyncio
        async def test_should_fail_without_enhanced_content(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="enhanced_content is required"):
                await supabase_service.save_enhancement_data(
                    iteration_id="test-iteration-id",
                    enhanced_content="",  # Empty content should fail
                    changes_made={"improved": True},
                    rationale="Made improvements",
                    confidence_score=8
                )
        
        @pytest.mark.asyncio
        async def test_should_fail_with_invalid_confidence_score(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="confidence_score must be between 0 and 10"):
                await supabase_service.save_enhancement_data(
                    iteration_id="test-iteration-id",
                    enhanced_content="Enhanced content",
                    changes_made={"improved": True},
                    rationale="Made improvements",
                    confidence_score=15  # Invalid score should fail
                )
        
        @pytest.mark.asyncio
        async def test_should_save_valid_enhancement_data(self, supabase_service, mock_supabase_client):
            """GREEN: This test should pass after proper implementation"""
            # Mock successful database response
            mock_response = Mock()
            mock_response.data = [{"id": "test-enhancement-uuid"}]
            mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response
            
            await supabase_service.save_enhancement_data(
                iteration_id="test-iteration-id",
                enhanced_content="Enhanced content",
                changes_made={"improved_plot": True, "added_details": True},
                rationale="Made improvements based on critique",
                confidence_score=8
            )
            
            mock_supabase_client.table.assert_called_with("enhancements")
    
    class TestSaveScoreData:
        """Tests that should have driven save_score_data design"""
        
        @pytest.mark.asyncio
        async def test_should_fail_without_iteration_id(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="iteration_id is required"):
                await supabase_service.save_score_data(
                    iteration_id="",  # Empty ID should fail
                    overall_score=8.5,
                    category_scores={"plot": 8.0},
                    score_rationale="Good improvement",
                    improvement_trajectory="improving",
                    recommendations="Keep going"
                )
        
        @pytest.mark.asyncio
        async def test_should_fail_with_invalid_overall_score(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="overall_score must be between 0 and 10"):
                await supabase_service.save_score_data(
                    iteration_id="test-iteration-id",
                    overall_score=15.0,  # Invalid score should fail
                    category_scores={"plot": 8.0},
                    score_rationale="Good improvement",
                    improvement_trajectory="improving",
                    recommendations="Keep going"
                )
        
        @pytest.mark.asyncio
        async def test_should_fail_with_invalid_category_scores(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="category_scores must be a dictionary"):
                await supabase_service.save_score_data(
                    iteration_id="test-iteration-id",
                    overall_score=8.5,
                    category_scores="not a dict",  # Invalid scores should fail
                    score_rationale="Good improvement",
                    improvement_trajectory="improving",
                    recommendations="Keep going"
                )
        
        @pytest.mark.asyncio
        async def test_should_save_valid_score_data(self, supabase_service, mock_supabase_client):
            """GREEN: This test should pass after proper implementation"""
            # Mock successful database response
            mock_response = Mock()
            mock_response.data = [{"id": "test-score-uuid"}]
            mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response
            
            await supabase_service.save_score_data(
                iteration_id="test-iteration-id",
                overall_score=8.5,
                category_scores={"plot": 8.0, "characters": 9.0, "style": 8.0},
                score_rationale="Good improvement in all areas",
                improvement_trajectory="improving",
                recommendations="Continue with character development"
            )
            
            mock_supabase_client.table.assert_called_with("scores")
    
    class TestUpdateImprovementSessionStatus:
        """Tests that should have driven update_improvement_session_status design"""
        
        @pytest.mark.asyncio
        async def test_should_fail_without_improvement_session_id(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="improvement_session_id is required"):
                await supabase_service.update_improvement_session_status(
                    improvement_session_id="",  # Empty ID should fail
                    status="completed",
                    final_content="Final content",
                    final_score=9.0,
                    completion_reason="target_reached"
                )
        
        @pytest.mark.asyncio
        async def test_should_fail_with_invalid_status(self, supabase_service):
            """RED: This test should have failed first"""
            with pytest.raises(ValueError, match="Invalid status"):
                await supabase_service.update_improvement_session_status(
                    improvement_session_id="test-session-id",
                    status="invalid_status",  # Invalid status should fail
                    final_content="Final content",
                    final_score=9.0,
                    completion_reason="target_reached"
                )
        
        @pytest.mark.asyncio
        async def test_should_update_valid_session_status(self, supabase_service, mock_supabase_client):
            """GREEN: This test should pass after proper implementation"""
            # Mock successful database response
            mock_response = Mock()
            mock_response.data = [{"id": "test-session-id", "status": "completed"}]
            mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response
            
            result = await supabase_service.update_improvement_session_status(
                improvement_session_id="test-session-id",
                status="completed",
                final_content="Final enhanced content",
                final_score=9.2,
                completion_reason="target_score_reached"
            )
            
            assert result["status"] == "completed"
            mock_supabase_client.table.assert_called_with("improvement_sessions")

# Integration tests that should have driven the overall design
class TestImprovementWorkflowIntegration:
    """Integration tests that should have driven the workflow design"""
    
    @pytest.mark.asyncio
    async def test_complete_improvement_session_workflow(self):
        """
        RED: This test should have failed first and driven the entire design
        This is the test that should have guided all implementation decisions
        """
        # This test should drive the design of the entire improvement workflow
        # It should fail initially and guide implementation step by step
        pass
    
    @pytest.mark.asyncio
    async def test_error_recovery_in_improvement_workflow(self):
        """RED: This test should have driven error handling design"""
        # This test should drive how we handle failures during improvement
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_improvement_sessions(self):
        """RED: This test should have driven concurrency design"""
        # This test should drive how we handle multiple simultaneous improvements
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])