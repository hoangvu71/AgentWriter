"""
Base controller with common functionality for all API controllers.
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException
from ..core.logging import get_logger
from ..core.validation import ValidationError


class BaseController:
    """Base controller with common functionality"""
    
    def __init__(self, name: str):
        self.logger = get_logger(f"controller.{name}")
        self.name = name
    
    def handle_error(self, error: Exception, message: str = "An error occurred") -> Dict[str, Any]:
        """Handle errors and return standardized error response"""
        if isinstance(error, ValidationError):
            self.logger.warning(f"Validation error: {error}")
            raise HTTPException(status_code=400, detail=str(error))
        
        elif isinstance(error, ValueError):
            self.logger.warning(f"Value error: {error}")
            raise HTTPException(status_code=400, detail=str(error))
        
        elif isinstance(error, KeyError):
            self.logger.warning(f"Key error: {error}")
            raise HTTPException(status_code=404, detail="Resource not found")
        
        elif isinstance(error, PermissionError):
            self.logger.warning(f"Permission error: {error}")
            raise HTTPException(status_code=403, detail="Access denied")
        
        else:
            self.logger.error(f"Unexpected error in {self.name}: {error}", error=error)
            raise HTTPException(status_code=500, detail=message)
    
    def success_response(self, data: Any = None, message: str = "Success") -> Dict[str, Any]:
        """Create standardized success response"""
        response = {"success": True, "message": message}
        if data is not None:
            response["data"] = data
        return response
    
    def error_response(self, message: str, details: Optional[Any] = None) -> Dict[str, Any]:
        """Create standardized error response"""
        response = {"success": False, "error": message}
        if details is not None:
            response["details"] = details
        return response
    
    def paginated_response(self, items: list, total: int, page: int, limit: int) -> Dict[str, Any]:
        """Create standardized paginated response"""
        return {
            "success": True,
            "data": items,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit  # Ceiling division
            }
        }
    
    def log_request(self, endpoint: str, **kwargs):
        """Log incoming request"""
        extra_info = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f"{endpoint} called", extra=kwargs)
    
    def validate_pagination(self, page: int, limit: int, max_limit: int = 100) -> tuple[int, int]:
        """Validate and normalize pagination parameters"""
        page = max(1, page)
        limit = max(1, min(limit, max_limit))
        return page, limit