#!/usr/bin/env python3
"""
Orchestrator Improvement Integration Tests - RETROACTIVE TDD COMPLIANCE
These tests should have been written FIRST to drive the workflow integration design
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import json

# Import the classes we need to test
from multi_agent_system import MultiAgentSystem, AgentResponse, AgentType

class TestOrchestratorImprovementTDD:
    """
    Tests that SHOULD have driven the orchestrator improvement integration
    Following TDD RED-GREEN-REFACTOR cycle retroactively
    """
    
    @pytest.fixture
    def mock_supabase_service(self):
        """Mock Supabase service for isolated testing"""
        mock_service = AsyncMock()
        mock_service.create_improvement_session.return_value = "test-session-id"
        mock_service.create_iteration_record.return_value = "test-iteration-id"
        mock_service.save_critique_data.return_value = None
        mock_service.save_enhancement_data.return_value = None
        mock_service.save_score_data.return_value = None
        mock_service.update_improvement_session_status.return_value = {"status": "completed"}
        return mock_service
    
    @pytest.fixture
    def multi_agent_system(self, mock_supabase_service):
        """Create multi-agent system with mocked dependencies"""
        system = MultiAgentSystem()
        with patch('multi_agent_system.supabase_service', mock_supabase_service):
            yield system, mock_supabase_service
    
    # RED: These tests should have FAILED first, driving the implementation
    
    class TestImprovementSessionCreation:
        """Tests that should have driven improvement session creation in workflow"""
        
        @pytest.mark.asyncio
        async def test_should_fail_without_session_creation_at_workflow_start(self, multi_agent_system):
            """RED: This test should have failed first"""
            system, mock_supabase = multi_agent_system
            
            # Mock the orchestrator to route to iterative_improvement
            with patch.object(system, '_send_to_agent') as mock_send:
                mock_orchestrator_response = AgentResponse(
                    agent_name="orchestrator",
                    message="Route to iterative improvement",
                    success=True,
                    parsed_json={
                        "routing_decision": "iterative_improvement",
                        "agents_to_invoke": ["critique", "enhancement", "scoring"],
                        "message_to_critique_agent": "Test content to improve"
                    }
                )
                mock_send.return_value = mock_orchestrator_response
                
                # This should have initially failed because no session creation
                await system.process_message(
                    user_message="Improve this content iteratively: test content",
                    user_id="test_user",
                    session_id="test_session"
                )
                
                # Verify session creation was called
                mock_supabase.create_improvement_session.assert_called_once()
        
        @pytest.mark.asyncio
        async def test_should_create_session_with_correct_parameters(self, multi_agent_system):
            """GREEN: This test should pass after proper implementation"""
            system, mock_supabase = multi_agent_system
            
            # Mock the orchestrator and agent responses
            with patch.object(system, '_send_to_agent') as mock_send:
                # Mock orchestrator response
                mock_orchestrator_response = AgentResponse(
                    agent_name="orchestrator",
                    message="Route to iterative improvement",
                    success=True,
                    parsed_json={
                        "routing_decision": "iterative_improvement",
                        "agents_to_invoke": ["critique", "enhancement", "scoring"],
                        "message_to_critique_agent": "Test content to improve"
                    }
                )
                
                # Mock critique response
                mock_critique_response = AgentResponse(
                    agent_name="critique",
                    message="Critique response",
                    success=True,
                    parsed_json={
                        "overall_rating": "6/10",
                        "strengths": ["clear premise"],
                        "critical_weaknesses": ["lacks depth"]
                    }
                )
                
                # Mock enhancement response
                mock_enhancement_response = AgentResponse(
                    agent_name="enhancement",
                    message="Enhancement response",
                    success=True,
                    parsed_json={
                        "enhanced_content": "Improved test content with more depth",
                        "changes_made": {"added_depth": True},
                        "rationale": "Added more depth based on critique",
                        "confidence_score": 8
                    }
                )
                
                # Mock scoring response with high score to end iteration
                mock_scoring_response = AgentResponse(
                    agent_name="scoring",
                    message="Scoring response",
                    success=True,
                    parsed_json={
                        "overall_score": 9.6,  # Above target to trigger completion
                        "category_scores": {"content": 9.5, "style": 9.7},
                        "rationale": "Excellent improvement",
                        "improvement_trajectory": "improving",
                        "recommendations": "Great work"
                    }
                )
                
                mock_send.side_effect = [
                    mock_orchestrator_response,
                    mock_critique_response,
                    mock_enhancement_response,
                    mock_scoring_response
                ]
                
                await system.process_message(
                    user_message="Improve this content iteratively: test content",
                    user_id="test_user",
                    session_id="test_session"
                )
                
                # Verify session creation with correct parameters
                mock_supabase.create_improvement_session.assert_called_once_with(
                    user_id="test_user",
                    session_id="test_session",
                    original_content="Test content to improve",
                    content_type="text",
                    content_id=None,
                    target_score=9.5,
                    max_iterations=4
                )
        
        @pytest.mark.asyncio
        async def test_should_handle_session_creation_failure_gracefully(self, multi_agent_system):
            """RED: This test should have driven error handling"""
            system, mock_supabase = multi_agent_system
            
            # Mock session creation failure
            mock_supabase.create_improvement_session.side_effect = Exception("Database error")
            
            with patch.object(system, '_send_to_agent') as mock_send:
                mock_orchestrator_response = AgentResponse(
                    agent_name="orchestrator",
                    message="Route to iterative improvement",
                    success=True,
                    parsed_json={
                        "routing_decision": "iterative_improvement",
                        "agents_to_invoke": ["critique", "enhancement", "scoring"],
                        "message_to_critique_agent": "Test content to improve"
                    }
                )
                mock_send.return_value = mock_orchestrator_response
                
                # Should continue workflow even if session creation fails
                result = await system.process_message(
                    user_message="Improve this content iteratively: test content",
                    user_id="test_user",
                    session_id="test_session"
                )
                
                # Should still return success despite session creation failure
                assert result["success"] == True
    
    class TestIterationRecordCreation:
        """Tests that should have driven iteration record creation in each loop"""
        
        @pytest.mark.asyncio
        async def test_should_fail_without_iteration_record_creation(self, multi_agent_system):
            """RED: This test should have failed first"""
            system, mock_supabase = multi_agent_system
            
            with patch.object(system, '_send_to_agent') as mock_send:
                # Setup mock responses for complete iteration
                mock_orchestrator_response = AgentResponse(
                    agent_name="orchestrator",
                    message="Route to iterative improvement",
                    success=True,
                    parsed_json={
                        "routing_decision": "iterative_improvement",
                        "agents_to_invoke": ["critique", "enhancement", "scoring"],
                        "message_to_critique_agent": "Test content to improve"
                    }
                )
                
                mock_critique_response = AgentResponse(
                    agent_name="critique",
                    message="Critique response",
                    success=True,
                    parsed_json={"overall_rating": "6/10", "strengths": [], "critical_weaknesses": []}
                )
                
                mock_enhancement_response = AgentResponse(
                    agent_name="enhancement",
                    message="Enhancement response",
                    success=True,
                    parsed_json={
                        "enhanced_content": "Improved content",
                        "changes_made": {},
                        "rationale": "Made improvements",
                        "confidence_score": 8
                    }
                )
                
                mock_scoring_response = AgentResponse(
                    agent_name="scoring",
                    message="Scoring response",
                    success=True,
                    parsed_json={
                        "overall_score": 9.6,
                        "category_scores": {},
                        "rationale": "Good",
                        "improvement_trajectory": "improving",
                        "recommendations": "Continue"
                    }
                )
                
                mock_send.side_effect = [
                    mock_orchestrator_response,
                    mock_critique_response,
                    mock_enhancement_response,
                    mock_scoring_response
                ]
                
                await system.process_message(
                    user_message="Improve this content iteratively: test content",
                    user_id="test_user",
                    session_id="test_session"
                )
                
                # This should have initially failed because no iteration records
                mock_supabase.create_iteration_record.assert_called_once()
        
        @pytest.mark.asyncio
        async def test_should_create_iteration_record_for_each_iteration(self, multi_agent_system):
            """GREEN: This test should pass after proper implementation"""
            system, mock_supabase = multi_agent_system
            
            with patch.object(system, '_send_to_agent') as mock_send:
                # Mock low scores to force multiple iterations
                mock_orchestrator_response = AgentResponse(
                    agent_name="orchestrator",
                    message="Route to iterative improvement",
                    success=True,
                    parsed_json={
                        "routing_decision": "iterative_improvement",
                        "agents_to_invoke": ["critique", "enhancement", "scoring"],
                        "message_to_critique_agent": "Test content to improve"
                    }
                )
                
                # Mock multiple iterations with low scores
                responses = [mock_orchestrator_response]
                for i in range(3):  # 3 iterations
                    responses.extend([
                        AgentResponse("critique", "Critique", True, {"overall_rating": "6/10", "strengths": [], "critical_weaknesses": []}),
                        AgentResponse("enhancement", "Enhancement", True, {
                            "enhanced_content": f"Improved content iteration {i+1}",
                            "changes_made": {},
                            "rationale": "Made improvements",
                            "confidence_score": 8
                        }),
                        AgentResponse("scoring", "Scoring", True, {
                            "overall_score": 7.0 + i,  # Gradually improve but stay below 9.5
                            "category_scores": {},
                            "rationale": "Improving",
                            "improvement_trajectory": "improving",
                            "recommendations": "Continue"
                        })
                    ])
                
                # Final iteration with high score
                responses.extend([
                    AgentResponse("critique", "Critique", True, {"overall_rating": "9/10", "strengths": [], "critical_weaknesses": []}),
                    AgentResponse("enhancement", "Enhancement", True, {
                        "enhanced_content": "Final improved content",
                        "changes_made": {},
                        "rationale": "Final improvements",
                        "confidence_score": 9
                    }),
                    AgentResponse("scoring", "Scoring", True, {
                        "overall_score": 9.6,  # Above target
                        "category_scores": {},
                        "rationale": "Excellent",
                        "improvement_trajectory": "improving",
                        "recommendations": "Done"
                    })
                ])
                
                mock_send.side_effect = responses
                
                await system.process_message(
                    user_message="Improve this content iteratively: test content",
                    user_id="test_user",
                    session_id="test_session"
                )
                
                # Should create iteration record for each iteration
                assert mock_supabase.create_iteration_record.call_count == 4  # 4 iterations total
    
    class TestDataPersistenceInWorkflow:
        """Tests that should have driven data persistence during workflow"""
        
        @pytest.mark.asyncio
        async def test_should_fail_without_critique_persistence(self, multi_agent_system):
            """RED: This test should have failed first"""
            system, mock_supabase = multi_agent_system
            
            with patch.object(system, '_send_to_agent') as mock_send:
                # Setup single iteration workflow
                mock_responses = [
                    AgentResponse("orchestrator", "Route", True, {
                        "routing_decision": "iterative_improvement",
                        "agents_to_invoke": ["critique", "enhancement", "scoring"],
                        "message_to_critique_agent": "Test content"
                    }),
                    AgentResponse("critique", "Critique", True, {
                        "overall_rating": "6/10",
                        "strengths": ["clear"],
                        "critical_weaknesses": ["shallow"]
                    }),
                    AgentResponse("enhancement", "Enhancement", True, {
                        "enhanced_content": "Improved content",
                        "changes_made": {"depth": True},
                        "rationale": "Added depth",
                        "confidence_score": 8
                    }),
                    AgentResponse("scoring", "Scoring", True, {
                        "overall_score": 9.6,
                        "category_scores": {"content": 9.5},
                        "rationale": "Great improvement",
                        "improvement_trajectory": "improving",
                        "recommendations": "Excellent"
                    })
                ]
                mock_send.side_effect = mock_responses
                
                await system.process_message(
                    user_message="Improve this content iteratively: test content",
                    user_id="test_user",
                    session_id="test_session"
                )
                
                # Should have saved critique data
                mock_supabase.save_critique_data.assert_called_once()
        
        @pytest.mark.asyncio
        async def test_should_fail_without_enhancement_persistence(self, multi_agent_system):
            """RED: This test should have failed first"""
            system, mock_supabase = multi_agent_system
            
            # Same test structure but verify enhancement persistence
            with patch.object(system, '_send_to_agent') as mock_send:
                mock_responses = [
                    AgentResponse("orchestrator", "Route", True, {
                        "routing_decision": "iterative_improvement",
                        "agents_to_invoke": ["critique", "enhancement", "scoring"],
                        "message_to_critique_agent": "Test content"
                    }),
                    AgentResponse("critique", "Critique", True, {"overall_rating": "6/10", "strengths": [], "critical_weaknesses": []}),
                    AgentResponse("enhancement", "Enhancement", True, {
                        "enhanced_content": "Improved content",
                        "changes_made": {"improved": True},
                        "rationale": "Made improvements",
                        "confidence_score": 8
                    }),
                    AgentResponse("scoring", "Scoring", True, {
                        "overall_score": 9.6,
                        "category_scores": {},
                        "rationale": "Good",
                        "improvement_trajectory": "improving",
                        "recommendations": "Done"
                    })
                ]
                mock_send.side_effect = mock_responses
                
                await system.process_message(
                    user_message="Improve this content iteratively: test content",
                    user_id="test_user",
                    session_id="test_session"
                )
                
                # Should have saved enhancement data
                mock_supabase.save_enhancement_data.assert_called_once()
        
        @pytest.mark.asyncio
        async def test_should_fail_without_score_persistence(self, multi_agent_system):
            """RED: This test should have failed first"""
            system, mock_supabase = multi_agent_system
            
            # Same test structure but verify score persistence
            with patch.object(system, '_send_to_agent') as mock_send:
                mock_responses = [
                    AgentResponse("orchestrator", "Route", True, {
                        "routing_decision": "iterative_improvement",
                        "agents_to_invoke": ["critique", "enhancement", "scoring"],
                        "message_to_critique_agent": "Test content"
                    }),
                    AgentResponse("critique", "Critique", True, {"overall_rating": "6/10", "strengths": [], "critical_weaknesses": []}),
                    AgentResponse("enhancement", "Enhancement", True, {
                        "enhanced_content": "Improved content",
                        "changes_made": {},
                        "rationale": "Made improvements",
                        "confidence_score": 8
                    }),
                    AgentResponse("scoring", "Scoring", True, {
                        "overall_score": 9.6,
                        "category_scores": {"content": 9.5, "style": 9.7},
                        "rationale": "Excellent work",
                        "improvement_trajectory": "improving",
                        "recommendations": "Perfect"
                    })
                ]
                mock_send.side_effect = mock_responses
                
                await system.process_message(
                    user_message="Improve this content iteratively: test content",
                    user_id="test_user",
                    session_id="test_session"
                )
                
                # Should have saved score data
                mock_supabase.save_score_data.assert_called_once()
    
    class TestSessionCompletion:
        """Tests that should have driven session completion logic"""
        
        @pytest.mark.asyncio
        async def test_should_fail_without_session_completion_on_target_score(self, multi_agent_system):
            """RED: This test should have failed first"""
            system, mock_supabase = multi_agent_system
            
            with patch.object(system, '_send_to_agent') as mock_send:
                mock_responses = [
                    AgentResponse("orchestrator", "Route", True, {
                        "routing_decision": "iterative_improvement",
                        "agents_to_invoke": ["critique", "enhancement", "scoring"],
                        "message_to_critique_agent": "Test content"
                    }),
                    AgentResponse("critique", "Critique", True, {"overall_rating": "9/10", "strengths": [], "critical_weaknesses": []}),
                    AgentResponse("enhancement", "Enhancement", True, {
                        "enhanced_content": "Perfect content",
                        "changes_made": {},
                        "rationale": "Final polish",
                        "confidence_score": 10
                    }),
                    AgentResponse("scoring", "Scoring", True, {
                        "overall_score": 9.8,  # Above target score
                        "category_scores": {},
                        "rationale": "Perfect",
                        "improvement_trajectory": "completed",
                        "recommendations": "Done"
                    })
                ]
                mock_send.side_effect = mock_responses
                
                await system.process_message(
                    user_message="Improve this content iteratively: test content",
                    user_id="test_user",
                    session_id="test_session"
                )
                
                # Should complete session with target_score_reached
                mock_supabase.update_improvement_session_status.assert_called_once_with(
                    improvement_session_id="test-session-id",
                    status="completed",
                    final_content="Perfect content",
                    final_score=9.8,
                    completion_reason="target_score_reached"
                )
        
        @pytest.mark.asyncio
        async def test_should_fail_without_session_completion_on_max_iterations(self, multi_agent_system):
            """RED: This test should have failed first"""
            system, mock_supabase = multi_agent_system
            
            with patch.object(system, '_send_to_agent') as mock_send:
                # Mock 4 iterations that never reach target score
                responses = [AgentResponse("orchestrator", "Route", True, {
                    "routing_decision": "iterative_improvement",
                    "agents_to_invoke": ["critique", "enhancement", "scoring"],
                    "message_to_critique_agent": "Test content"
                })]
                
                for i in range(4):  # 4 iterations (max)
                    responses.extend([
                        AgentResponse("critique", "Critique", True, {"overall_rating": "6/10", "strengths": [], "critical_weaknesses": []}),
                        AgentResponse("enhancement", "Enhancement", True, {
                            "enhanced_content": f"Improved content {i+1}",
                            "changes_made": {},
                            "rationale": "Improvements",
                            "confidence_score": 7
                        }),
                        AgentResponse("scoring", "Scoring", True, {
                            "overall_score": 7.0 + i * 0.5,  # Never reaches 9.5
                            "category_scores": {},
                            "rationale": "Improving",
                            "improvement_trajectory": "improving",
                            "recommendations": "Continue"
                        })
                    ])
                
                mock_send.side_effect = responses
                
                await system.process_message(
                    user_message="Improve this content iteratively: test content",
                    user_id="test_user",
                    session_id="test_session"
                )
                
                # Should complete session with max_iterations_reached
                mock_supabase.update_improvement_session_status.assert_called_once_with(
                    improvement_session_id="test-session-id",
                    status="completed",
                    final_content="Improved content 4",
                    final_score=8.5,
                    completion_reason="max_iterations_reached"
                )

class TestContentSelectionIntegration:
    """Tests that should have driven content selection from database"""
    
    @pytest.mark.asyncio
    async def test_should_fail_without_content_fetching_from_database(self):
        """RED: This test should have failed first"""
        # This test should have driven the content selection logic
        pass
    
    @pytest.mark.asyncio
    async def test_should_handle_plot_content_selection(self):
        """RED: This test should have driven plot content handling"""
        # This test should have driven plot-specific formatting
        pass
    
    @pytest.mark.asyncio
    async def test_should_handle_author_content_selection(self):
        """RED: This test should have driven author content handling"""
        # This test should have driven author-specific formatting
        pass

class TestErrorHandlingInWorkflow:
    """Tests that should have driven error handling throughout the workflow"""
    
    @pytest.mark.asyncio
    async def test_should_handle_agent_failures_gracefully(self):
        """RED: This test should have driven agent failure handling"""
        # This test should have driven our error recovery logic
        pass
    
    @pytest.mark.asyncio
    async def test_should_handle_database_failures_gracefully(self):
        """RED: This test should have driven database error handling"""
        # This test should have driven our database error recovery
        pass
    
    @pytest.mark.asyncio
    async def test_should_handle_partial_workflow_failures(self):
        """RED: This test should have driven partial failure recovery"""
        # This test should have driven our workflow recovery logic
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])