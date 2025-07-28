"""
LoreEmbeddingManager Module
Handles embedding generation, caching, and management for LoreGen agent.
Provides optimized embedding operations for semantic analysis.
"""

import asyncio
import hashlib
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import json

try:
    import vertexai
    from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput
    from google.cloud import aiplatform
except ImportError as e:
    logging.error(f"Vertex AI dependencies not available: {e}")
    vertexai = None
    TextEmbeddingModel = None

from ...core.configuration import Configuration


@dataclass
class EmbeddingCache:
    """Cache entry for embeddings"""
    text_hash: str
    embedding: List[float]
    model_name: str
    timestamp: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)


@dataclass
class EmbeddingBatch:
    """Batch of embeddings for processing"""
    texts: List[str]
    embeddings: List[List[float]]
    processing_time: float
    model_used: str
    cache_hits: int
    cache_misses: int


class LoreEmbeddingManager:
    """
    Service for managing embeddings specifically for LoreGen agent.
    Handles generation, caching, and optimization of text embeddings.
    """
    
    def __init__(self, config: Optional[Configuration] = None):
        """Initialize embedding manager with configuration"""
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
            
            # Initialize embedding model
            self._embedding_model_name = "text-embedding-004"
            self._embedding_model = TextEmbeddingModel.from_pretrained(self._embedding_model_name)
            self._embedding_dimension = 768
            
            self.logger.info(f"Embedding model initialized: {self._embedding_model_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Vertex AI embedding model: {e}")
            self._embedding_model = None
        
        # Initialize cache
        self._embedding_cache: Dict[str, EmbeddingCache] = {}
        self._cache_max_size = 1000
        self._cache_ttl = 3600  # 1 hour
        
        # Batch processing settings
        self._batch_size = 32
        self._max_concurrent_batches = 4
        
        # Performance metrics
        self._metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_processing_time': 0.0,
            'average_embedding_time': 0.0
        }
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a list of texts with caching and batch optimization.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            if not texts:
                return []
            
            start_time = time.time()
            
            # Process in batches if needed
            if len(texts) > self._batch_size:
                embeddings = await self._process_large_batch(texts)
            else:
                embeddings = await self._process_single_batch(texts)
            
            # Update metrics
            processing_time = time.time() - start_time
            self._update_metrics(len(texts), processing_time)
            
            self.logger.info(f"Generated embeddings for {len(texts)} texts in {processing_time:.2f}s")
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {e}")
            return []
    
    async def _process_large_batch(self, texts: List[str]) -> List[List[float]]:
        """Process large batch of texts by splitting into smaller batches"""
        all_embeddings = []
        
        # Split into batches
        batches = [
            texts[i:i + self._batch_size]
            for i in range(0, len(texts), self._batch_size)
        ]
        
        # Process batches concurrently (with limit)
        semaphore = asyncio.Semaphore(self._max_concurrent_batches)
        
        async def process_batch_with_semaphore(batch_texts):
            async with semaphore:
                return await self._process_single_batch(batch_texts)
        
        # Process all batches
        batch_results = await asyncio.gather(*[
            process_batch_with_semaphore(batch) 
            for batch in batches
        ])
        
        # Combine results
        for batch_embeddings in batch_results:
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    async def _process_single_batch(self, texts: List[str]) -> List[List[float]]:
        """Process a single batch of texts"""
        # Check cache first
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cached_embedding = await self._get_from_cache(text)
            if cached_embedding is not None:
                embeddings.append((i, cached_embedding))
                self._metrics['cache_hits'] += 1
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
                self._metrics['cache_misses'] += 1
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            new_embeddings = await self._generate_vertex_embeddings(uncached_texts)
            
            # Cache new embeddings
            for text, embedding in zip(uncached_texts, new_embeddings):
                await self._add_to_cache(text, embedding)
            
            # Add to results
            for idx, embedding in zip(uncached_indices, new_embeddings):
                embeddings.append((idx, embedding))
        
        # Sort by original index and extract embeddings
        embeddings.sort(key=lambda x: x[0])
        return [emb for _, emb in embeddings]
    
    async def _generate_vertex_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Vertex AI"""
        if not self._embedding_model:
            self.logger.error("Embedding model not available")
            return [[0.0] * self._embedding_dimension for _ in texts]
        
        try:
            # Prepare embedding inputs
            embedding_inputs = [
                TextEmbeddingInput(text=text, task_type="RETRIEVAL_DOCUMENT")
                for text in texts
            ]
            
            # Generate embeddings
            embeddings_response = await asyncio.to_thread(
                self._embedding_model.get_embeddings,
                embedding_inputs
            )
            
            # Extract embedding vectors
            embeddings = [
                embedding.values for embedding in embeddings_response
            ]
            
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Vertex AI embedding generation failed: {e}")
            # Return zero embeddings as fallback
            return [[0.0] * self._embedding_dimension for _ in texts]
    
    async def _get_from_cache(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache if available and not expired"""
        text_hash = self._hash_text(text)
        
        if text_hash not in self._embedding_cache:
            return None
        
        cache_entry = self._embedding_cache[text_hash]
        
        # Check if expired
        if time.time() - cache_entry.timestamp > self._cache_ttl:
            del self._embedding_cache[text_hash]
            return None
        
        # Update access info
        cache_entry.access_count += 1
        cache_entry.last_accessed = time.time()
        
        return cache_entry.embedding
    
    async def _add_to_cache(self, text: str, embedding: List[float]):
        """Add embedding to cache"""
        text_hash = self._hash_text(text)
        
        # Check cache size limit
        if len(self._embedding_cache) >= self._cache_max_size:
            await self._evict_cache_entries()
        
        # Add to cache
        cache_entry = EmbeddingCache(
            text_hash=text_hash,
            embedding=embedding,
            model_name=self._embedding_model_name,
            timestamp=time.time()
        )
        
        self._embedding_cache[text_hash] = cache_entry
    
    def _hash_text(self, text: str) -> str:
        """Generate hash for text to use as cache key"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    async def _evict_cache_entries(self):
        """Evict old cache entries when cache is full"""
        # Sort by last accessed time and remove oldest 25%
        cache_items = list(self._embedding_cache.items())
        cache_items.sort(key=lambda x: x[1].last_accessed)
        
        num_to_remove = len(cache_items) // 4
        for i in range(num_to_remove):
            text_hash, _ = cache_items[i]
            del self._embedding_cache[text_hash]
        
        self.logger.info(f"Evicted {num_to_remove} cache entries")
    
    def _update_metrics(self, num_texts: int, processing_time: float):
        """Update performance metrics"""
        self._metrics['total_requests'] += num_texts
        self._metrics['total_processing_time'] += processing_time
        
        if self._metrics['total_requests'] > 0:
            self._metrics['average_embedding_time'] = (
                self._metrics['total_processing_time'] / self._metrics['total_requests']
            )
    
    async def precompute_embeddings(
        self,
        texts: List[str],
        batch_size: Optional[int] = None
    ) -> Dict[str, List[float]]:
        """
        Precompute and cache embeddings for a list of texts.
        
        Args:
            texts: Texts to precompute embeddings for
            batch_size: Override default batch size
            
        Returns:
            Dictionary mapping text hash to embedding
        """
        try:
            original_batch_size = self._batch_size
            if batch_size:
                self._batch_size = batch_size
            
            embeddings = await self.get_embeddings(texts)
            
            # Create hash-to-embedding mapping
            result = {}
            for text, embedding in zip(texts, embeddings):
                text_hash = self._hash_text(text)
                result[text_hash] = embedding
            
            self.logger.info(f"Precomputed embeddings for {len(texts)} texts")
            return result
            
        except Exception as e:
            self.logger.error(f"Precomputation failed: {e}")
            return {}
        finally:
            if batch_size:
                self._batch_size = original_batch_size
    
    async def get_similar_embeddings(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
        top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Find most similar embeddings to query.
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embeddings
            top_k: Number of top results to return
            
        Returns:
            List of (index, similarity_score) tuples
        """
        try:
            similarities = []
            
            for i, candidate in enumerate(candidate_embeddings):
                similarity = await self._calculate_cosine_similarity(
                    query_embedding, candidate
                )
                similarities.append((i, similarity))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            self.logger.error(f"Similarity calculation failed: {e}")
            return []
    
    async def _calculate_cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            # Convert to numpy arrays for efficiency
            import numpy as np
            
            a = np.array(vec1)
            b = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Cosine similarity calculation failed: {e}")
            return 0.0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_size': len(self._embedding_cache),
            'cache_max_size': self._cache_max_size,
            'cache_hit_rate': (
                self._metrics['cache_hits'] / 
                max(1, self._metrics['cache_hits'] + self._metrics['cache_misses'])
            ),
            'total_cache_hits': self._metrics['cache_hits'],
            'total_cache_misses': self._metrics['cache_misses']
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            'total_requests': self._metrics['total_requests'],
            'total_processing_time': self._metrics['total_processing_time'],
            'average_embedding_time': self._metrics['average_embedding_time'],
            'cache_stats': self.get_cache_stats(),
            'batch_size': self._batch_size,
            'max_concurrent_batches': self._max_concurrent_batches,
            'embedding_dimension': self._embedding_dimension,
            'model_name': self._embedding_model_name
        }
    
    async def clear_cache(self):
        """Clear the embedding cache"""
        self._embedding_cache.clear()
        self.logger.info("Embedding cache cleared")
    
    async def warm_cache(self, texts: List[str]):
        """Warm the cache by precomputing embeddings"""
        self.logger.info(f"Warming cache with {len(texts)} texts")
        await self.precompute_embeddings(texts)
    
    def configure_caching(
        self,
        max_size: Optional[int] = None,
        ttl: Optional[int] = None
    ):
        """Configure cache settings"""
        if max_size is not None:
            self._cache_max_size = max_size
        if ttl is not None:
            self._cache_ttl = ttl
        
        self.logger.info(
            f"Cache configured: max_size={self._cache_max_size}, "
            f"ttl={self._cache_ttl}s"
        )
    
    def configure_batching(
        self,
        batch_size: Optional[int] = None,
        max_concurrent_batches: Optional[int] = None
    ):
        """Configure batch processing settings"""
        if batch_size is not None:
            self._batch_size = batch_size
        if max_concurrent_batches is not None:
            self._max_concurrent_batches = max_concurrent_batches
        
        self.logger.info(
            f"Batching configured: batch_size={self._batch_size}, "
            f"max_concurrent={self._max_concurrent_batches}"
        )