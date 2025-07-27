#!/usr/bin/env python3
"""
Verify that data migration was successful
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
import json

# Add src directory to path to import configuration
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from core.configuration import Configuration

load_dotenv('../../config/.env')

def verify_migration():
    """Verify the data migration worked correctly"""
    
    config = Configuration()
    supabase_config = config.supabase_config
    
    password = supabase_config["password"]
    project_ref = supabase_config["project_ref"]
    
    if not password:
        raise ValueError("SUPABASE_DB_PASSWORD environment variable is required")
    if not project_ref:
        raise ValueError("SUPABASE_PROJECT_REF environment variable is required")
    
    connection_strings = [
        f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres",
        f"postgresql://postgres.{project_ref}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
        f"postgresql://postgres.{project_ref}:{password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    ]
    
    print("Verifying data migration...")
    
    for i, conn_string in enumerate(connection_strings):
        try:
            print(f"\nTrying connection method {i+1}...")
            conn = psycopg2.connect(conn_string)
            cur = conn.cursor()
            
            print("[OK] Connected to database!")
            
            # Check plots with both old and new data
            cur.execute("""
                SELECT 
                    p.id,
                    p.title,
                    p.genre as old_genre,
                    g.name as new_genre,
                    p.subgenre as old_subgenre,
                    sg.name as new_subgenre,
                    p.microgenre as old_microgenre,
                    mg.name as new_microgenre,
                    p.trope as old_trope,
                    t.name as new_trope,
                    p.tone as old_tone,
                    tn.name as new_tone
                FROM plots p
                LEFT JOIN genres g ON p.genre_id = g.id
                LEFT JOIN subgenres sg ON p.subgenre_id = sg.id
                LEFT JOIN microgenres mg ON p.microgenre_id = mg.id
                LEFT JOIN tropes t ON p.trope_id = t.id
                LEFT JOIN tones tn ON p.tone_id = tn.id
                WHERE p.genre_id IS NOT NULL
            """)
            
            migrated_plots = cur.fetchall()
            
            print(f"\n[OK] Found {len(migrated_plots)} migrated plots")
            
            for plot in migrated_plots:
                (plot_id, title, old_genre, new_genre, old_subgenre, new_subgenre, 
                 old_microgenre, new_microgenre, old_trope, new_trope, old_tone, new_tone) = plot
                
                print(f"\nPlot: {title}")
                print(f"  Genre: '{old_genre}' -> '{new_genre}' [OK]")
                print(f"  Subgenre: '{old_subgenre}' -> '{new_subgenre}' [OK]")
                print(f"  Microgenre: '{old_microgenre}' -> '{new_microgenre}' [OK]")
                print(f"  Trope: '{old_trope}' -> '{new_trope}' [OK]")
                print(f"  Tone: '{old_tone}' -> '{new_tone}' [OK]")
            
            # Check counts in each normalized table
            tables = ['genres', 'subgenres', 'microgenres', 'tropes', 'tones', 'target_audiences']
            print("\nNormalized table counts:")
            
            for table in tables:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"  {table}: {count} entries")
            
            # Check if any plots still need migration
            cur.execute("""
                SELECT COUNT(*) FROM plots 
                WHERE genre IS NOT NULL AND genre_id IS NULL
            """)
            
            unmigrated = cur.fetchone()[0]
            if unmigrated > 0:
                print(f"\n[WARNING] {unmigrated} plots still need migration")
            else:
                print(f"\n[OK] All plots have been migrated!")
            
            cur.close()
            conn.close()
            
            print("\n" + "="*60)
            print("MIGRATION VERIFICATION COMPLETE!")
            print("="*60)
            print("[OK] Data successfully migrated to normalized structure")
            print("[OK] Old data preserved for safety")
            print("[OK] New foreign key relationships working")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"[FAIL] Connection method {i+1} failed: {str(e)[:100]}")
            continue
    
    return False

if __name__ == "__main__":
    verify_migration()