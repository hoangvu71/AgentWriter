"""
Library service for managing plots and authors data
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LibraryService:
    """Service for handling library operations with proper error handling and caching"""
    
    def __init__(self, supabase_service):
        self.supabase_service = supabase_service
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
        
    async def get_user_library_data(self, user_id: str, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """
        Get paginated library data for a specific user
        Returns both plots and authors with metadata
        """
        try:
            # Calculate offset for pagination
            offset = (page - 1) * limit
            
            # Get user plots and authors in parallel
            plots_task = self._get_user_plots_paginated(user_id, offset, limit)
            authors_task = self._get_user_authors_paginated(user_id, offset, limit)
            
            plots_data, authors_data = await asyncio.gather(plots_task, authors_task)
            
            return {
                "success": True,
                "plots": plots_data,
                "authors": authors_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "has_more_plots": len(plots_data["items"]) == limit,
                    "has_more_authors": len(authors_data["items"]) == limit
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting library data for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "plots": {"items": [], "total": 0},
                "authors": {"items": [], "total": 0}
            }
    
    async def _get_user_plots_paginated(self, user_id: str, offset: int, limit: int) -> Dict[str, Any]:
        """Get paginated plots for a user with metadata"""
        try:
            # Get total count first
            count_response = self.supabase_service.client.table("plots").select("id", count="exact").eq("user_id", user_id).execute()
            total_count = count_response.count if count_response.count else 0
            
            # Get paginated plots with metadata
            plots_response = self.supabase_service.client.table("plots").select(
                "id, title, plot_summary, genre, subgenre, microgenre, trope, tone, target_audience, created_at, user_id, session_id"
            ).eq("user_id", user_id).order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            
            # Process plots and add metadata
            plots = []
            for plot in plots_response.data:
                processed_plot = {
                    **plot,
                    "type": "plot",
                    "display_title": plot.get("title", "Untitled Plot"),
                    "display_description": plot.get("plot_summary", "No summary available"),
                    "metadata": {
                        "genre": plot.get("genre", "Unknown"),
                        "subgenre": plot.get("subgenre"),
                        "microgenre": plot.get("microgenre"),
                        "trope": plot.get("trope"),
                        "tone": plot.get("tone"),
                        "target_audience": plot.get("target_audience")
                    }
                }
                plots.append(processed_plot)
            
            return {
                "items": plots,
                "total": total_count,
                "offset": offset,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Error getting plots for user {user_id}: {e}")
            return {"items": [], "total": 0, "offset": offset, "limit": limit}
    
    async def _get_user_authors_paginated(self, user_id: str, offset: int, limit: int) -> Dict[str, Any]:
        """Get paginated authors for a user"""
        try:
            # Get total count first
            count_response = self.supabase_service.client.table("authors").select("id", count="exact").eq("user_id", user_id).execute()
            total_count = count_response.count if count_response.count else 0
            
            # Get paginated authors
            authors_response = self.supabase_service.client.table("authors").select(
                "id, author_name, pen_name, biography, writing_style, created_at, user_id, session_id"
            ).eq("user_id", user_id).order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            
            # Process authors
            authors = []
            for author in authors_response.data:
                processed_author = {
                    **author,
                    "type": "author",
                    "display_title": author.get("author_name", "Unnamed Author"),
                    "display_description": author.get("biography", "No biography available"),
                    "metadata": {
                        "pen_name": author.get("pen_name"),
                        "writing_style": author.get("writing_style")
                    }
                }
                authors.append(processed_author)
            
            return {
                "items": authors,
                "total": total_count,
                "offset": offset,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Error getting authors for user {user_id}: {e}")
            return {"items": [], "total": 0, "offset": offset, "limit": limit}
    
    async def search_user_content(self, user_id: str, query: str, content_type: str = "both", limit: int = 20) -> Dict[str, Any]:
        """
        Search user's plots and authors
        content_type: 'plots', 'authors', or 'both'
        """
        try:
            results = {"plots": [], "authors": []}
            
            if content_type in ["plots", "both"]:
                # Search plots
                plots_response = self.supabase_service.client.table("plots").select(
                    "id, title, plot_summary, genre, created_at"
                ).eq("user_id", user_id).or_(
                    f"title.ilike.%{query}%,plot_summary.ilike.%{query}%,genre.ilike.%{query}%"
                ).order("created_at", desc=True).limit(limit).execute()
                
                results["plots"] = [
                    {
                        **plot,
                        "type": "plot",
                        "display_title": plot.get("title", "Untitled Plot"),
                        "display_description": plot.get("plot_summary", "No summary available")
                    }
                    for plot in plots_response.data
                ]
            
            if content_type in ["authors", "both"]:
                # Search authors
                authors_response = self.supabase_service.client.table("authors").select(
                    "id, author_name, pen_name, biography, created_at"
                ).eq("user_id", user_id).or_(
                    f"author_name.ilike.%{query}%,pen_name.ilike.%{query}%,biography.ilike.%{query}%"
                ).order("created_at", desc=True).limit(limit).execute()
                
                results["authors"] = [
                    {
                        **author,
                        "type": "author",
                        "display_title": author.get("author_name", "Unnamed Author"),
                        "display_description": author.get("biography", "No biography available")
                    }
                    for author in authors_response.data
                ]
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_results": len(results["plots"]) + len(results["authors"])
            }
            
        except Exception as e:
            logger.error(f"Error searching content for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": {"plots": [], "authors": []},
                "total_results": 0
            }
    
    async def get_content_details(self, content_id: str, content_type: str) -> Dict[str, Any]:
        """Get detailed information about a specific plot or author"""
        try:
            if content_type == "plot":
                # Use the same metadata-enriched method as the main plots endpoint
                all_plots = self.supabase_service.get_all_plots_with_metadata()
                
                # Find the specific plot
                plot = None
                for p in all_plots:
                    if p["id"] == content_id:
                        plot = p
                        break
                
                if plot:
                    # Get associated author if exists (plot has author_id)
                    author_response = None
                    if plot.get("author_id"):
                        author_response = self.supabase_service.client.table("authors").select(
                            "id, author_name, pen_name"
                        ).eq("id", plot["author_id"]).execute()
                    
                    plot["associated_author"] = author_response.data[0] if author_response and author_response.data else None
                    return {"success": True, "content": plot}
            
            elif content_type == "author":
                response = self.supabase_service.client.table("authors").select("*").eq("id", content_id).execute()
                if response.data:
                    author = response.data[0]
                    # Get associated plot if exists (plots have author_id pointing to this author)
                    plot_response = self.supabase_service.client.table("plots").select(
                        "id, title, plot_summary"
                    ).eq("author_id", author["id"]).execute()
                    
                    author["associated_plot"] = plot_response.data[0] if plot_response.data else None
                    return {"success": True, "content": author}
            
            return {"success": False, "error": "Content not found"}
            
        except Exception as e:
            logger.error(f"Error getting content details for {content_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get user's library statistics"""
        try:
            # Get counts in parallel
            plots_count_task = self.supabase_service.client.table("plots").select("id", count="exact").eq("user_id", user_id).execute()
            authors_count_task = self.supabase_service.client.table("authors").select("id", count="exact").eq("user_id", user_id).execute()
            
            plots_count_response, authors_count_response = await asyncio.gather(plots_count_task, authors_count_task)
            
            # Get recent activity
            recent_plots = self.supabase_service.client.table("plots").select(
                "id, title, created_at"
            ).eq("user_id", user_id).order("created_at", desc=True).limit(5).execute()
            
            recent_authors = self.supabase_service.client.table("authors").select(
                "id, author_name, created_at"
            ).eq("user_id", user_id).order("created_at", desc=True).limit(5).execute()
            
            return {
                "success": True,
                "statistics": {
                    "total_plots": plots_count_response.count or 0,
                    "total_authors": authors_count_response.count or 0,
                    "recent_plots": recent_plots.data,
                    "recent_authors": recent_authors.data
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "statistics": {
                    "total_plots": 0,
                    "total_authors": 0,
                    "recent_plots": [],
                    "recent_authors": []
                }
            }