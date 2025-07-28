"""
TDD Tests for LoreGen Agent Refactoring
Tests the refactored LoreGen agent following the successful Phase 1A pattern.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from src.core.interfaces import AgentRequest, AgentResponse, ContentType
from src.core.configuration import Configuration


class TestLoreGenAgentRefactored:
    """Test suite for refactored LoreGen agent"""
    
    @pytest.fixture
    def config(self):
        """Mock configuration"""
        config = Mock(spec=Configuration)
        config.google_cloud_project = "test-project"
        config.google_cloud_location = "us-central1"
        config.model_name = "gemini-2.0-flash-exp"
        return config
    
    @pytest.fixture
    def mock_world_data(self):
        """Mock world building data"""
        return {
            'id': 'world-123',
            'world_name': 'Eldoria',
            'world_type': 'fantasy',
            'world_content': """
            The Kingdom of Eldoria spans vast territories with ancient forests and towering mountains.
            
            The noble houses control different regions: House Drakmoor rules the eastern provinces,
            while House Silverbrook governs the western coastlands.
            
            Magic flows through ley lines that intersect at sacred groves throughout the realm.
            The Academy of Mystic Arts trains new mages in the capital city.
            
            Trade routes connect major cities, with merchants traveling between settlements.
            The Royal Treasury manages the kingdom's economic affairs.
            """
        }
    
    @pytest.fixture
    def mock_sparse_areas(self):
        """Mock sparse areas detected by clustering"""
        return [
            {
                'concept_area': 'House Drakmoor',
                'avg_pairwise_distance': 0.8,
                'cluster_id': 1,
                'chunk_indices': [0, 3],
                'expansion_needed': True,
                'chunks': [
                    {'text': 'House Drakmoor rules the eastern provinces', 'metadata': {}}
                ]
            },
            {
                'concept_area': 'Trade System',
                'avg_pairwise_distance': 0.75,
                'cluster_id': 2,
                'chunk_indices': [5],
                'expansion_needed': True,
                'chunks': [
                    {'text': 'Trade routes connect major cities', 'metadata': {}}
                ]
            }
        ]
    
    @pytest.fixture
    def mock_expansions(self):
        """Mock generated expansions"""
        return [
            {
                'concept_area': 'House Drakmoor',
                'expanded_content': """House Drakmoor, founded three centuries ago by Lord Commander Theron Drakmoor, 
                stands as one of the most powerful noble houses in Eldoria. Their ancestral seat, Castle Shadowpeak, 
                overlooks the Whispering Valley where their famed knights train. The house motto "Strength Through Unity" 
                reflects their military traditions and tight family bonds. Current Lord Aldric Drakmoor maintains a 
                formidable cavalry force known as the Eastern Guard, while his daughter Lady Mira serves as the kingdom's 
                chief military strategist.""",
                'original_content': 'House Drakmoor rules the eastern provinces'
            },
            {
                'concept_area': 'Trade System',
                'expanded_content': """The Eldorian trade network operates on a sophisticated guild system established 
                during the reign of King Marcus the Merchant. The Merchant's Guild maintains way stations every fifty 
                miles along major routes, providing security escorts and standardized weights and measures. The Royal 
                Road connects the capital to five major trading hubs, each specializing in different commodities: 
                Ironhold for metals and weapons, Greenwater for agricultural goods, Saltmere for coastal trade, 
                Goldbridge for luxury items, and Thornwick for magical components and rare materials.""",
                'original_content': 'Trade routes connect major cities'
            }
        ]
    
    @pytest.mark.asyncio
    async def test_loregen_agent_initialization(self, config):
        """Test: LoreGen agent initializes correctly with all required services"""
        # This will test the main agent after refactoring
        from src.agents.loregen import LoreGenAgent
        
        agent = LoreGenAgent(config)
        
        assert agent.name == "loregen"
        assert agent.description == "Generates expanded world building by detecting and filling sparse lore areas"
        assert agent._get_content_type() == ContentType.WORLD_BUILDING
        assert hasattr(agent, '_rag_service')
        assert hasattr(agent, '_clustering_service')
        assert hasattr(agent, '_document_processor')
        assert hasattr(agent, '_embedding_manager')
    
    @pytest.mark.asyncio
    async def test_rag_service_initialization(self, config):
        """Test: LoreRAGService initializes correctly"""
        from src.agents.loregen_modules.rag_service import LoreRAGService
        
        service = LoreRAGService(config)
        
        assert service.config == config
        assert hasattr(service, 'logger')
        assert hasattr(service, '_vertex_client')
    
    @pytest.mark.asyncio
    async def test_clustering_service_initialization(self):
        """Test: LoreClusteringService initializes correctly"""
        from src.agents.loregen_modules.clustering_service import LoreClusteringService
        
        service = LoreClusteringService()
        
        assert hasattr(service, 'logger')
        assert hasattr(service, '_kmeans_clusters')
    
    @pytest.mark.asyncio
    async def test_document_processor_initialization(self):
        """Test: LoreDocumentProcessor initializes correctly"""
        from src.agents.loregen_modules.document_processor import LoreDocumentProcessor
        
        processor = LoreDocumentProcessor()
        
        assert hasattr(processor, 'logger')
        assert hasattr(processor, '_chunk_size')
        assert hasattr(processor, '_chunk_overlap')
    
    @pytest.mark.asyncio
    async def test_embedding_manager_initialization(self, config):
        """Test: LoreEmbeddingManager initializes correctly"""
        from src.agents.loregen_modules.embedding_manager import LoreEmbeddingManager
        
        manager = LoreEmbeddingManager(config)
        
        assert manager.config == config
        assert hasattr(manager, 'logger')
        assert hasattr(manager, '_embedding_model')
    
    @pytest.mark.asyncio
    async def test_process_request_success(self, config, mock_world_data, mock_sparse_areas, mock_expansions):
        """Test: LoreGen processes request successfully and returns expanded world building"""
        from src.agents.loregen import LoreGenAgent
        
        agent = LoreGenAgent(config)
        
        # Mock the internal methods
        agent._extract_plot_id = Mock(return_value="plot-123")
        agent._get_world_building = AsyncMock(return_value=mock_world_data)
        agent._detect_sparse_areas = AsyncMock(return_value=mock_sparse_areas)
        agent._generate_expansions = AsyncMock(return_value=mock_expansions)
        agent._integrate_expansions = AsyncMock(
            return_value=mock_world_data['world_content'] + "\n\nExpanded content here..."
        )
        
        request = AgentRequest(
            content="Use this plot's worldbuilding and expand",
            user_id="test-user",
            session_id="test-session",
            context={"plot_id": "plot-123"}
        )
        
        response = await agent.process_request(request)
        
        assert response.success is True
        assert response.agent_name == "loregen"
        assert response.content_type == ContentType.WORLD_BUILDING
        assert "Lore expansion completed" in response.content
        assert response.parsed_json is not None
        assert response.parsed_json['world_name'] == 'Eldoria'
        assert response.parsed_json['expanded_areas_count'] == 2
        assert 'processing_time_seconds' in response.parsed_json
        assert 'expansion_metrics' in response.parsed_json
    
    @pytest.mark.asyncio
    async def test_process_request_missing_plot_id(self, config):
        """Test: LoreGen handles missing plot_id gracefully"""
        from src.agents.loregen import LoreGenAgent
        
        agent = LoreGenAgent(config)
        
        request = AgentRequest(
            agent_name="loregen",
            content="Use this plot's worldbuilding and expand",
            context={}  # Missing plot_id
        )
        
        response = await agent.process_request(request)
        
        assert response.success is False
        assert "Missing plot_id" in response.content
        assert response.error == "plot_id is required in request context"
    
    @pytest.mark.asyncio
    async def test_process_request_no_world_data(self, config):
        """Test: LoreGen handles missing world building data gracefully"""
        from src.agents.loregen import LoreGenAgent
        
        agent = LoreGenAgent(config)
        agent._extract_plot_id = Mock(return_value="plot-123")
        agent._get_world_building = AsyncMock(return_value=None)
        
        request = AgentRequest(
            content="Use this plot's worldbuilding and expand",
            user_id="test-user",
            session_id="test-session",
            context={"plot_id": "plot-123"}
        )
        
        response = await agent.process_request(request)
        
        assert response.success is False
        assert "No world building found" in response.content
        assert response.error == "No world building data available"
    
    @pytest.mark.asyncio
    async def test_detect_sparse_areas_workflow(self, config, mock_world_data):
        """Test: Sparse area detection workflow integrates all services"""
        from src.agents.loregen import LoreGenAgent
        
        agent = LoreGenAgent(config)
        
        # Mock service calls
        mock_chunks = [
            {'text': 'House Drakmoor rules the eastern provinces', 'metadata': {'topic': 'nobility'}},
            {'text': 'Trade routes connect major cities', 'metadata': {'topic': 'economics'}}
        ]
        mock_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_clusters = [{'cluster_id': 0, 'chunks': [0]}, {'cluster_id': 1, 'chunks': [1]}]
        
        agent._document_processor.chunk_content = AsyncMock(return_value=mock_chunks)
        agent._embedding_manager.get_embeddings = AsyncMock(return_value=mock_embeddings)
        agent._clustering_service.perform_kmeans_clustering = AsyncMock(return_value=mock_clusters)
        agent._clustering_service.detect_sparse_areas = AsyncMock(return_value=mock_sparse_areas)
        
        sparse_areas = await agent._detect_sparse_areas(mock_world_data['world_content'], "plot-123")
        
        assert len(sparse_areas) == 2
        assert sparse_areas[0]['concept_area'] == 'House Drakmoor'
        assert sparse_areas[1]['concept_area'] == 'Trade System'
        agent._document_processor.chunk_content.assert_called_once()
        agent._embedding_manager.get_embeddings.assert_called_once()
        agent._clustering_service.perform_kmeans_clustering.assert_called_once()
        agent._clustering_service.detect_sparse_areas.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_expansions_workflow(self, config, mock_sparse_areas):
        """Test: Expansion generation workflow produces detailed content"""
        from src.agents.loregen import LoreGenAgent
        
        agent = LoreGenAgent(config)
        agent._generate_content = AsyncMock(
            return_value="Detailed expansion content for the sparse area..."
        )
        
        expansions = await agent._generate_expansions(mock_sparse_areas)
        
        assert len(expansions) == 2
        assert all('concept_area' in exp for exp in expansions)
        assert all('expanded_content' in exp for exp in expansions)
        assert all(len(exp['expanded_content']) > 100 for exp in expansions)
    
    @pytest.mark.asyncio
    async def test_integrate_expansions_workflow(self, config, mock_world_data, mock_expansions):
        """Test: Expansion integration maintains content coherence"""
        from src.agents.loregen import LoreGenAgent
        
        agent = LoreGenAgent(config)
        
        integrated_content = await agent._integrate_expansions(
            mock_world_data['world_content'],
            mock_expansions
        )
        
        assert len(integrated_content) > len(mock_world_data['world_content'])
        assert 'House Drakmoor' in integrated_content
        assert 'Trade System' in integrated_content
        # Verify original content is preserved
        assert 'Kingdom of Eldoria' in integrated_content
    
    @pytest.mark.asyncio
    async def test_expansion_metrics_calculation(self, config):
        """Test: Expansion metrics provide detailed analytics"""
        from src.agents.loregen import LoreGenAgent
        
        agent = LoreGenAgent(config)
        
        original_content = "Short original content."
        expanded_content = "Short original content. With much longer expanded detailed content that adds significant value and depth to the world building."
        expansions = [
            {
                'concept_area': 'Test Area',
                'expanded_content': 'With much longer expanded detailed content that adds significant value and depth to the world building.',
                'original_content': 'Short original content.'
            }
        ]
        
        metrics = agent._calculate_expansion_metrics(original_content, expanded_content, expansions)
        
        assert 'original_stats' in metrics
        assert 'expanded_stats' in metrics
        assert 'expansion_summary' in metrics
        assert 'expansion_details' in metrics
        assert metrics['expanded_stats']['words'] > metrics['original_stats']['words']
        assert 'character_expansion_ratio' in metrics['expansion_summary']
        assert len(metrics['expansion_details']) == 1
    
    @pytest.mark.asyncio
    async def test_concept_keywords_extraction(self, config):
        """Test: Concept keywords are extracted correctly for intelligent insertion"""
        from src.agents.loregen import LoreGenAgent
        
        agent = LoreGenAgent(config)
        
        house_keywords = agent._get_concept_keywords('House Drakmoor')
        magic_keywords = agent._get_concept_keywords('Magic System')
        trade_keywords = agent._get_concept_keywords('Trade Economics')
        
        assert 'house' in house_keywords
        assert 'noble' in house_keywords
        assert 'magic' in magic_keywords
        assert 'spell' in magic_keywords
        assert 'trade' in trade_keywords
        assert 'merchant' in trade_keywords
    
    @pytest.mark.asyncio
    async def test_analyze_lore_density_integration(self, config, mock_world_data, mock_sparse_areas):
        """Test: Lore density analysis for orchestrator integration"""
        from src.agents.loregen import LoreGenAgent
        
        agent = LoreGenAgent(config)
        agent._extract_plot_id = Mock(return_value="plot-123")
        agent._get_world_building = AsyncMock(return_value=mock_world_data)
        agent._detect_sparse_areas = AsyncMock(return_value=mock_sparse_areas)
        
        request = AgentRequest(
            content="Analyze density",
            user_id="test-user",
            session_id="test-session",
            context={"plot_id": "plot-123"}
        )
        
        density_analysis = await agent._analyze_lore_density(request)
        
        assert 'needs_expansion' in density_analysis
        assert density_analysis['needs_expansion'] is True
        assert 'sparse_areas' in density_analysis
        assert len(density_analysis['sparse_areas']) <= 3  # Summary for orchestrator
        assert 'overall_density' in density_analysis
        assert 0.0 <= density_analysis['overall_density'] <= 1.0
    
    @pytest.mark.asyncio
    async def test_error_handling_resilience(self, config):
        """Test: Agent handles various error conditions gracefully"""
        from src.agents.loregen import LoreGenAgent
        
        agent = LoreGenAgent(config)
        
        # Test with service failure
        agent._get_world_building = AsyncMock(side_effect=Exception("Database connection failed"))
        
        request = AgentRequest(
            content="Use this plot's worldbuilding and expand",
            user_id="test-user",
            session_id="test-session",
            context={"plot_id": "plot-123"}
        )
        
        response = await agent.process_request(request)
        
        assert response.success is False
        assert "failed" in response.content.lower()
        assert response.error is not None
    
    @pytest.mark.asyncio
    async def test_api_compatibility_preservation(self, config):
        """Test: Refactored agent maintains full API compatibility"""
        from src.agents.loregen import LoreGenAgent
        
        agent = LoreGenAgent(config)
        
        # Verify all expected public methods exist
        assert hasattr(agent, 'process_request')
        assert hasattr(agent, '_get_content_type')
        assert hasattr(agent, '_analyze_lore_density')
        
        # Verify expected attributes
        assert agent.name == "loregen"
        assert hasattr(agent, '_rag_service')
        assert hasattr(agent, '_clustering_service')
        
        # Verify content type
        assert agent._get_content_type() == ContentType.WORLD_BUILDING


class TestLoreRAGService:
    """Test suite for LoreRAGService module"""
    
    @pytest.fixture
    def config(self):
        """Mock configuration"""
        config = Mock(spec=Configuration)
        config.google_cloud_project = "test-project"
        config.google_cloud_location = "us-central1"
        config.model_name = "gemini-2.0-flash-exp"
        return config
    
    @pytest.mark.asyncio
    async def test_rag_service_chunk_content(self, config):
        """Test: RAG service chunks content correctly"""
        from src.agents.loregen_modules.rag_service import LoreRAGService
        
        service = LoreRAGService(config)
        
        content = "This is a test content that should be chunked into smaller pieces for processing."
        
        with patch.object(service, '_create_semantic_chunks') as mock_chunk:
            mock_chunk.return_value = [
                {'text': 'This is a test content', 'metadata': {'chunk_id': 0}},
                {'text': 'that should be chunked', 'metadata': {'chunk_id': 1}}
            ]
            
            chunks = await service.chunk_content(content, chunk_size=20, chunk_overlap=5)
            
            assert len(chunks) == 2
            assert all('text' in chunk for chunk in chunks)
            assert all('metadata' in chunk for chunk in chunks)
            mock_chunk.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rag_service_corpus_management(self, config):
        """Test: RAG service manages Vertex AI corpus correctly"""
        from src.agents.loregen_modules.rag_service import LoreRAGService
        
        service = LoreRAGService(config)
        
        with patch.object(service, '_create_vertex_corpus') as mock_create:
            mock_create.return_value = "corpus-123"
            
            corpus_id = await service.create_corpus_for_plot("plot-123")
            
            assert corpus_id == "corpus-123"
            mock_create.assert_called_once_with("plot-123")
    
    @pytest.mark.asyncio
    async def test_rag_service_chunk_import(self, config):
        """Test: RAG service imports chunks to corpus correctly"""
        from src.agents.loregen_modules.rag_service import LoreRAGService
        
        service = LoreRAGService(config)
        
        chunks = [
            {'text': 'Test chunk 1', 'metadata': {}},
            {'text': 'Test chunk 2', 'metadata': {}}
        ]
        
        with patch.object(service, '_import_to_vertex_corpus') as mock_import:
            mock_import.return_value = True
            
            result = await service.import_chunks_to_corpus("corpus-test", chunks)
            
            assert result is True
            mock_import.assert_called_once_with("corpus-test", chunks)


class TestLoreClusteringService:
    """Test suite for LoreClusteringService module"""
    
    @pytest.mark.asyncio
    async def test_clustering_service_kmeans(self):
        """Test: Clustering service performs k-means correctly"""
        from src.agents.loregen_modules.clustering_service import LoreClusteringService
        
        service = LoreClusteringService()
        
        embeddings = [[0.1, 0.2], [0.2, 0.1], [0.8, 0.9], [0.9, 0.8]]
        chunks = [
            {'text': 'chunk1', 'metadata': {}},
            {'text': 'chunk2', 'metadata': {}},
            {'text': 'chunk3', 'metadata': {}},
            {'text': 'chunk4', 'metadata': {}}
        ]
        
        clusters = await service.perform_kmeans_clustering(embeddings, chunks)
        
        assert len(clusters) > 0
        assert all('cluster_id' in cluster for cluster in clusters)
        assert all('chunks' in cluster for cluster in clusters)
    
    @pytest.mark.asyncio
    async def test_clustering_service_sparse_detection(self):
        """Test: Clustering service detects sparse areas correctly"""
        from src.agents.loregen_modules.clustering_service import LoreClusteringService
        
        service = LoreClusteringService()
        
        embeddings = [[0.1, 0.2], [0.8, 0.9]]
        chunks = [
            {'text': 'sparse chunk', 'metadata': {'topic': 'sparse_area'}},
            {'text': 'another sparse chunk', 'metadata': {'topic': 'sparse_area'}}
        ]
        clusters = [{'cluster_id': 0, 'chunks': [0, 1]}]
        
        sparse_areas = await service.detect_sparse_areas(embeddings, chunks, clusters, max_areas=2)
        
        assert len(sparse_areas) <= 2
        assert all('concept_area' in area for area in sparse_areas)
        assert all('avg_pairwise_distance' in area for area in sparse_areas)


class TestLoreDocumentProcessor:
    """Test suite for LoreDocumentProcessor module"""
    
    @pytest.mark.asyncio
    async def test_document_processor_chunking(self):
        """Test: Document processor creates semantic chunks"""
        from src.agents.loregen_modules.document_processor import LoreDocumentProcessor
        
        processor = LoreDocumentProcessor()
        
        content = "This is a long document that needs to be chunked. It contains multiple concepts and ideas."
        
        chunks = await processor.create_semantic_chunks(content, chunk_size=50, overlap=10)
        
        assert len(chunks) > 0
        assert all('text' in chunk for chunk in chunks)
        assert all('metadata' in chunk for chunk in chunks)
        assert all(chunk.get('estimated_tokens', 0) <= 50 for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_document_processor_concept_extraction(self):
        """Test: Document processor extracts concept areas"""
        from src.agents.loregen_modules.document_processor import LoreDocumentProcessor
        
        processor = LoreDocumentProcessor()
        
        chunks = [
            {'text': 'House Drakmoor rules the eastern provinces', 'metadata': {}},
            {'text': 'The magic system relies on ley lines', 'metadata': {}}
        ]
        
        concepts = await processor.extract_concept_areas(chunks)
        
        assert len(concepts) > 0
        assert all(isinstance(concept, str) for concept in concepts)


class TestLoreEmbeddingManager:
    """Test suite for LoreEmbeddingManager module"""
    
    @pytest.fixture
    def config(self):
        """Mock configuration"""
        config = Mock(spec=Configuration)
        config.google_cloud_project = "test-project"
        config.google_cloud_location = "us-central1"
        return config
    
    @pytest.mark.asyncio
    async def test_embedding_manager_generation(self, config):
        """Test: Embedding manager generates embeddings correctly"""
        from src.agents.loregen_modules.embedding_manager import LoreEmbeddingManager
        
        manager = LoreEmbeddingManager(config)
        
        texts = ["This is test text", "Another test text"]
        
        with patch.object(manager, '_generate_vertex_embeddings') as mock_embed:
            mock_embed.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
            
            embeddings = await manager.get_embeddings(texts)
            
            assert len(embeddings) == 2
            assert all(len(emb) == 3 for emb in embeddings)
            mock_embed.assert_called_once_with(texts)
    
    @pytest.mark.asyncio
    async def test_embedding_manager_caching(self, config):
        """Test: Embedding manager caches embeddings efficiently"""
        from src.agents.loregen_modules.embedding_manager import LoreEmbeddingManager
        
        manager = LoreEmbeddingManager(config)
        
        texts = ["Cached text"]
        
        with patch.object(manager, '_generate_vertex_embeddings') as mock_embed:
            mock_embed.return_value = [[0.1, 0.2, 0.3]]
            
            # First call should generate
            embeddings1 = await manager.get_embeddings(texts)
            # Second call should use cache
            embeddings2 = await manager.get_embeddings(texts)
            
            assert embeddings1 == embeddings2
            mock_embed.assert_called_once()  # Only called once due to caching