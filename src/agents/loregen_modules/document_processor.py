"""
LoreDocumentProcessor Module
Handles document processing, content analysis, and concept extraction for LoreGen agent.
Processes world building content for semantic analysis and expansion.
"""

import asyncio
import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
import string


@dataclass
class ConceptExtraction:
    """Results of concept extraction"""
    concept_name: str
    confidence: float
    context: str
    keyword_matches: List[str]
    location_in_text: int


@dataclass
class DocumentMetrics:
    """Metrics about processed document"""
    total_chars: int
    total_words: int
    total_sentences: int
    unique_concepts: int
    concept_density: float
    readability_score: float


class LoreDocumentProcessor:
    """
    Service for processing world building documents.
    Handles content analysis, concept extraction, and semantic preparation.
    """
    
    def __init__(self):
        """Initialize document processor"""
        self.logger = logging.getLogger(__name__)
        
        # Default chunking parameters
        self._chunk_size = 80  # tokens
        self._chunk_overlap = 20  # tokens
        self._sentence_min_length = 10
        
        # Concept extraction patterns
        self._concept_patterns = self._initialize_concept_patterns()
        
        # World building vocabulary
        self._world_vocabulary = self._initialize_world_vocabulary()
    
    def _initialize_concept_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for concept extraction"""
        return {
            'nobility': [
                r'\b[Hh]ouse\s+[A-Z][a-z]+\b',
                r'\b[Ll]ord\s+[A-Z][a-z]+\b',
                r'\b[Ll]ady\s+[A-Z][a-z]+\b',
                r'\b[Kk]ing\s+[A-Z][a-z]+\b',
                r'\b[Qq]ueen\s+[A-Z][a-z]+\b',
                r'\b[Dd]uke\s+[A-Z][a-z]+\b',
                r'\b[Cc]ount\s+[A-Z][a-z]+\b'
            ],
            'geography': [
                r'\b[Kk]ingdom\s+of\s+[A-Z][a-z]+\b',
                r'\b[Cc]ity\s+of\s+[A-Z][a-z]+\b',
                r'\b[Mm]ountain\s+[A-Z][a-z]+\b',
                r'\b[Rr]iver\s+[A-Z][a-z]+\b',
                r'\b[Ff]orest\s+of\s+[A-Z][a-z]+\b',
                r'\b[Ll]and\s+of\s+[A-Z][a-z]+\b'
            ],
            'organizations': [
                r'\b[Gg]uild\s+of\s+[A-Z][a-z\s]+\b',
                r'\b[Oo]rder\s+of\s+[A-Z][a-z\s]+\b',
                r'\b[Aa]cademy\s+of\s+[A-Z][a-z\s]+\b',
                r'\b[Cc]ouncil\s+of\s+[A-Z][a-z\s]+\b'
            ],
            'magic': [
                r'\b[Ss]chool\s+of\s+[A-Z][a-z\s]+\b',
                r'\b[Aa]rt\s+of\s+[A-Z][a-z\s]+\b',
                r'\b[Pp]ower\s+of\s+[A-Z][a-z\s]+\b'
            ]
        }
    
    def _initialize_world_vocabulary(self) -> Dict[str, Set[str]]:
        """Initialize world building vocabulary by category"""
        return {
            'nobility_titles': {
                'king', 'queen', 'prince', 'princess', 'duke', 'duchess',
                'lord', 'lady', 'earl', 'count', 'baron', 'knight', 'sir'
            },
            'magic_terms': {
                'magic', 'spell', 'wizard', 'mage', 'sorcerer', 'enchanter',
                'arcane', 'mystical', 'enchantment', 'incantation', 'ritual'
            },
            'geography_terms': {
                'kingdom', 'realm', 'empire', 'duchy', 'province', 'territory',
                'city', 'town', 'village', 'capital', 'fortress', 'castle'
            },
            'economic_terms': {
                'trade', 'merchant', 'guild', 'commerce', 'market', 'gold',
                'silver', 'currency', 'wealth', 'treasury', 'tax'
            },
            'military_terms': {
                'army', 'guard', 'soldier', 'knight', 'cavalry', 'infantry',
                'siege', 'battle', 'war', 'defense', 'garrison'
            },
            'cultural_terms': {
                'tradition', 'custom', 'festival', 'ceremony', 'ritual',
                'art', 'music', 'dance', 'religion', 'temple', 'shrine'
            }
        }
    
    async def create_semantic_chunks(
        self,
        content: str,
        chunk_size: int = None,
        overlap: int = None
    ) -> List[Dict[str, Any]]:
        """
        Create semantic chunks from world building content.
        
        Args:
            content: Text content to chunk
            chunk_size: Target size per chunk in tokens
            overlap: Overlap between chunks in tokens
            
        Returns:
            List of semantic chunks with metadata
        """
        try:
            chunk_size = chunk_size or self._chunk_size
            overlap = overlap or self._chunk_overlap
            
            # Preprocess content
            processed_content = await self._preprocess_content(content)
            
            # Create sentence-aware chunks
            chunks = await self._create_sentence_aware_chunks(
                processed_content, chunk_size, overlap
            )
            
            # Enhance chunks with semantic metadata
            enhanced_chunks = []
            for i, chunk in enumerate(chunks):
                enhanced_chunk = await self._enhance_chunk_metadata(chunk, i)
                enhanced_chunks.append(enhanced_chunk)
            
            self.logger.info(f"Created {len(enhanced_chunks)} semantic chunks")
            return enhanced_chunks
            
        except Exception as e:
            self.logger.error(f"Semantic chunking failed: {e}")
            return []
    
    async def _preprocess_content(self, content: str) -> str:
        """Preprocess content for better semantic chunking"""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content.strip())
        
        # Normalize sentence endings
        content = re.sub(r'([.!?])\s*([A-Z])', r'\1\n\2', content)
        
        # Handle paragraph breaks
        content = re.sub(r'\n{2,}', '\n\n', content)
        
        # Fix common formatting issues
        content = re.sub(r'([a-z])([A-Z])', r'\1. \2', content)
        
        return content
    
    async def _create_sentence_aware_chunks(
        self,
        content: str,
        chunk_size: int,
        overlap: int
    ) -> List[Dict[str, Any]]:
        """Create chunks that respect sentence boundaries"""
        # Split into sentences
        sentences = await self._split_into_sentences(content)
        
        chunks = []
        current_chunk_sentences = []
        current_token_count = 0
        
        for sentence in sentences:
            sentence_tokens = self._estimate_token_count(sentence)
            
            # Check if adding this sentence would exceed chunk size
            if current_token_count + sentence_tokens > chunk_size and current_chunk_sentences:
                # Create chunk from current sentences
                chunk_text = ' '.join(current_chunk_sentences)
                chunk = {
                    'text': chunk_text,
                    'sentence_count': len(current_chunk_sentences),
                    'estimated_tokens': current_token_count
                }
                chunks.append(chunk)
                
                # Handle overlap
                if overlap > 0 and len(current_chunk_sentences) > 1:
                    # Keep last few sentences for overlap
                    overlap_sentences = self._get_overlap_sentences(
                        current_chunk_sentences, overlap
                    )
                    current_chunk_sentences = overlap_sentences
                    current_token_count = sum(
                        self._estimate_token_count(s) for s in overlap_sentences
                    )
                else:
                    current_chunk_sentences = []
                    current_token_count = 0
            
            # Add current sentence
            current_chunk_sentences.append(sentence)
            current_token_count += sentence_tokens
        
        # Add final chunk
        if current_chunk_sentences:
            chunk_text = ' '.join(current_chunk_sentences)
            chunk = {
                'text': chunk_text,
                'sentence_count': len(current_chunk_sentences),
                'estimated_tokens': current_token_count
            }
            chunks.append(chunk)
        
        return chunks
    
    async def _split_into_sentences(self, content: str) -> List[str]:
        """Split content into sentences intelligently"""
        # Handle common abbreviations
        abbreviations = {'Mr.', 'Mrs.', 'Dr.', 'Prof.', 'St.', 'Mt.'}
        
        # Simple sentence splitting (can be enhanced with NLTK)
        sentences = re.split(r'[.!?]+\s*', content)
        
        # Filter out very short sentences
        valid_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) >= self._sentence_min_length:
                valid_sentences.append(sentence)
        
        return valid_sentences
    
    def _estimate_token_count(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        # Simple heuristic: 1 token ≈ 4 characters
        return max(1, len(text) // 4)
    
    def _get_overlap_sentences(self, sentences: List[str], overlap_tokens: int) -> List[str]:
        """Get sentences for overlap based on token count"""
        if not sentences:
            return []
        
        overlap_sentences = []
        token_count = 0
        
        # Start from the end and work backwards
        for sentence in reversed(sentences):
            sentence_tokens = self._estimate_token_count(sentence)
            if token_count + sentence_tokens <= overlap_tokens:
                overlap_sentences.insert(0, sentence)
                token_count += sentence_tokens
            else:
                break
        
        return overlap_sentences
    
    async def _enhance_chunk_metadata(
        self,
        chunk: Dict[str, Any],
        chunk_index: int
    ) -> Dict[str, Any]:
        """Enhance chunk with semantic metadata"""
        text = chunk['text']
        
        # Extract concepts
        concepts = await self.extract_concept_areas([chunk])
        primary_concept = concepts[0] if concepts else 'General'
        
        # Analyze content type
        content_type = await self._analyze_content_type(text)
        
        # Calculate importance
        importance = self._calculate_content_importance(text)
        
        # Extract key entities
        entities = await self._extract_key_entities(text)
        
        # Calculate readability
        readability = self._calculate_readability_score(text)
        
        enhanced_metadata = {
            'chunk_index': chunk_index,
            'concept_area': primary_concept,
            'content_type': content_type,
            'importance': importance,
            'key_entities': entities,
            'readability_score': readability,
            'word_count': len(text.split()),
            'char_count': len(text)
        }
        
        # Merge with original chunk data
        chunk['metadata'] = enhanced_metadata
        return chunk
    
    async def extract_concept_areas(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Extract concept areas from chunks.
        
        Args:
            chunks: List of chunks to analyze
            
        Returns:
            List of concept areas identified
        """
        try:
            concepts = set()
            
            for chunk in chunks:
                text = chunk.get('text', '')
                chunk_concepts = await self._extract_concepts_from_text(text)
                concepts.update(chunk_concepts)
            
            # Sort by frequency/importance
            concept_list = list(concepts)
            concept_list.sort()
            
            return concept_list
            
        except Exception as e:
            self.logger.error(f"Concept area extraction failed: {e}")
            return ['General']
    
    async def _extract_concepts_from_text(self, text: str) -> List[str]:
        """Extract concepts from a single text"""
        concepts = []
        text_lower = text.lower()
        
        # Check each concept category
        for category, patterns in self._concept_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    concepts.append(category.title())
                    break
        
        # Check vocabulary-based concepts
        for category, vocabulary in self._world_vocabulary.items():
            if any(word in text_lower for word in vocabulary):
                concept_name = category.replace('_terms', '').title()
                concepts.append(concept_name)
        
        # Fallback to extracting proper nouns
        if not concepts:
            proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
            if proper_nouns:
                concepts.append(proper_nouns[0])
        
        return concepts or ['General']
    
    async def _analyze_content_type(self, text: str) -> str:
        """Analyze the type of content in the text"""
        text_lower = text.lower()
        
        # Check for different content types
        if any(word in text_lower for word in ['history', 'founded', 'ancient', 'past']):
            return 'historical'
        elif any(word in text_lower for word in ['rule', 'govern', 'law', 'policy']):
            return 'political'
        elif any(word in text_lower for word in ['trade', 'merchant', 'gold', 'commerce']):
            return 'economic'
        elif any(word in text_lower for word in ['tradition', 'custom', 'festival', 'culture']):
            return 'cultural'
        elif any(word in text_lower for word in ['magic', 'spell', 'wizard', 'mystical']):
            return 'magical'
        elif any(word in text_lower for word in ['mountain', 'river', 'forest', 'land']):
            return 'geographical'
        else:
            return 'descriptive'
    
    def _calculate_content_importance(self, text: str) -> str:
        """Calculate importance level of content"""
        # Heuristics for importance
        word_count = len(text.split())
        
        if word_count > 100:
            return 'high'
        elif word_count > 50:
            return 'medium'
        else:
            return 'low'
    
    async def _extract_key_entities(self, text: str) -> List[str]:
        """Extract key named entities from text"""
        entities = []
        
        # Extract proper nouns (simple approach)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Filter out common words
        common_words = {'The', 'This', 'That', 'These', 'Those', 'When', 'Where', 'What'}
        entities = [noun for noun in proper_nouns if noun not in common_words]
        
        # Limit to most relevant
        return entities[:5]
    
    def _calculate_readability_score(self, text: str) -> float:
        """Calculate simple readability score"""
        if not text:
            return 0.0
        
        words = text.split()
        sentences = len(re.split(r'[.!?]+', text))
        
        if sentences == 0:
            return 0.0
        
        avg_words_per_sentence = len(words) / sentences
        
        # Simple readability heuristic (lower is more readable)
        # Score between 0 and 1, where 1 is most readable
        readability = max(0.0, min(1.0, 1.0 - (avg_words_per_sentence - 10) / 20))
        
        return round(readability, 2)
    
    async def analyze_document_structure(self, content: str) -> Dict[str, Any]:
        """Analyze the overall structure of the document"""
        try:
            # Basic metrics
            char_count = len(content)
            word_count = len(content.split())
            sentence_count = len(re.split(r'[.!?]+', content))
            
            # Extract all concepts
            temp_chunk = [{'text': content}]
            concepts = await self.extract_concept_areas(temp_chunk)
            
            # Calculate concept density
            concept_density = len(concepts) / word_count if word_count > 0 else 0
            
            # Overall readability
            readability = self._calculate_readability_score(content)
            
            metrics = DocumentMetrics(
                total_chars=char_count,
                total_words=word_count,
                total_sentences=sentence_count,
                unique_concepts=len(set(concepts)),
                concept_density=concept_density,
                readability_score=readability
            )
            
            structure_analysis = {
                'metrics': metrics.__dict__,
                'concepts_found': concepts,
                'content_types': await self._analyze_content_distribution(content),
                'entity_density': await self._calculate_entity_density(content)
            }
            
            return structure_analysis
            
        except Exception as e:
            self.logger.error(f"Document structure analysis failed: {e}")
            return {}
    
    async def _analyze_content_distribution(self, content: str) -> Dict[str, float]:
        """Analyze distribution of different content types"""
        sentences = await self._split_into_sentences(content)
        
        type_counts = {
            'historical': 0,
            'political': 0,
            'economic': 0,
            'cultural': 0,
            'magical': 0,
            'geographical': 0,
            'descriptive': 0
        }
        
        for sentence in sentences:
            content_type = await self._analyze_content_type(sentence)
            type_counts[content_type] = type_counts.get(content_type, 0) + 1
        
        total = len(sentences)
        if total == 0:
            return type_counts
        
        # Convert to percentages
        return {k: round(v / total, 2) for k, v in type_counts.items()}
    
    async def _calculate_entity_density(self, content: str) -> float:
        """Calculate density of named entities in content"""
        entities = await self._extract_key_entities(content)
        word_count = len(content.split())
        
        return len(entities) / word_count if word_count > 0 else 0.0
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing configuration and stats"""
        return {
            'chunk_size': self._chunk_size,
            'chunk_overlap': self._chunk_overlap,
            'sentence_min_length': self._sentence_min_length,
            'concept_categories': list(self._concept_patterns.keys()),
            'vocabulary_categories': list(self._world_vocabulary.keys()),
            'total_vocabulary_terms': sum(len(v) for v in self._world_vocabulary.values())
        }