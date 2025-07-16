#!/usr/bin/env python3
"""
Apply Migration 005: Hierarchical Genre System directly to database
This creates the proper hierarchy: Genre -> Subgenre -> Microgenre -> Trope -> Tone
"""

import json
from datetime import datetime
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

def apply_hierarchical_migration():
    """Apply the hierarchical genre migration directly to database"""
    print("Applying Migration 005: Hierarchical Genre System")
    print("Hierarchy: Genre -> Subgenre -> Microgenre -> Trope -> Tone")
    
    password = os.getenv("SUPABASE_DB_PASSWORD")
    project_ref = "cfqgzbudjnvtyxrrvvmo"
    
    # Try multiple connection formats
    connection_strings = [
        f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres",
        f"postgresql://postgres.{project_ref}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
        f"postgresql://postgres.{project_ref}:{password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    ]
    
    for i, conn_string in enumerate(connection_strings):
        try:
            print(f"\nTrying connection method {i+1}...")
            conn = psycopg2.connect(conn_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            print("[OK] Connected to database!")
            break
        except Exception as e:
            print(f"[FAIL] Connection method {i+1} failed: {e}")
            if i == len(connection_strings) - 1:
                raise Exception("All connection methods failed")
            continue
    
    try:
        
        print("\nExecuting hierarchical migration...")
        
        # Read migration file
        with open('migrations/005_hierarchical_genre_system.sql', 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        cursor.execute(migration_sql)
        conn.commit()
        print("[OK] Migration executed successfully!")
        
        # Verify the changes
        print("\nVerifying hierarchical relationships:")
        
        # Check if tropes now have microgenre_id
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'tropes' AND column_name = 'microgenre_id';")
        if cursor.fetchone():
            print("[OK] Tropes table has microgenre_id column")
        else:
            print("[WARNING] Tropes table missing microgenre_id column")
        
        # Check if tones now have trope_id
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'tones' AND column_name = 'trope_id';")
        if cursor.fetchone():
            print("[OK] Tones table has trope_id column")
        else:
            print("[WARNING] Tones table missing trope_id column")
        
        # Check foreign key constraints
        cursor.execute("""
            SELECT tc.constraint_name, tc.table_name, kcu.column_name 
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu 
                ON tc.constraint_name = kcu.constraint_name 
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name IN ('subgenres', 'microgenres', 'tropes', 'tones')
            ORDER BY tc.table_name, kcu.column_name;
        """)
        constraints = cursor.fetchall()
        
        print(f"[OK] Found {len(constraints)} foreign key constraints:")
        for constraint in constraints:
            print(f"  - {constraint[1]}.{constraint[2]} -> {constraint[0]}")
        
        cursor.close()
        conn.close()
        
        # Update applied migrations file
        applied_file = 'migrations/applied_migrations.json'
        try:
            with open(applied_file, 'r') as f:
                applied_data = json.load(f)
        except FileNotFoundError:
            applied_data = {"applied": [], "last_updated": ""}
        
        if "005_hierarchical_genre_system.sql" not in applied_data["applied"]:
            applied_data["applied"].append("005_hierarchical_genre_system.sql")
            applied_data["last_updated"] = datetime.now().isoformat()
            
            with open(applied_file, 'w') as f:
                json.dump(applied_data, f, indent=2)
            
            print("[OK] Migration 005 marked as applied")
        
        print("\n" + "="*60)
        print("HIERARCHICAL MIGRATION COMPLETE!")
        print("="*60)
        print("\nHierarchy established:")
        print("- Genres -> Subgenres")
        print("- Subgenres -> Microgenres")
        print("- Microgenres -> Tropes")
        print("- Tropes -> Tones")
        print("\nYou can now click on microgenres to see their tropes!")
        print("And click on tropes to see their tones!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = apply_hierarchical_migration()
    if success:
        print("[SUCCESS] Hierarchical migration completed!")
    else:
        print("[ERROR] Hierarchical migration failed!")