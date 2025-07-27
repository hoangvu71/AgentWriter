"""
Writing tools for agents to persist content to the database
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import uuid
from functools import wraps

# Google ADK uses simple functions as tools, not FunctionDeclaration objects

from ..core.container import get_container
from ..core.safe_async_runner import run_async_safe

logger = logging.getLogger(__name__)


# Legacy function replaced with safe async runner - kept for backward compatibility
def run_async_in_sync(coro):
    """Helper to run async operations synchronously for ADK compatibility (DEPRECATED)"""
    logger.warning("run_async_in_sync is deprecated, use run_async_safe instead")
    return run_async_safe(coro, timeout=10.0)


def save_plot(
    title: str,
    plot_summary: str,
    genre: Optional[str] = None,
    themes: Optional[List[str]] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    author_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Save a generated plot to the database
    
    Args:
        title: The title of the plot
        plot_summary: The full plot summary
        genre: The genre of the plot
        themes: List of themes in the plot
        session_id: Current session ID
        user_id: Current user ID
        author_id: Associated author ID if any
        
    Returns:
        Dict containing the saved plot ID and confirmation
    """
    try:
        container = get_container()
        plot_repository = container.plot_repository()
        session_repository = container.session_repository()
        
        # Get session info from context if not provided
        if not session_id:
            session_id = container.get_current_session_id()
            logger.info(f"Retrieved session_id from container: {session_id}")
        if not user_id:
            user_id = container.get_current_user_id()
            logger.info(f"Retrieved user_id from container: {user_id}")
        
        # Ensure session exists before creating plot using safe async runner
        run_async_safe(session_repository.ensure_session_exists(session_id, user_id), timeout=10.0)
        logger.info(f"Session {session_id} ensured to exist")
        
        logger.info(f"Final session_id: {session_id}, user_id: {user_id}")
        
        # Generate proper UUIDs if not provided
        
        from ..models.entities import Plot
        plot_entity = Plot(
            session_id=session_id or str(uuid.uuid4()),
            user_id=user_id or str(uuid.uuid4()), 
            title=title,
            plot_summary=plot_summary,
            author_id=author_id
        )
        
        # Add metadata if provided
        if genre or themes:
            plot_entity.metadata = {
                "genre": genre,
                "themes": themes or []
            }
        
        # Run async operation synchronously for ADK compatibility
        def run_create():
            try:
                # Try to run in new event loop
                return asyncio.run(plot_repository.create(plot_entity))
            except RuntimeError:
                # We're in an async context, run in thread
                import concurrent.futures
                import threading
                
                def threaded_create():
                    new_loop = asyncio.new_event_loop()
                    try:
                        asyncio.set_event_loop(new_loop)
                        return new_loop.run_until_complete(plot_repository.create(plot_entity))
                    finally:
                        new_loop.close()
                        asyncio.set_event_loop(None)
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(threaded_create)
                    return future.result(timeout=10)
        
        plot_id = run_create()
        
        logger.info(f"Saved plot '{title}' with ID: {plot_id}")
        
        return {
            "success": True,
            "plot_id": plot_id,
            "message": f"Successfully saved plot '{title}'"
        }
        
    except Exception as e:
        logger.error(f"Error saving plot: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to save plot"
        }


def save_author(
    author_name: str,
    author_bio: str,
    writing_style: str,
    pen_name: Optional[str] = None,
    genres: Optional[List[str]] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Save a generated author profile to the database
    
    Args:
        author_name: The author's full name
        author_bio: Biography of the author
        writing_style: Description of writing style
        pen_name: Optional pen name
        genres: List of genres the author writes
        session_id: Current session ID
        user_id: Current user ID
        
    Returns:
        Dict containing the saved author ID and confirmation
    """
    logger.info(f"Creating author: {author_name}")
    try:
        container = get_container()
        author_repository = container.author_repository()
        
        # Note: Duplicate check removed due to timeout issues in async context
        # The AI agent instructions now emphasize creating unique names instead
        
        # Get session info from context if not provided
        if not session_id:
            session_id = container.get_current_session_id()
        if not user_id:
            user_id = container.get_current_user_id()
        
        
        # Ensure we have valid UUIDs - this is critical for database compatibility
        def ensure_valid_uuid(value, fallback_prefix="generated"):
            if not value:
                return str(uuid.uuid4())
            # If it's already a valid UUID, return as-is
            try:
                uuid.UUID(value)
                return value
            except (ValueError, TypeError):
                # If not a valid UUID, generate a new one
                logger.warning(f"Invalid UUID '{value}', generating new one")
                return str(uuid.uuid4())
        
        session_id = ensure_valid_uuid(session_id)
        user_id = ensure_valid_uuid(user_id)
        
        logger.info(f"Creating author '{author_name}' with session_id: {session_id}, user_id: {user_id}")
        
        from ..models.entities import Author
        author_entity = Author(
            session_id=session_id,
            user_id=user_id,
            author_name=author_name,
            biography=author_bio,  # Field name is 'biography' in entity
            writing_style=writing_style,
            pen_name=pen_name
        )
        
        # Add metadata if provided
        if genres:
            author_entity.metadata = {"genres": genres}
        
        author_id = run_async_in_sync(author_repository.create(author_entity))
        
        logger.info(f"Saved author '{author_name}' with ID: {author_id}")
        
        return {
            "success": True,
            "author_id": author_id,
            "message": f"Successfully saved author '{author_name}'"
        }
        
    except Exception as e:
        logger.error(f"Error saving author '{author_name}': {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to save author '{author_name}': {str(e)}"
        }


def save_world_building(
    world_name: str,
    description: str,
    plot_id: str,
    geography: Optional[Dict[str, Any]] = None,
    culture: Optional[Dict[str, Any]] = None,
    history: Optional[Dict[str, Any]] = None,
    magic_system: Optional[Dict[str, Any]] = None,
    technology: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Save world building details to the database
    
    Args:
        world_name: Name of the world
        description: Overall world description
        plot_id: Associated plot ID
        geography: Geographic details
        culture: Cultural information
        history: Historical background
        magic_system: Magic system details (if applicable)
        technology: Technology level and details
        session_id: Current session ID
        user_id: Current user ID
        
    Returns:
        Dict containing the saved world building ID and confirmation
    """
    try:
        container = get_container()
        world_repository = container.world_building_repository()
        
        # Get session info from context if not provided
        if not session_id:
            session_id = container.get_current_session_id()
        if not user_id:
            user_id = container.get_current_user_id()
        
        from ..models.entities import WorldBuilding
        
        # Combine all the world building details into world_content
        world_details = [description]
        
        if geography:
            world_details.append(f"Geography: {geography}")
        if culture:
            world_details.append(f"Culture: {culture}")
        if history:
            world_details.append(f"History: {history}")
        if magic_system:
            world_details.append(f"Magic System: {magic_system}")
        if technology:
            world_details.append(f"Technology: {technology}")
            
        world_content = "\n\n".join(world_details)
        
        world_entity = WorldBuilding(
            session_id=session_id or str(uuid.uuid4()),
            user_id=user_id or str(uuid.uuid4()),
            plot_id=plot_id,
            world_name=world_name,
            world_type="fantasy",  # Default type, could be parameterized
            world_content=world_content
        )
        
        world_id = run_async_in_sync(world_repository.create(world_entity))
        
        logger.info(f"Saved world '{world_name}' with ID: {world_id}")
        
        return {
            "success": True,
            "world_building_id": world_id,
            "message": f"Successfully saved world '{world_name}'"
        }
        
    except Exception as e:
        logger.error(f"Error saving world building: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to save world building"
        }


def save_characters(
    plot_id: str,
    world_building_id: str,
    characters: List[Dict[str, Any]],
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Save character information to the database
    
    Args:
        plot_id: Associated plot ID
        world_building_id: Associated world building ID
        characters: List of character dictionaries
        session_id: Current session ID
        user_id: Current user ID
        
    Returns:
        Dict containing the saved characters ID and confirmation
    """
    try:
        container = get_container()
        characters_repository = container.characters_repository()
        
        # Get session info from context if not provided
        if not session_id:
            session_id = container.get_current_session_id()
        if not user_id:
            user_id = container.get_current_user_id()
        
        from ..models.entities import Characters
        characters_entity = Characters(
            session_id=session_id or str(uuid.uuid4()),
            user_id=user_id or str(uuid.uuid4()),
            plot_id=plot_id,
            world_id=world_building_id,  # Entity uses 'world_id', not 'world_building_id'
            character_count=len(characters),
            characters=characters
        )
        
        characters_id = run_async_in_sync(characters_repository.create(characters_entity))
        
        logger.info(f"Saved {len(characters)} characters with ID: {characters_id}")
        
        return {
            "success": True,
            "characters_id": characters_id,
            "character_count": len(characters),
            "message": f"Successfully saved {len(characters)} characters"
        }
        
    except Exception as e:
        logger.error(f"Error saving characters: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to save characters"
        }


def get_plot(plot_id: str) -> Dict[str, Any]:
    """
    Retrieve a plot by ID
    
    Args:
        plot_id: The plot ID to retrieve
        
    Returns:
        Dict containing the plot data or error
    """
    try:
        container = get_container()
        plot_repository = container.plot_repository()
        
        plot = run_async_in_sync(plot_repository.get_by_id(plot_id))
        
        if plot:
            return {
                "success": True,
                "plot": plot.to_dict()
            }
        else:
            return {
                "success": False,
                "message": f"Plot with ID {plot_id} not found"
            }
            
    except Exception as e:
        logger.error(f"Error retrieving plot: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve plot"
        }


def get_author(author_id: str) -> Dict[str, Any]:
    """
    Retrieve an author by ID
    
    Args:
        author_id: The author ID to retrieve
        
    Returns:
        Dict containing the author data or error
    """
    try:
        container = get_container()
        author_repository = container.author_repository()
        
        author = run_async_in_sync(author_repository.get_by_id(author_id))
        
        if author:
            return {
                "success": True,
                "author": author.to_dict()
            }
        else:
            return {
                "success": False,
                "message": f"Author with ID {author_id} not found"
            }
            
    except Exception as e:
        logger.error(f"Error retrieving author: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve author"
        }


def list_plots(
    session_id: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    List recent plots for the current session
    
    Args:
        session_id: Session ID to filter by
        limit: Maximum number of plots to return
        
    Returns:
        Dict containing list of plots
    """
    try:
        container = get_container()
        plot_repository = container.plot_repository()
        
        if not session_id:
            session_id = container.get_current_session_id()
        
        plots = run_async_in_sync(plot_repository.get_by_session(session_id, limit=limit))
        
        return {
            "success": True,
            "plots": [plot.to_dict() for plot in plots],
            "count": len(plots)
        }
        
    except Exception as e:
        logger.error(f"Error listing plots: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to list plots"
        }


def list_authors(
    session_id: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    List recent authors for the current session
    
    Args:
        session_id: Session ID to filter by
        limit: Maximum number of authors to return
        
    Returns:
        Dict containing list of authors
    """
    try:
        container = get_container()
        author_repository = container.author_repository()
        
        if not session_id:
            session_id = container.get_current_session_id()
        
        authors = run_async_in_sync(author_repository.get_by_session(session_id, limit=limit))
        
        return {
            "success": True,
            "authors": [author.to_dict() for author in authors],
            "count": len(authors)
        }
        
    except Exception as e:
        logger.error(f"Error listing authors: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to list authors"
        }


# Google ADK uses simple functions as tools
# The functions above are the actual tools that agents can use
