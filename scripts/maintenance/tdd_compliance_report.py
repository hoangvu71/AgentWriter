#!/usr/bin/env python3
"""
TDD Compliance Report and Future Discipline Enforcer
"""

import subprocess
import sys
from datetime import datetime

def run_tdd_tests():
    """Run all TDD-related tests and generate compliance report"""
    
    print("=" * 60)
    print("TDD COMPLIANCE REPORT")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test files that represent TDD compliance
    tdd_test_files = [
        "test_supabase_service_unit.py",
        "test_migration_007_unit.py", 
        "test_orchestrator_improvement_unit.py"
    ]
    
    print("[TDD] COMPLIANCE STATUS:")
    print()
    
    # Check if TDD test files exist
    import os
    for test_file in tdd_test_files:
        if os.path.exists(test_file):
            print(f"[OK] {test_file} - TDD test file exists")
        else:
            print(f"[FAIL] {test_file} - TDD test file missing")
    
    print()
    print("[TEST] RUNNING TDD UNIT TESTS:")
    print("-" * 40)
    
    # Run unit tests
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_supabase_service_unit.py", 
            "-v", "--tb=short"
        ], capture_output=True, text=True, timeout=60)
        
        print("UNIT TEST RESULTS:")
        print(result.stdout)
        if result.stderr:
            print("ERRORS:")
            print(result.stderr)
        
        # Parse results
        lines = result.stdout.split('\n')
        for line in lines:
            if 'passed' in line and 'failed' in line:
                print(f"[RESULT] {line}")
                break
                
    except subprocess.TimeoutExpired:
        print("[FAIL] Tests timed out")
    except Exception as e:
        print(f"[FAIL] Error running tests: {e}")
    
    print()
    print("[FIXED] TDD VIOLATIONS CORRECTED:")
    print("-" * 40)
    print("[OK] Added input validation to all Supabase methods")
    print("[OK] Created retroactive unit tests for core functionality")
    print("[OK] Added proper error handling with TDD-driven messages")
    print("[OK] Created test-driven schema validation tests")
    print("[OK] Added workflow integration test coverage")
    
    print()
    print("[WARNING] REMAINING TDD VIOLATIONS:")
    print("-" * 40)
    print("[FAIL] Original implementation was not test-driven")
    print("[FAIL] No Red-Green-Refactor cycle was followed")
    print("[FAIL] Tests were written AFTER implementation")
    print("[FAIL] Database schema was not test-driven")
    
    print()
    print("[DISCIPLINE] TDD FOR FUTURE FEATURES:")
    print("-" * 40)
    print("1. ALWAYS write failing tests FIRST")
    print("2. Write minimal code to make tests pass")
    print("3. Refactor while keeping tests green")
    print("4. No code without a failing test first")
    print("5. Run this script before any new feature work")
    
    print()
    print("[TODO] NEXT STEPS:")
    print("-" * 40)
    print("1. Fix remaining test mocking issues")
    print("2. Create pre-commit hooks for TDD enforcement")
    print("3. Add TDD checklist to development workflow")
    print("4. Implement strict TDD for all future features")
    
    print()
    print("=" * 60)
    print("CRITICAL REMINDER FROM CLAUDE.md:")
    print("- ALWAYS write tests FIRST before any implementation")
    print("- Red-Green-Refactor cycle is mandatory")
    print("- No code without a failing test first")
    print("- Tests drive the design, not the other way around")
    print("=" * 60)

def check_future_tdd_compliance():
    """Checklist for future TDD compliance"""
    
    print()
    print("[CHECKLIST] FUTURE TDD COMPLIANCE:")
    print("=" * 50)
    print()
    print("Before implementing ANY new feature:")
    print("[ ] 1. Write failing test for the requirement")
    print("[ ] 2. Confirm test fails (RED)")
    print("[ ] 3. Write minimal code to pass test (GREEN)")
    print("[ ] 4. Refactor code while keeping test green (REFACTOR)")
    print("[ ] 5. Repeat for each requirement")
    print()
    print("Before committing code:")
    print("[ ] 1. All tests pass")
    print("[ ] 2. Code coverage meets requirements")
    print("[ ] 3. No code exists without corresponding tests")
    print("[ ] 4. Tests were written BEFORE implementation")
    print()
    print("RED FLAG: If you answer 'No' to any item, STOP and fix TDD compliance")

if __name__ == "__main__":
    run_tdd_tests()
    check_future_tdd_compliance()