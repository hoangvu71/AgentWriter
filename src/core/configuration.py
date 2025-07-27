"""
Configuration management for the multi-agent book writing system.
"""

import os
from dataclasses import dataclass
from typing import Dict, Optional, List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    url: str
    anon_key: str
    service_role_key: Optional[str] = None
    password: Optional[str] = None
    project_ref: Optional[str] = None


@dataclass
class GoogleCloudConfig:
    """Google Cloud configuration settings"""
    project_id: str
    location: str
    credentials_path: str
    use_vertex_ai: bool = True


@dataclass
class ServerConfig:
    """Server configuration settings"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


@dataclass
class AgentConfig:
    """Agent configuration settings"""
    model: str = "gemini-2.0-flash"
    max_retries: int = 3
    timeout: int = 30
    temperature: float = 0.7


class Configuration:
    """Centralized configuration management"""
    
    def __init__(self):
        self._database_config = self._load_database_config()
        self._google_cloud_config = self._load_google_cloud_config()
        self._server_config = self._load_server_config()
        self._agent_config = self._load_agent_config()
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration from environment"""
        return DatabaseConfig(
            url=os.getenv("SUPABASE_URL", ""),
            anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
            service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            password=os.getenv("SUPABASE_DB_PASSWORD"),
            project_ref=os.getenv("SUPABASE_PROJECT_REF")
        )
    
    def _load_google_cloud_config(self) -> GoogleCloudConfig:
        """Load Google Cloud configuration from environment"""
        return GoogleCloudConfig(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT", ""),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
            use_vertex_ai=os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "true").lower() == "true"
        )
    
    def _load_server_config(self) -> ServerConfig:
        """Load server configuration from environment"""
        return ServerConfig(
            host=os.getenv("SERVER_HOST", "0.0.0.0"),
            port=int(os.getenv("SERVER_PORT", "8000")),
            debug=os.getenv("DEBUG", "false").lower() == "true"
        )
    
    def _load_agent_config(self) -> AgentConfig:
        """Load agent configuration from environment"""
        return AgentConfig(
            model=os.getenv("AI_MODEL", "gemini-2.0-flash"),
            max_retries=int(os.getenv("AGENT_MAX_RETRIES", "3")),
            timeout=int(os.getenv("AGENT_TIMEOUT", "30")),
            temperature=float(os.getenv("AGENT_TEMPERATURE", "0.7"))
        )
    
    @property
    def model_name(self) -> str:
        """Current AI model name"""
        return self._agent_config.model
    
    @property
    def database_url(self) -> str:
        """Database connection URL"""
        return self._database_config.url
    
    @property
    def supabase_config(self) -> Dict[str, str]:
        """Supabase configuration"""
        return {
            "url": self._database_config.url,
            "anon_key": self._database_config.anon_key,
            "service_role_key": self._database_config.service_role_key or "",
            "password": self._database_config.password or "",
            "project_ref": self._database_config.project_ref or ""
        }
    
    @property
    def google_cloud_config(self) -> Dict[str, str]:
        """Google Cloud configuration"""
        return {
            "project_id": self._google_cloud_config.project_id,
            "location": self._google_cloud_config.location,
            "credentials_path": self._google_cloud_config.credentials_path,
            "use_vertex_ai": str(self._google_cloud_config.use_vertex_ai)
        }
    
    @property
    def server_config(self) -> ServerConfig:
        """Server configuration"""
        return self._server_config
    
    @property
    def agent_config(self) -> AgentConfig:
        """Agent configuration"""
        return self._agent_config
    
    def is_supabase_enabled(self) -> bool:
        """Check if Supabase is properly configured"""
        return bool(self._database_config.url and self._database_config.anon_key)
    
    def is_google_cloud_enabled(self) -> bool:
        """Check if Google Cloud is properly configured"""
        return bool(self._google_cloud_config.project_id and 
                   self._google_cloud_config.credentials_path)
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not self.is_google_cloud_enabled():
            errors.append("Google Cloud configuration incomplete")
        
        if not self.is_supabase_enabled():
            errors.append("Supabase configuration incomplete")
        
        if not os.path.exists(self._google_cloud_config.credentials_path):
            errors.append(f"Google Cloud credentials file not found: {self._google_cloud_config.credentials_path}")
        
        return errors


# Global configuration instance
config = Configuration()