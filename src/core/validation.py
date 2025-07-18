"""
Input validation and sanitization for the multi-agent book writing system.
"""

import re
import uuid
from typing import Dict, Any
from .interfaces import IValidator, AgentRequest


class ValidationError(Exception):
    """Custom validation error"""
    pass


class Validator(IValidator):
    """Input validation and sanitization"""
    
    def __init__(self):
        self.uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
        self.alphanumeric_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
    
    def validate_uuid(self, value: str) -> str:
        """Validate and return UUID"""
        if not isinstance(value, str):
            raise ValidationError("UUID must be a string")
        
        value = value.strip()
        if not self.uuid_pattern.match(value):
            raise ValidationError("Invalid UUID format")
        
        return value
    
    def validate_text(self, value: str, max_length: int = 1000) -> str:
        """Validate and sanitize text input"""
        if not isinstance(value, str):
            raise ValidationError("Text input must be a string")
        
        # Remove null bytes and control characters except newlines and tabs
        sanitized = ''.join(char for char in value if ord(char) >= 32 or char in '\n\t')
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        # Check length
        if len(sanitized) > max_length:
            raise ValidationError(f"Text exceeds maximum length of {max_length} characters")
        
        if not sanitized:
            raise ValidationError("Text cannot be empty")
        
        return sanitized
    
    def validate_alphanumeric(self, value: str, max_length: int = 50) -> str:
        """Validate alphanumeric string"""
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")
        
        value = value.strip()
        
        if len(value) > max_length:
            raise ValidationError(f"Value exceeds maximum length of {max_length} characters")
        
        if not self.alphanumeric_pattern.match(value):
            raise ValidationError("Value must contain only letters, numbers, underscores, and hyphens")
        
        return value
    
    def validate_request(self, request: AgentRequest) -> AgentRequest:
        """Validate an agent request"""
        # Validate required fields
        if not request.content:
            raise ValidationError("Request content cannot be empty")
        
        if not request.user_id:
            raise ValidationError("User ID is required")
        
        if not request.session_id:
            raise ValidationError("Session ID is required")
        
        # Sanitize content
        request.content = self.validate_text(request.content, max_length=50000)
        request.user_id = self.validate_alphanumeric(request.user_id, max_length=50)
        request.session_id = self.validate_alphanumeric(request.session_id, max_length=50)
        
        return request
    
    def validate_email(self, email: str) -> str:
        """Validate email format"""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        if not isinstance(email, str):
            raise ValidationError("Email must be a string")
        
        email = email.strip().lower()
        
        if not email_pattern.match(email):
            raise ValidationError("Invalid email format")
        
        return email
    
    def validate_integer(self, value: Any, min_value: int = None, max_value: int = None) -> int:
        """Validate integer with optional range"""
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                raise ValidationError("Invalid integer format")
        
        if not isinstance(value, int):
            raise ValidationError("Value must be an integer")
        
        if min_value is not None and value < min_value:
            raise ValidationError(f"Value must be at least {min_value}")
        
        if max_value is not None and value > max_value:
            raise ValidationError(f"Value must be at most {max_value}")
        
        return value
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file operations"""
        if not isinstance(filename, str):
            raise ValidationError("Filename must be a string")
        
        # Remove path separators and dangerous characters
        dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
        sanitized = re.sub(dangerous_chars, '_', filename)
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        
        # Ensure it's not empty
        if not sanitized:
            raise ValidationError("Filename cannot be empty")
        
        # Limit length
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
        
        return sanitized