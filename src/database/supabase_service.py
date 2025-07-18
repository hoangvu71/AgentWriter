#!/usr/bin/env python3
"""
Supabase service for data persistence in multi-agent book writing system
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv('config/.env')

class SupabaseService:
    """Service class for Supabase database operations"""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        
        self.client: Client = create_client(self.url, self.key)
    
    async def create_or_get_user(self, user_id: str) -> Dict[str, Any]:
        """Create or get user by user_id"""
        try:
            # Check if user exists
            response = self.client.table("users").select("*").eq("user_id", user_id).execute()
            
            if response.data:
                return response.data[0]
            
            # Create new user
            new_user = {
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("users").insert(new_user).execute()
            return response.data[0]
            
        except Exception as e:
            print(f"Error creating/getting user: {e}")
            raise
    
    async def create_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Create a new session"""
        try:
            # Get user UUID
            user_data = await self.create_or_get_user(user_id)
            user_uuid = user_data["id"]
            
            # Check if session exists
            response = self.client.table("sessions").select("*").eq("session_id", session_id).execute()
            
            if response.data:
                return response.data[0]
            
            # Create new session
            new_session = {
                "session_id": session_id,
                "user_id": user_uuid,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("sessions").insert(new_session).execute()
            return response.data[0]
            
        except Exception as e:
            print(f"Error creating session: {e}")
            raise
    
    async def save_orchestrator_decision(self, session_id: str, user_id: str, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save orchestrator decision to database"""
        try:
            # Get user and session UUIDs
            user_data = await self.create_or_get_user(user_id)
            session_data = await self.create_session(session_id, user_id)
            
            orchestrator_record = {
                "session_id": session_data["id"],
                "user_id": user_data["id"],
                "routing_decision": decision_data.get("routing_decision"),
                "agents_invoked": decision_data.get("agents_to_invoke", []),
                "extracted_parameters": decision_data.get("extracted_parameters", {}),
                "workflow_plan": decision_data.get("workflow_plan"),
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("orchestrator_decisions").insert(orchestrator_record).execute()
            return response.data[0]
            
        except Exception as e:
            print(f"Error saving orchestrator decision: {e}")
            raise
    
    async def save_plot(self, session_id: str, user_id: str, plot_data: Dict[str, Any], orchestrator_params: Dict[str, Any] = None, author_id: str = None) -> Dict[str, Any]:
        """Save plot to database"""
        try:
            # Get user and session UUIDs
            user_data = await self.create_or_get_user(user_id)
            session_data = await self.create_session(session_id, user_id)
            
            # Extract parameters from orchestrator data if provided
            params = orchestrator_params.get("extracted_parameters", {}) if orchestrator_params else {}
            target_audience = params.get("target_audience", {})
            
            # Get or create foreign key IDs for normalized tables
            genre_id = await self._get_or_create_genre(params.get("genre")) if params.get("genre") else None
            subgenre_id = await self._get_or_create_subgenre(params.get("subgenre"), genre_id) if params.get("subgenre") and genre_id else None
            microgenre_id = await self._get_or_create_microgenre(params.get("microgenre"), subgenre_id) if params.get("microgenre") and subgenre_id else None
            trope_id = await self._get_or_create_trope(params.get("trope"), microgenre_id) if params.get("trope") and microgenre_id else None
            tone_id = await self._get_or_create_tone(params.get("tone"), trope_id) if params.get("tone") and trope_id else None
            target_audience_id = await self._get_or_create_target_audience(target_audience) if target_audience else None
            
            plot_record = {
                "session_id": session_data["id"],
                "user_id": user_data["id"],
                "title": plot_data.get("title"),
                "plot_summary": plot_data.get("plot_summary"),
                "genre_id": genre_id,
                "subgenre_id": subgenre_id,
                "microgenre_id": microgenre_id,
                "trope_id": trope_id,
                "tone_id": tone_id,
                "target_audience_id": target_audience_id,
                "author_id": author_id,  # New: assign plot to author
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("plots").insert(plot_record).execute()
            return response.data[0]
            
        except Exception as e:
            print(f"Error saving plot: {e}")
            raise
    
    async def save_author(self, session_id: str, user_id: str, author_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save author to database"""
        try:
            # Get user and session UUIDs
            user_data = await self.create_or_get_user(user_id)
            session_data = await self.create_session(session_id, user_id)
            
            author_record = {
                "session_id": session_data["id"],
                "user_id": user_data["id"],
                "author_name": author_data.get("author_name"),
                "pen_name": author_data.get("pen_name"),
                "biography": author_data.get("biography"),
                "writing_style": author_data.get("writing_style"),
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("authors").insert(author_record).execute()
            return response.data[0]
            
        except Exception as e:
            print(f"Error saving author: {e}")
            raise
    
    async def get_user_plots(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all plots for a user"""
        try:
            user_data = await self.create_or_get_user(user_id)
            
            response = self.client.table("plots").select("*").eq("user_id", user_data["id"]).order("created_at", desc=True).limit(limit).execute()
            return response.data
            
        except Exception as e:
            print(f"Error getting user plots: {e}")
            raise
    
    async def get_user_authors(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all authors for a user"""
        try:
            user_data = await self.create_or_get_user(user_id)
            
            response = self.client.table("authors").select("*").eq("user_id", user_data["id"]).order("created_at", desc=True).limit(limit).execute()
            return response.data
            
        except Exception as e:
            print(f"Error getting user authors: {e}")
            raise
    
    async def get_session_data(self, session_id: str) -> Dict[str, Any]:
        """Get all data for a session (plots, authors, decisions)"""
        try:
            # Get session
            session_response = self.client.table("sessions").select("*").eq("session_id", session_id).execute()
            
            if not session_response.data:
                return {"session": None, "plots": [], "authors": [], "decisions": []}
            
            session_uuid = session_response.data[0]["id"]
            
            # Get plots
            plots_response = self.client.table("plots").select("*").eq("session_id", session_uuid).execute()
            
            # Get authors
            authors_response = self.client.table("authors").select("*").eq("session_id", session_uuid).execute()
            
            # Get orchestrator decisions
            decisions_response = self.client.table("orchestrator_decisions").select("*").eq("session_id", session_uuid).execute()
            
            return {
                "session": session_response.data[0],
                "plots": plots_response.data,
                "authors": authors_response.data,
                "decisions": decisions_response.data
            }
            
        except Exception as e:
            print(f"Error getting session data: {e}")
            raise
    
    async def get_plot_with_author(self, plot_id: str) -> Dict[str, Any]:
        """Get plot with associated author"""
        try:
            # Get plot
            plot_response = self.client.table("plots").select("*").eq("id", plot_id).execute()
            
            if not plot_response.data:
                return {"plot": None, "author": None}
            
            plot_data = plot_response.data[0]
            author_data = None
            
            # Get associated author if plot has author_id
            if plot_data.get("author_id"):
                author_response = self.client.table("authors").select("*").eq("id", plot_data["author_id"]).execute()
                if author_response.data:
                    author_data = author_response.data[0]
            
            return {
                "plot": plot_data,
                "author": author_data
            }
            
        except Exception as e:
            print(f"Error getting plot with author: {e}")
            raise
    
    async def search_plots(self, user_id: str, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search plots by title or summary"""
        try:
            user_data = await self.create_or_get_user(user_id)
            
            # Search in title and plot_summary
            response = self.client.table("plots").select("*").eq("user_id", user_data["id"]).or_(f"title.ilike.%{search_term}%,plot_summary.ilike.%{search_term}%").order("created_at", desc=True).limit(limit).execute()
            
            return response.data
            
        except Exception as e:
            print(f"Error searching plots: {e}")
            raise
    
    async def get_analytics(self, user_id: str = None) -> Dict[str, Any]:
        """Get analytics data"""
        try:
            # Base queries
            plots_query = self.client.table("plots").select("*", count="exact")
            authors_query = self.client.table("authors").select("*", count="exact")
            decisions_query = self.client.table("orchestrator_decisions").select("*", count="exact")
            
            # Filter by user if provided
            if user_id:
                user_data = await self.create_or_get_user(user_id)
                plots_query = plots_query.eq("user_id", user_data["id"])
                authors_query = authors_query.eq("user_id", user_data["id"])
                decisions_query = decisions_query.eq("user_id", user_data["id"])
            
            plots_response = plots_query.execute()
            authors_response = authors_query.execute()
            decisions_response = decisions_query.execute()
            
            return {
                "total_plots": plots_response.count,
                "total_authors": authors_response.count,
                "total_decisions": decisions_response.count,
                "plots_data": plots_response.data,
                "authors_data": authors_response.data,
                "decisions_data": decisions_response.data
            }
            
        except Exception as e:
            print(f"Error getting analytics: {e}")
            raise
    
    def get_all_plots_with_metadata(self) -> List[Dict[str, Any]]:
        """Get all plots with normalized metadata"""
        try:
            # Get all plots first
            plots_response = self.client.table("plots").select("*").order("created_at", desc=True).execute()
            
            plots = []
            for plot in plots_response.data:
                # Add metadata by doing individual lookups
                flattened_plot = {**plot}
                
                # Get genre info
                if plot.get("genre_id"):
                    genre_response = self.client.table("genres").select("name, description").eq("id", plot["genre_id"]).execute()
                    if genre_response.data:
                        flattened_plot["genre_name"] = genre_response.data[0]["name"]
                    else:
                        flattened_plot["genre_name"] = None
                else:
                    flattened_plot["genre_name"] = None
                
                # Get subgenre info
                if plot.get("subgenre_id"):
                    subgenre_response = self.client.table("subgenres").select("name, description").eq("id", plot["subgenre_id"]).execute()
                    if subgenre_response.data:
                        flattened_plot["subgenre_name"] = subgenre_response.data[0]["name"]
                    else:
                        flattened_plot["subgenre_name"] = None
                else:
                    flattened_plot["subgenre_name"] = None
                
                # Get microgenre info
                if plot.get("microgenre_id"):
                    microgenre_response = self.client.table("microgenres").select("name, description").eq("id", plot["microgenre_id"]).execute()
                    if microgenre_response.data:
                        flattened_plot["microgenre_name"] = microgenre_response.data[0]["name"]
                    else:
                        flattened_plot["microgenre_name"] = None
                else:
                    flattened_plot["microgenre_name"] = None
                
                # Get trope info
                if plot.get("trope_id"):
                    trope_response = self.client.table("tropes").select("name, description").eq("id", plot["trope_id"]).execute()
                    if trope_response.data:
                        flattened_plot["trope_name"] = trope_response.data[0]["name"]
                    else:
                        flattened_plot["trope_name"] = None
                else:
                    flattened_plot["trope_name"] = None
                
                # Get tone info
                if plot.get("tone_id"):
                    tone_response = self.client.table("tones").select("name, description").eq("id", plot["tone_id"]).execute()
                    if tone_response.data:
                        flattened_plot["tone_name"] = tone_response.data[0]["name"]
                    else:
                        flattened_plot["tone_name"] = None
                else:
                    flattened_plot["tone_name"] = None
                
                # Get target audience info
                if plot.get("target_audience_id"):
                    audience_response = self.client.table("target_audiences").select("age_group, gender, sexual_orientation").eq("id", plot["target_audience_id"]).execute()
                    if audience_response.data:
                        audience = audience_response.data[0]
                        flattened_plot["target_audience_age_group"] = audience["age_group"]
                        flattened_plot["target_audience_gender"] = audience["gender"]
                        flattened_plot["target_audience_sexual_orientation"] = audience["sexual_orientation"]
                    else:
                        flattened_plot["target_audience_age_group"] = None
                        flattened_plot["target_audience_gender"] = None
                        flattened_plot["target_audience_sexual_orientation"] = None
                else:
                    flattened_plot["target_audience_age_group"] = None
                    flattened_plot["target_audience_gender"] = None
                    flattened_plot["target_audience_sexual_orientation"] = None
                
                plots.append(flattened_plot)
            
            return plots
            
        except Exception as e:
            print(f"Error getting all plots: {e}")
            raise
    
    async def get_all_authors(self) -> List[Dict[str, Any]]:
        """Get all authors"""
        try:
            response = self.client.table("authors").select("*").order("created_at", desc=True).execute()
            return response.data
            
        except Exception as e:
            print(f"Error getting all authors: {e}")
            raise
    
    async def get_plots_by_author(self, author_id: str) -> List[Dict[str, Any]]:
        """Get all plots by a specific author"""
        try:
            response = self.client.table("plots").select("*").eq("author_id", author_id).order("created_at", desc=True).execute()
            return response.data
            
        except Exception as e:
            print(f"Error getting plots by author: {e}")
            raise
    
    def get_plots_by_author_sync(self, author_id: str) -> List[Dict[str, Any]]:
        """Get all plots by a specific author (synchronous)"""
        try:
            response = self.client.table("plots").select("*").eq("author_id", author_id).order("created_at", desc=True).execute()
            return response.data
            
        except Exception as e:
            print(f"Error getting plots by author: {e}")
            raise
    
    async def _get_or_create_genre(self, name: str) -> str:
        """Get or create genre and return its ID"""
        if not name:
            return None
            
        try:
            # Check if genre exists
            response = self.client.table("genres").select("id").eq("name", name).execute()
            
            if response.data:
                return response.data[0]["id"]
            
            # Create new genre
            new_genre = {
                "name": name,
                "description": f"Genre: {name}"
            }
            
            response = self.client.table("genres").insert(new_genre).execute()
            return response.data[0]["id"]
            
        except Exception as e:
            print(f"Error with genre: {e}")
            # If it's a duplicate key error, try to get the existing one
            if "duplicate key" in str(e):
                response = self.client.table("genres").select("id").eq("name", name).execute()
                if response.data:
                    return response.data[0]["id"]
            return None
    
    async def _get_or_create_subgenre(self, name: str, genre_id: str) -> str:
        """Get or create subgenre and return its ID"""
        if not name or not genre_id:
            return None
            
        try:
            # Check if subgenre exists (by name only first)
            response = self.client.table("subgenres").select("id").eq("name", name).execute()
            
            if response.data:
                return response.data[0]["id"]
            
            # Create new subgenre
            new_subgenre = {
                "name": name,
                "genre_id": genre_id,
                "description": f"Subgenre: {name}"
            }
            
            response = self.client.table("subgenres").insert(new_subgenre).execute()
            return response.data[0]["id"]
            
        except Exception as e:
            print(f"Error with subgenre: {e}")
            # If it's a duplicate key error, try to get the existing one
            if "duplicate key" in str(e):
                response = self.client.table("subgenres").select("id").eq("name", name).execute()
                if response.data:
                    return response.data[0]["id"]
            return None
    
    async def _get_or_create_microgenre(self, name: str, subgenre_id: str) -> str:
        """Get or create microgenre and return its ID"""
        if not name or not subgenre_id:
            return None
            
        try:
            # Check if microgenre exists (by name only first)
            response = self.client.table("microgenres").select("id").eq("name", name).execute()
            
            if response.data:
                return response.data[0]["id"]
            
            # Create new microgenre
            new_microgenre = {
                "name": name,
                "subgenre_id": subgenre_id,
                "description": f"Microgenre: {name}"
            }
            
            response = self.client.table("microgenres").insert(new_microgenre).execute()
            return response.data[0]["id"]
            
        except Exception as e:
            print(f"Error with microgenre: {e}")
            # If it's a duplicate key error, try to get the existing one
            if "duplicate key" in str(e):
                response = self.client.table("microgenres").select("id").eq("name", name).execute()
                if response.data:
                    return response.data[0]["id"]
            return None
    
    async def _get_or_create_trope(self, name: str, microgenre_id: str) -> str:
        """Get or create trope and return its ID"""
        if not name or not microgenre_id:
            return None
            
        try:
            # Check if trope exists (first by name only due to unique constraint)
            response = self.client.table("tropes").select("id").eq("name", name).execute()
            
            if response.data:
                return response.data[0]["id"]
            
            # Create new trope
            new_trope = {
                "name": name,
                "microgenre_id": microgenre_id,
                "description": f"Trope: {name}"
            }
            
            response = self.client.table("tropes").insert(new_trope).execute()
            return response.data[0]["id"]
            
        except Exception as e:
            print(f"Error with trope: {e}")
            # If it's a duplicate key error, try to get the existing one
            if "duplicate key" in str(e):
                response = self.client.table("tropes").select("id").eq("name", name).execute()
                if response.data:
                    return response.data[0]["id"]
            return None
    
    async def _get_or_create_tone(self, name: str, trope_id: str) -> str:
        """Get or create tone and return its ID"""
        if not name or not trope_id:
            return None
            
        try:
            # Check if tone exists (by name only first)
            response = self.client.table("tones").select("id").eq("name", name).execute()
            
            if response.data:
                return response.data[0]["id"]
            
            # Create new tone
            new_tone = {
                "name": name,
                "trope_id": trope_id,
                "description": f"Tone: {name}"
            }
            
            response = self.client.table("tones").insert(new_tone).execute()
            return response.data[0]["id"]
            
        except Exception as e:
            print(f"Error with tone: {e}")
            # If it's a duplicate key error, try to get the existing one
            if "duplicate key" in str(e):
                response = self.client.table("tones").select("id").eq("name", name).execute()
                if response.data:
                    return response.data[0]["id"]
            return None
    
    async def _get_or_create_target_audience(self, audience_data: Dict[str, Any]) -> str:
        """Get or create target audience and return its ID"""
        if not audience_data:
            return None
            
        try:
            # Extract audience details
            age_group = audience_data.get("age") or audience_data.get("age_group", "Unknown")
            gender = audience_data.get("gender", "All")
            orientation = audience_data.get("sexual_orientation", "All")
            
            # Check if target audience exists
            response = self.client.table("target_audiences").select("id").eq("age_group", age_group).eq("gender", gender).eq("sexual_orientation", orientation).execute()
            
            if response.data:
                return response.data[0]["id"]
            
            # Create new target audience
            new_audience = {
                "age_group": age_group,
                "gender": gender,
                "sexual_orientation": orientation
            }
            
            response = self.client.table("target_audiences").insert(new_audience).execute()
            return response.data[0]["id"]
            
        except Exception as e:
            print(f"Error with target audience: {e}")
            return None
    
    async def get_all_genres(self) -> List[Dict[str, Any]]:
        """Get all genres with their hierarchical data"""
        try:
            # Get all genres
            genres_response = self.client.table("genres").select("*").order("name").execute()
            genres = []
            
            for genre in genres_response.data:
                genre_data = {
                    "id": genre["id"],
                    "name": genre["name"],
                    "description": genre.get("description", ""),
                    "subgenres": []
                }
                
                # Get subgenres for this genre
                subgenres_response = self.client.table("subgenres").select("*").eq("genre_id", genre["id"]).order("name").execute()
                
                for subgenre in subgenres_response.data:
                    subgenre_data = {
                        "id": subgenre["id"],
                        "name": subgenre["name"],
                        "description": subgenre.get("description", ""),
                        "microgenres": []
                    }
                    
                    # Get microgenres for this subgenre
                    microgenres_response = self.client.table("microgenres").select("*").eq("subgenre_id", subgenre["id"]).order("name").execute()
                    
                    for microgenre in microgenres_response.data:
                        microgenre_data = {
                            "id": microgenre["id"],
                            "name": microgenre["name"],
                            "description": microgenre.get("description", "")
                        }
                        subgenre_data["microgenres"].append(microgenre_data)
                    
                    genre_data["subgenres"].append(subgenre_data)
                
                genres.append(genre_data)
            
            return genres
            
        except Exception as e:
            print(f"Error getting all genres: {e}")
            return []
    
    async def create_genre(self, name: str, description: str) -> Dict[str, Any]:
        """Create a new genre"""
        try:
            new_genre = {
                "name": name,
                "description": description
            }
            
            response = self.client.table("genres").insert(new_genre).execute()
            return response.data[0]
            
        except Exception as e:
            print(f"Error creating genre: {e}")
            raise
    
    async def get_all_target_audiences(self) -> List[Dict[str, Any]]:
        """Get all target audiences"""
        try:
            response = self.client.table("target_audiences").select("*").order("age_group").execute()
            return response.data
            
        except Exception as e:
            print(f"Error getting all target audiences: {e}")
            return []
    
    async def create_target_audience(self, age_group: str, gender: str, sexual_orientation: str) -> Dict[str, Any]:
        """Create a new target audience"""
        try:
            new_audience = {
                "age_group": age_group,
                "gender": gender,
                "sexual_orientation": sexual_orientation
            }
            
            response = self.client.table("target_audiences").insert(new_audience).execute()
            return response.data[0]
            
        except Exception as e:
            print(f"Error creating target audience: {e}")
            raise
    
    async def update_plot_author(self, plot_id: str, author_id: str) -> Dict[str, Any]:
        """Update a plot to assign it to an author"""
        try:
            response = self.client.table("plots").update({"author_id": author_id}).eq("id", plot_id).execute()
            return response.data[0] if response.data else None
            
        except Exception as e:
            print(f"Error updating plot author: {e}")
            raise
    
    async def get_plot_by_id(self, plot_id: str) -> Dict[str, Any]:
        """Get a single plot by ID"""
        try:
            response = self.client.table("plots").select("*").eq("id", plot_id).execute()
            return response.data[0] if response.data else None
            
        except Exception as e:
            print(f"Error getting plot by ID: {e}")
            return None
    
    async def get_author_by_id(self, author_id: str) -> Dict[str, Any]:
        """Get a single author by ID"""
        try:
            response = self.client.table("authors").select("*").eq("id", author_id).execute()
            return response.data[0] if response.data else None
            
        except Exception as e:
            print(f"Error getting author by ID: {e}")
            return None
    
    async def save_enhanced_plot(self, plot_id: str, enhanced_content: Dict[str, Any]) -> Dict[str, Any]:
        """Save enhanced plot content back to database"""
        try:
            # Update the existing plot with enhanced content
            update_data = {
                "title": enhanced_content.get("title"),
                "plot_summary": enhanced_content.get("plot_summary"),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("plots").update(update_data).eq("id", plot_id).execute()
            return response.data[0] if response.data else None
            
        except Exception as e:
            print(f"Error saving enhanced plot: {e}")
            return None
    
    async def save_enhanced_author(self, author_id: str, enhanced_content: Dict[str, Any]) -> Dict[str, Any]:
        """Save enhanced author content back to database"""
        try:
            # Update the existing author with enhanced content
            update_data = {
                "author_name": enhanced_content.get("author_name"),
                "biography": enhanced_content.get("biography"),
                "writing_style": enhanced_content.get("writing_style"),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("authors").update(update_data).eq("id", author_id).execute()
            return response.data[0] if response.data else None
            
        except Exception as e:
            print(f"Error saving enhanced author: {e}")
            return None

    # ========== IMPROVEMENT SESSION MANAGEMENT ==========
    
    async def create_improvement_session(
        self, 
        user_id: str, 
        session_id: str, 
        original_content: str,
        content_type: str,
        content_id: str = None,
        target_score: float = 9.5,
        max_iterations: int = 4
    ) -> str:
        """Create new improvement session and return improvement_session_id"""
        
        # TDD-driven validation that should have been implemented from the start
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")
        if not session_id or not session_id.strip():
            raise ValueError("session_id is required")
        if not original_content or not original_content.strip():
            raise ValueError("original_content is required")
        if content_type not in ["plot", "author", "text"]:
            raise ValueError("Invalid content_type. Must be 'plot', 'author', or 'text'")
        if target_score < 0 or target_score > 10:
            raise ValueError("target_score must be between 0 and 10")
        if max_iterations < 1 or max_iterations > 10:
            raise ValueError("max_iterations must be between 1 and 10")
        
        try:
            # Get user UUID
            user_data = await self.create_or_get_user(user_id)
            user_uuid = user_data["id"]
            
            # Create improvement session record
            session_record = {
                "user_id": user_uuid,
                "session_id": session_id,
                "original_content": original_content,
                "content_type": content_type,
                "target_score": target_score,
                "max_iterations": max_iterations,
                "status": "in_progress",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Store content_id in the session_id field as a reference for now
            # Note: original_content_id field doesn't exist in current schema
            if content_id:
                session_record["session_id"] = f"{session_id}_{content_id}"
            
            response = self.client.table("improvement_sessions").insert(session_record).execute()
            
            if response.data:
                improvement_session_id = response.data[0]["id"]
                print(f"Created improvement session: {improvement_session_id}")
                return improvement_session_id
            else:
                raise Exception("No data returned from improvement session creation")
            
        except Exception as e:
            print(f"Error creating improvement session: {e}")
            raise Exception(f"Failed to create improvement session: {str(e)}")

    async def update_improvement_session_status(
        self,
        improvement_session_id: str,
        status: str = "completed",
        final_content: str = None,
        final_score: float = None,
        completion_reason: str = None
    ) -> Dict[str, Any]:
        """Update improvement session with final results"""
        
        # TDD-driven validation that should have been implemented from the start
        if not improvement_session_id or not improvement_session_id.strip():
            raise ValueError("improvement_session_id is required")
        if status not in ["in_progress", "completed", "failed", "cancelled"]:
            raise ValueError("Invalid status. Must be 'in_progress', 'completed', 'failed', or 'cancelled'")
        if final_score is not None and (final_score < 0 or final_score > 10):
            raise ValueError("final_score must be between 0 and 10")
        
        try:
            update_data = {
                "status": status,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            if final_content:
                update_data["final_content"] = final_content
            if final_score:
                update_data["final_score"] = final_score
            if completion_reason:
                update_data["completion_reason"] = completion_reason
            
            response = self.client.table("improvement_sessions").update(update_data).eq("id", improvement_session_id).execute()
            
            if response.data:
                print(f"Updated improvement session: {improvement_session_id}")
                return response.data[0]
            else:
                raise Exception("No data returned from improvement session update")
            
        except Exception as e:
            print(f"Error updating improvement session: {e}")
            raise

    # ========== ITERATION DATA PERSISTENCE ==========
    
    async def create_iteration_record(
        self,
        improvement_session_id: str,
        iteration_number: int,
        content: str
    ) -> str:
        """Create iteration record and return iteration_id"""
        
        # TDD-driven validation that should have been implemented from the start
        if not improvement_session_id or not improvement_session_id.strip():
            raise ValueError("improvement_session_id is required")
        if iteration_number < 1:
            raise ValueError("iteration_number must be positive")
        if not content or not content.strip():
            raise ValueError("content is required")
        
        try:
            iteration_record = {
                "improvement_session_id": improvement_session_id,
                "iteration_number": iteration_number,
                "content": content,
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("iterations").insert(iteration_record).execute()
            
            if response.data:
                iteration_id = response.data[0]["id"]
                print(f"Created iteration {iteration_number}: {iteration_id}")
                return iteration_id
            else:
                raise Exception("No data returned from iteration creation")
            
        except Exception as e:
            print(f"Error creating iteration record: {e}")
            raise

    async def save_critique_data(
        self,
        iteration_id: str,
        critique_json: Dict[str, Any],
        agent_response: str
    ) -> Dict[str, Any]:
        """Save critique response to database"""
        
        # TDD-driven validation that should have been implemented from the start
        if not iteration_id or not iteration_id.strip():
            raise ValueError("iteration_id is required")
        if not isinstance(critique_json, dict):
            raise ValueError("critique_json must be a dictionary")
        if not agent_response or not agent_response.strip():
            raise ValueError("agent_response is required")
        
        try:
            critique_record = {
                "iteration_id": iteration_id,
                "critique_json": critique_json,
                "agent_response": agent_response,
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("critiques").insert(critique_record).execute()
            
            if response.data:
                print(f"Saved critique for iteration: {iteration_id}")
                return response.data[0]
            else:
                raise Exception("No data returned from critique save")
            
        except Exception as e:
            print(f"Error saving critique: {e}")
            raise

    async def save_enhancement_data(
        self,
        iteration_id: str,
        enhanced_content: str,
        changes_made: Dict[str, Any],
        rationale: str,
        confidence_score: int = None
    ) -> Dict[str, Any]:
        """Save enhancement response to database"""
        
        # TDD-driven validation that should have been implemented from the start
        if not iteration_id or not iteration_id.strip():
            raise ValueError("iteration_id is required")
        if not enhanced_content or not enhanced_content.strip():
            raise ValueError("enhanced_content is required")
        if not isinstance(changes_made, dict):
            raise ValueError("changes_made must be a dictionary")
        if not rationale or not rationale.strip():
            raise ValueError("rationale is required")
        if confidence_score is not None and (confidence_score < 0 or confidence_score > 10):
            raise ValueError("confidence_score must be between 0 and 10")
        
        try:
            enhancement_record = {
                "iteration_id": iteration_id,
                "enhanced_content": enhanced_content,
                "changes_made": changes_made,
                "rationale": rationale,
                "created_at": datetime.utcnow().isoformat()
            }
            
            if confidence_score is not None:
                enhancement_record["confidence_score"] = confidence_score
            
            response = self.client.table("enhancements").insert(enhancement_record).execute()
            
            if response.data:
                print(f"Saved enhancement for iteration: {iteration_id}")
                return response.data[0]
            else:
                raise Exception("No data returned from enhancement save")
            
        except Exception as e:
            print(f"Error saving enhancement: {e}")
            raise

    async def save_score_data(
        self,
        iteration_id: str,
        overall_score: float,
        category_scores: Dict[str, float],
        score_rationale: str,
        improvement_trajectory: str,
        recommendations: str = None
    ) -> Dict[str, Any]:
        """Save scoring response to database"""
        
        # TDD-driven validation that should have been implemented from the start
        if not iteration_id or not iteration_id.strip():
            raise ValueError("iteration_id is required")
        if overall_score < 0 or overall_score > 10:
            raise ValueError("overall_score must be between 0 and 10")
        if not isinstance(category_scores, dict):
            raise ValueError("category_scores must be a dictionary")
        if not score_rationale or not score_rationale.strip():
            raise ValueError("score_rationale is required")
        if not improvement_trajectory or not improvement_trajectory.strip():
            raise ValueError("improvement_trajectory is required")
        
        try:
            score_record = {
                "iteration_id": iteration_id,
                "overall_score": overall_score,
                "category_scores": category_scores,
                "score_rationale": score_rationale,
                "improvement_trajectory": improvement_trajectory,
                "created_at": datetime.utcnow().isoformat()
            }
            
            if recommendations:
                score_record["recommendations"] = recommendations
            
            response = self.client.table("scores").insert(score_record).execute()
            
            if response.data:
                print(f"Saved score for iteration: {iteration_id}")
                return response.data[0]
            else:
                raise Exception("No data returned from score save")
            
        except Exception as e:
            print(f"Error saving score: {e}")
            raise

    # ========== RETRIEVAL METHODS ==========
    
    async def get_improvement_session_with_iterations(
        self,
        improvement_session_id: str
    ) -> Dict[str, Any]:
        """Get complete improvement session with all iterations"""
        try:
            # Get improvement session
            session_response = self.client.table("improvement_sessions").select("*").eq("id", improvement_session_id).execute()
            
            if not session_response.data:
                return {"session": None, "iterations": []}
            
            session_data = session_response.data[0]
            
            # Get all iterations for this session
            iterations_response = self.client.table("iterations").select("*").eq("improvement_session_id", improvement_session_id).order("iteration_number").execute()
            
            iterations = []
            for iteration in iterations_response.data:
                iteration_id = iteration["id"]
                
                # Get critique for this iteration
                critique_response = self.client.table("critiques").select("*").eq("iteration_id", iteration_id).execute()
                critique_data = critique_response.data[0] if critique_response.data else None
                
                # Get enhancement for this iteration
                enhancement_response = self.client.table("enhancements").select("*").eq("iteration_id", iteration_id).execute()
                enhancement_data = enhancement_response.data[0] if enhancement_response.data else None
                
                # Get score for this iteration
                score_response = self.client.table("scores").select("*").eq("iteration_id", iteration_id).execute()
                score_data = score_response.data[0] if score_response.data else None
                
                # Combine iteration data
                iteration_complete = {
                    **iteration,
                    "critique": critique_data,
                    "enhancement": enhancement_data,
                    "score": score_data
                }
                
                iterations.append(iteration_complete)
            
            return {
                "session": session_data,
                "iterations": iterations
            }
            
        except Exception as e:
            print(f"Error getting improvement session with iterations: {e}")
            raise

    async def get_user_improvement_sessions(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get user's improvement session history"""
        try:
            # Get user UUID
            user_data = await self.create_or_get_user(user_id)
            user_uuid = user_data["id"]
            
            # Get improvement sessions for user
            response = self.client.table("improvement_sessions").select("*").eq("user_id", user_uuid).order("created_at", desc=True).limit(limit).execute()
            
            return response.data
            
        except Exception as e:
            print(f"Error getting user improvement sessions: {e}")
            raise

    async def get_content_improvement_sessions(
        self,
        content_id: str,
        content_type: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get improvement sessions for specific content"""
        try:
            # Since original_content_id doesn't exist, search by session_id pattern
            response = self.client.table("improvement_sessions").select("*").like("session_id", f"%_{content_id}").eq("content_type", content_type).order("created_at", desc=True).limit(limit).execute()
            
            return response.data
            
        except Exception as e:
            print(f"Error getting content improvement sessions: {e}")
            raise

# Global Supabase service instance
supabase_service = SupabaseService()