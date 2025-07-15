#!/usr/bin/env python3
"""
Apply migration 004: Reverse author-plot relationship
Changes from authors.plot_id -> plots.author_id (multiple plots per author)
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

def apply_relationship_fix():
    """Apply the author-plot relationship fix"""
    
    password = os.getenv("SUPABASE_DB_PASSWORD")
    project_ref = "cfqgzbudjnvtyxrrvvmo"
    
    connection_strings = [
        f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres",
        f"postgresql://postgres.{project_ref}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres",
        f"postgresql://postgres.{project_ref}:{password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    ]
    
    print("Applying author-plot relationship fix...")
    print("Changing from: authors.plot_id -> plots.author_id")
    print("This allows one author to have multiple plots (correct relationship)")
    
    for i, conn_string in enumerate(connection_strings):
        try:
            print(f"\nTrying connection method {i+1}...")
            conn = psycopg2.connect(conn_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            
            print("[OK] Connected to database!")
            
            # Check current state
            print("\nChecking current schema...")
            
            # Check if plots.author_id already exists
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'plots' AND column_name = 'author_id'
            """)
            author_id_exists = cur.fetchone() is not None
            
            # Check if authors.plot_id still exists  
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'authors' AND column_name = 'plot_id'
            """)
            plot_id_exists = cur.fetchone() is not None
            
            print(f"plots.author_id exists: {author_id_exists}")
            print(f"authors.plot_id exists: {plot_id_exists}")
            
            if author_id_exists and not plot_id_exists:
                print("[INFO] Relationship already fixed!")
                return True
            
            # Step 1: Add author_id column to plots table
            if not author_id_exists:
                print("\nStep 1: Adding author_id column to plots table...")
                cur.execute("""
                    ALTER TABLE plots 
                    ADD COLUMN author_id UUID REFERENCES authors(id) ON DELETE SET NULL
                """)
                print("[OK] Added author_id column to plots table")
            else:
                print("[SKIP] author_id column already exists")
            
            # Step 2: Migrate existing relationships
            if plot_id_exists:
                print("\nStep 2: Migrating existing relationships...")
                
                # Check how many relationships exist
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM authors 
                    WHERE plot_id IS NOT NULL
                """)
                relationship_count = cur.fetchone()[0]
                print(f"Found {relationship_count} existing author-plot relationships")
                
                if relationship_count > 0:
                    # Migrate the relationships
                    cur.execute("""
                        UPDATE plots 
                        SET author_id = (
                            SELECT id 
                            FROM authors 
                            WHERE authors.plot_id = plots.id 
                            LIMIT 1
                        )
                        WHERE EXISTS (
                            SELECT 1 
                            FROM authors 
                            WHERE authors.plot_id = plots.id
                        )
                    """)
                    
                    # Check how many were migrated
                    cur.execute("SELECT COUNT(*) FROM plots WHERE author_id IS NOT NULL")
                    migrated_count = cur.fetchone()[0]
                    print(f"[OK] Migrated {migrated_count} relationships to new structure")
                else:
                    print("[INFO] No existing relationships to migrate")
            
            # Step 3: Remove the old plot_id column from authors table
            if plot_id_exists:
                print("\nStep 3: Removing old plot_id column from authors table...")
                cur.execute("ALTER TABLE authors DROP COLUMN plot_id")
                print("[OK] Removed plot_id column from authors table")
            else:
                print("[SKIP] plot_id column already removed")
            
            # Step 4: Add index for efficient lookups
            print("\nStep 4: Adding index for efficient lookups...")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_plots_author_id ON plots(author_id)")
            print("[OK] Added index on plots.author_id")
            
            # Step 5: Drop old index if it exists
            cur.execute("DROP INDEX IF EXISTS idx_authors_plot_id")
            print("[OK] Dropped old index on authors.plot_id")
            
            # Verify final structure
            print("\nVerifying final structure...")
            
            # Check plots table structure
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'plots' 
                ORDER BY ordinal_position
            """)
            plots_columns = cur.fetchall()
            
            print("\nPlots table structure:")
            for col_name, col_type, nullable in plots_columns:
                print(f"  - {col_name} ({col_type}) {'NULL' if nullable == 'YES' else 'NOT NULL'}")
            
            # Check authors table structure
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'authors' 
                ORDER BY ordinal_position
            """)
            authors_columns = cur.fetchall()
            
            print("\nAuthors table structure:")
            for col_name, col_type, nullable in authors_columns:
                print(f"  - {col_name} ({col_type}) {'NULL' if nullable == 'YES' else 'NOT NULL'}")
            
            # Check relationship counts
            cur.execute("SELECT COUNT(*) FROM plots WHERE author_id IS NOT NULL")
            plots_with_authors = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM authors")
            total_authors = cur.fetchone()[0]
            
            print(f"\nRelationship summary:")
            print(f"  - Total authors: {total_authors}")
            print(f"  - Plots with authors: {plots_with_authors}")
            
            cur.close()
            conn.close()
            
            print("\n" + "="*60)
            print("AUTHOR-PLOT RELATIONSHIP FIX COMPLETE!")
            print("="*60)
            print("✅ Changed from: authors.plot_id -> plots.author_id")
            print("✅ One author can now have multiple plots")
            print("✅ Database relationships properly configured")
            print("✅ Indexes optimized for new structure")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"[FAIL] Connection method {i+1} failed: {str(e)[:100]}")
            continue
    
    print("\nAll connection methods failed.")
    return False

if __name__ == "__main__":
    print("="*60)
    print("FIXING AUTHOR-PLOT RELATIONSHIP")
    print("="*60)
    print("\nChanging from: authors.plot_id -> plots.author_id")
    print("This will allow one author to have multiple plots")
    print("(This is the correct relationship for a book writing system)")
    print("="*60)
    
    # Apply the fix automatically
    success = apply_relationship_fix()
    
    if success:
        print("\n[SUCCESS] Relationship fix completed!")
        print("\nNext steps:")
        print("1. Update supabase_service.py to use new relationship")
        print("2. Update multi_agent_system.py logic")
        print("3. Test the new author-plot workflow")
    else:
        print("\n[FAIL] Relationship fix failed.")