"""
Dynamic schema service for generating JSON structures from database schemas.
"""

from typing import Dict, List, Any, Optional
from .logging import get_logger
from ..database.database_factory import db_factory


class SchemaService:
    """Service for dynamically generating JSON schemas from database tables"""
    
    def __init__(self):
        self.logger = get_logger("schema_service")
        
        # Map content types to database tables
        self.content_type_mappings = {
            "plot": "plots",
            "author": "authors", 
            "world_building": "world_building",
            "characters": "characters",
            "critique": "critiques",
            "enhancement": "enhancements",
            "scoring": "scores",
            "loregen": None  # LoreGen doesn't map to a database table
        }
        
        # System columns to exclude from agent JSON schemas
        self.system_columns = {
            "id", "session_id", "user_id", "created_at", "updated_at",
            "genre_id", "subgenre_id", "microgenre_id", "trope_id", 
            "tone_id", "target_audience_id", "author_id", "plot_id", 
            "world_id", "improvement_session_id", "iteration_id"
        }
        
        # Type mappings for JSON schema generation
        self.type_mappings = {
            "text": "string",
            "varchar": "string", 
            "character varying": "string",
            "integer": "number",
            "bigint": "number",
            "numeric": "number",
            "decimal": "number",
            "real": "number",
            "double precision": "number",
            "boolean": "boolean",
            "jsonb": "object",
            "json": "object",
            "uuid": "string",
            "timestamp with time zone": "string",
            "timestamp without time zone": "string",
            "date": "string",
            "time": "string"
        }
    
    async def get_agent_json_schema(self, content_type: str) -> Dict[str, Any]:
        """Generate JSON schema for agent based on content type"""
        try:
            # Get table name for content type
            table_name = self.content_type_mappings.get(content_type)
            if not table_name:
                raise ValueError(f"Unknown content type: {content_type}")
            
            # Get table schema from database
            columns = await self._get_table_schema(table_name)
            
            # Generate JSON schema
            json_schema = self._generate_json_schema(columns, content_type)
            
            self.logger.info(f"Generated schema for {content_type}: {list(json_schema.keys())}")
            return json_schema
            
        except Exception as e:
            self.logger.error(f"Error generating schema for {content_type}: {e}")
            # Return fallback schema
            return self._get_fallback_json_schema(content_type)
    
    async def _get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for a specific table via database adapter"""
        try:
            adapter = await db_factory.get_adapter()
            
            # For SQLite, we'll use a simple approach since it doesn't have information_schema
            # For Supabase, we can use direct client access if available
            if hasattr(adapter, 'service') and hasattr(adapter.service, 'client'):
                # Supabase - use information_schema query
                query = f"""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                AND table_schema = 'public'
                ORDER BY ordinal_position;
                """
                
                response = adapter.service.client.rpc('exec_sql', {'sql': query}).execute()
                return response.data
            else:
                # SQLite or other - return basic schema info for now
                # This is a fallback since SQLite schema introspection is complex
                self.logger.warning(f"Using fallback schema for {table_name} (SQLite mode)")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting table schema for {table_name}: {e}")
            return []
    
    def _generate_json_schema(self, columns: List[Dict[str, Any]], content_type: str) -> Dict[str, Any]:
        """Generate JSON schema structure from database columns"""
        schema = {}
        
        for column in columns:
            column_name = column.get("column_name")
            data_type = column.get("data_type", "text")
            is_nullable = column.get("is_nullable", "YES")
            
            # Skip system columns
            if column_name in self.system_columns:
                continue
            
            # Map database type to JSON type
            json_type = self.type_mappings.get(data_type, "string")
            
            # Create field entry
            field_info = {
                "type": json_type,
                "description": self._generate_field_description(column_name, content_type),
                "required": is_nullable == "NO"
            }
            
            # Add special handling for certain field types
            if json_type == "object":
                field_info["description"] += " (JSON object)"
            elif column_name.endswith("_count"):
                field_info["description"] += " (numeric value as string)"
            
            schema[column_name] = field_info
        
        return schema
    
    def _generate_field_description(self, column_name: str, content_type: str) -> str:
        """Generate human-readable descriptions for database fields"""
        descriptions = {
            # Plot fields
            "title": "Compelling story title that captures the essence",
            "plot_summary": "Detailed 2-3 paragraph plot summary with full story arc",
            
            # Author fields
            "author_name": "Full name of the author",
            "pen_name": "Publishing pen name or pseudonym",
            "biography": "Author biography and background",
            "writing_style": "Description of the author's writing style and voice",
            
            # World building fields
            "world_name": "Name of the fictional world or setting",
            "world_type": "Type of world (fantasy, sci-fi, contemporary, etc.)",
            "overview": "General overview of the world and its key features",
            "geography": "Physical geography and locations within the world",
            "political_landscape": "Government systems and political structures",
            "cultural_systems": "Cultural norms, traditions, and social structures",
            "economic_framework": "Economic systems and trade relationships",
            "historical_timeline": "Key historical events and timeline",
            "power_systems": "Magic systems, technology, or supernatural elements",
            "languages_and_communication": "Languages spoken and communication methods",
            "religious_and_belief_systems": "Religions, belief systems, and mythologies",
            "unique_elements": "Unique aspects that distinguish this world",
            
            # Character fields
            "character_count": "Number of characters being created",
            "world_context_integration": "How characters fit into the world context",
            "characters": "Detailed character profiles and descriptions",
            "relationship_networks": "Character relationships and connections",
            "character_dynamics": "How characters interact and influence each other"
        }
        
        return descriptions.get(column_name, f"{column_name.replace('_', ' ').title()}")
    
    def _get_fallback_json_schema(self, content_type: str) -> Dict[str, Any]:
        """Fallback schemas when database introspection fails"""
        fallback_schemas = {
            "plot": {
                "title": {
                    "type": "string",
                    "description": "Compelling story title that captures the essence",
                    "required": True
                },
                "plot_summary": {
                    "type": "string", 
                    "description": "Detailed 2-3 paragraph plot summary with full story arc",
                    "required": True
                }
            },
            "author": {
                "author_name": {
                    "type": "string",
                    "description": "Full name of the author",
                    "required": True
                },
                "pen_name": {
                    "type": "string",
                    "description": "Publishing pen name or pseudonym",
                    "required": False
                },
                "biography": {
                    "type": "string",
                    "description": "Author biography and background",
                    "required": True
                },
                "writing_style": {
                    "type": "string",
                    "description": "Description of the author's writing style and voice",
                    "required": True
                }
            },
            "world_building": {
                "world_name": {
                    "type": "string",
                    "description": "Name of the fictional world or setting",
                    "required": True
                },
                "world_type": {
                    "type": "string",
                    "description": "Type of world (high_fantasy, urban_fantasy, science_fiction, historical_fiction, contemporary, dystopian, other)",
                    "required": True
                },
                "world_content": {
                    "type": "string",
                    "description": "Complete world building content as a single comprehensive string. Create whatever depth and scope the story requires, structured however works best for the genre and narrative.",
                    "required": True
                }
            },
            "characters": {
                "character_count": {
                    "type": "string",
                    "description": "Number of characters being created",
                    "required": True
                },
                "world_context_integration": {
                    "type": "string",
                    "description": "How characters fit into the world context",
                    "required": True
                },
                "characters": {
                    "type": "object",
                    "description": "Detailed character profiles and descriptions (JSON object)",
                    "required": True
                },
                "relationship_networks": {
                    "type": "string",
                    "description": "Character relationships and connections",
                    "required": False
                },
                "character_dynamics": {
                    "type": "string",
                    "description": "How characters interact and influence each other",
                    "required": False
                }
            },
            "critique": {
                "content_quality": {
                    "type": "string",
                    "description": "Analysis of overall content quality and coherence",
                    "required": True
                },
                "structure_assessment": {
                    "type": "string",
                    "description": "Evaluation of structure and organization",
                    "required": True
                },
                "strengths": {
                    "type": "string",
                    "description": "Key strengths and positive aspects",
                    "required": True
                },
                "weaknesses": {
                    "type": "string",
                    "description": "Areas that need improvement",
                    "required": True
                },
                "specific_recommendations": {
                    "type": "string",
                    "description": "Detailed actionable recommendations",
                    "required": True
                },
                "reader_experience": {
                    "type": "string",
                    "description": "Assessment of reader engagement and experience",
                    "required": False
                }
            },
            "enhancement": {
                "enhanced_content": {
                    "type": "object",
                    "description": "The improved content addressing critique points (JSON object)",
                    "required": True
                },
                "improvements_made": {
                    "type": "string",
                    "description": "Summary of improvements and changes made",
                    "required": True
                },
                "enhancement_rationale": {
                    "type": "string",
                    "description": "Reasoning behind the enhancement decisions",
                    "required": False
                }
            },
            "scoring": {
                "overall_score": {
                    "type": "string",
                    "description": "Overall score from 0-10",
                    "required": True
                },
                "content_quality_score": {
                    "type": "string",
                    "description": "Content quality score (0-10)",
                    "required": True
                },
                "structure_score": {
                    "type": "string",
                    "description": "Structure and organization score (0-10)",
                    "required": True
                },
                "writing_style_score": {
                    "type": "string",
                    "description": "Writing style and voice score (0-10)",
                    "required": True
                },
                "genre_appropriateness_score": {
                    "type": "string",
                    "description": "Genre appropriateness score (0-10)",
                    "required": True
                },
                "technical_execution_score": {
                    "type": "string",
                    "description": "Technical execution score (0-10)",
                    "required": True
                },
                "scoring_rationale": {
                    "type": "string",
                    "description": "Detailed justification for scores",
                    "required": True
                },
                "improvement_suggestions": {
                    "type": "string",
                    "description": "Specific suggestions for improvement",
                    "required": False
                }
            },
            "loregen": {
                "world_name": {
                    "type": "string",
                    "description": "Original world name",
                    "required": True
                },
                "world_type": {
                    "type": "string",
                    "description": "Original world type",
                    "required": True
                },
                "world_content": {
                    "type": "string",
                    "description": "Complete expanded content (original + all expansions integrated)",
                    "required": True
                },
                "expanded_areas_count": {
                    "type": "number",
                    "description": "Number of sparse areas that were expanded",
                    "required": True
                },
                "processing_time_seconds": {
                    "type": "number",
                    "description": "Time taken to process the expansion in seconds",
                    "required": True
                }
            }
        }
        
        return fallback_schemas.get(content_type, {})
    
    def generate_json_schema_instruction(self, content_type: str, schema: Dict[str, Any]) -> str:
        """Generate instruction text for agents based on JSON schema"""
        instruction = f"\nResponse Format for {content_type.replace('_', ' ').title()}:\n"
        instruction += "Always respond with JSON containing exactly these fields:\n\n"
        instruction += "{\n"
        
        for field_name, field_info in schema.items():
            field_type = field_info.get("type", "string")
            description = field_info.get("description", "")
            required = field_info.get("required", False)
            
            if field_type == "string":
                example_value = f'"{description[:30]}..."'
            elif field_type == "number":
                example_value = "0"
            elif field_type == "boolean":
                example_value = "true"
            elif field_type == "object":
                example_value = "{}"
            else:
                example_value = '""'
            
            required_text = " (REQUIRED)" if required else " (optional)"
            instruction += f'    "{field_name}": {example_value}, // {description}{required_text}\n'
        
        instruction += "}\n\n"
        instruction += "Important: Only include these exact field names. Do not add additional fields.\n"
        instruction += "All field values should be appropriate for the specified genre, tone, and target audience.\n"
        
        return instruction
    
    def get_content_type_from_agent(self, agent_name: str) -> str:
        """Map agent name to content type"""
        agent_mappings = {
            "plot_generator": "plot",
            "author_generator": "author", 
            "world_building": "world_building",
            "characters": "characters",
            "critique": "critique",
            "enhancement": "enhancement",
            "scoring": "scoring",
            "orchestrator": "orchestrator",  # Special case - doesn't need database schema
            "loregen": "loregen"  # LoreGen has its own custom schema
        }
        
        return agent_mappings.get(agent_name, "plot")
    
    async def get_schema_for_agent(self, agent_name: str) -> Dict[str, Any]:
        """Get JSON schema for a specific agent"""
        content_type = self.get_content_type_from_agent(agent_name)
        
        # Special case for orchestrator - it doesn't need database schema
        if content_type == "orchestrator":
            return {}
            
        return await self.get_agent_json_schema(content_type)


# Global schema service instance
schema_service = SchemaService()