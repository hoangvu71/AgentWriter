"""
Security middleware and utilities for the BooksWriter application.
Provides CSRF protection, input validation, and security headers.
"""

import secrets
import hmac
import hashlib
import time
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
import html
import re
import logging

logger = logging.getLogger(__name__)

class CSRFProtection:
    """CSRF Token generation and validation"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.token_lifetime = 3600 * 24  # 24 hours
    
    def generate_token(self, session_id: str = None) -> str:
        """Generate a CSRF token"""
        timestamp = str(int(time.time()))
        session_id = session_id or secrets.token_urlsafe(16)
        
        # Create token data
        token_data = f"{session_id}:{timestamp}"
        
        # Create HMAC signature
        signature = hmac.new(
            self.secret_key.encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Combine data and signature
        token = f"{token_data}:{signature}"
        return token
    
    def validate_token(self, token: str, session_id: str = None) -> bool:
        """Validate a CSRF token"""
        if not token:
            return False
        
        try:
            parts = token.split(':')
            if len(parts) != 3:
                return False
            
            token_session_id, timestamp, signature = parts
            
            # Check if session_id matches (if provided)
            if session_id and token_session_id != session_id:
                return False
            
            # Check token age
            token_time = int(timestamp)
            if time.time() - token_time > self.token_lifetime:
                return False
            
            # Verify signature
            expected_data = f"{token_session_id}:{timestamp}"
            expected_signature = hmac.new(
                self.secret_key.encode(),
                expected_data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Invalid CSRF token format: {e}")
            return False


class InputValidator:
    """Input validation and sanitization utilities"""
    
    # Patterns for dangerous content
    SCRIPT_PATTERN = re.compile(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', re.IGNORECASE)
    JAVASCRIPT_PATTERN = re.compile(r'javascript:', re.IGNORECASE)
    VBSCRIPT_PATTERN = re.compile(r'vbscript:', re.IGNORECASE)
    DATA_URL_PATTERN = re.compile(r'data:text\/html', re.IGNORECASE)
    EVENT_HANDLER_PATTERN = re.compile(r'on\w+\s*=', re.IGNORECASE)
    
    @classmethod
    def sanitize_text(cls, text: str, max_length: int = 10000) -> str:
        """Sanitize text input"""
        if not isinstance(text, str):
            return ""
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove dangerous patterns
        text = cls.SCRIPT_PATTERN.sub('', text)
        text = cls.JAVASCRIPT_PATTERN.sub('', text)
        text = cls.VBSCRIPT_PATTERN.sub('', text)
        text = cls.DATA_URL_PATTERN.sub('', text)
        text = cls.EVENT_HANDLER_PATTERN.sub('', text)
        
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        return text.strip()
    
    @classmethod
    def sanitize_html(cls, html_content: str, max_length: int = 50000) -> str:
        """Sanitize HTML content"""
        if not isinstance(html_content, str):
            return ""
        
        # First apply text sanitization
        sanitized = cls.sanitize_text(html_content, max_length)
        
        # HTML escape for safety
        sanitized = html.escape(sanitized)
        
        return sanitized
    
    @classmethod
    def validate_json_data(cls, data: Dict[Any, Any]) -> Dict[str, Any]:
        """Validate and sanitize JSON data"""
        if not isinstance(data, dict):
            return {}
        
        validated = {}
        
        # Define allowed keys and their validation rules
        allowed_keys = {
            'type': ('str', 100),
            'content': ('str', 10000),
            'user_id': ('str', 100),
            'timestamp': ('str', 50),
            'context': ('dict', None),
            'agent': ('str', 100),
            'json_data': ('dict', None)
        }
        
        for key, value in data.items():
            if key in allowed_keys:
                expected_type, max_length = allowed_keys[key]
                
                if expected_type == 'str' and isinstance(value, str):
                    validated[key] = cls.sanitize_text(value, max_length)
                elif expected_type == 'dict' and isinstance(value, dict):
                    validated[key] = cls.validate_nested_dict(value)
                elif expected_type == 'int' and isinstance(value, int):
                    validated[key] = value
        
        return validated
    
    @classmethod
    def validate_nested_dict(cls, data: Dict[Any, Any], max_depth: int = 3) -> Dict[str, Any]:
        """Validate nested dictionary with depth limit"""
        if max_depth <= 0 or not isinstance(data, dict):
            return {}
        
        validated = {}
        for key, value in data.items():
            if isinstance(key, str) and len(key) <= 100:
                clean_key = cls.sanitize_text(key, 100)
                
                if isinstance(value, str):
                    validated[clean_key] = cls.sanitize_text(value, 1000)
                elif isinstance(value, (int, float, bool)):
                    validated[clean_key] = value
                elif isinstance(value, dict) and max_depth > 1:
                    nested_result = cls.validate_nested_dict(value, max_depth - 1)
                    if nested_result:  # Only add if not empty
                        validated[clean_key] = nested_result
        
        return validated


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses"""
    
    def __init__(self, app, csrf_protection: CSRFProtection = None):
        super().__init__(app)
        self.csrf_protection = csrf_protection or CSRFProtection()
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        
        # Add CSRF token to HTML responses
        if (request.url.path == "/" or request.url.path.endswith(".html")) and \
           response.headers.get("content-type", "").startswith("text/html"):
            
            csrf_token = self.csrf_protection.generate_token()
            
            # Store token in session or response header for validation
            response.headers["X-CSRF-Token"] = csrf_token
            
            # Replace template placeholder with actual token
            if hasattr(response, 'body'):
                body = response.body.decode('utf-8')
                body = body.replace('{{csrf_token}}', csrf_token)
                response.body = body.encode('utf-8')
                response.headers["content-length"] = str(len(response.body))
        
        return response


class SecurityService:
    """Main security service for the application"""
    
    def __init__(self):
        self.csrf_protection = CSRFProtection()
        self.input_validator = InputValidator()
    
    def validate_csrf_token(self, request: Request) -> bool:
        """Validate CSRF token from request"""
        # Skip CSRF validation for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        
        # Get token from header
        token = request.headers.get("X-CSRF-Token")
        if not token:
            return False
        
        # Validate token
        return self.csrf_protection.validate_token(token)
    
    def sanitize_request_data(self, data: Dict[Any, Any]) -> Dict[str, Any]:
        """Sanitize data from request"""
        return self.input_validator.validate_json_data(data)
    
    def check_rate_limit(self, request: Request, max_requests: int = 100, window_seconds: int = 3600) -> bool:
        """Basic rate limiting (can be enhanced with Redis/database)"""
        # This is a basic implementation
        # In production, use Redis or database for rate limiting
        client_ip = request.client.host if request.client else "unknown"
        
        # For now, just log the request
        logger.info(f"Request from {client_ip}: {request.method} {request.url}")
        
        # Always allow for basic implementation
        return True
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], request: Request = None):
        """Log security events for monitoring"""
        client_ip = request.client.host if request and request.client else "unknown"
        
        log_data = {
            "event_type": event_type,
            "client_ip": client_ip,
            "timestamp": time.time(),
            **details
        }
        
        logger.warning(f"Security Event: {log_data}")


# Global security service instance
security_service = SecurityService()


def verify_csrf_token(request: Request) -> bool:
    """Dependency for CSRF token verification"""
    if not security_service.validate_csrf_token(request):
        security_service.log_security_event(
            "csrf_validation_failed",
            {"method": request.method, "url": str(request.url)},
            request
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token validation failed"
        )
    return True


def sanitize_input(data: Dict[Any, Any]) -> Dict[str, Any]:
    """Dependency for input sanitization"""
    return security_service.sanitize_request_data(data)