#!/usr/bin/env python3
"""
Supabase service for data persistence in multi-agent book writing system
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

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
            
            plot_record = {
                "session_id": session_data["id"],
                "user_id": user_data["id"],
                "title": plot_data.get("title"),
                "plot_summary": plot_data.get("plot_summary"),
                "genre": params.get("genre"),
                "subgenre": params.get("subgenre"),
                "microgenre": params.get("microgenre"),
                "trope": params.get("trope"),
                "tone": params.get("tone"),
                "target_audience": target_audience,
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
                    audience_response = self.client.table("target_audiences").select("age_group, gender, sexual_orientation, description").eq("id", plot["target_audience_id"]).execute()
                    if audience_response.data:
                        audience = audience_response.data[0]
                        flattened_plot["target_audience_age_group"] = audience["age_group"]
                        flattened_plot["target_audience_description"] = audience["description"]
                    else:
                        flattened_plot["target_audience_age_group"] = None
                        flattened_plot["target_audience_description"] = None
                else:
                    flattened_plot["target_audience_age_group"] = None
                    flattened_plot["target_audience_description"] = None
                
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

# Global Supabase service instance
supabase_service = SupabaseService()