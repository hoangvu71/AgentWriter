-- Migration 008: World Building and Characters System
-- Description: Create tables for world building and character management
-- Date: 2025-07-18

-- Create world_building table
CREATE TABLE IF NOT EXISTS world_building (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plot_id UUID REFERENCES plots(id) ON DELETE SET NULL,
    world_name TEXT NOT NULL,
    world_type TEXT NOT NULL CHECK (world_type IN ('high_fantasy', 'urban_fantasy', 'science_fiction', 'historical_fiction', 'contemporary', 'dystopian', 'other')),
    overview TEXT NOT NULL,
    geography JSONB NOT NULL DEFAULT '{}',
    political_landscape JSONB NOT NULL DEFAULT '{}',
    cultural_systems JSONB NOT NULL DEFAULT '{}',
    economic_framework JSONB NOT NULL DEFAULT '{}',
    historical_timeline JSONB NOT NULL DEFAULT '{}',
    power_systems JSONB NOT NULL DEFAULT '{}',
    languages_and_communication JSONB NOT NULL DEFAULT '{}',
    religious_and_belief_systems JSONB NOT NULL DEFAULT '{}',
    unique_elements JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create characters table
CREATE TABLE IF NOT EXISTS characters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    world_id UUID REFERENCES world_building(id) ON DELETE SET NULL,
    plot_id UUID REFERENCES plots(id) ON DELETE SET NULL,
    character_count INTEGER NOT NULL DEFAULT 0,
    world_context_integration TEXT,
    characters JSONB NOT NULL DEFAULT '[]',
    relationship_networks JSONB NOT NULL DEFAULT '{}',
    character_dynamics JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_world_building_user_id ON world_building(user_id);
CREATE INDEX IF NOT EXISTS idx_world_building_session_id ON world_building(session_id);
CREATE INDEX IF NOT EXISTS idx_world_building_plot_id ON world_building(plot_id);
CREATE INDEX IF NOT EXISTS idx_world_building_world_type ON world_building(world_type);
CREATE INDEX IF NOT EXISTS idx_world_building_created_at ON world_building(created_at);

CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id);
CREATE INDEX IF NOT EXISTS idx_characters_session_id ON characters(session_id);
CREATE INDEX IF NOT EXISTS idx_characters_world_id ON characters(world_id);
CREATE INDEX IF NOT EXISTS idx_characters_plot_id ON characters(plot_id);
CREATE INDEX IF NOT EXISTS idx_characters_created_at ON characters(created_at);

-- Create GIN indexes for JSONB fields for faster searches
CREATE INDEX IF NOT EXISTS idx_world_building_geography_gin ON world_building USING GIN(geography);
CREATE INDEX IF NOT EXISTS idx_world_building_political_landscape_gin ON world_building USING GIN(political_landscape);
CREATE INDEX IF NOT EXISTS idx_world_building_cultural_systems_gin ON world_building USING GIN(cultural_systems);
CREATE INDEX IF NOT EXISTS idx_world_building_unique_elements_gin ON world_building USING GIN(unique_elements);

CREATE INDEX IF NOT EXISTS idx_characters_characters_gin ON characters USING GIN(characters);
CREATE INDEX IF NOT EXISTS idx_characters_relationship_networks_gin ON characters USING GIN(relationship_networks);
CREATE INDEX IF NOT EXISTS idx_characters_character_dynamics_gin ON characters USING GIN(character_dynamics);

-- Add sample data for testing (will be removed in production)
-- Insert a sample world building entry
INSERT INTO world_building (
    world_name, 
    world_type, 
    overview,
    geography,
    political_landscape,
    cultural_systems,
    economic_framework,
    historical_timeline,
    power_systems,
    languages_and_communication,
    religious_and_belief_systems,
    unique_elements,
    session_id,
    user_id
) VALUES (
    'Aethermoor Realms',
    'high_fantasy',
    'A vast continent where elemental magic shapes both politics and daily life. Seven distinct kingdoms compete for control of ancient ley lines that channel raw magical energy across the land. The balance between order and chaos hangs by a thread as an ancient prophecy begins to unfold.',
    '{"continents": ["Aethermoor - the primary continent with seven kingdoms"], "major_regions": ["The Ironhold Mountains", "Whisperwind Plains", "Shadowmere Swamps", "Crystal Coast"], "climate_zones": ["Temperate forests in the north", "Arid deserts in the south", "Coastal regions with maritime climate"], "natural_resources": ["Aetherium crystals", "Ironwood trees", "Dragonscale ore", "Mana springs"]}',
    '{"major_powers": ["Kingdom of Valenhall", "Crimson Republic", "The Mage Towers Confederacy", "Shadow Court"], "conflicts": ["The Aetherium Wars", "Succession crisis in Valenhall", "Mage-Noble tensions"], "alliances": ["Northern Pact", "Crystal Coast Trading Alliance"], "power_dynamics": "Magic users hold significant influence but face political persecution in some regions"}',
    '{"major_cultures": ["Northern Clans", "Desert Nomads", "Coastal Merchants", "Mountain Dwarves"], "social_hierarchies": ["Nobility", "Mage Circles", "Merchant Guilds", "Common Folk", "Bonded"], "traditions": ["Harvest festivals", "Mage trials", "Honor duels"], "values_and_beliefs": ["Honor above all", "Magic as gift and curse", "Balance between elements"]}',
    '{"currency_systems": ["Gold Sovereigns", "Silver Marks", "Copper Bits", "Aetherium Tokens"], "trade_networks": ["The Great Trade Route", "Northern Passage", "Sea Lanes"], "key_industries": ["Aetherium mining", "Magical item crafting", "Agriculture", "Shipbuilding"], "economic_disparities": "Vast wealth gap between magic users and common folk"}',
    '{"ancient_era": "Age of First Magic - when the ley lines were discovered", "classical_period": "The Great Unification under Archmage Theron", "recent_history": "The Sundering War that split the empire", "current_era": "The Fractured Age - seven kingdoms in uneasy peace"}',
    '{"magic_or_technology": "Elemental magic channeled through ley lines and personal affinities", "rules_and_limitations": "Magic drains life force, requires focus and training, limited by elemental affinity", "accessibility": "1 in 10 people have magical aptitude, training available only to nobility or guild members", "societal_impact": "Magic determines social status, economic power, and political influence"}',
    '{"major_languages": ["Common Tongue", "High Aetheric", "Ancient Draconic"], "naming_conventions": ["Celtic-inspired names for northerners", "Arabic-inspired for desert folk"], "communication_systems": ["Raven post", "Crystal communion", "Magical sending stones"]}',
    '{"major_religions": ["The Elemental Faith", "Order of the Eternal Flame", "Shadow Mysteries"], "pantheons_or_deities": ["The Four Primarchs - elemental deities", "The Unnamed One - chaos deity"], "religious_institutions": ["Elemental Temples", "Fire Monasteries", "Shadow Cults"], "spiritual_conflicts": ["Elemental vs Shadow worship", "Magic as divine gift vs curse"]}',
    '{"distinctive_features": ["Floating islands held aloft by concentrated magic", "Ley line intersections create wild magic zones", "Dragons that bond with worthy magic users"], "mysterious_elements": ["The Void Tear - a growing crack in reality", "Ancient ruins with pre-Sundering technology"], "evolving_dynamics": ["Ley lines are weakening", "New magical abilities manifesting", "Prophecy of the Convergence approaching"]}',
    (SELECT id FROM sessions WHERE session_id = 'default_session' LIMIT 1),
    (SELECT id FROM users WHERE user_id = 'default_user' LIMIT 1)
) ON CONFLICT DO NOTHING;

-- Add comment for tracking
COMMENT ON TABLE world_building IS 'Stores complex fictional world data with detailed geography, politics, culture, and systems';
COMMENT ON TABLE characters IS 'Stores character populations that belong to specific worlds with relationship networks';

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language plpgsql;

CREATE TRIGGER update_world_building_updated_at BEFORE UPDATE ON world_building FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_characters_updated_at BEFORE UPDATE ON characters FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();