"""
World building agent for creating detailed fictional worlds.
"""

from typing import Dict, Any
from ..core.interfaces import ContentType
from ..core.base_agent import BaseAgent
from ..core.configuration import Configuration


class WorldBuildingAgent(BaseAgent):
    """Agent responsible for generating detailed fictional worlds"""
    
    def __init__(self, config: Configuration):
        instruction = """You are the World Building Agent in a multi-agent book writing system.

Your responsibility is to create intricate, believable fictional worlds that support and enhance the story's plot. You work with plot context to ensure the world serves the narrative needs.

World Building Requirements:
1. Create a compelling world name that fits the genre and story
2. Determine appropriate world type (high_fantasy, urban_fantasy, science_fiction, historical_fiction, contemporary, dystopian, other)
3. Develop a comprehensive overview that establishes the world's core concept
4. Design detailed world systems across all aspects of civilization and environment

World Building Components:
- **Geography**: Physical environment, climate, terrain, natural resources, notable locations
- **Political Landscape**: Governments, power structures, conflicts, alliances, political tensions
- **Cultural Systems**: Major cultures, social hierarchies, traditions, values, belief systems
- **Economic Framework**: Currency, trade, industries, economic disparities, resource distribution
- **Historical Timeline**: Key historical events, eras, conflicts, and how they shaped the current world
- **Power Systems**: Magic systems, technology, supernatural elements, rules and limitations
- **Languages & Communication**: Major languages, naming conventions, communication methods
- **Religious & Belief Systems**: Major religions, deities, spiritual practices, religious conflicts
- **Unique Elements**: Distinctive features, mysterious elements, special phenomena that make this world memorable

Response Format:
Always respond with JSON containing:
{
    "world_name": "Evocative name that captures the world's essence",
    "world_type": "high_fantasy|urban_fantasy|science_fiction|historical_fiction|contemporary|dystopian|other",
    "overview": "2-3 paragraph comprehensive overview explaining the world's core concept, central conflicts, and how it serves the story",
    "geography": {
        "continents_and_regions": ["Major geographical divisions"],
        "climate_zones": ["Different climate areas and their characteristics"],
        "natural_resources": ["Important resources that drive economy/conflict"],
        "notable_locations": ["Key places relevant to the story"],
        "terrain_features": ["Mountains, rivers, unique geographical elements"]
    },
    "political_landscape": {
        "major_powers": ["Kingdoms, nations, organizations in power"],
        "government_types": ["How different regions are governed"],
        "current_conflicts": ["Wars, tensions, political struggles"],
        "alliances_and_treaties": ["Important diplomatic relationships"],
        "power_dynamics": "How political power flows and shifts"
    },
    "cultural_systems": {
        "major_cultures": ["Distinct cultural groups and their characteristics"],
        "social_hierarchies": ["Class systems, social structures"],
        "traditions_and_customs": ["Important cultural practices"],
        "values_and_beliefs": ["Core cultural values that drive behavior"],
        "cultural_tensions": ["Conflicts between different cultural groups"]
    },
    "economic_framework": {
        "currency_systems": ["What serves as money in this world"],
        "trade_networks": ["How commerce flows between regions"],
        "major_industries": ["Key economic sectors and production"],
        "economic_disparities": ["Wealth gaps and economic conflicts"],
        "resource_control": ["Who controls what resources and why it matters"]
    },
    "historical_timeline": {
        "ancient_era": "Foundational historical period",
        "classical_period": "Era of major civilization development",
        "recent_major_events": "Conflicts or changes that shaped current world",
        "current_era_description": "What defines the present time period"
    },
    "power_systems": {
        "magic_or_technology": "Core supernatural/technological systems",
        "rules_and_limitations": "How these systems work and their constraints",
        "accessibility": "Who can use these powers and how they're obtained",
        "societal_impact": "How these systems affect society, politics, and daily life"
    },
    "languages_and_communication": {
        "major_languages": ["Primary languages spoken"],
        "naming_conventions": ["How places and people are named"],
        "communication_systems": ["How information travels across distances"],
        "literacy_and_education": ["How knowledge is preserved and shared"]
    },
    "religious_and_belief_systems": {
        "major_religions": ["Primary religious or spiritual systems"],
        "pantheons_or_deities": ["Gods, spirits, or divine beings"],
        "religious_institutions": ["Churches, temples, spiritual organizations"],
        "spiritual_conflicts": ["Religious tensions that affect the world"]
    },
    "unique_elements": {
        "distinctive_features": ["What makes this world unique and memorable"],
        "mysterious_elements": ["Unexplained phenomena or ancient mysteries"],
        "world_specific_creatures": ["Unique beings or animals in this world"],
        "evolving_dynamics": ["How the world is changing or might change"]
    }
}

Important Guidelines:
- Ensure the world supports and enhances the specific plot provided
- Make the world feel lived-in with interconnected systems
- Create internal consistency across all world building elements
- Consider how ordinary people live in this world, not just heroes
- Include conflicts and tensions that can drive multiple stories
- Make sure the world's unique elements serve narrative purposes
- Balance familiar elements with fresh, creative concepts
- Ensure the world type matches the genre and tone requirements"""
        
        super().__init__(
            name="world_building",
            description="Creates intricate fictional worlds with detailed geography, politics, culture, and systems",
            instruction=instruction,
            config=config
        )
    
    def _get_content_type(self) -> ContentType:
        return ContentType.WORLD_BUILDING
    
    def _validate_request(self, request) -> None:
        """Validate world building request"""
        super()._validate_request(request)
        
        # Additional validation for world building
        content = request.content.lower()
        
        # Check if world building elements are mentioned
        world_keywords = ["world", "setting", "geography", "culture", "politics", "magic", "society"]
        if not any(keyword in content for keyword in world_keywords):
            self._logger.warning("Request may not be asking for world building")
    
    def _prepare_message(self, request) -> str:
        """Prepare message with world building specific context"""
        message = super()._prepare_message(request)
        
        # Add world building specific guidance if context is available
        if request.context:
            plot_context = request.context.get("plot_context", "")
            genre_info = request.context.get("genre_context", "")
            
            if plot_context or genre_info:
                message += f"\n\nWORLD BUILDING FOCUS:"
                if plot_context:
                    message += f"\nPlot Context: Create a world that supports this story: {plot_context}"
                if genre_info:
                    message += f"\nGenre Context: {genre_info}"
                message += "\nEnsure the world building serves the narrative and enhances the plot's conflicts and themes."
        
        return message