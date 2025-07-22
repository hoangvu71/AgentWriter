"""
Content management and search API routes using repository pattern.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, List, Optional
from ..core.container import container
from ..repositories.plot_repository import PlotRepository
from ..repositories.author_repository import AuthorRepository
from ..repositories.world_building_repository import WorldBuildingRepository
from ..repositories.characters_repository import CharactersRepository
from ..core.logging import get_logger

router = APIRouter()
logger = get_logger("content")


def get_repositories():
    """Dependency injection for all content repositories"""
    try:
        return {
            "plot_repo": container.get("plot_repository"),
            "author_repo": container.get("author_repository"),
            "world_repo": container.get("world_building_repository"),
            "characters_repo": container.get("characters_repository")
        }
    except Exception as e:
        logger.error(f"Failed to get content repositories: {e}")
        raise HTTPException(status_code=500, detail="Content services unavailable")


@router.get("/content-selection")
async def get_content_selection(repos = Depends(get_repositories)) -> Dict[str, Any]:
    """Get content selection overview"""
    try:
        # Get counts from each repository
        plot_count = await repos["plot_repo"].count()
        author_count = await repos["author_repo"].count()
        world_count = await repos["world_repo"].count()
        characters_count = await repos["characters_repo"].count()
        
        return {
            "success": True,
            "content_types": {
                "plots": {"count": plot_count, "type": "plot"},
                "authors": {"count": author_count, "type": "author"},
                "world_building": {"count": world_count, "type": "world"},
                "characters": {"count": characters_count, "type": "characters"}
            },
            "total_content": plot_count + author_count + world_count + characters_count
        }
    except Exception as e:
        logger.error(f"Error getting content selection: {e}")
        return {"success": False, "error": "Failed to get content overview", "content": []}


@router.get("/search/{user_id}")
async def search_user_content(
    user_id: str,
    query: str = Query(..., description="Search query"),
    content_type: Optional[str] = Query(None, description="Filter by content type: plot, author, world, characters"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results")
) -> Dict[str, Any]:
    """
    Search through user's content across all types.
    
    Args:
        user_id: User ID to search within
        query: Search query string
        content_type: Optional filter by content type
        limit: Maximum number of results to return
        
    Returns:
        Search results with relevance scoring
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    
    try:
        search_results = []
        query_lower = query.lower()
        
        # Get repositories
        repos = get_repositories()
        
        # Search plots if no type filter or type is 'plot'
        if not content_type or content_type == "plot":
            plots = await repos["plot_repo"].get_user_plots(user_id)
            for plot in plots:
                score = 0
                title = plot.get("title", "").lower()
                summary = plot.get("plot_summary", "").lower()
                
                # Calculate relevance score
                if query_lower in title:
                    score += 10
                if query_lower in summary:
                    score += 5
                
                # Word matching for more complex queries
                query_words = query_lower.split()
                for word in query_words:
                    if word in title:
                        score += 3
                    if word in summary:
                        score += 1
                
                if score > 0:
                    search_results.append({
                        "type": "plot",
                        "id": plot.get("id"),
                        "title": plot.get("title"),
                        "summary": plot.get("plot_summary", "")[:200] + "...",
                        "created_at": plot.get("created_at"),
                        "session_id": plot.get("session_id"),
                        "relevance_score": score
                    })
        
        # Search authors if no type filter or type is 'author'
        if not content_type or content_type == "author":
            authors = await repos["author_repo"].get_user_authors(user_id)
            for author in authors:
                score = 0
                name = author.get("author_name", "").lower()
                pen_name = author.get("pen_name", "").lower()
                bio = author.get("biography", "").lower()
                
                # Calculate relevance score
                if query_lower in name:
                    score += 10
                if query_lower in pen_name:
                    score += 8
                if query_lower in bio:
                    score += 3
                
                # Word matching
                query_words = query_lower.split()
                for word in query_words:
                    if word in name:
                        score += 5
                    if word in pen_name:
                        score += 4
                    if word in bio:
                        score += 1
                
                if score > 0:
                    search_results.append({
                        "type": "author",
                        "id": author.get("id"),
                        "title": author.get("author_name"),
                        "summary": f"Pen name: {author.get('pen_name', 'N/A')}",
                        "created_at": author.get("created_at"),
                        "session_id": author.get("session_id"),
                        "relevance_score": score
                    })
        
        # Search world building if no type filter or type is 'world'
        if not content_type or content_type == "world":
            worlds = await repos["world_repo"].get_user_world_building(user_id)
            for world in worlds:
                score = 0
                name = world.get("world_name", "").lower()
                content_text = world.get("world_content", "").lower()
                
                # Calculate relevance score
                if query_lower in name:
                    score += 10
                if query_lower in content_text:
                    score += 3
                
                # Word matching
                query_words = query_lower.split()
                for word in query_words:
                    if word in name:
                        score += 5
                    if word in content_text:
                        score += 1
                
                if score > 0:
                    search_results.append({
                        "type": "world_building",
                        "id": world.get("id"),
                        "title": world.get("world_name"),
                        "summary": world.get("world_content", "")[:200] + "...",
                        "created_at": world.get("created_at"),
                        "session_id": world.get("session_id"),
                        "relevance_score": score
                    })
        
        # Search characters if no type filter or type is 'characters'
        if not content_type or content_type == "characters":
            characters = await repos["characters_repo"].get_user_characters(user_id)
            for char_set in characters:
                score = 0
                context = char_set.get("world_context_integration", "").lower()
                characters_data = str(char_set.get("characters", [])).lower()
                
                # Calculate relevance score
                if query_lower in context:
                    score += 5
                if query_lower in characters_data:
                    score += 3
                
                # Word matching
                query_words = query_lower.split()
                for word in query_words:
                    if word in context:
                        score += 2
                    if word in characters_data:
                        score += 1
                
                if score > 0:
                    search_results.append({
                        "type": "characters",
                        "id": char_set.get("id"),
                        "title": f"Character Set ({char_set.get('character_count', 0)} characters)",
                        "summary": char_set.get("world_context_integration", "")[:200] + "...",
                        "created_at": char_set.get("created_at"),
                        "session_id": char_set.get("session_id"),
                        "relevance_score": score
                    })
        
        # Sort by relevance score (highest first) and apply limit
        search_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        search_results = search_results[:limit]
        
        return {
            "query": query,
            "content_type": content_type,
            "results": search_results,
            "total_results": len(search_results),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error searching content for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/{user_id}/suggestions")
async def get_search_suggestions(
    user_id: str,
    prefix: str = Query(..., min_length=2, description="Search prefix for suggestions")
) -> List[str]:
    """
    Get search suggestions based on user's content.
    
    Args:
        user_id: User ID to generate suggestions for
        prefix: Prefix to match suggestions against
        
    Returns:
        List of search suggestions
    """
    try:
        suggestions = set()
        prefix_lower = prefix.lower()
        
        # Get repositories
        repos = get_repositories()
        
        # Get suggestions from plot titles
        plots = await repos["plot_repo"].get_user_plots(user_id)
        for plot in plots:
            title = plot.get("title", "")
            if title.lower().startswith(prefix_lower):
                suggestions.add(title)
            
            # Add individual words that start with prefix
            for word in title.split():
                if word.lower().startswith(prefix_lower) and len(word) > 2:
                    suggestions.add(word)
        
        # Get suggestions from author names
        authors = await repos["author_repo"].get_user_authors(user_id)
        for author in authors:
            name = author.get("author_name", "")
            pen_name = author.get("pen_name", "")
            
            if name.lower().startswith(prefix_lower):
                suggestions.add(name)
            if pen_name.lower().startswith(prefix_lower):
                suggestions.add(pen_name)
            
            # Add individual words
            for word in (name + " " + pen_name).split():
                if word.lower().startswith(prefix_lower) and len(word) > 2:
                    suggestions.add(word)
        
        # Limit suggestions and sort
        suggestion_list = sorted(list(suggestions))[:10]
        
        return suggestion_list
        
    except Exception as e:
        logger.error(f"Error generating suggestions for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")