"""
Clustering and Sparse Detection Service
Performs k-means clustering on Vertex AI embeddings and detects sparse areas
using average pairwise distance analysis.
Based on confirmed requirements:
- K-means clustering on 768-dimensional embeddings
- Average pairwise distance calculation
- "Large radius => sparse lore => expansion needed" formula
- Top 5 sparse areas detection (no threshold, just limit count)
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

try:
    from sklearn.cluster import KMeans
    from sklearn.metrics.pairwise import cosine_distances
    from sklearn.metrics import silhouette_score
except ImportError as e:
    logging.error(f"scikit-learn not available: {e}")
    KMeans = None
    cosine_distances = None


@dataclass
class SparseArea:
    """Represents a sparse area detected in the lore"""
    concept_area: str
    avg_pairwise_distance: float
    cluster_id: int
    chunk_indices: List[int]
    expansion_needed: bool
    chunks: List[Dict[str, Any]]


class ClusteringService:
    """
    Service for k-means clustering and sparse area detection on embeddings.
    """
    
    def __init__(self):
        """Initialize clustering service"""
        if not KMeans:
            raise ImportError("scikit-learn not installed. Run: pip install scikit-learn")
            
        self.logger = logging.getLogger(__name__)
    
    async def perform_kmeans_clustering(
        self,
        embeddings: List[List[float]],
        chunks: List[Dict[str, Any]],
        n_clusters: Optional[int] = None
    ) -> Dict[int, List[int]]:
        """
        Perform k-means clustering on 768-dimensional embeddings.
        Returns dict mapping cluster_id -> list of chunk indices.
        """
        if not embeddings:
            raise ValueError("Embeddings list cannot be empty")
            
        if len(embeddings) != len(chunks):
            raise ValueError("Embeddings and chunks length mismatch")
            
        # Validate embedding dimensions (should be 768 from Vertex AI)
        if embeddings and len(embeddings[0]) != 768:
            raise ValueError(f"Expected 768-dimensional embeddings, got {len(embeddings[0])}")
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings)
        
        # Determine optimal cluster count if not provided
        if n_clusters is None:
            n_clusters = await self.detect_optimal_clusters(embeddings)
            
        # Handle edge cases
        if len(embeddings) == 1:
            return {0: [0]}
        
        if n_clusters >= len(embeddings):
            # Each point is its own cluster
            return {i: [i] for i in range(len(embeddings))}
        
        try:
            # Perform k-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings_array)
            
            # Group chunk indices by cluster
            clusters = {}
            for chunk_idx, cluster_id in enumerate(cluster_labels):
                if cluster_id not in clusters:
                    clusters[cluster_id] = []
                clusters[cluster_id].append(chunk_idx)
                
            self.logger.info(f"Created {len(clusters)} clusters from {len(embeddings)} embeddings")
            return clusters
            
        except Exception as e:
            self.logger.error(f"K-means clustering failed: {e}")
            raise
    
    async def detect_optimal_clusters(
        self,
        embeddings: List[List[float]],
        max_k: Optional[int] = None
    ) -> int:
        """
        Detect optimal number of clusters using silhouette analysis.
        """
        if max_k is None:
            max_k = min(len(embeddings) - 1, 8)  # Reasonable upper limit
            
        max_k = max(2, min(max_k, len(embeddings) - 1))
        
        if max_k < 2:
            return 1
            
        embeddings_array = np.array(embeddings)
        best_k = 2
        best_score = -1
        
        try:
            for k in range(2, max_k + 1):
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(embeddings_array)
                
                # Calculate silhouette score
                score = silhouette_score(embeddings_array, cluster_labels, metric='cosine')
                
                if score > best_score:
                    best_score = score
                    best_k = k
                    
            self.logger.info(f"Optimal cluster count: {best_k} (silhouette score: {best_score:.3f})")
            return best_k
            
        except Exception as e:
            self.logger.warning(f"Optimal cluster detection failed, using default: {e}")
            return min(3, len(embeddings))
    
    async def calculate_average_pairwise_distance(
        self,
        cluster_embeddings: List[List[float]]
    ) -> float:
        """
        Calculate average pairwise cosine distance within a cluster.
        Large radius (distance) indicates sparse lore.
        """
        if not cluster_embeddings:
            raise ValueError("Embedding cluster cannot be empty")
            
        if len(cluster_embeddings) == 1:
            return 0.0  # Single point has no distance
            
        # Convert to numpy array
        embeddings_array = np.array(cluster_embeddings)
        
        try:
            # Calculate pairwise cosine distances
            distances = cosine_distances(embeddings_array)
            
            # Get upper triangular indices (avoid diagonal and duplicates)
            triu_indices = np.triu_indices_from(distances, k=1)
            pairwise_distances = distances[triu_indices]
            
            # Calculate average
            avg_distance = np.mean(pairwise_distances)
            
            return float(avg_distance)
            
        except Exception as e:
            self.logger.error(f"Pairwise distance calculation failed: {e}")
            raise
    
    async def detect_sparse_areas(
        self,
        embeddings: List[List[float]],
        chunks: List[Dict[str, Any]],
        clusters: Dict[int, List[int]],
        max_areas: int = 5
    ) -> List[SparseArea]:
        """
        Detect sparse areas using large radius formula.
        Returns top N sparse areas ranked by average pairwise distance.
        """
        sparse_areas = []
        
        for cluster_id, chunk_indices in clusters.items():
            if len(chunk_indices) == 0:
                continue
                
            # Get embeddings for this cluster
            cluster_embeddings = [embeddings[idx] for idx in chunk_indices]
            cluster_chunks = [chunks[idx] for idx in chunk_indices]
            
            # Calculate average pairwise distance
            avg_distance = await self.calculate_average_pairwise_distance(cluster_embeddings)
            
            # Extract concept area from chunks
            concept_area = await self.extract_concept_area(cluster_chunks)
            
            # Create sparse area object
            sparse_area = SparseArea(
                concept_area=concept_area,
                avg_pairwise_distance=avg_distance,
                cluster_id=cluster_id,
                chunk_indices=chunk_indices,
                expansion_needed=True,  # All areas are candidates for expansion
                chunks=cluster_chunks
            )
            
            sparse_areas.append(sparse_area)
        
        # Sort by distance (largest radius first = most sparse first)
        sparse_areas.sort(key=lambda x: x.avg_pairwise_distance, reverse=True)
        
        # Limit to top N areas
        limited_areas = sparse_areas[:max_areas]
        
        self.logger.info(f"Detected {len(limited_areas)} sparse areas (limited to {max_areas})")
        
        # Convert to dict format for consistency with tests
        return [
            {
                'concept_area': area.concept_area,
                'avg_pairwise_distance': area.avg_pairwise_distance,
                'cluster_id': area.cluster_id,
                'chunk_indices': area.chunk_indices,
                'expansion_needed': area.expansion_needed,
                'chunks': area.chunks
            }
            for area in limited_areas
        ]
    
    async def extract_concept_area(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Extract main concept area from chunk metadata or content.
        """
        if not chunks:
            return "Unknown Area"
            
        # Try to extract from metadata first
        concept_areas = []
        for chunk in chunks:
            metadata = chunk.get('metadata', {})
            concept_area = metadata.get('concept_area', '')
            if concept_area:
                concept_areas.append(concept_area)
        
        if concept_areas:
            # Return most common concept area
            return max(set(concept_areas), key=concept_areas.count)
        
        # Fallback to text analysis
        all_text = " ".join([chunk.get('text', '') for chunk in chunks])
        return self._extract_concept_from_text(all_text)
    
    def _extract_concept_from_text(self, text: str) -> str:
        """Extract concept area from raw text"""
        import re
        
        # Look for House names
        house_match = re.search(r'\bHouse\s+(\w+)', text, re.IGNORECASE)
        if house_match:
            return f"House {house_match.group(1)}"
        
        # Look for other key concepts
        text_lower = text.lower()
        
        if 'magic' in text_lower:
            return "Magic System"
        elif any(word in text_lower for word in ['trade', 'economy', 'merchant']):
            return "Economic System"
        elif any(word in text_lower for word in ['kingdom', 'realm', 'geography']):
            return "Geography"
        elif any(word in text_lower for word in ['character', 'people', 'person']):
            return "Characters"
        elif any(word in text_lower for word in ['politic', 'govern', 'rule']):
            return "Political System"
        
        # Extract proper nouns as fallback
        proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', text)
        if proper_nouns:
            return max(set(proper_nouns), key=proper_nouns.count)
            
        return "General Lore"
    
    async def get_embeddings_from_rag_service(
        self,
        texts: List[str],
        rag_service=None
    ) -> List[List[float]]:
        """
        Get embeddings from RAG service for clustering.
        Integration point with Vertex AI RAG service.
        """
        if rag_service and hasattr(rag_service, 'get_embeddings'):
            return await rag_service.get_embeddings(texts)
        else:
            # Fallback for testing
            self.logger.warning("No RAG service provided, using mock embeddings")
            return [[0.1] * 768 for _ in texts]
    
    async def analyze_content_sparsity(
        self,
        embeddings: List[List[float]],
        chunks: List[Dict[str, Any]],
        plot_id: str
    ) -> Dict[str, Any]:
        """
        Complete sparsity analysis workflow.
        Returns comprehensive analysis results.
        """
        try:
            # Perform clustering
            clusters = await self.perform_kmeans_clustering(embeddings, chunks)
            
            # Detect sparse areas
            sparse_areas = await self.detect_sparse_areas(embeddings, chunks, clusters)
            
            # Create analysis summary
            analysis_summary = {
                'total_chunks': len(chunks),
                'cluster_count': len(clusters),
                'sparse_areas_found': len(sparse_areas),
                'plot_id': plot_id
            }
            
            return {
                'clusters': clusters,
                'sparse_areas': sparse_areas,
                'analysis_summary': analysis_summary
            }
            
        except Exception as e:
            self.logger.error(f"Content sparsity analysis failed for plot {plot_id}: {e}")
            raise
    
    async def calculate_sparse_areas(
        self,
        embeddings: List[List[float]],
        chunks: List[Dict[str, Any]],
        clusters: Dict[int, List[int]]
    ) -> List[Dict[str, Any]]:
        """
        Alternative method name for compatibility with tests.
        Same as detect_sparse_areas but with different signature.
        """
        return await self.detect_sparse_areas(embeddings, chunks, clusters)