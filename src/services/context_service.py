"""
Efficient context injection service for LLM prompts.
Replaces the inefficient text-based context injection with structured, optimized context.
"""

import logging
from typing import Dict, Any, List, Optional
from ..core.interfaces import AgentRequest


class ContextInjectionService:
    """
    Service for efficient context injection into LLM prompts.
    
    Instead of appending 300-500+ tokens of verbose context to every message,
    this service generates minimal, agent-specific context only when needed.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Agent-specific context strategies
        self.agent_context_strategies = {
            'plot_generator': ['genre_hierarchy', 'target_audience', 'content_selection'],
            'world_building': ['genre_hierarchy', 'story_elements', 'target_audience'],
            'characters': ['story_elements', 'target_audience', 'genre_hierarchy'],
            'author_generator': ['target_audience', 'story_elements'],
            'critique': ['content_selection', 'target_audience'],
            'enhancement': ['content_selection', 'story_elements'],
            'scoring': ['content_selection', 'target_audience'],
            'loregen': ['genre_hierarchy', 'story_elements']
        }
    
    def inject_context_for_agent(self, base_prompt: str, context: Dict[str, Any], 
                                agent_type: str) -> str:
        """
        Inject context optimally based on agent type and available context data.
        
        Args:
            base_prompt: Clean user message or agent prompt
            context: Structured context parameters from AgentRequest
            agent_type: Type of agent that will process this prompt
            
        Returns:
            Optimized prompt with minimal, relevant context
        """
        if not context or not isinstance(context, dict):
            return base_prompt
            
        # Get relevant context types for this agent
        relevant_types = self.agent_context_strategies.get(agent_type, [])
        if not relevant_types:
            return base_prompt
            
        # Build minimal context parts
        context_parts = []
        
        for context_type in relevant_types:
            if context_type in context:
                formatted_context = self._format_context_type(context_type, context[context_type])
                if formatted_context:
                    context_parts.append(formatted_context)
        
        if not context_parts:
            return base_prompt
            
        # Inject efficiently with minimal formatting
        context_block = "Context: " + " | ".join(context_parts)
        return f"{base_prompt}\n\n{context_block}"
    
    def _format_context_type(self, context_type: str, context_data: Dict[str, Any]) -> Optional[str]:
        """
        Format a specific context type into a concise string.
        
        Args:
            context_type: Type of context (genre_hierarchy, story_elements, etc.)
            context_data: The actual context data
            
        Returns:
            Formatted context string or None if no useful data
        """
        if context_type == 'genre_hierarchy':
            return self._format_genre_context(context_data)
        elif context_type == 'story_elements':
            return self._format_story_elements(context_data)
        elif context_type == 'target_audience':
            return self._format_audience_context(context_data)
        elif context_type == 'content_selection':
            return self._format_content_selection(context_data)
        
        return None
    
    def _format_genre_context(self, genre_hierarchy: Dict[str, Any]) -> str:
        """
        Format genre context efficiently.
        
        OLD FORMAT: 6-9 lines with descriptions
        NEW FORMAT: 1 concise line
        """
        parts = []
        
        if 'genre' in genre_hierarchy:
            genre_name = genre_hierarchy['genre'].get('name', '')
            if genre_name:
                parts.append(f"Genre: {genre_name}")
        
        if 'subgenre' in genre_hierarchy:
            subgenre_name = genre_hierarchy['subgenre'].get('name', '')
            if subgenre_name:
                parts.append(f"Subgenre: {subgenre_name}")
        
        if 'microgenre' in genre_hierarchy:
            microgenre_name = genre_hierarchy['microgenre'].get('name', '')
            if microgenre_name:
                parts.append(f"Microgenre: {microgenre_name}")
        
        return ", ".join(parts) if parts else ""
    
    def _format_story_elements(self, story_elements: Dict[str, Any]) -> str:
        """
        Format story elements context efficiently.
        
        OLD FORMAT: 6-8 lines with descriptions and instructions
        NEW FORMAT: 1 concise line
        """
        parts = []
        
        if 'trope' in story_elements:
            trope_name = story_elements['trope'].get('name', '')
            if trope_name:
                parts.append(f"Trope: {trope_name}")
        
        if 'tone' in story_elements:
            tone_name = story_elements['tone'].get('name', '')
            if tone_name:
                parts.append(f"Tone: {tone_name}")
        
        return ", ".join(parts) if parts else ""
    
    def _format_audience_context(self, target_audience: Dict[str, Any]) -> str:
        """
        Format target audience context efficiently.
        
        OLD FORMAT: 6+ lines with demographic breakdown and instructions
        NEW FORMAT: 1 concise line
        """
        parts = []
        
        age_group = target_audience.get('age_group', '')
        gender = target_audience.get('gender', '')
        orientation = target_audience.get('sexual_orientation', '')
        
        if age_group:
            parts.append(f"Age: {age_group}")
        
        if gender and gender != 'All':
            parts.append(f"Gender: {gender}")
        
        if orientation and orientation != 'All':
            parts.append(f"Orientation: {orientation}")
        
        return "Audience: " + ", ".join(parts) if parts else ""
    
    def _format_content_selection(self, content_selection: Dict[str, Any]) -> str:
        """
        Format content selection context efficiently.
        
        OLD FORMAT: 4-5 lines with ID, type, title, and database instructions
        NEW FORMAT: 1 concise line
        """
        content_type = content_selection.get('type', '')
        content_title = content_selection.get('title', '')
        content_id = content_selection.get('id', '')
        
        if content_type and content_title:
            return f"Improve {content_type}: {content_title} ({content_id})"
        elif content_id:
            return f"Content ID: {content_id}"
        
        return ""
    
    def estimate_token_savings(self, context: Dict[str, Any], agent_type: str) -> Dict[str, int]:
        """
        Estimate token savings from using structured context vs old text injection.
        
        Returns:
            Dictionary with old_tokens, new_tokens, and savings
        """
        # Estimate old verbose format token count
        old_tokens = 0
        
        if context.get('genre_hierarchy'):
            old_tokens += 80  # Genre hierarchy section with descriptions
        if context.get('story_elements'):
            old_tokens += 70  # Story elements with instructions
        if context.get('target_audience'):
            old_tokens += 50  # Audience analysis section
        if context.get('content_selection'):
            old_tokens += 40  # Content selection section
        
        # Add overhead for headers, separators, guidelines
        old_tokens += 60  # Headers, footers, creative guidelines
        
        # Calculate new efficient format
        new_prompt = self.inject_context_for_agent("", context, agent_type)
        new_tokens = len(new_prompt.split()) if new_prompt else 0
        
        savings = old_tokens - new_tokens
        
        return {
            'old_tokens': old_tokens,
            'new_tokens': new_tokens, 
            'savings': savings,
            'efficiency_ratio': savings / old_tokens if old_tokens > 0 else 0
        }
    
    def create_structured_context(self, legacy_content: str) -> Dict[str, Any]:
        """
        DEPRECATED: Extract structured context from legacy text-injection format.
        
        This method provides backward compatibility for old message formats.
        New clients should use structured context directly in AgentRequest.context.
        
        Args:
            legacy_content: Message content with embedded legacy context format
            
        Returns:
            Structured context dictionary
        """
        self.logger.warning("Using deprecated create_structured_context - migrate to structured context format")
        context = {}
        
        try:
            # Extract genre hierarchy
            if "MAIN GENRE:" in legacy_content:
                genre_match = self._extract_between_markers(legacy_content, "MAIN GENRE:", "\n")
                if genre_match:
                    context.setdefault('genre_hierarchy', {})['genre'] = {'name': genre_match.strip()}
            
            if "SUBGENRE:" in legacy_content:
                subgenre_match = self._extract_between_markers(legacy_content, "SUBGENRE:", "\n")
                if subgenre_match:
                    context.setdefault('genre_hierarchy', {})['subgenre'] = {'name': subgenre_match.strip()}
            
            # Extract story elements
            if "TROPE:" in legacy_content:
                trope_match = self._extract_between_markers(legacy_content, "TROPE:", "\n")
                if trope_match:
                    context.setdefault('story_elements', {})['trope'] = {'name': trope_match.strip()}
            
            if "TONE:" in legacy_content:
                tone_match = self._extract_between_markers(legacy_content, "TONE:", "\n")
                if tone_match:
                    context.setdefault('story_elements', {})['tone'] = {'name': tone_match.strip()}
            
            # Extract target audience
            if "Age Group:" in legacy_content:
                age_match = self._extract_between_markers(legacy_content, "Age Group:", "\n")
                if age_match:
                    context.setdefault('target_audience', {})['age_group'] = age_match.strip()
            
        except Exception as e:
            self.logger.warning(f"Failed to extract legacy context: {e}")
        
        return context
    
    def _extract_between_markers(self, text: str, start_marker: str, end_marker: str) -> Optional[str]:
        """Helper method to extract text between markers"""
        start_idx = text.find(start_marker)
        if start_idx == -1:
            return None
            
        start_idx += len(start_marker)
        end_idx = text.find(end_marker, start_idx)
        if end_idx == -1:
            return None
            
        return text[start_idx:end_idx]
    
    def remove_legacy_context_injection(self, content: str) -> str:
        """
        DEPRECATED: Remove legacy context injection from message content.
        
        This method provides backward compatibility for old message formats.
        New clients should send clean messages with structured context separately.
        
        Args:
            content: Message content that may contain injected context
            
        Returns:
            Clean user message with context injection removed
        """
        self.logger.warning("Using deprecated remove_legacy_context_injection - send clean messages with structured context")
        # Find the start of context injection
        context_start = content.find("========== DETAILED CONTENT SPECIFICATIONS ==========")
        
        if context_start == -1:
            return content  # No legacy context found
        
        # Return everything before the context injection
        return content[:context_start].strip()


# Global service instance for convenient access
_default_service = ContextInjectionService()


def inject_context(base_prompt: str, context: Dict[str, Any], agent_type: str) -> str:
    """
    Convenience function for context injection.
    
    Args:
        base_prompt: Clean user message or agent prompt
        context: Structured context parameters
        agent_type: Type of agent processing the prompt
        
    Returns:
        Optimized prompt with minimal context
    """
    return _default_service.inject_context_for_agent(base_prompt, context, agent_type)


def estimate_savings(context: Dict[str, Any], agent_type: str) -> Dict[str, int]:
    """
    Convenience function for estimating token savings.
    """
    return _default_service.estimate_token_savings(context, agent_type)