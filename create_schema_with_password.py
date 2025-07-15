#!/usr/bin/env python3
"""
Create schema using the database password
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

def create_schema_now():
    """Create the schema using direct PostgreSQL connection"""
    
    password = os.getenv("SUPABASE_DB_PASSWORD")
    project_ref = "cfqgzbudjnvtyxrrvvmo"
    
    # Try different connection formats
    connection_strings = [
        f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres",
        f"postgresql://postgres.{project_ref}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
        f"postgresql://postgres.{project_ref}:{password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    ]
    
    print("Creating database schema...")
    
    for i, conn_string in enumerate(connection_strings):
        try:
            print(f"\nTrying connection method {i+1}...")
            conn = psycopg2.connect(conn_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            
            print("[OK] Connected to database!")
            
            # Read and execute schema
            with open('create_supabase_schema.sql', 'r') as f:
                schema_sql = f.read()
            
            print("Executing schema...")
            cur.execute(schema_sql)
            
            print("[OK] Schema executed successfully!")
            
            # Verify tables
            tables = ['users', 'sessions', 'plots', 'authors', 'orchestrator_decisions']
            print("\nVerifying tables:")
            
            for table in tables:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"[OK] Table '{table}' exists (rows: {count})")
            
            cur.close()
            conn.close()
            
            print("\n" + "="*60)
            print("SUCCESS! DATABASE SCHEMA CREATED!")
            print("="*60)
            print("\nYour database is ready!")
            print("You can now run: python main.py")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"[FAIL] Connection method {i+1} failed: {str(e)[:100]}")
            continue
    
    print("\nAll connection methods failed. Please check:")
    print("1. Password is correct")
    print("2. Network connection")
    print("3. Supabase project is active")
    
    return False

if __name__ == "__main__":
    create_schema_now()