"""
Content parameters API routes for genres and target audiences.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from ..core.container import container
from ..core.logging import get_logger

router = APIRouter()
logger = get_logger("parameters")


def get_database():
    """Get database service from container"""
    try:
        return container.get("database")
    except Exception as e:
        logger.error(f"Failed to get database service: {e}")
        raise HTTPException(status_code=500, detail="Database service unavailable")


@router.get("/genres")
async def get_genres_hierarchy(db = Depends(get_database)) -> Dict[str, Any]:
    """Get complete genre hierarchy with all levels"""
    try:
        # Get all genres
        genres = await db.get_all("genres", limit=100)
        
        # Get all subgenres
        subgenres = await db.get_all("subgenres", limit=500)
        
        # Get all microgenres
        microgenres = await db.get_all("microgenres", limit=1000)
        
        # Get all tropes
        tropes = await db.get_all("tropes", limit=1000)
        
        # Get all tones
        tones = await db.get_all("tones", limit=1000)
        
        return {
            "success": True,
            "genres": genres,
            "subgenres": subgenres,
            "microgenres": microgenres,
            "tropes": tropes,
            "tones": tones
        }
        
    except Exception as e:
        logger.error(f"Error fetching genre hierarchy: {e}")
        return {
            "success": False,
            "genres": [],
            "subgenres": [],
            "microgenres": [],
            "tropes": [],
            "tones": [],
            "error": str(e)
        }


@router.get("/target-audiences")
async def get_target_audiences(db = Depends(get_database)) -> Dict[str, Any]:
    """Get all target audience options"""
    try:
        audiences = await db.get_all("target_audiences", limit=100)
        
        return {
            "success": True,
            "audiences": audiences
        }
        
    except Exception as e:
        logger.error(f"Error fetching target audiences: {e}")
        return {
            "success": False,
            "audiences": [],
            "error": str(e)
        }


@router.post("/genres")
async def create_genre(
    name: str,
    description: str,
    db = Depends(get_database)
) -> Dict[str, Any]:
    """Create a new genre"""
    try:
        # Check if genre already exists
        existing = await db.search("genres", {"name": name})
        if existing:
            raise HTTPException(status_code=400, detail="Genre already exists")
        
        # Create new genre
        genre_id = await db.insert("genres", {
            "name": name,
            "description": description
        })
        
        return {
            "success": True,
            "id": genre_id,
            "message": f"Genre '{name}' created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating genre: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create genre: {str(e)}")


@router.post("/target-audiences")
async def create_target_audience(
    age_group: str,
    gender: str,
    sexual_orientation: str,
    description: str = None,
    db = Depends(get_database)
) -> Dict[str, Any]:
    """Create a new target audience"""
    try:
        # Create new target audience
        audience_id = await db.insert("target_audiences", {
            "age_group": age_group,
            "gender": gender,
            "sexual_orientation": sexual_orientation,
            "description": description
        })
        
        return {
            "success": True,
            "id": audience_id,
            "message": "Target audience created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating target audience: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create target audience: {str(e)}")