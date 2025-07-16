#!/usr/bin/env python3
"""
Remove migration backup tables
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

def remove_migration_backups():
    """Remove migration backup tables"""
    
    # Connection details
    supabase_url = os.getenv("SUPABASE_URL")
    db_password = os.getenv("SUPABASE_DB_PASSWORD")
    
    if not supabase_url or not db_password:
        print("ERROR: Missing SUPABASE_URL or SUPABASE_DB_PASSWORD")
        return False
    
    # Extract project reference from URL
    project_ref = supabase_url.split('//')[1].split('.')[0]
    
    connection_strings = [
        f"postgresql://postgres.{project_ref}:{db_password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
        f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"
    ]
    
    for i, conn_string in enumerate(connection_strings, 1):
        print(f"Trying connection method {i}...")
        try:
            conn = psycopg2.connect(conn_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            print("[OK] Connected to database!")
            
            # Get list of backup tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'migration_backup_%'
                ORDER BY table_name;
            """)
            
            backup_tables = cur.fetchall()
            
            if not backup_tables:
                print("No migration backup tables found.")
                return True
            
            print(f"\nFound {len(backup_tables)} migration backup tables to remove:")
            for table in backup_tables:
                table_name = table[0]
                print(f"  - {table_name}")
            
            # Remove each backup table
            for table in backup_tables:
                table_name = table[0]
                try:
                    print(f"\nRemoving table: {table_name}")
                    cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
                    print(f"[OK] Successfully removed {table_name}")
                except Exception as e:
                    print(f"[ERROR] Error removing {table_name}: {e}")
            
            # Verify removal
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'migration_backup_%'
                ORDER BY table_name;
            """)
            
            remaining_tables = cur.fetchall()
            
            if not remaining_tables:
                print("\n[OK] All migration backup tables have been successfully removed!")
            else:
                print(f"\n[WARNING] {len(remaining_tables)} backup tables still exist:")
                for table in remaining_tables:
                    print(f"  - {table[0]}")
            
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"[ERROR] {e}")
            continue
    
    print("\n[ERROR] All connection methods failed!")
    return False

if __name__ == "__main__":
    print("Removing Migration Backup Tables")
    print("=" * 60)
    remove_migration_backups()