"""
LoreRAGService Module
Handles RAG (Retrieval Augmented Generation) operations for LoreGen agent.
Includes content chunking, corpus management, and Vertex AI RAG integration.
"""

import asyncio
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import vertexai
    from vertexai import rag
    from vertexai.generative_models import GenerativeModel, Tool
    from google.cloud import aiplatform
except ImportError as e:
    logging.error(f"Vertex AI dependencies not available: {e}")
    vertexai = None
    rag = None

from ...core.configuration import Configuration


@dataclass
class ChunkMetadata:
    """Metadata for semantic chunks"""
    concept_area: str
    topic: str
    chunk_order: int
    importance: str = "medium"
    semantic_tags: List[str] = None


class LoreRAGService:
    """
    Service for Vertex AI RAG operations specifically for LoreGen agent.
    Handles semantic chunking, corpus management, and content retrieval.
    """
    
    def __init__(self, config: Optional[Configuration] = None):
        """Initialize LoreRAG service with configuration"""
        if not vertexai:
            raise ImportError("Vertex AI dependencies not installed. Run: pip install google-cloud-aiplatform")
            
        self.config = config or Configuration()
        self.logger = logging.getLogger(__name__)
        
        # Initialize Vertex AI
        try:
            vertexai.init(
                project=self.config.google_cloud_project,
                location=self.config.google_cloud_location
            )
            self._vertex_client = rag
            self.logger.info("Vertex AI RAG client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Vertex AI: {e}")
            self._vertex_client = None
    
    async def chunk_content(
        self,
        content: str,
        chunk_size: int = 80,
        chunk_overlap: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Create semantic chunks from world building content.
        
        Args:
            content: World building text to chunk
            chunk_size: Target tokens per chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of chunks with text and metadata
        """
        try:
            # Preprocess content
            cleaned_content = self._preprocess_content(content)
            
            # Create semantic chunks
            chunks = await self._create_semantic_chunks(
                cleaned_content,
                chunk_size,
                chunk_overlap
            )
            
            self.logger.info(f"Created {len(chunks)} semantic chunks")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Content chunking failed: {e}")
            return []
    
    def _preprocess_content(self, content: str) -> str:
        """Preprocess content for better chunking"""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content.strip())
        
        # Ensure proper sentence endings
        content = re.sub(r'([.!?])\s*([A-Z])', r'\1\n\n\2', content)
        
        # Clean up formatting
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content
    
    async def _create_semantic_chunks(
        self,
        content: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[Dict[str, Any]]:
        """Create semantic chunks using improved algorithm"""
        chunks = []
        
        # Split into paragraphs first
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        current_chunk = ""
        chunk_order = 0
        
        for paragraph in paragraphs:
            # Estimate token count (rough: 1 token ≈ 4 characters)
            paragraph_tokens = len(paragraph) // 4
            current_tokens = len(current_chunk) // 4
            
            if current_tokens + paragraph_tokens <= chunk_size:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Finish current chunk and start new one
                if current_chunk:
                    chunks.append(await self._create_chunk_with_metadata(
                        current_chunk, chunk_order
                    ))
                    chunk_order += 1
                
                # Handle overlap
                if chunks and chunk_overlap > 0:
                    overlap_text = self._get_overlap_text(current_chunk, chunk_overlap)
                    current_chunk = overlap_text + "\n\n" + paragraph if overlap_text else paragraph
                else:
                    current_chunk = paragraph
        
        # Add final chunk
        if current_chunk:
            chunks.append(await self._create_chunk_with_metadata(
                current_chunk, chunk_order
            ))
        
        return chunks
    
    async def _create_chunk_with_metadata(
        self,
        text: str,
        chunk_order: int
    ) -> Dict[str, Any]:
        """Create chunk with rich metadata"""
        # Extract concept area from text
        concept_area = await self._extract_concept_area(text)
        
        # Determine topic
        topic = self._determine_topic(text)
        
        # Calculate importance
        importance = self._calculate_importance(text)
        
        # Extract semantic tags
        semantic_tags = self._extract_semantic_tags(text)
        
        metadata = ChunkMetadata(
            concept_area=concept_area,
            topic=topic,
            chunk_order=chunk_order,
            importance=importance,
            semantic_tags=semantic_tags
        )
        
        return {
            'text': text,
            'metadata': metadata.__dict__,
            'token_count': len(text) // 4,  # Rough estimate
            'char_count': len(text)
        }
    
    async def _extract_concept_area(self, text: str) -> str:
        """Extract the main concept area from chunk text"""
        text_lower = text.lower()
        
        # Look for specific patterns
        patterns = {
            'nobility': ['house', 'lord', 'lady', 'noble', 'family', 'dynasty'],
            'magic': ['magic', 'spell', 'wizard', 'mage', 'enchant', 'arcane'],
            'geography': ['kingdom', 'land', 'region', 'territory', 'realm', 'province'],
            'economics': ['trade', 'merchant', 'gold', 'commerce', 'wealth', 'economy'],
            'politics': ['rule', 'govern', 'king', 'queen', 'council', 'court'],
            'religion': ['god', 'temple', 'priest', 'divine', 'sacred', 'holy'],
            'military': ['army', 'soldier', 'war', 'battle', 'guard', 'knight'],
            'culture': ['tradition', 'custom', 'festival', 'art', 'music', 'dance']
        }
        
        for concept, keywords in patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return concept.title()
        
        # Extract from proper nouns if no pattern match
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', text)
        if proper_nouns:
            return proper_nouns[0]
        
        return "General"
    
    def _determine_topic(self, text: str) -> str:
        """Determine the primary topic of the chunk"""
        # Simple keyword-based topic detection
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['house', 'family', 'noble']):
            return 'nobility'
        elif any(word in text_lower for word in ['magic', 'spell', 'wizard']):
            return 'magic'
        elif any(word in text_lower for word in ['trade', 'merchant', 'commerce']):
            return 'economics'
        elif any(word in text_lower for word in ['land', 'region', 'territory']):
            return 'geography'
        else:
            return 'general'
    
    def _calculate_importance(self, text: str) -> str:
        """Calculate the importance level of the chunk"""
        # Heuristics for importance
        if len(text) > 300:
            return "high"
        elif len(text) > 150:
            return "medium"
        else:
            return "low"
    
    def _extract_semantic_tags(self, text: str) -> List[str]:
        """Extract semantic tags from text"""
        tags = []
        text_lower = text.lower()
        
        # Common fantasy/world-building tags
        tag_patterns = {
            'leadership': ['king', 'queen', 'lord', 'ruler', 'leader'],
            'conflict': ['war', 'battle', 'fight', 'enemy', 'conflict'],
            'mystical': ['magic', 'magical', 'enchanted', 'mystical'],
            'historical': ['ancient', 'old', 'history', 'past', 'founded'],
            'geographical': ['mountain', 'river', 'forest', 'city', 'capital'],
            'social': ['people', 'culture', 'tradition', 'custom', 'society']
        }
        
        for tag, keywords in tag_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)
        
        return tags
    
    def _get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """Get overlap text for chunk continuity"""
        words = text.split()
        overlap_words = min(overlap_tokens, len(words))
        return ' '.join(words[-overlap_words:]) if overlap_words > 0 else ""
    
    async def create_corpus_for_plot(self, plot_id: str) -> Optional[str]:
        """Create a new Vertex AI RAG corpus for a plot"""
        if not self._vertex_client:
            self.logger.error("Vertex AI client not available")
            return None
        
        try:
            corpus_name = f"corpus-book-{plot_id}"
            vertex_corpus_id = await self._create_vertex_corpus(plot_id)
            
            self.logger.info(f"Created Vertex AI corpus {vertex_corpus_id} for plot {plot_id}")
            return vertex_corpus_id
            
        except Exception as e:
            self.logger.error(f"Failed to create corpus for plot {plot_id}: {e}")
            return None
    
    async def _create_vertex_corpus(self, plot_id: str) -> str:
        """Create corpus in Vertex AI RAG"""
        # This would be the actual Vertex AI corpus creation
        # For now, return a mock corpus ID
        return f"vertex-corpus-{plot_id}"
    
    async def import_chunks_to_corpus(
        self,
        corpus_name: str,
        chunks: List[Dict[str, Any]]
    ) -> bool:
        """Import chunks to Vertex AI corpus"""
        if not self._vertex_client:
            self.logger.error("Vertex AI client not available")
            return False
        
        try:
            result = await self._import_to_vertex_corpus(corpus_name, chunks)
            self.logger.info(f"Imported {len(chunks)} chunks to corpus {corpus_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to import chunks to corpus {corpus_name}: {e}")
            return False
    
    async def _import_to_vertex_corpus(
        self,
        corpus_name: str,
        chunks: List[Dict[str, Any]]
    ) -> bool:
        """Import chunks to Vertex AI corpus"""
        # This would be the actual Vertex AI import operation
        # For now, simulate success
        await asyncio.sleep(0.1)  # Simulate API call
        return True
    
    async def query_corpus(
        self,
        corpus_name: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Query the RAG corpus for relevant chunks"""
        if not self._vertex_client:
            self.logger.error("Vertex AI client not available")
            return []
        
        try:
            results = await self._query_vertex_corpus(corpus_name, query, top_k)
            self.logger.info(f"Retrieved {len(results)} results from corpus {corpus_name}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to query corpus {corpus_name}: {e}")
            return []
    
    async def _query_vertex_corpus(
        self,
        corpus_name: str,
        query: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Query Vertex AI corpus"""
        # This would be the actual Vertex AI query operation
        # For now, return mock results
        await asyncio.sleep(0.1)  # Simulate API call
        return []
    
    def get_corpus_stats(self, corpus_name: str) -> Dict[str, Any]:
        """Get statistics about a corpus"""
        # This would return actual corpus statistics
        return {
            'chunk_count': 0,
            'total_tokens': 0,
            'created_at': None,
            'last_updated': None
        }