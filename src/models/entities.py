"""
Domain entities for the multi-agent book writing system.
Aligned with actual Supabase database schema.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class WorldType(Enum):
    """World types for world building"""
    HIGH_FANTASY = "high_fantasy"
    URBAN_FANTASY = "urban_fantasy"
    SCIENCE_FICTION = "science_fiction"
    HISTORICAL_FICTION = "historical_fiction"
    CONTEMPORARY = "contemporary"
    DYSTOPIAN = "dystopian"
    OTHER = "other"


@dataclass
class User:
    """User entity - matches users table"""
    id: Optional[str] = None  # UUID
    user_id: str = ""  # VARCHAR(255) - external user ID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Session:
    """Session entity - matches sessions table"""
    id: Optional[str] = None  # UUID
    session_id: str = ""  # VARCHAR(255) - external session ID
    user_id: str = ""  # UUID - references users.id
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Plot:
    """Plot entity - matches plots table structure"""
    id: Optional[str] = None  # UUID
    session_id: str = ""  # UUID - references sessions.id
    user_id: str = ""  # UUID - references users.id
    title: str = ""  # TEXT
    plot_summary: str = ""  # TEXT
    
    # Genre fields (originally VARCHAR, now foreign keys after migrations)
    genre_id: Optional[str] = None  # UUID - references genres.id
    subgenre_id: Optional[str] = None  # UUID - references subgenres.id
    microgenre_id: Optional[str] = None  # UUID - references microgenres.id
    trope_id: Optional[str] = None  # UUID - references tropes.id
    tone_id: Optional[str] = None  # UUID - references tones.id
    
    # Target audience (JSONB in original, now foreign key after migration)
    target_audience_id: Optional[str] = None  # UUID - references target_audiences.id
    
    # Author relationship (added in migration 004)
    author_id: Optional[str] = None  # UUID - references authors.id
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Author:
    """Author entity - matches authors table structure"""
    id: Optional[str] = None  # UUID
    session_id: str = ""  # UUID - references sessions.id
    user_id: str = ""  # UUID - references users.id
    # Note: plot_id was removed in migration 004 - authors can have multiple plots now
    author_name: str = ""  # VARCHAR(255)
    pen_name: Optional[str] = None  # VARCHAR(255)
    biography: str = ""  # TEXT
    writing_style: str = ""  # TEXT
    created_at: Optional[datetime] = None


@dataclass
class WorldBuilding:
    """World building entity - matches simplified world_building table schema"""
    id: Optional[str] = None  # UUID
    session_id: str = ""  # UUID - references sessions.id
    user_id: str = ""  # UUID - references users.id
    plot_id: Optional[str] = None  # UUID - references plots.id (nullable)
    world_name: str = ""  # TEXT
    world_type: str = ""  # TEXT - Type of world (high_fantasy, urban_fantasy, science_fiction, etc.)
    world_content: str = ""  # TEXT - Complete world building content as single comprehensive string
    
    # Timestamps
    created_at: Optional[datetime] = None


@dataclass
class Characters:
    """Characters entity - matches characters table from migration 008"""
    id: Optional[str] = None  # UUID
    session_id: str = ""  # UUID - references sessions.id
    user_id: str = ""  # UUID - references users.id
    world_id: Optional[str] = None  # UUID - references world_building.id (nullable)
    plot_id: Optional[str] = None  # UUID - references plots.id (nullable)
    character_count: int = 0  # INTEGER
    world_context_integration: Optional[str] = None  # TEXT
    
    # JSONB fields for character data
    characters: List[Dict[str, Any]] = field(default_factory=list)  # JSONB
    relationship_networks: Dict[str, Any] = field(default_factory=dict)  # JSONB
    character_dynamics: Dict[str, Any] = field(default_factory=dict)  # JSONB
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Genre:
    """Genre entity - hierarchical genre system"""
    id: Optional[str] = None  # UUID
    name: str = ""  # TEXT with UNIQUE constraint
    description: str = ""  # TEXT
    created_at: Optional[datetime] = None


@dataclass
class Subgenre:
    """Subgenre entity - belongs to genre"""
    id: Optional[str] = None  # UUID
    genre_id: str = ""  # UUID - references genres.id
    name: str = ""  # TEXT with UNIQUE constraint
    description: str = ""  # TEXT
    created_at: Optional[datetime] = None


@dataclass
class Microgenre:
    """Microgenre entity - belongs to subgenre"""
    id: Optional[str] = None  # UUID
    subgenre_id: str = ""  # UUID - references subgenres.id
    name: str = ""  # TEXT with UNIQUE constraint
    description: str = ""  # TEXT
    created_at: Optional[datetime] = None


@dataclass
class Trope:
    """Trope entity - belongs to microgenre (after migration 005)"""
    id: Optional[str] = None  # UUID
    microgenre_id: str = ""  # UUID - references microgenres.id
    name: str = ""  # TEXT with UNIQUE constraint
    description: str = ""  # TEXT
    created_at: Optional[datetime] = None


@dataclass
class Tone:
    """Tone entity - belongs to trope (after migration 005)"""
    id: Optional[str] = None  # UUID
    trope_id: str = ""  # UUID - references tropes.id
    name: str = ""  # TEXT with UNIQUE constraint
    description: str = ""  # TEXT
    created_at: Optional[datetime] = None


@dataclass
class TargetAudience:
    """Target audience entity - simplified after migration 006"""
    id: Optional[str] = None  # UUID
    age_group: str = ""  # TEXT (e.g., "Young Adult", "Adult")
    gender: str = ""  # TEXT (e.g., "All", "Male", "Female")
    sexual_orientation: str = ""  # TEXT (e.g., "All", "Heterosexual", "LGBTQ+")
    created_at: Optional[datetime] = None


@dataclass
class OrchestratorDecision:
    """Orchestrator decision entity - for analytics"""
    id: Optional[str] = None  # UUID
    session_id: str = ""  # UUID - references sessions.id
    user_id: str = ""  # UUID - references users.id
    routing_decision: str = ""  # VARCHAR(50)
    agents_invoked: List[str] = field(default_factory=list)  # TEXT[]
    extracted_parameters: Dict[str, Any] = field(default_factory=dict)  # JSONB
    workflow_plan: Optional[str] = None  # TEXT
    created_at: Optional[datetime] = None


@dataclass
class ImprovementSession:
    """Improvement session entity - from migration 007"""
    id: Optional[str] = None  # UUID
    user_id: str = ""  # UUID - references users.id
    session_id: str = ""  # VARCHAR(255)
    original_content: str = ""  # TEXT
    content_type: str = ""  # VARCHAR(50) - 'plot', 'author', 'text'
    target_score: float = 9.5  # DECIMAL
    max_iterations: int = 4  # INTEGER
    status: str = "in_progress"  # VARCHAR(20)
    final_content: Optional[str] = None  # TEXT
    final_score: Optional[float] = None  # DECIMAL
    completion_reason: Optional[str] = None  # TEXT
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class Iteration:
    """Iteration entity - from migration 007"""
    id: Optional[str] = None  # UUID
    improvement_session_id: str = ""  # UUID - references improvement_sessions.id
    iteration_number: int = 1  # INTEGER
    content: str = ""  # TEXT
    created_at: Optional[datetime] = None