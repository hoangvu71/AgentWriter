"""
Domain entities for the multi-agent book writing system.
Contains all data models aligned with the Supabase database schema.
"""

# Core entity classes
from .entities import (
    # User and session management
    User,
    Session,
    
    # Content entities
    Plot,
    Author,
    WorldBuilding,
    Characters,
    
    # Genre hierarchy
    Genre,
    Subgenre,
    Microgenre,
    Trope,
    Tone,
    TargetAudience,
    
    # System entities
    OrchestratorDecision,
    ImprovementSession,
    Iteration,
    
    # Enums
    WorldType,
)

__all__ = [
    # User and session management
    "User",
    "Session",
    
    # Content entities
    "Plot",
    "Author", 
    "WorldBuilding",
    "Characters",
    
    # Genre hierarchy
    "Genre",
    "Subgenre",
    "Microgenre",
    "Trope",
    "Tone",
    "TargetAudience",
    
    # System entities
    "OrchestratorDecision",
    "ImprovementSession",
    "Iteration",
    
    # Enums
    "WorldType",
]