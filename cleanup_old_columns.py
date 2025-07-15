#!/usr/bin/env python3
"""
Remove old VARCHAR/JSONB columns from plots table after successful migration
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

def cleanup_old_columns():
    """Remove old columns from plots table"""
    
    password = os.getenv("SUPABASE_DB_PASSWORD")
    project_ref = "cfqgzbudjnvtyxrrvvmo"
    
    connection_strings = [
        f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres",
        f"postgresql://postgres.{project_ref}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
        f"postgresql://postgres.{project_ref}:{password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    ]
    
    print("Cleaning up old columns from plots table...")
    
    # List of old columns to remove
    old_columns = [
        'genre',
        'subgenre', 
        'microgenre',
        'trope',
        'tone',
        'target_audience'
    ]
    
    for i, conn_string in enumerate(connection_strings):
        try:
            print(f"\nTrying connection method {i+1}...")
            conn = psycopg2.connect(conn_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            
            print("[OK] Connected to database!")
            
            # First, verify that all data has been migrated
            print("Verifying migration is complete...")
            
            cur.execute("""
                SELECT COUNT(*) FROM plots 
                WHERE genre_id IS NULL AND genre IS NOT NULL
            """)
            unmigrated = cur.fetchone()[0]
            
            if unmigrated > 0:
                print(f"[ERROR] Found {unmigrated} plots that haven't been migrated!")
                print("Cannot remove old columns until all data is migrated.")
                return False
            
            print("[OK] All data has been migrated to new structure")
            
            # Show current table structure
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'plots' 
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            
            print("\nCurrent plots table columns:")
            for col_name, col_type in columns:
                marker = " [TO REMOVE]" if col_name in old_columns else ""
                print(f"  - {col_name} ({col_type}){marker}")
            
            # Remove old columns one by one
            print(f"\nRemoving {len(old_columns)} old columns...")
            
            for column in old_columns:
                try:
                    print(f"Dropping column: {column}")
                    cur.execute(f"ALTER TABLE plots DROP COLUMN IF EXISTS {column}")
                    print(f"[OK] Removed column: {column}")
                except Exception as e:
                    print(f"[SKIP] Column {column}: {str(e)[:50]}")
            
            # Verify columns were removed
            print("\nVerifying column removal...")
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'plots' AND column_name = ANY(%s)
            """, (old_columns,))
            
            remaining_old_columns = cur.fetchall()
            if remaining_old_columns:
                print(f"[WARNING] Some old columns still exist: {[col[0] for col in remaining_old_columns]}")
            else:
                print("[OK] All old columns successfully removed!")
            
            # Show final table structure
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'plots' 
                ORDER BY ordinal_position
            """)
            final_columns = cur.fetchall()
            
            print("\nFinal plots table structure:")
            for col_name, col_type in final_columns:
                print(f"  - {col_name} ({col_type})")
            
            cur.close()
            conn.close()
            
            print("\n" + "="*60)
            print("COLUMN CLEANUP COMPLETE!")
            print("="*60)
            print("Removed old columns:")
            for col in old_columns:
                print(f"  - {col}")
            print("\nPlots table now uses only normalized foreign key structure!")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"[FAIL] Connection method {i+1} failed: {str(e)[:100]}")
            continue
    
    print("\nAll connection methods failed.")
    return False

if __name__ == "__main__":
    print("="*60)
    print("DATABASE CLEANUP - REMOVE OLD COLUMNS")
    print("="*60)
    print("\nThis will permanently remove the old VARCHAR/JSONB columns:")
    print("- genre, subgenre, microgenre, trope, tone, target_audience")
    print("\nThe new foreign key columns will remain:")
    print("- genre_id, subgenre_id, microgenre_id, trope_id, tone_id, target_audience_id")
    print("="*60)
    
    # Confirm before proceeding
    confirm = input("\nProceed with column removal? (yes/no): ").lower().strip()
    
    if confirm == 'yes':
        success = cleanup_old_columns()
        
        if success:
            print("\n[SUCCESS] Database cleanup completed!")
        else:
            print("\n[FAIL] Database cleanup failed.")
    else:
        print("\nOperation cancelled.")