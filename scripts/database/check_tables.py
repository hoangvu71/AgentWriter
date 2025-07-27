#!/usr/bin/env python3
"""Check if world_building and characters tables exist in Supabase"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")

if not url or not key:
    print("Error: Missing Supabase credentials in .env file")
    exit(1)

supabase: Client = create_client(url, key)

# Check if tables exist
tables_to_check = ['world_building', 'characters']

print("Checking database tables...")
for table in tables_to_check:
    try:
        # Try to query the table
        response = supabase.table(table).select("id").limit(1).execute()
        print(f"✓ Table '{table}' exists")
        
        # Get count
        count_response = supabase.table(table).select("id", count="exact").execute()
        print(f"  - Has {count_response.count} records")
        
    except Exception as e:
        print(f"✗ Table '{table}' does not exist or error: {str(e)}")

# Also check migration tracking
try:
    migrations = supabase.table("schema_migrations").select("*").execute()
    print("\nApplied migrations:")
    for m in migrations.data:
        print(f"  - {m['migration_name']} (applied at {m['applied_at']})")
except Exception as e:
    print(f"\nNo migration tracking table found: {e}")