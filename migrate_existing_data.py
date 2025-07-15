#!/usr/bin/env python3
"""
Migrate existing plot data to use new normalized foreign key structure
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import json

load_dotenv()

def migrate_existing_data():
    """Migrate existing plot data to normalized structure"""
    
    password = os.getenv("SUPABASE_DB_PASSWORD")
    project_ref = "cfqgzbudjnvtyxrrvvmo"
    
    connection_strings = [
        f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres",
        f"postgresql://postgres.{project_ref}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
        f"postgresql://postgres.{project_ref}:{password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    ]
    
    print("Migrating existing plot data to normalized structure...")
    
    for i, conn_string in enumerate(connection_strings):
        try:
            print(f"\nTrying connection method {i+1}...")
            conn = psycopg2.connect(conn_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            
            print("[OK] Connected to database!")
            
            # First, check if we have any plots with old data
            cur.execute("""
                SELECT id, genre, subgenre, microgenre, trope, tone, target_audience
                FROM plots 
                WHERE genre_id IS NULL AND genre IS NOT NULL
            """)
            
            plots_to_migrate = cur.fetchall()
            print(f"Found {len(plots_to_migrate)} plots to migrate")
            
            if len(plots_to_migrate) == 0:
                print("[INFO] No data to migrate or already migrated")
                return True
            
            migrated_count = 0
            
            for plot_row in plots_to_migrate:
                plot_id, genre, subgenre, microgenre, trope, tone, target_audience_json = plot_row
                
                print(f"\nMigrating plot {plot_id}...")
                print(f"  Genre: {genre}")
                print(f"  Subgenre: {subgenre}")
                print(f"  Microgenre: {microgenre}")
                print(f"  Trope: {trope}")
                print(f"  Tone: {tone}")
                
                # Migrate genre
                genre_id = None
                if genre:
                    # Find or create genre
                    cur.execute("SELECT id FROM genres WHERE name = %s", (genre,))
                    result = cur.fetchone()
                    if result:
                        genre_id = result[0]
                    else:
                        # Create new genre
                        cur.execute("""
                            INSERT INTO genres (name, description) 
                            VALUES (%s, %s) 
                            RETURNING id
                        """, (genre, f"Auto-migrated genre: {genre}"))
                        genre_id = cur.fetchone()[0]
                        print(f"    Created new genre: {genre}")
                
                # Migrate subgenre
                subgenre_id = None
                if subgenre and genre_id:
                    # Find or create subgenre
                    cur.execute("SELECT id FROM subgenres WHERE name = %s AND genre_id = %s", (subgenre, genre_id))
                    result = cur.fetchone()
                    if result:
                        subgenre_id = result[0]
                    else:
                        # Create new subgenre
                        cur.execute("""
                            INSERT INTO subgenres (genre_id, name, description) 
                            VALUES (%s, %s, %s) 
                            RETURNING id
                        """, (genre_id, subgenre, f"Auto-migrated subgenre: {subgenre}"))
                        subgenre_id = cur.fetchone()[0]
                        print(f"    Created new subgenre: {subgenre}")
                
                # Migrate microgenre
                microgenre_id = None
                if microgenre and subgenre_id:
                    # Find or create microgenre
                    cur.execute("SELECT id FROM microgenres WHERE name = %s AND subgenre_id = %s", (microgenre, subgenre_id))
                    result = cur.fetchone()
                    if result:
                        microgenre_id = result[0]
                    else:
                        # Create new microgenre
                        cur.execute("""
                            INSERT INTO microgenres (subgenre_id, name, description) 
                            VALUES (%s, %s, %s) 
                            RETURNING id
                        """, (subgenre_id, microgenre, f"Auto-migrated microgenre: {microgenre}"))
                        microgenre_id = cur.fetchone()[0]
                        print(f"    Created new microgenre: {microgenre}")
                
                # Migrate trope
                trope_id = None
                if trope:
                    # Find or create trope
                    cur.execute("SELECT id FROM tropes WHERE name = %s", (trope,))
                    result = cur.fetchone()
                    if result:
                        trope_id = result[0]
                    else:
                        # Create new trope
                        cur.execute("""
                            INSERT INTO tropes (name, description, category) 
                            VALUES (%s, %s, %s) 
                            RETURNING id
                        """, (trope, f"Auto-migrated trope: {trope}", "Plot"))
                        trope_id = cur.fetchone()[0]
                        print(f"    Created new trope: {trope}")
                
                # Migrate tone
                tone_id = None
                if tone:
                    # Find or create tone
                    cur.execute("SELECT id FROM tones WHERE name = %s", (tone,))
                    result = cur.fetchone()
                    if result:
                        tone_id = result[0]
                    else:
                        # Create new tone
                        cur.execute("""
                            INSERT INTO tones (name, description) 
                            VALUES (%s, %s) 
                            RETURNING id
                        """, (tone, f"Auto-migrated tone: {tone}"))
                        tone_id = cur.fetchone()[0]
                        print(f"    Created new tone: {tone}")
                
                # Migrate target audience
                target_audience_id = None
                if target_audience_json:
                    try:
                        if isinstance(target_audience_json, str):
                            target_audience = json.loads(target_audience_json)
                        else:
                            target_audience = target_audience_json
                        
                        age_group = target_audience.get('age_group', 'Adult')
                        gender = target_audience.get('gender', 'All')
                        orientation = target_audience.get('sexual_orientation', 'All')
                        interests = target_audience.get('interests', [])
                        
                        # Find or create target audience
                        cur.execute("""
                            SELECT id FROM target_audiences 
                            WHERE age_group = %s AND gender = %s AND sexual_orientation = %s
                        """, (age_group, gender, orientation))
                        result = cur.fetchone()
                        
                        if result:
                            target_audience_id = result[0]
                        else:
                            # Create new target audience
                            cur.execute("""
                                INSERT INTO target_audiences (age_group, gender, sexual_orientation, interests, description) 
                                VALUES (%s, %s, %s, %s, %s) 
                                RETURNING id
                            """, (age_group, gender, orientation, interests, f"Auto-migrated: {age_group}, {gender}, {orientation}"))
                            target_audience_id = cur.fetchone()[0]
                            print(f"    Created new target audience: {age_group}, {gender}, {orientation}")
                            
                    except Exception as e:
                        print(f"    Error parsing target_audience: {e}")
                
                # Update the plot with new foreign keys
                cur.execute("""
                    UPDATE plots 
                    SET genre_id = %s, subgenre_id = %s, microgenre_id = %s, 
                        trope_id = %s, tone_id = %s, target_audience_id = %s
                    WHERE id = %s
                """, (genre_id, subgenre_id, microgenre_id, trope_id, tone_id, target_audience_id, plot_id))
                
                migrated_count += 1
                print(f"    [OK] Migrated plot {plot_id}")
            
            cur.close()
            conn.close()
            
            print("\n" + "="*60)
            print("DATA MIGRATION COMPLETE!")
            print("="*60)
            print(f"Successfully migrated {migrated_count} plots")
            print("Old VARCHAR/JSONB data preserved alongside new foreign keys")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"[FAIL] Connection method {i+1} failed: {str(e)[:100]}")
            continue
    
    print("\nAll connection methods failed.")
    return False

if __name__ == "__main__":
    success = migrate_existing_data()
    
    if success:
        print("\n[SUCCESS] Data migration completed!")
    else:
        print("\n[FAIL] Data migration failed.")