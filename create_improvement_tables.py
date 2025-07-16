#!/usr/bin/env python3
"""
Create improvement tables manually using Supabase table operations
"""

import asyncio
from supabase_service import supabase_service

async def create_improvement_tables():
    """Create improvement tables manually"""
    print("Creating Improvement System Tables")
    print("=" * 50)
    
    try:
        # Test 1: Try to create a test record to see current table status
        print("1. Testing current table status...")
        try:
            test_session = {
                "user_id": "test_user",
                "session_id": "test_session",
                "original_content": "Test content",
                "content_type": "plot"
            }
            
            result = supabase_service.client.table("improvement_sessions").insert(test_session).execute()
            session_id = result.data[0]['id']
            
            # Clean up test record
            supabase_service.client.table("improvement_sessions").delete().eq('id', session_id).execute()
            
            print("[OK] Tables already exist and working!")
            return True
            
        except Exception as e:
            print(f"[INFO] Tables don't exist yet: {e}")
        
        # Test 2: Check what tables do exist
        print("2. Checking existing tables...")
        try:
            # Try some common table operations to see what exists
            tables_to_check = ['improvement_sessions', 'iterations', 'critiques', 'enhancements', 'scores']
            existing_tables = []
            
            for table_name in tables_to_check:
                try:
                    result = supabase_service.client.table(table_name).select("*").limit(1).execute()
                    existing_tables.append(table_name)
                    print(f"   [OK] Table '{table_name}' exists")
                except:
                    print(f"   [MISSING] Table '{table_name}' does not exist")
            
            if len(existing_tables) == 5:
                print("[OK] All tables exist! Testing functionality...")
                # Test the main functions we created
                improvement_session_id = await supabase_service.create_improvement_session(
                    user_id="test_user",
                    session_id="test_session_123",
                    original_content="Test content",
                    content_type="plot",
                    content_id="test-content-id",
                    target_score=9.5,
                    max_iterations=4
                )
                print(f"[OK] Created test improvement session: {improvement_session_id}")
                
                # Clean up
                supabase_service.client.table("improvement_sessions").delete().eq('id', improvement_session_id).execute()
                print("[OK] Cleaned up test session")
                
                return True
            else:
                print(f"[ERROR] Only {len(existing_tables)}/5 tables exist")
                return False
        
        except Exception as e:
            print(f"[ERROR] Failed to check tables: {e}")
            return False
        
    except Exception as e:
        print(f"[ERROR] Table creation failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(create_improvement_tables())
    if success:
        print("\n" + "=" * 50)
        print("IMPROVEMENT TABLES READY!")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("TABLES NOT READY!")
        print("=" * 50)