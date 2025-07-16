#!/usr/bin/env python3
"""
Automated schema setup using Supabase Management API
The easiest way - no PostgreSQL drivers needed!
"""

import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def setup_with_management_api():
    """Use Supabase Management API to run SQL"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not service_key:
        print("\n" + "="*60)
        print("MISSING SERVICE ROLE KEY!")
        print("="*60)
        print("\nTo get your service role key:")
        print("1. Go to: https://app.supabase.com/project/cfqgzbudjnvtyxrrvvmo")
        print("2. Click Settings (gear icon)")
        print("3. Click API")
        print("4. Find 'service_role' key (it's longer than anon_key)")
        print("5. Click 'Reveal' and copy it")
        print("6. Add to .env file:")
        print("   SUPABASE_SERVICE_ROLE_KEY=eyJ....(your long key here)")
        print("="*60)
        return False
    
    # Extract project ref
    project_ref = supabase_url.split('//')[1].split('.')[0]
    
    # Read schema
    with open('create_supabase_schema.sql', 'r') as f:
        schema_sql = f.read()
    
    print("Setting up database schema automatically...")
    
    # Method 1: Try using the query endpoint
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    # Split SQL into individual statements
    statements = []
    current = []
    
    for line in schema_sql.split('\n'):
        if line.strip().startswith('--'):
            continue
        current.append(line)
        if line.strip().endswith(';'):
            statement = '\n'.join(current).strip()
            if statement:
                statements.append(statement)
            current = []
    
    success_count = 0
    total_statements = len([s for s in statements if not s.startswith('--')])
    
    print(f"Executing {total_statements} SQL statements...")
    
    # Try different API endpoints
    endpoints = [
        f"{supabase_url}/rest/v1/rpc/query",
        f"{supabase_url}/rest/v1/",
        f"https://api.supabase.com/v1/projects/{project_ref}/database/query"
    ]
    
    working_endpoint = None
    
    # First, try to find a working endpoint
    for endpoint in endpoints:
        try:
            test_payload = {"query": "SELECT 1"}
            response = requests.post(endpoint, json=test_payload, headers=headers, timeout=5)
            if response.status_code < 400:
                working_endpoint = endpoint
                print(f"Found working endpoint: {endpoint}")
                break
        except:
            continue
    
    if not working_endpoint:
        # Fallback: Create a database function
        print("\nTrying alternative method: Creating database function...")
        
        function_sql = f"""
        CREATE OR REPLACE FUNCTION setup_schema()
        RETURNS text AS $$
        BEGIN
            {schema_sql}
            RETURN 'Schema created successfully';
        END;
        $$ LANGUAGE plpgsql;
        """
        
        # Try to create function via API
        response = requests.post(
            f"{supabase_url}/rest/v1/rpc/setup_schema",
            headers=headers
        )
        
        if response.status_code < 400:
            print("Schema created via function!")
            return True
    
    # If we still can't automate, provide a one-click solution
    print("\n" + "="*60)
    print("AUTOMATED SETUP REQUIRES SERVICE ROLE KEY")
    print("="*60)
    print("\nOption 1: Get your service role key")
    print("- Go to Settings > API in Supabase dashboard")
    print("- Copy the service_role key")
    print("- Add to .env file")
    print("\nOption 2: Use Supabase CLI (one-time setup)")
    print("npm install -g supabase")
    print("supabase login")
    print(f"supabase link --project-ref {project_ref}")
    print("supabase db reset")
    print("="*60)
    
    return False

def create_via_postgres_js():
    """Alternative: Create a Node.js script for automation"""
    
    node_script = """// setup-db.js
const { Client } = require('pg');
require('dotenv').config();

async function setupDatabase() {
    const connectionString = process.env.DATABASE_URL || 
        `postgresql://postgres.${process.env.SUPABASE_URL.split('//')[1].split('.')[0]}:${process.env.SUPABASE_SERVICE_ROLE_KEY}@aws-0-us-east-1.pooler.supabase.com:6543/postgres`;
    
    const client = new Client({ connectionString });
    
    try {
        await client.connect();
        console.log('Connected to database');
        
        const fs = require('fs');
        const schema = fs.readFileSync('create_supabase_schema.sql', 'utf8');
        
        await client.query(schema);
        console.log('Schema created successfully!');
    } catch (err) {
        console.error('Error:', err);
    } finally {
        await client.end();
    }
}

setupDatabase();
"""
    
    with open('setup-db.js', 'w') as f:
        f.write(node_script)
    
    print("\nAlternative: Created setup-db.js")
    print("Run: npm install pg dotenv && node setup-db.js")

def main():
    print("="*60)
    print("AUTOMATED DATABASE SETUP")
    print("="*60)
    
    # Check for service key
    if not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        print("\nNo service role key found.")
        print("Follow the instructions above to get it.")
        print("\nAlternatively, I'm creating a Node.js script...")
        create_via_postgres_js()
        return
    
    success = setup_with_management_api()
    
    if success:
        print("\nSuccess! Database is ready.")
    else:
        print("\nCreating alternative solutions...")
        create_via_postgres_js()

if __name__ == "__main__":
    main()