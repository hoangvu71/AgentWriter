#!/usr/bin/env python3
"""
Add normalized tables using the exact same method that worked for initial schema
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

def add_normalized_tables():
    """Add normalized tables using the working connection method"""
    
    password = os.getenv("SUPABASE_DB_PASSWORD")
    project_ref = "cfqgzbudjnvtyxrrvvmo"
    
    # Use the EXACT same connection that worked in create_schema_with_password.py
    connection_strings = [
        f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres",
        f"postgresql://postgres.{project_ref}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
        f"postgresql://postgres.{project_ref}:{password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    ]
    
    print("Adding normalized tables to database...")
    
    for i, conn_string in enumerate(connection_strings):
        try:
            print(f"\nTrying connection method {i+1}...")
            conn = psycopg2.connect(conn_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            
            print("[OK] Connected to database!")
            
            # Read the new schema from the migration file
            schema_sql = """
            -- Create normalized target audience table
            CREATE TABLE IF NOT EXISTS target_audiences (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                age_group VARCHAR(50) NOT NULL,
                gender VARCHAR(50),
                sexual_orientation VARCHAR(50),
                interests TEXT[],
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );

            -- Create genres table (main categories)
            CREATE TABLE IF NOT EXISTS genres (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );

            -- Create subgenres table (linked to main genres)
            CREATE TABLE IF NOT EXISTS subgenres (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                genre_id UUID REFERENCES genres(id) ON DELETE CASCADE,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(genre_id, name)
            );

            -- Create microgenres table (specific niches)
            CREATE TABLE IF NOT EXISTS microgenres (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                subgenre_id UUID REFERENCES subgenres(id) ON DELETE CASCADE,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(subgenre_id, name)
            );

            -- Create tropes table (story patterns/themes)
            CREATE TABLE IF NOT EXISTS tropes (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                category VARCHAR(100),
                created_at TIMESTAMP DEFAULT NOW()
            );

            -- Create tones table (story mood/atmosphere)
            CREATE TABLE IF NOT EXISTS tones (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );

            -- Add new foreign key columns to plots table
            ALTER TABLE plots ADD COLUMN IF NOT EXISTS target_audience_id UUID REFERENCES target_audiences(id);
            ALTER TABLE plots ADD COLUMN IF NOT EXISTS genre_id UUID REFERENCES genres(id);
            ALTER TABLE plots ADD COLUMN IF NOT EXISTS subgenre_id UUID REFERENCES subgenres(id);
            ALTER TABLE plots ADD COLUMN IF NOT EXISTS microgenre_id UUID REFERENCES microgenres(id);
            ALTER TABLE plots ADD COLUMN IF NOT EXISTS trope_id UUID REFERENCES tropes(id);
            ALTER TABLE plots ADD COLUMN IF NOT EXISTS tone_id UUID REFERENCES tones(id);

            -- Insert sample data
            INSERT INTO genres (name, description) VALUES 
                ('Fantasy', 'Stories with magical or supernatural elements'),
                ('Science Fiction', 'Stories based on future scientific and technological advances'),
                ('Romance', 'Stories focused on relationships and romantic love'),
                ('Mystery', 'Stories involving puzzles, crimes, or unexplained events')
            ON CONFLICT (name) DO NOTHING;

            INSERT INTO target_audiences (age_group, gender, sexual_orientation, interests, description) VALUES 
                ('Young Adult', 'All', 'All', ARRAY['Adventure', 'Coming of Age'], 'Teens and young adults seeking adventure and growth stories'),
                ('Adult', 'Male', 'Heterosexual', ARRAY['Action', 'Adventure'], 'Adult men interested in action and adventure')
            ON CONFLICT DO NOTHING;

            INSERT INTO tropes (name, description, category) VALUES 
                ('Chosen One', 'A character destined to save the world or fulfill a prophecy', 'Character'),
                ('Survive and Family', 'Characters fighting to survive while protecting family', 'Plot')
            ON CONFLICT (name) DO NOTHING;

            INSERT INTO tones (name, description) VALUES 
                ('Dark', 'Serious, gritty, or pessimistic atmosphere'),
                ('Humorous', 'Light-hearted, funny, comedic elements')
            ON CONFLICT (name) DO NOTHING;
            """
            
            print("Executing normalized schema...")
            cur.execute(schema_sql)
            
            print("[OK] Schema executed successfully!")
            
            # Verify new tables
            new_tables = ['target_audiences', 'genres', 'subgenres', 'microgenres', 'tropes', 'tones']
            print("\nVerifying new tables:")
            
            for table in new_tables:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"[OK] Table '{table}' exists (rows: {count})")
            
            cur.close()
            conn.close()
            
            print("\n" + "="*60)
            print("NORMALIZED SCHEMA SUCCESSFULLY ADDED!")
            print("="*60)
            print("\nYour database now has:")
            print("- 6 new normalized tables for metadata")
            print("- Foreign key columns in plots table")
            print("- Sample data to get started")
            print("- Better data integrity and query capabilities")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"[FAIL] Connection method {i+1} failed: {str(e)[:100]}")
            continue
    
    print("\nAll connection methods failed.")
    return False

if __name__ == "__main__":
    success = add_normalized_tables()
    
    if success:
        print("\n[SUCCESS] Normalized schema added successfully!")
    else:
        print("\n[FAIL] Could not add normalized schema.")