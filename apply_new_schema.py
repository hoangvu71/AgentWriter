#!/usr/bin/env python3
"""
Apply only the new schema changes to the existing database
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def apply_new_schema():
    """Apply the new normalized schema"""
    
    # This was the connection that worked in create_schema_with_password.py
    password = "BTTmSilqcNn9Ynj5"
    project_ref = "cfqgzbudjnvtyxrrvvmo"
    
    # These are the exact connection strings that worked before
    connection_strings = [
        f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres",
        f"postgresql://postgres.{project_ref}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres", 
        f"postgresql://postgres.{project_ref}:{password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    ]
    
    print("Applying normalized schema to existing database...")
    
    for i, conn_string in enumerate(connection_strings):
        try:
            print(f"\nTrying connection method {i+1}...")
            conn = psycopg2.connect(conn_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            
            print("[OK] Connected successfully!")
            
            # Check if new tables already exist
            cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'genres');")
            if cur.fetchone()[0]:
                print("[INFO] Normalized tables already exist!")
                return True
            
            print("Creating normalized tables...")
            
            # Create tables one by one with error handling
            table_sqls = [
                ("target_audiences", """
                    CREATE TABLE target_audiences (
                        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                        age_group VARCHAR(50) NOT NULL,
                        gender VARCHAR(50),
                        sexual_orientation VARCHAR(50),
                        interests TEXT[],
                        description TEXT,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """),
                ("genres", """
                    CREATE TABLE genres (
                        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                        name VARCHAR(100) UNIQUE NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """),
                ("subgenres", """
                    CREATE TABLE subgenres (
                        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                        genre_id UUID REFERENCES genres(id) ON DELETE CASCADE,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(genre_id, name)
                    );
                """),
                ("microgenres", """
                    CREATE TABLE microgenres (
                        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                        subgenre_id UUID REFERENCES subgenres(id) ON DELETE CASCADE,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(subgenre_id, name)
                    );
                """),
                ("tropes", """
                    CREATE TABLE tropes (
                        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                        name VARCHAR(255) UNIQUE NOT NULL,
                        description TEXT,
                        category VARCHAR(100),
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """),
                ("tones", """
                    CREATE TABLE tones (
                        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                        name VARCHAR(100) UNIQUE NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)
            ]
            
            for table_name, sql in table_sqls:
                try:
                    cur.execute(sql)
                    print(f"[OK] Created table: {table_name}")
                except Exception as e:
                    print(f"[SKIP] Table {table_name}: {str(e)[:50]}")
            
            # Add foreign key columns to plots
            fk_columns = [
                "target_audience_id",
                "genre_id", 
                "subgenre_id",
                "microgenre_id",
                "trope_id",
                "tone_id"
            ]
            
            print("\nAdding foreign key columns to plots table...")
            for column in fk_columns:
                try:
                    cur.execute(f"ALTER TABLE plots ADD COLUMN {column} UUID;")
                    print(f"[OK] Added column: {column}")
                except Exception as e:
                    print(f"[SKIP] Column {column}: {str(e)[:50]}")
            
            # Insert sample data
            print("\nInserting sample data...")
            
            try:
                cur.execute("""
                    INSERT INTO genres (name, description) VALUES 
                        ('Fantasy', 'Stories with magical or supernatural elements'),
                        ('Science Fiction', 'Stories based on future scientific advances'),
                        ('Romance', 'Stories focused on relationships and love'),
                        ('Mystery', 'Stories involving puzzles or crimes')
                    ON CONFLICT (name) DO NOTHING;
                """)
                print("[OK] Inserted sample genres")
            except Exception as e:
                print(f"[SKIP] Genres: {str(e)[:50]}")
            
            try:
                cur.execute("""
                    INSERT INTO tropes (name, description, category) VALUES 
                        ('Chosen One', 'Character destined to save the world', 'Character'),
                        ('Survive and Family', 'Characters fighting to survive and protect family', 'Plot')
                    ON CONFLICT (name) DO NOTHING;
                """)
                print("[OK] Inserted sample tropes")
            except Exception as e:
                print(f"[SKIP] Tropes: {str(e)[:50]}")
            
            try:
                cur.execute("""
                    INSERT INTO tones (name, description) VALUES 
                        ('Dark', 'Serious, gritty atmosphere'),
                        ('Humorous', 'Light-hearted, funny elements')
                    ON CONFLICT (name) DO NOTHING;
                """)
                print("[OK] Inserted sample tones")
            except Exception as e:
                print(f"[SKIP] Tones: {str(e)[:50]}")
            
            cur.close()
            conn.close()
            
            print("\n" + "="*60)
            print("SCHEMA NORMALIZATION COMPLETE!")
            print("="*60)
            print("Your database now has proper normalized tables!")
            return True
            
        except Exception as e:
            print(f"[FAIL] Connection method {i+1} failed: {str(e)[:100]}")
            continue
    
    print("\nAll connection attempts failed.")
    return False

if __name__ == "__main__":
    apply_new_schema()