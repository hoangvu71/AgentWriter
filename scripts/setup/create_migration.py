#!/usr/bin/env python3
"""
Create a new migration file
Usage: python create_migration.py "add character development tables"
"""

import sys
from datetime import datetime
from pathlib import Path

def create_migration(description):
    """Create a new migration file with proper naming"""
    
    migrations_dir = Path("migrations")
    
    # Find next migration number
    existing = list(migrations_dir.glob("[0-9][0-9][0-9]_*.sql"))
    next_num = len(existing) + 1
    
    # Clean description for filename
    clean_desc = description.lower().replace(" ", "_")
    clean_desc = "".join(c for c in clean_desc if c.isalnum() or c == "_")
    
    # Create filename
    filename = f"{next_num:03d}_{clean_desc}.sql"
    filepath = migrations_dir / filename
    
    # Create migration file
    with open(filepath, "w") as f:
        f.write(f"""-- Migration: {filename}
-- Created: {datetime.now().isoformat()}
-- Description: {description}

-- Add your schema changes below
-- Remember to use IF NOT EXISTS for new tables
-- Use ALTER TABLE for modifications to existing tables

""")
    
    print(f"[OK] Created new migration: {filepath}")
    print(f"\nNext steps:")
    print(f"1. Edit {filepath} with your schema changes")
    print(f"2. Copy the contents to Supabase SQL Editor")
    print(f"3. Run the migration")
    print(f"4. Update applied_migrations.json")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_migration.py \"description of changes\"")
        sys.exit(1)
    
    description = " ".join(sys.argv[1:])
    create_migration(description)
