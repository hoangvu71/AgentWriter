"""
LoreClusteringService Module
Handles k-means clustering and sparse area detection for LoreGen agent.
Analyzes embeddings to identify sparse lore areas needing expansion.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

try:
    from sklearn.cluster import KMeans
    from sklearn.metrics.pairwise import cosine_distances, euclidean_distances
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler
except ImportError as e:
    logging.error(f"scikit-learn not available: {e}")
    KMeans = None
    cosine_distances = None


@dataclass
class ClusterAnalysis:
    """Analysis results for a cluster"""
    cluster_id: int
    centroid: List[float]
    chunk_indices: List[int]
    avg_pairwise_distance: float
    silhouette_score: float
    concept_area: str
    density_score: float


@dataclass
class SparseArea:
    """Represents a sparse area detected in the lore"""
    concept_area: str
    avg_pairwise_distance: float
    cluster_id: int
    chunk_indices: List[int]
    expansion_needed: bool
    chunks: List[Dict[str, Any]]
    density_score: float


class LoreClusteringService:
    """
    Service for k-means clustering and sparse area detection specifically for LoreGen.
    Analyzes embeddings to identify areas needing lore expansion.
    """
    
    def __init__(self):
        """Initialize clustering service"""
        if not KMeans:
            raise ImportError("scikit-learn not installed. Run: pip install scikit-learn")
            
        self.logger = logging.getLogger(__name__)
        self._kmeans_clusters = 5  # Default cluster count
        self._min_cluster_size = 2
        self._distance_threshold = 0.7
    
    async def perform_kmeans_clustering(
        self,
        embeddings: List[List[float]],
        chunks: List[Dict[str, Any]],
        n_clusters: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform k-means clustering on embeddings.
        
        Args:
            embeddings: List of embedding vectors
            chunks: Corresponding chunk data
            n_clusters: Number of clusters (auto-determined if None)
            
        Returns:
            List of cluster information
        """
        try:
            if len(embeddings) == 0:
                self.logger.warning("No embeddings provided for clustering")
                return []
            
            # Convert to numpy array
            X = np.array(embeddings)
            
            # Normalize embeddings
            X_normalized = self._normalize_embeddings(X)
            
            # Determine optimal cluster count
            optimal_clusters = n_clusters or await self._determine_optimal_clusters(X_normalized)
            
            # Perform k-means clustering
            clusters = await self._perform_kmeans(X_normalized, chunks, optimal_clusters)
            
            self.logger.info(f"Created {len(clusters)} clusters from {len(embeddings)} embeddings")
            return clusters
            
        except Exception as e:
            self.logger.error(f"K-means clustering failed: {e}")
            return []
    
    def _normalize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """Normalize embeddings for better clustering"""
        # Use L2 normalization for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        return embeddings / norms
    
    async def _determine_optimal_clusters(self, embeddings: np.ndarray) -> int:
        """Determine optimal number of clusters using elbow method"""
        n_samples = len(embeddings)
        
        # Limit cluster range based on data size
        max_clusters = min(10, n_samples // 2)
        min_clusters = min(2, n_samples)
        
        if max_clusters <= min_clusters:
            return min_clusters
        
        # Test different cluster counts
        inertias = []
        cluster_range = range(min_clusters, max_clusters + 1)
        
        for k in cluster_range:
            try:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                kmeans.fit(embeddings)
                inertias.append(kmeans.inertia_)
            except Exception as e:
                self.logger.warning(f"Failed to fit k-means with k={k}: {e}")
                continue
        
        if not inertias:
            return self._kmeans_clusters
        
        # Find elbow point
        optimal_k = self._find_elbow_point(cluster_range, inertias)
        return optimal_k
    
    def _find_elbow_point(self, k_range: range, inertias: List[float]) -> int:
        """Find elbow point in inertia curve"""
        if len(inertias) < 2:
            return k_range[0]
        
        # Calculate rate of change
        deltas = []
        for i in range(1, len(inertias)):
            delta = inertias[i-1] - inertias[i]
            deltas.append(delta)
        
        # Find the point where improvement starts diminishing
        if len(deltas) >= 2:
            for i in range(1, len(deltas)):
                if deltas[i] < deltas[i-1] * 0.5:  # Significant drop in improvement
                    return list(k_range)[i]
        
        # Default to middle of range
        return list(k_range)[len(k_range) // 2]
    
    async def _perform_kmeans(
        self,
        embeddings: np.ndarray,
        chunks: List[Dict[str, Any]],
        n_clusters: int
    ) -> List[Dict[str, Any]]:
        """Perform k-means clustering and analyze results"""
        try:
            # Fit k-means
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings)
            
            # Calculate silhouette score
            overall_silhouette = silhouette_score(embeddings, cluster_labels) if len(set(cluster_labels)) > 1 else 0
            
            # Analyze each cluster
            clusters = []
            for cluster_id in range(n_clusters):
                cluster_analysis = await self._analyze_cluster(
                    cluster_id,
                    embeddings,
                    chunks,
                    cluster_labels,
                    kmeans.cluster_centers_[cluster_id]
                )
                
                if cluster_analysis:
                    clusters.append({
                        'cluster_id': cluster_analysis.cluster_id,
                        'centroid': cluster_analysis.centroid.tolist(),
                        'chunk_indices': cluster_analysis.chunk_indices,
                        'avg_pairwise_distance': cluster_analysis.avg_pairwise_distance,
                        'silhouette_score': cluster_analysis.silhouette_score,
                        'concept_area': cluster_analysis.concept_area,
                        'density_score': cluster_analysis.density_score,
                        'chunks': [chunks[i] for i in cluster_analysis.chunk_indices]
                    })
            
            self.logger.info(f"K-means clustering completed with silhouette score: {overall_silhouette:.3f}")
            return clusters
            
        except Exception as e:
            self.logger.error(f"K-means execution failed: {e}")
            return []
    
    async def _analyze_cluster(
        self,
        cluster_id: int,
        embeddings: np.ndarray,
        chunks: List[Dict[str, Any]],
        cluster_labels: np.ndarray,
        centroid: np.ndarray
    ) -> Optional[ClusterAnalysis]:
        """Analyze a single cluster in detail"""
        try:
            # Get indices of points in this cluster
            cluster_indices = np.where(cluster_labels == cluster_id)[0].tolist()
            
            if len(cluster_indices) < self._min_cluster_size:
                return None
            
            # Extract cluster embeddings
            cluster_embeddings = embeddings[cluster_indices]
            
            # Calculate average pairwise distance
            avg_distance = self._calculate_avg_pairwise_distance(cluster_embeddings)
            
            # Calculate silhouette score for cluster
            if len(set(cluster_labels)) > 1:
                cluster_silhouette = silhouette_score(embeddings, cluster_labels)
            else:
                cluster_silhouette = 0
            
            # Determine concept area from chunks
            concept_area = await self._determine_cluster_concept_area(
                [chunks[i] for i in cluster_indices]
            )
            
            # Calculate density score
            density_score = self._calculate_density_score(avg_distance)
            
            return ClusterAnalysis(
                cluster_id=cluster_id,
                centroid=centroid,
                chunk_indices=cluster_indices,
                avg_pairwise_distance=avg_distance,
                silhouette_score=cluster_silhouette,
                concept_area=concept_area,
                density_score=density_score
            )
            
        except Exception as e:
            self.logger.error(f"Cluster analysis failed for cluster {cluster_id}: {e}")
            return None
    
    def _calculate_avg_pairwise_distance(self, embeddings: np.ndarray) -> float:
        """Calculate average pairwise cosine distance within cluster"""
        if len(embeddings) < 2:
            return 0.0
        
        try:
            # Calculate cosine distances
            distances = cosine_distances(embeddings)
            
            # Get upper triangular matrix (excluding diagonal)
            n = len(embeddings)
            total_distance = 0
            count = 0
            
            for i in range(n):
                for j in range(i + 1, n):
                    total_distance += distances[i, j]
                    count += 1
            
            return total_distance / count if count > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"Distance calculation failed: {e}")
            return 1.0  # High distance indicates sparse area
    
    async def _determine_cluster_concept_area(
        self,
        cluster_chunks: List[Dict[str, Any]]
    ) -> str:
        """Determine the main concept area for a cluster"""
        # Collect metadata from chunks
        concept_areas = []
        topics = []
        
        for chunk in cluster_chunks:
            metadata = chunk.get('metadata', {})
            if isinstance(metadata, dict):
                concept_areas.append(metadata.get('concept_area', 'General'))
                topics.append(metadata.get('topic', 'general'))
        
        # Find most common concept area
        if concept_areas:
            concept_counter = {}
            for concept in concept_areas:
                concept_counter[concept] = concept_counter.get(concept, 0) + 1
            
            most_common = max(concept_counter.items(), key=lambda x: x[1])
            return most_common[0]
        
        # Fallback: analyze text content
        all_text = ' '.join([chunk.get('text', '') for chunk in cluster_chunks])
        return await self._extract_concept_from_text(all_text)
    
    async def _extract_concept_from_text(self, text: str) -> str:
        """Extract concept area from combined text"""
        text_lower = text.lower()
        
        # Check for specific patterns
        if any(word in text_lower for word in ['house', 'family', 'lord', 'noble']):
            return 'Nobility'
        elif any(word in text_lower for word in ['magic', 'spell', 'wizard', 'mage']):
            return 'Magic System'
        elif any(word in text_lower for word in ['trade', 'merchant', 'commerce', 'gold']):
            return 'Trade System'
        elif any(word in text_lower for word in ['kingdom', 'land', 'region', 'territory']):
            return 'Geography'
        elif any(word in text_lower for word in ['rule', 'govern', 'king', 'politics']):
            return 'Politics'
        else:
            return 'General Lore'
    
    def _calculate_density_score(self, avg_distance: float) -> float:
        """Calculate density score from average distance"""
        # Higher distance = lower density
        # Convert to 0-1 scale where 1 = high density, 0 = low density
        return max(0.0, 1.0 - avg_distance)
    
    async def detect_sparse_areas(
        self,
        embeddings: List[List[float]],
        chunks: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        max_areas: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Detect sparse areas that need expansion.
        
        Args:
            embeddings: Original embeddings
            chunks: Original chunks
            clusters: Cluster analysis results
            max_areas: Maximum number of sparse areas to return
            
        Returns:
            List of sparse areas ranked by expansion priority
        """
        try:
            sparse_areas = []
            
            # Analyze each cluster for sparseness
            for cluster in clusters:
                sparse_area = await self._analyze_cluster_sparseness(cluster)
                if sparse_area:
                    sparse_areas.append(sparse_area)
            
            # Sort by expansion priority (highest distance = most sparse = highest priority)
            sparse_areas.sort(key=lambda x: x['avg_pairwise_distance'], reverse=True)
            
            # Limit to max_areas
            result = sparse_areas[:max_areas]
            
            self.logger.info(f"Detected {len(result)} sparse areas for expansion")
            return result
            
        except Exception as e:
            self.logger.error(f"Sparse area detection failed: {e}")
            return []
    
    async def _analyze_cluster_sparseness(
        self,
        cluster: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Analyze if a cluster represents a sparse area"""
        try:
            avg_distance = cluster['avg_pairwise_distance']
            density_score = cluster['density_score']
            
            # Consider area sparse if distance is above threshold OR density is low
            is_sparse = avg_distance > self._distance_threshold or density_score < 0.3
            
            if is_sparse:
                return {
                    'concept_area': cluster['concept_area'],
                    'avg_pairwise_distance': avg_distance,
                    'cluster_id': cluster['cluster_id'],
                    'chunk_indices': cluster['chunk_indices'],
                    'expansion_needed': True,
                    'chunks': cluster['chunks'],
                    'density_score': density_score,
                    'sparseness_score': avg_distance  # Higher = more sparse
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Cluster sparseness analysis failed: {e}")
            return None
    
    def get_clustering_stats(
        self,
        clusters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get comprehensive clustering statistics"""
        if not clusters:
            return {}
        
        try:
            distances = [c['avg_pairwise_distance'] for c in clusters]
            densities = [c['density_score'] for c in clusters]
            
            return {
                'total_clusters': len(clusters),
                'avg_pairwise_distance': {
                    'mean': np.mean(distances),
                    'std': np.std(distances),
                    'min': np.min(distances),
                    'max': np.max(distances)
                },
                'density_scores': {
                    'mean': np.mean(densities),
                    'std': np.std(densities),
                    'min': np.min(densities),
                    'max': np.max(densities)
                },
                'concept_areas': [c['concept_area'] for c in clusters],
                'cluster_sizes': [len(c['chunk_indices']) for c in clusters]
            }
            
        except Exception as e:
            self.logger.error(f"Clustering stats calculation failed: {e}")
            return {}
    
    def set_clustering_parameters(
        self,
        distance_threshold: float = None,
        min_cluster_size: int = None,
        default_clusters: int = None
    ):
        """Update clustering parameters"""
        if distance_threshold is not None:
            self._distance_threshold = distance_threshold
        if min_cluster_size is not None:
            self._min_cluster_size = min_cluster_size
        if default_clusters is not None:
            self._kmeans_clusters = default_clusters
        
        self.logger.info(
            f"Updated clustering parameters: threshold={self._distance_threshold}, "
            f"min_size={self._min_cluster_size}, default_clusters={self._kmeans_clusters}"
        )