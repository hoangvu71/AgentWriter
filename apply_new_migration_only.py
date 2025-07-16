#!/usr/bin/env python3
"""
Apply only the new migration using Supabase client
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def apply_new_migration():
    """Apply the new migration using Supabase client"""
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    print("Applying new schema migration...")
    
    try:
        # Connect to Supabase
        supabase = create_client(url, key)
        
        # Read the migration SQL
        with open('migrations/003_normalize_target_audience_and_genre_tables.sql', 'r') as f:
            migration_sql = f.read()
        
        # Split into individual statements
        statements = []
        current_statement = []
        
        for line in migration_sql.split('\n'):
            if line.strip().startswith('--'):
                continue
            current_statement.append(line)
            if line.strip().endswith(';'):
                statement = '\n'.join(current_statement).strip()
                if statement and not statement.startswith('--'):
                    statements.append(statement)
                current_statement = []
        
        print(f"Found {len(statements)} SQL statements to execute...")
        
        # Check if tables already exist
        try:
            result = supabase.table('genres').select("*").limit(1).execute()
            print("[INFO] New tables already exist. Migration may have been applied already.")
            return True
        except:
            print("[INFO] New tables don't exist yet. Proceeding with migration...")
        
        print("\n" + "="*60)
        print("MANUAL MIGRATION REQUIRED")
        print("="*60)
        print("\nDue to Supabase API limitations, please apply the migration manually:")
        print("\n1. Go to: https://app.supabase.com/project/cfqgzbudjnvtyxrrvvmo/sql/new")
        print("2. Copy the contents of migrations/003_normalize_target_audience_and_genre_tables.sql")
        print("3. Paste into SQL Editor and click 'Run'")
        print("\nThe migration will:")
        print("- Create 6 new normalized tables")
        print("- Add foreign key columns to plots table") 
        print("- Add indexes for performance")
        print("- Insert sample data")
        print("="*60)
        
        return False
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

if __name__ == "__main__":
    apply_new_migration()