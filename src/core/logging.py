"""
Centralized logging configuration for the multi-agent book writing system.
"""

import logging
import sys
from typing import Optional
from datetime import datetime


class StructuredLogger:
    """Structured logger with consistent formatting"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with consistent formatting"""
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message with optional context"""
        extra_info = self._format_extras(kwargs)
        self.logger.info(f"{message}{extra_info}")
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log error message with optional exception"""
        extra_info = self._format_extras(kwargs)
        if error:
            self.logger.error(f"{message} - Error: {str(error)}{extra_info}", exc_info=error)
        else:
            self.logger.error(f"{message}{extra_info}")
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with optional context"""
        extra_info = self._format_extras(kwargs)
        self.logger.debug(f"{message}{extra_info}")
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with optional context"""
        extra_info = self._format_extras(kwargs)
        self.logger.warning(f"{message}{extra_info}")
    
    def _format_extras(self, extras: dict) -> str:
        """Format extra context information"""
        if not extras:
            return ""
        
        formatted = []
        for key, value in extras.items():
            formatted.append(f"{key}={value}")
        
        return f" | {', '.join(formatted)}"


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)


def setup_logging(level: str = "INFO"):
    """Setup global logging configuration"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)