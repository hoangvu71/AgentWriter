"""
LoreGen Agent
Generates expanded world building by detecting sparse areas and creating detailed lore.
Based on confirmed requirements:
- Input: "Use this plot's worldbuilding and expand"
- Output: Complete expanded world building (Option B format)
- Uses k-means clustering + sparse detection to find top 5 areas needing expansion
- Real-time processing (~20-30 seconds acceptable)
- No user interaction during processing
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
import json

from ..core.base_agent import BaseAgent
from ..core.interfaces import AgentRequest, AgentResponse, ContentType
from ..core.configuration import Configuration
from ..services.vertex_rag_service import VertexRAGService
from ..services.clustering_service import ClusteringService


class LoreGenAgent(BaseAgent):
    """
    Agent for generating expanded world building through sparse lore detection and expansion.
    """
    
    def __init__(self, config: Configuration):
        """Initialize LoreGen agent with RAG and clustering services"""
        
        instruction = """
        You are the LoreGen agent, specialized in expanding world building by detecting and filling sparse areas in existing lore.

        Your task is to:
        1. Analyze existing world building content for sparse areas (concepts that lack detail)
        2. Generate comprehensive expansions for the sparsest areas (up to 5 areas)
        3. Integrate expansions seamlessly with original content
        4. Return complete expanded world building

        Process:
        - Take world building content and perform semantic analysis
        - Use clustering to identify concept areas with insufficient detail
        - Focus on areas with large "radius" (sparse coverage) like Houses, magic systems, economics, etc.
        - Generate detailed, creative expansions that add depth while maintaining consistency
        - Integrate all expansions into the original content naturally

        Output format (JSON):
        {
            "world_name": "Original world name",
            "world_type": "Original world type", 
            "world_content": "Complete expanded content (original + all expansions integrated)",
            "expanded_areas_count": number,
            "processing_time_seconds": float
        }

        Guidelines:
        - Be creative but consistent with established lore
        - Expansions should feel natural and integrated, not tacked on
        - Focus on adding depth, history, culture, and detail
        - Maintain the original tone and style
        - Each expansion should be substantial (200+ words per concept area)
        """
        
        super().__init__(
            name="loregen",
            description="Generates expanded world building by detecting and filling sparse lore areas",
            instruction=instruction,
            config=config
        )
        
        # Initialize services
        self._rag_service = VertexRAGService(config)
        self._clustering_service = ClusteringService()
        
        # Database service will be injected
        self._database_service = None
        
        self.logger = logging.getLogger(__name__)
    
    def _get_content_type(self) -> ContentType:
        """Return content type for this agent"""
        return ContentType.WORLD_BUILDING
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """
        Process LoreGen request to expand world building.
        Main entry point for the expansion workflow.
        """
        start_time = time.time()
        
        try:
            # Validate request
            plot_id = self._extract_plot_id(request)
            if not plot_id:
                return AgentResponse(
                    agent_name=self.name,
                    content="Missing plot_id in request context",
                    content_type=self._get_content_type(),
                    success=False,
                    error="plot_id is required in request context"
                )
            
            # Get world building data
            world_data = await self._get_world_building(plot_id)
            if not world_data:
                return AgentResponse(
                    agent_name=self.name,
                    content="No world building found for this plot",
                    content_type=self._get_content_type(),
                    success=False,
                    error="No world building data available"
                )
            
            # Detect sparse areas
            sparse_areas = await self._detect_sparse_areas(world_data['world_content'], plot_id)
            
            # Generate expansions for sparse areas
            expansions = await self._generate_expansions(sparse_areas)
            
            # Integrate expansions with original content
            expanded_content = await self._integrate_expansions(
                world_data['world_content'],
                expansions
            )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Calculate expansion metrics
            original_content = world_data['world_content']
            expansion_metrics = self._calculate_expansion_metrics(
                original_content, 
                expanded_content, 
                expansions
            )
            
            # Create response in Option B format (complete expanded world)
            response_data = {
                'world_name': world_data.get('world_name', 'Unnamed World'),
                'world_type': world_data.get('world_type', 'fantasy'),
                'world_content': expanded_content,
                'expanded_areas_count': len(expansions),
                'processing_time_seconds': round(processing_time, 1),
                'expansion_metrics': expansion_metrics
            }
            
            self.logger.info(f"LoreGen completed: {len(expansions)} areas expanded in {processing_time:.1f}s")
            
            return AgentResponse(
                agent_name=self.name,
                content=f"Lore expansion completed. Expanded {len(expansions)} areas.",
                content_type=self._get_content_type(),
                parsed_json=response_data,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"LoreGen failed after {processing_time:.1f}s: {e}")
            
            return AgentResponse(
                agent_name=self.name,
                content=f"Lore expansion failed: {e}",
                content_type=self._get_content_type(),
                success=False,
                error=str(e)
            )
    
    def _extract_plot_id(self, request: AgentRequest) -> Optional[str]:
        """Extract plot_id from request context"""
        if not request.context:
            return None
        # Try plot_id first, then fall back to content_id
        return request.context.get('plot_id') or request.context.get('content_id')
    
    async def _get_world_building(self, plot_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve world building data for the plot"""
        if not self._database_service:
            # Use dependency injection from container instead of direct instantiation
            from ..core.container import container
            self._database_service = container.get("world_building_repository")
        
        try:
            world_data = await self._database_service.get_world_building_by_plot(plot_id)
            return world_data
        except Exception as e:
            self.logger.error(f"Failed to get world building for plot {plot_id}: {e}")
            return None
    
    async def _detect_sparse_areas(self, world_content: str, plot_id: str = None) -> List[Dict[str, Any]]:
        """
        Detect sparse areas in world building content using clustering analysis.
        Returns top 5 sparse areas ranked by pairwise distance.
        """
        try:
            # Chunk the content semantically
            chunks = await self._rag_service.chunk_content(
                content=world_content,
                chunk_size=80,
                chunk_overlap=20
            )
            
            if not chunks:
                self.logger.warning("No chunks created from world content")
                return []
            
            # Save chunks to database and Vertex AI RAG corpus
            if plot_id and self._database_service:
                try:
                    # Check if corpus already exists for this plot
                    corpus_data = await self._database_service.get_rag_corpus_by_plot(plot_id)
                    corpus_name = f"corpus-book-{plot_id}"
                    
                    if not corpus_data:
                        # Create new Vertex AI corpus
                        vertex_corpus_id = await self._rag_service.create_corpus_for_plot(plot_id)
                        
                        # Save corpus metadata to database
                        corpus_data = await self._database_service.save_rag_corpus(
                            vertex_corpus_id=vertex_corpus_id,
                            plot_id=plot_id,
                            corpus_name=corpus_name
                        )
                        self.logger.info(f"Created new Vertex AI RAG corpus for plot {plot_id}")
                        
                        # Import chunks to Vertex AI corpus
                        await self._rag_service.import_chunks_to_corpus(corpus_name, chunks)
                        self.logger.info(f"Imported {len(chunks)} chunks to Vertex AI corpus")
                        
                    else:
                        self.logger.info(f"Using existing RAG corpus for plot {plot_id}")
                        
                        # Check if we need to add new chunks to existing corpus
                        existing_chunk_count = corpus_data.get('chunk_count', 0)
                        if len(chunks) > existing_chunk_count:
                            # Add new chunks to existing corpus
                            new_chunks = chunks[existing_chunk_count:]
                            await self._rag_service.import_chunks_to_corpus(corpus_name, new_chunks)
                            self.logger.info(f"Added {len(new_chunks)} new chunks to existing corpus")
                    
                    if corpus_data:
                        # Save chunks metadata to database
                        await self._database_service.save_rag_chunks(
                            corpus_uuid=corpus_data['id'],
                            chunks=chunks,
                            source_type="world_building",
                            source_id=plot_id
                        )
                        self.logger.info(f"Saved {len(chunks)} chunks metadata to database for plot {plot_id}")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to save chunks to database/Vertex AI: {e}")
                    # Continue processing even if save fails
            
            # Get embeddings for clustering
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = await self._rag_service.get_embeddings(chunk_texts)
            
            # Perform k-means clustering
            clusters = await self._clustering_service.perform_kmeans_clustering(
                embeddings=embeddings,
                chunks=chunks
            )
            
            # Detect sparse areas using pairwise distance analysis
            sparse_areas = await self._clustering_service.detect_sparse_areas(
                embeddings=embeddings,
                chunks=chunks,
                clusters=clusters,
                max_areas=5  # Limit to top 5 as specified
            )
            
            self.logger.info(f"Detected {len(sparse_areas)} sparse areas for expansion")
            return sparse_areas
            
        except Exception as e:
            self.logger.error(f"Sparse area detection failed: {e}")
            return []
    
    async def _generate_expansions(self, sparse_areas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate detailed expansions for identified sparse areas.
        Each expansion should be creative and substantial.
        """
        expansions = []
        
        for area in sparse_areas:
            try:
                expansion = await self._generate_single_expansion(area)
                if expansion:
                    expansions.append(expansion)
            except Exception as e:
                self.logger.error(f"Failed to generate expansion for {area.get('concept_area', 'unknown')}: {e}")
                continue
        
        self.logger.info(f"Generated {len(expansions)} expansions")
        return expansions
    
    async def _generate_single_expansion(self, sparse_area: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate expansion for a single sparse area"""
        concept_area = sparse_area['concept_area']
        current_chunks = sparse_area.get('chunks', [])
        current_content = " ".join([chunk.get('text', '') for chunk in current_chunks])
        
        # Create expansion prompt
        expansion_prompt = f"""
        Based on the existing brief mention: "{current_content[:200]}..."
        
        Create a detailed expansion for {concept_area}. This area currently lacks sufficient detail and depth.
        
        Provide comprehensive lore including:
        - Historical background and origins
        - Key figures, leaders, or notable members
        - Customs, traditions, or unique characteristics  
        - Relationships with other elements in the world
        - Current status and influence
        - Interesting details that add depth and authenticity
        
        Write 200-400 words that seamlessly expand this concept while maintaining consistency with the existing world.
        """
        
        try:
            # Use the base agent's LLM to generate expansion
            expansion_response = await self._generate_content(expansion_prompt)
            
            if expansion_response and len(expansion_response) > 100:
                return {
                    'concept_area': concept_area,
                    'expanded_content': expansion_response,
                    'original_content': current_content
                }
        except Exception as e:
            self.logger.error(f"Expansion generation failed for {concept_area}: {e}")
            
        return None
    
    async def _integrate_expansions(
        self,
        original_content: str,
        expansions: List[Dict[str, Any]]
    ) -> str:
        """
        Integrate expansions seamlessly with original content.
        This creates the complete expanded world building (Option B format).
        """
        if not expansions:
            return original_content
        
        # Start with original content
        integrated_content = original_content
        
        for expansion in expansions:
            concept_area = expansion['concept_area']
            expanded_content = expansion['expanded_content']
            original_mention = expansion.get('original_content', '')
            
            try:
                # Find the location to insert expansion
                if original_mention and original_mention.strip() in integrated_content:
                    # Replace brief mention with detailed expansion
                    integrated_content = integrated_content.replace(
                        original_mention.strip(),
                        expanded_content
                    )
                else:
                    # Append expansion to relevant section or end
                    integrated_content = await self._append_expansion_intelligently(
                        integrated_content,
                        concept_area,
                        expanded_content
                    )
                    
            except Exception as e:
                self.logger.warning(f"Failed to integrate expansion for {concept_area}: {e}")
                # Fallback: append at end
                integrated_content += f"\n\n{expanded_content}"
        
        return integrated_content
    
    async def _append_expansion_intelligently(
        self,
        content: str,
        concept_area: str,
        expansion: str
    ) -> str:
        """
        Intelligently append expansion to relevant section of content.
        """
        # Simple heuristic: find related section and append there
        lines = content.split('\n')
        best_position = len(lines)  # Default to end
        
        # Look for relevant section based on concept area
        concept_keywords = self._get_concept_keywords(concept_area)
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in concept_keywords):
                # Found relevant section, insert after this paragraph
                best_position = i + 1
                break
        
        # Insert expansion at best position
        lines.insert(best_position, f"\n{expansion}\n")
        return '\n'.join(lines)
    
    def _get_concept_keywords(self, concept_area: str) -> List[str]:
        """Get keywords related to a concept area for intelligent insertion"""
        concept_lower = concept_area.lower()
        
        if 'house' in concept_lower:
            return ['house', 'noble', 'family', 'lord', 'lady']
        elif 'magic' in concept_lower:
            return ['magic', 'spell', 'wizard', 'enchant', 'power']
        elif 'econom' in concept_lower or 'trade' in concept_lower:
            return ['trade', 'merchant', 'gold', 'commerce', 'wealth']
        elif 'geograph' in concept_lower:
            return ['land', 'region', 'kingdom', 'territory', 'realm']
        elif 'politic' in concept_lower:
            return ['rule', 'govern', 'king', 'queen', 'council']
        else:
            return [concept_lower.split()[0]] if concept_lower else ['general']
    
    async def _generate_content(self, prompt: str, user_id: str = None, session_id: str = None) -> str:
        """Generate content using the base agent's LLM capabilities"""
        try:
            # Import Google GenAI types
            from google.genai import types
            
            # Use provided session or create default
            actual_user_id = user_id or "loregen_system"
            actual_session_id = session_id or "loregen_generation"
            
            # Ensure session exists first
            await self._ensure_session(actual_user_id, actual_session_id)
            
            # Create proper message content object
            content = types.Content(
                role='user',
                parts=[types.Part(text=prompt)]
            )
            
            # Use the same pattern as BaseAgent
            content_parts = []
            async for event in self._runner.run_async(
                user_id=actual_user_id,
                session_id=actual_session_id,
                new_message=content
            ):
                # Extract text content from events
                if hasattr(event, 'content') and event.content:
                    content_parts.append(str(event.content))
                elif hasattr(event, 'text') and event.text:
                    content_parts.append(event.text)
                elif hasattr(event, 'delta') and event.delta:
                    content_parts.append(event.delta)
            
            return ''.join(content_parts)
        except Exception as e:
            self.logger.error(f"Content generation failed: {e}")
            return ""
    
    # Additional methods for integration with existing agent factory
    
    async def _analyze_lore_density(self, request: AgentRequest) -> Dict[str, Any]:
        """
        Analyze lore density for orchestrator integration.
        This method supports orchestrator's RAG detection.
        """
        plot_id = self._extract_plot_id(request)
        if not plot_id:
            return {'needs_expansion': False, 'sparse_areas': []}
        
        world_data = await self._get_world_building(plot_id)
        if not world_data:
            return {'needs_expansion': False, 'sparse_areas': []}
        
        sparse_areas = await self._detect_sparse_areas(world_data['world_content'])
        
        return {
            'needs_expansion': len(sparse_areas) > 0,
            'sparse_areas': sparse_areas[:3],  # Summary for orchestrator
            'overall_density': self._calculate_overall_density(sparse_areas)
        }
    
    def _calculate_overall_density(self, sparse_areas: List[Dict[str, Any]]) -> float:
        """Calculate overall lore density score"""
        if not sparse_areas:
            return 1.0  # Perfect density if no sparse areas
        
        # Average inverse of distances (higher distance = lower density)
        total_distance = sum(area['avg_pairwise_distance'] for area in sparse_areas)
        avg_distance = total_distance / len(sparse_areas)
        
        # Convert to density score (0.0 to 1.0, where 1.0 is perfect density)
        density = max(0.0, 1.0 - avg_distance)
        return round(density, 2)
    
    def _calculate_expansion_metrics(
        self, 
        original_content: str, 
        expanded_content: str, 
        expansions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate detailed expansion metrics for user visualization"""
        
        # Basic counts
        original_chars = len(original_content)
        expanded_chars = len(expanded_content)
        original_words = len(original_content.split())
        expanded_words = len(expanded_content.split())
        
        # Calculate ratios
        char_expansion_ratio = round(expanded_chars / original_chars, 1) if original_chars > 0 else 1.0
        word_expansion_ratio = round(expanded_words / original_words, 1) if original_words > 0 else 1.0
        
        # Calculate reading times (average 200 words per minute)
        original_reading_time = round(original_words / 200, 1)
        expanded_reading_time = round(expanded_words / 200, 1)
        
        # Expansion details per area
        expansion_details = []
        total_expansion_words = 0
        
        for expansion in expansions:
            concept_area = expansion.get('concept_area', 'Unknown')
            expanded_text = expansion.get('expanded_content', '')
            original_text = expansion.get('original_content', '')
            
            expansion_words = len(expanded_text.split())
            original_snippet_words = len(original_text.split())
            
            total_expansion_words += expansion_words
            
            expansion_details.append({
                'concept_area': concept_area,
                'words_added': expansion_words,
                'original_snippet_words': original_snippet_words,
                'expansion_preview': expanded_text[:150] + '...' if len(expanded_text) > 150 else expanded_text
            })
        
        return {
            'original_stats': {
                'characters': original_chars,
                'words': original_words,
                'estimated_reading_time_minutes': original_reading_time
            },
            'expanded_stats': {
                'characters': expanded_chars,
                'words': expanded_words,
                'estimated_reading_time_minutes': expanded_reading_time
            },
            'expansion_summary': {
                'characters_added': expanded_chars - original_chars,
                'words_added': expanded_words - original_words,
                'character_expansion_ratio': f"{char_expansion_ratio}x",
                'word_expansion_ratio': f"{word_expansion_ratio}x",
                'reading_time_increase_minutes': round(expanded_reading_time - original_reading_time, 1),
                'total_new_content_words': total_expansion_words
            },
            'expansion_details': expansion_details
        }