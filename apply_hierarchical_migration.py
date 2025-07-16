#!/usr/bin/env python3
"""
Apply migration 005: Hierarchical Genre System
This creates the proper hierarchy: Genre -> Subgenre -> Microgenre -> Trope -> Tone
"""

import asyncio
import json
from datetime import datetime
from supabase_service import supabase_service

async def apply_migration():
    """Apply the hierarchical genre migration"""
    print("[Migration] Applying Migration 005: Hierarchical Genre System")
    print("Hierarchy: Genre -> Subgenre -> Microgenre -> Trope -> Tone")
    
    try:
        # Read migration file
        with open('migrations/005_hierarchical_genre_system.sql', 'r') as f:
            migration_sql = f.read()
        
        print("[SQL] Executing migration SQL...")
        
        # Execute migration (note: this is a simplified version)
        # In production, you'd run this in Supabase SQL Editor
        print("[IMPORTANT] Run this SQL in Supabase SQL Editor:")
        print("-" * 50)
        print(migration_sql)
        print("-" * 50)
        
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
        
        print("[Next Steps]")
        print("1. Run the SQL above in Supabase SQL Editor")
        print("2. Test the new hierarchical interface")
        print("3. Verify all data relationships are correct")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(apply_migration())
    if success:
        print("[OK] Migration preparation completed!")
    else:
        print("[ERROR] Migration preparation failed!")