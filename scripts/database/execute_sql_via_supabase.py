#!/usr/bin/env python3
"""Execute migration SQL via Supabase"""

import os
import sys
from pathlib import Path

# Check if we can use npx supabase
print("Attempting to apply migration 008...")

migration_file = Path("migrations/008_world_building_and_characters_system.sql")
if not migration_file.exists():
    print(f"Error: Migration file not found: {migration_file}")
    sys.exit(1)

# Try using npx supabase db push
import subprocess

print("\nUsing npx supabase to apply migration...")
try:
    # First, let's check if we need to link the project
    result = subprocess.run(
        ["npx", "supabase", "status"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    if "Cannot find project ref" in result.stderr:
        print("Project not linked. You need to run: npx supabase link")
        print("\nTo link your project:")
        print("1. Get your project reference ID from Supabase dashboard")
        print("2. Run: npx supabase link --project-ref your-project-ref")
        print("3. Then run this script again")
        sys.exit(1)
    
    # Try to push the specific migration file
    print(f"Pushing migration file: {migration_file}")
    result = subprocess.run(
        ["npx", "supabase", "db", "push", "--file", str(migration_file)],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    if result.returncode == 0:
        print("[OK] Migration applied successfully!")
        print(result.stdout)
        
        # Update tracking
        import json
        from datetime import datetime
        
        migration_tracking = Path("migrations/applied_migrations.json")
        with open(migration_tracking, 'r') as f:
            data = json.load(f)
        
        if "008_world_building_and_characters_system.sql" not in data["applied"]:
            data["applied"].append("008_world_building_and_characters_system.sql")
            data["last_updated"] = datetime.now().isoformat()
            
            with open(migration_tracking, 'w') as f:
                json.dump(data, f, indent=2)
            
            print("[OK] Updated migration tracking")
        
        print("\n[READY] World Building and Characters tables created!")
        print("You can now use the features!")
    else:
        print("[ERROR] Failed to apply migration")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        
except FileNotFoundError:
    print("[ERROR] npx command not found. Make sure Node.js is installed.")
except Exception as e:
    print(f"[ERROR] {e}")