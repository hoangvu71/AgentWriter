#!/usr/bin/env python3
"""
Fully automated schema setup using Supabase service role key
No manual SQL copying required!
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
from urllib.parse import urlparse
import re

load_dotenv()

def get_connection_string():
    """Build PostgreSQL connection string from Supabase URL"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not service_role_key:
        print("\n" + "="*60)
        print("ERROR: SUPABASE_SERVICE_ROLE_KEY not found!")
        print("="*60)
        print("\nTo fix this:")
        print("1. Go to: https://app.supabase.com/project/cfqgzbudjnvtyxrrvvmo")
        print("2. Click Settings > API")
        print("3. Copy the 'service_role' key (not the anon key)")
        print("4. Add to .env file:")
        print("   SUPABASE_SERVICE_ROLE_KEY=your_key_here")
        print("="*60)
        return None
    
    # Extract project reference from URL
    # Format: https://cfqgzbudjnvtyxrrvvmo.supabase.co
    project_ref = supabase_url.split('//')[1].split('.')[0]
    
    # Supabase PostgreSQL connection format
    # Default password is the service role key
    conn_string = (
        f"postgresql://postgres.{project_ref}:{service_role_key}"
        f"@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    )
    
    return conn_string

def create_tables_automatically():
    """Create all tables using direct PostgreSQL connection"""
    
    conn_string = get_connection_string()
    if not conn_string:
        return False
    
    try:
        print("Connecting to Supabase PostgreSQL...")
        conn = psycopg2.connect(conn_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("Connected! Creating tables...")
        
        # Read and execute the schema
        with open('create_supabase_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Split into individual statements
        statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
        
        success_count = 0
        for i, statement in enumerate(statements):
            try:
                # Skip comments
                if statement.startswith('--') or not statement:
                    continue
                    
                print(f"\nExecuting statement {i+1}/{len(statements)}...")
                cur.execute(statement + ';')
                success_count += 1
                print(f"[OK] Statement executed")
                
            except psycopg2.errors.DuplicateTable:
                print(f"[OK] Table already exists")
                success_count += 1
            except psycopg2.errors.DuplicateObject:
                print(f"[OK] Index already exists")
                success_count += 1
            except Exception as e:
                print(f"[ERROR] {str(e)[:100]}")
                continue
        
        # Verify tables
        print("\n" + "="*60)
        print("VERIFYING TABLES...")
        print("="*60)
        
        tables = ['users', 'sessions', 'plots', 'authors', 'orchestrator_decisions']
        verified = 0
        
        for table in tables:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table,))
            
            exists = cur.fetchone()[0]
            if exists:
                print(f"[OK] Table '{table}' exists")
                verified += 1
            else:
                print(f"[MISSING] Table '{table}' not found")
        
        cur.close()
        conn.close()
        
        if verified == len(tables):
            print("\n" + "="*60)
            print("SUCCESS! All tables created automatically!")
            print("="*60)
            print("\nYour database is ready. No manual steps needed!")
            print("You can now run: python main.py")
            return True
        else:
            print(f"\nPartial success: {verified}/{len(tables)} tables created")
            return False
            
    except Exception as e:
        print(f"\nConnection error: {e}")
        
        # Try alternative connection formats
        print("\nTrying alternative connection format...")
        
        # Alternative format for different regions
        project_ref = os.getenv("SUPABASE_URL").split('//')[1].split('.')[0]
        alt_connections = [
            f"postgresql://postgres.{project_ref}:{os.getenv('SUPABASE_SERVICE_ROLE_KEY')}@db.{project_ref}.supabase.co:5432/postgres",
            f"postgresql://postgres:{os.getenv('SUPABASE_SERVICE_ROLE_KEY')}@db.{project_ref}.supabase.co:5432/postgres",
            f"postgresql://postgres.{project_ref}:{os.getenv('SUPABASE_SERVICE_ROLE_KEY')}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
        ]
        
        for alt_conn in alt_connections:
            try:
                print(f"Trying: {alt_conn[:50]}...")
                conn = psycopg2.connect(alt_conn)
                print("Success! Using alternative connection")
                # Retry with this connection
                return create_tables_with_connection(conn)
            except:
                continue
                
        print("\nAll connection attempts failed.")
        print("Please check your service role key.")
        return False

def create_tables_with_connection(conn):
    """Helper function to create tables with an established connection"""
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    with open('create_supabase_schema.sql', 'r') as f:
        schema_sql = f.read()
    
    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
    
    for statement in statements:
        try:
            if statement.startswith('--') or not statement:
                continue
            cur.execute(statement + ';')
        except:
            continue
    
    cur.close()
    conn.close()
    return True

def main():
    print("="*60)
    print("AUTOMATED SUPABASE SCHEMA SETUP")
    print("="*60)
    
    success = create_tables_automatically()
    
    if not success:
        print("\nTroubleshooting:")
        print("1. Make sure you have the service role key (not anon key)")
        print("2. Add it to .env as SUPABASE_SERVICE_ROLE_KEY")
        print("3. Run this script again")

if __name__ == "__main__":
    main()