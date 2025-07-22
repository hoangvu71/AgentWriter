"""
Robust JSON parser for LLM responses with fallback mechanisms.
Handles common LLM JSON formatting mistakes and provides reliable extraction.
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List, Tuple


class JSONParseError(Exception):
    """Custom exception for JSON parsing failures"""
    pass


class RobustJSONParser:
    """
    Robust JSON parser designed to handle common LLM response formatting issues.
    
    Features:
    - Multiple extraction patterns with fallback mechanisms
    - JSON repair for common LLM mistakes (trailing commas, comments, etc.)
    - Balanced brace matching instead of greedy regex
    - Comprehensive error handling and logging
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Compile regex patterns for better performance
        self._markdown_patterns = [
            # Standard markdown with newlines: ```json\n{...}\n```
            re.compile(r'```json\s*\n(.*?)\n```', re.DOTALL),
            # Compact markdown: ```json {...}```  
            re.compile(r'```json\s*(.*?)```', re.DOTALL),
            # Alternative markers
            re.compile(r'```JSON\s*\n(.*?)\n```', re.DOTALL | re.IGNORECASE),
            re.compile(r'```JSON\s*(.*?)```', re.DOTALL | re.IGNORECASE),
        ]
    
    def extract_and_parse(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Main entry point: Extract and parse JSON from LLM response text.
        
        Args:
            text: Raw LLM response text that may contain JSON
            
        Returns:
            Parsed JSON dictionary or None if no valid JSON found
        """
        if not text or not isinstance(text, str):
            return None
            
        text = text.strip()
        if not text:
            return None
            
        # Strategy 1: Try to parse entire response as JSON first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract JSON candidates using multiple patterns
        candidates = self._extract_json_candidates(text)
        
        # Strategy 3: Try to parse each candidate with repair fallbacks
        for candidate in candidates:
            result = self._parse_with_fallbacks(candidate)
            if result is not None:
                return result
                
        # No valid JSON found
        self.logger.debug(f"No valid JSON found in response (length: {len(text)})")
        return None
    
    def _extract_json_candidates(self, text: str) -> List[str]:
        """
        Extract potential JSON strings using multiple patterns.
        
        Returns:
            List of candidate JSON strings ordered by likelihood of success
        """
        candidates = []
        
        # Pattern 1: Markdown code blocks (highest priority)
        for pattern in self._markdown_patterns:
            matches = pattern.findall(text)
            for match in matches:
                candidate = match.strip()
                if candidate and candidate not in candidates:
                    candidates.append(candidate)
        
        # Pattern 2: Balanced brace extraction (safer than greedy matching)
        brace_candidates = self._extract_balanced_braces(text)
        for candidate in brace_candidates:
            if candidate and candidate not in candidates:
                candidates.append(candidate)
        
        # Pattern 3: Simple heuristic - looks like JSON structure
        json_like_candidates = self._extract_json_like_structures(text)
        for candidate in json_like_candidates:
            if candidate and candidate not in candidates:
                candidates.append(candidate)
                
        return candidates
    
    def _extract_balanced_braces(self, text: str) -> List[str]:
        """
        Extract JSON using balanced brace matching instead of greedy regex.
        This prevents capturing too much content between unrelated braces.
        """
        candidates = []
        i = 0
        
        while i < len(text):
            if text[i] == '{':
                # Found opening brace, find matching closing brace
                brace_count = 1
                start = i
                i += 1
                
                while i < len(text) and brace_count > 0:
                    if text[i] == '{':
                        brace_count += 1
                    elif text[i] == '}':
                        brace_count -= 1
                    i += 1
                
                # If braces are balanced, we found a candidate
                if brace_count == 0:
                    candidate = text[start:i].strip()
                    if len(candidate) > 2:  # More than just "{}"
                        candidates.append(candidate)
                # If unbalanced, continue searching from where we left off
            else:
                i += 1
                
        return candidates
    
    def _extract_json_like_structures(self, text: str) -> List[str]:
        """
        Extract structures that look like JSON using heuristics.
        Less reliable but catches edge cases.
        """
        candidates = []
        
        # Look for array structures
        array_pattern = re.compile(r'\[[\s\S]*?\]', re.DOTALL)
        for match in array_pattern.finditer(text):
            candidate = match.group(0).strip()
            # Basic validation - should have some content
            if len(candidate) > 4 and ('"' in candidate or "'" in candidate):
                candidates.append(candidate)
        
        return candidates
    
    def _parse_with_fallbacks(self, json_str: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to parse JSON with multiple repair strategies.
        
        Args:
            json_str: Candidate JSON string
            
        Returns:
            Parsed dictionary or None if all attempts fail
        """
        if not json_str:
            return None
            
        # Attempt 1: Parse as-is
        try:
            result = json.loads(json_str)
            if isinstance(result, dict):
                return result
            elif isinstance(result, list) and result and isinstance(result[0], dict):
                # If it's a list of dicts, return the first dict
                return result[0]
        except json.JSONDecodeError:
            pass
        
        # Attempt 2: Clean and repair common issues
        cleaned = self._clean_json_string(json_str)
        if cleaned != json_str:
            try:
                result = json.loads(cleaned)
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                pass
        
        # Attempt 3: Try to fix incomplete JSON
        completed = self._attempt_completion(cleaned)
        if completed != cleaned:
            try:
                result = json.loads(completed)
                if isinstance(result, dict):
                    self.logger.debug("Successfully repaired incomplete JSON")
                    return result
            except json.JSONDecodeError:
                pass
                
        return None
    
    def _clean_json_string(self, json_str: str) -> str:
        """
        Clean and repair common LLM JSON formatting mistakes.
        
        Args:
            json_str: Raw JSON string that may have formatting issues
            
        Returns:
            Cleaned JSON string
        """
        if not json_str:
            return json_str
            
        # Remove common prefixes/suffixes
        cleaned = json_str.strip()
        
        # Remove markdown artifacts that might have been missed
        if cleaned.startswith('```'):
            lines = cleaned.split('\n')
            if len(lines) > 2:
                cleaned = '\n'.join(lines[1:-1])
            else:
                cleaned = cleaned.replace('```', '')
        
        # Fix single quotes to double quotes (common LLM mistake)
        # This is tricky - we need to be careful not to break strings that contain apostrophes
        cleaned = self._fix_quotes(cleaned)
        
        # Remove trailing commas (common JSON error)
        cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
        
        # Remove comments (sometimes LLMs include these)
        cleaned = re.sub(r'//.*?$', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
        
        # Remove extra whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _fix_quotes(self, text: str) -> str:
        """
        Convert single quotes to double quotes while preserving apostrophes in strings.
        This is a simplified approach - a full solution would require proper parsing.
        """
        # Simple heuristic: replace single quotes that appear to be JSON delimiters
        # Look for patterns like 'key': or :'value'
        
        # Replace single quotes around keys
        text = re.sub(r"'(\w+)'(\s*:)", r'"\1"\2', text)
        
        # Replace single quotes around simple string values  
        text = re.sub(r"(:(\s*))'([^']*)'", r'\1\2"\3"', text)
        
        return text
    
    def _attempt_completion(self, json_str: str) -> str:
        """
        Attempt to complete incomplete JSON structures.
        
        Args:
            json_str: Potentially incomplete JSON string
            
        Returns:
            JSON string with completion attempts applied
        """
        if not json_str:
            return json_str
            
        # Count braces and brackets to detect incomplete structures
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        
        # Add missing closing braces
        missing_braces = open_braces - close_braces
        if missing_braces > 0:
            json_str += '}' * missing_braces
            
        # Add missing closing brackets  
        missing_brackets = open_brackets - close_brackets
        if missing_brackets > 0:
            json_str += ']' * missing_brackets
        
        # If the JSON looks like it was cut off mid-string, try to close it
        if json_str.endswith('"') and json_str.count('"') % 2 == 1:
            # Odd number of quotes suggests unclosed string
            json_str += '"'
        
        return json_str


# Global parser instance for convenient access
_default_parser = RobustJSONParser()


def parse_llm_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function for parsing JSON from LLM responses.
    
    Args:
        text: Raw LLM response text
        
    Returns:
        Parsed JSON dictionary or None if parsing fails
    """
    return _default_parser.extract_and_parse(text)


def create_parser(logger: Optional[logging.Logger] = None) -> RobustJSONParser:
    """
    Create a new parser instance with optional custom logger.
    
    Args:
        logger: Custom logger instance
        
    Returns:
        New RobustJSONParser instance
    """
    return RobustJSONParser(logger)