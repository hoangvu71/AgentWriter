#!/usr/bin/env python3
"""Verify tables exist and apply migration if needed"""

import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import Supabase service
from src.database.supabase_service import SupabaseService

def check_and_apply_migration():
    print("Checking World Building and Characters tables...")
    print("=" * 50)
    
    try:
        # Initialize Supabase service
        service = SupabaseService()
        print("[OK] Connected to Supabase")
        
        # Check if tables exist
        tables_status = {
            'world_building': False,
            'characters': False
        }
        
        # Test world_building table
        try:
            result = service.client.table('world_building').select("id").limit(1).execute()
            tables_status['world_building'] = True
            print("[OK] world_building table exists")
        except Exception as e:
            print("[X] world_building table does not exist")
            error_msg = str(e)
            if "relation" in error_msg and "does not exist" in error_msg:
                print("    Table not found in database")
        
        # Test characters table
        try:
            result = service.client.table('characters').select("id").limit(1).execute()
            tables_status['characters'] = True
            print("[OK] characters table exists")
        except Exception as e:
            print("[X] characters table does not exist")
            error_msg = str(e)
            if "relation" in error_msg and "does not exist" in error_msg:
                print("    Table not found in database")
        
        # If both tables exist, update migration tracking
        if tables_status['world_building'] and tables_status['characters']:
            print("\n[OK] Both tables exist! Updating migration tracking...")
            
            # Update applied_migrations.json
            migration_file = "migrations/applied_migrations.json"
            with open(migration_file, 'r') as f:
                applied_data = json.load(f)
            
            if "008_world_building_and_characters_system.sql" not in applied_data["applied"]:
                applied_data["applied"].append("008_world_building_and_characters_system.sql")
                applied_data["last_updated"] = datetime.now().isoformat()
                
                with open(migration_file, 'w') as f:
                    json.dump(applied_data, f, indent=2)
                
                print("[OK] Updated applied_migrations.json")
            else:
                print("[OK] Migration already marked as applied")
            
            print("\n[READY] World Building and Characters functionality is available!")
            return True
        else:
            print("\n[ERROR] Tables are missing. Migration needs to be applied.")
            print("\nThe migration SQL is in: migrations/008_world_building_and_characters_system.sql")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return False

if __name__ == "__main__":
    success = check_and_apply_migration()
    sys.exit(0 if success else 1)