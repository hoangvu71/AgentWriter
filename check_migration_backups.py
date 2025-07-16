#!/usr/bin/env python3
"""
Check migration backup tables and determine if they can be safely removed
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

def check_backup_tables():
    """Check the migration backup tables"""
    
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
            
            # Check if backup tables exist
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
            
            print(f"\nFound {len(backup_tables)} migration backup tables:")
            for table in backup_tables:
                table_name = table[0]
                print(f"\n--- {table_name} ---")
                
                # Get table structure
                cur.execute(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """)
                
                columns = cur.fetchall()
                print("Columns:")
                for col_name, col_type in columns:
                    print(f"  - {col_name}: {col_type}")
                
                # Get row count
                cur.execute(f"SELECT COUNT(*) FROM {table_name};")
                row_count = cur.fetchone()[0]
                print(f"Row count: {row_count}")
                
                # Show sample data (first 3 rows)
                if row_count > 0:
                    cur.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                    sample_data = cur.fetchall()
                    print("Sample data:")
                    for i, row in enumerate(sample_data, 1):
                        print(f"  {i}: {row}")
            
            # Compare with current tables
            print("\n" + "="*60)
            print("COMPARISON WITH CURRENT TABLES")
            print("="*60)
            
            for table in backup_tables:
                backup_table = table[0]
                current_table = backup_table.replace('migration_backup_', '')
                
                print(f"\nComparing {backup_table} vs {current_table}:")
                
                # Check if current table exists
                cur.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{current_table}'
                    );
                """)
                
                current_exists = cur.fetchone()[0]
                
                if not current_exists:
                    print(f"  WARNING: Current table '{current_table}' does not exist!")
                    continue
                
                # Compare row counts
                cur.execute(f"SELECT COUNT(*) FROM {backup_table};")
                backup_count = cur.fetchone()[0]
                
                cur.execute(f"SELECT COUNT(*) FROM {current_table};")
                current_count = cur.fetchone()[0]
                
                print(f"  Backup table: {backup_count} rows")
                print(f"  Current table: {current_count} rows")
                
                if current_count >= backup_count:
                    print(f"  ✅ Current table has same or more data")
                else:
                    print(f"  ⚠️ Current table has less data than backup")
            
            # Recommendation
            print("\n" + "="*60)
            print("RECOMMENDATION")
            print("="*60)
            
            all_safe = True
            for table in backup_tables:
                backup_table = table[0]
                current_table = backup_table.replace('migration_backup_', '')
                
                cur.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{current_table}'
                    );
                """)
                
                if not cur.fetchone()[0]:
                    all_safe = False
                    continue
                
                cur.execute(f"SELECT COUNT(*) FROM {backup_table};")
                backup_count = cur.fetchone()[0]
                cur.execute(f"SELECT COUNT(*) FROM {current_table};")
                current_count = cur.fetchone()[0]
                
                if current_count < backup_count:
                    all_safe = False
            
            if all_safe:
                print("✅ SAFE TO REMOVE: All backup tables can be safely deleted.")
                print("   Migration was successful and current tables have complete data.")
            else:
                print("⚠️ KEEP BACKUPS: Some data may be missing from current tables.")
                print("   Review the differences before removing backup tables.")
            
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"[ERROR] {e}")
            continue
    
    print("\n[ERROR] All connection methods failed!")
    return False

if __name__ == "__main__":
    print("Checking Migration Backup Tables")
    print("="*60)
    check_backup_tables()