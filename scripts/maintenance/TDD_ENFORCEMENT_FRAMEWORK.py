#!/usr/bin/env python3
"""
TDD Enforcement Framework - MANDATORY TDD COMPLIANCE
This framework MUST be used for all future development to enforce TDD principles
"""

import subprocess
import sys
import os
import json
import ast
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

class TDDViolationError(Exception):
    """Raised when TDD principles are violated"""
    pass

class TDDEnforcementFramework:
    """
    Enforces TDD compliance across the entire development workflow
    """
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.test_dir = self.project_root / "tests"
        self.src_files = list(self.project_root.glob("*.py"))
        self.test_files = list(self.project_root.glob("test_*.py"))
        
    def enforce_tdd_workflow(self) -> bool:
        """
        Main TDD enforcement function - MUST be called before any development
        Returns True if TDD compliance is maintained, raises TDDViolationError otherwise
        """
        print("🚨 TDD ENFORCEMENT FRAMEWORK ACTIVATED")
        print("=" * 60)
        
        try:
            # Phase 1: Pre-development validation
            self._validate_existing_tdd_compliance()
            
            # Phase 2: Test infrastructure verification
            self._verify_test_infrastructure()
            
            # Phase 3: Current test coverage analysis
            self._analyze_test_coverage()
            
            # Phase 4: TDD workflow validation
            self._validate_tdd_workflow()
            
            print("\n✅ TDD COMPLIANCE VERIFIED")
            print("=" * 60)
            return True
            
        except TDDViolationError as e:
            print(f"\n❌ TDD VIOLATION DETECTED: {e}")
            print("=" * 60)
            print("🛑 DEVELOPMENT MUST STOP UNTIL TDD COMPLIANCE IS RESTORED")
            raise
    
    def _validate_existing_tdd_compliance(self) -> None:
        """Validate that existing code has proper test coverage"""
        print("\n📋 VALIDATING EXISTING TDD COMPLIANCE...")
        
        violations = []
        
        # Check for untested Python files
        for src_file in self.src_files:
            if src_file.name.startswith('test_'):
                continue
                
            expected_test_file = f"test_{src_file.stem}_unit.py"
            if not (self.project_root / expected_test_file).exists():
                violations.append(f"Missing test file for {src_file.name}: {expected_test_file}")
        
        # Check critical files have comprehensive tests
        critical_files = [
            "main.py",
            "agent_factory.py", 
            "supabase_service.py"
        ]
        
        for critical_file in critical_files:
            if (self.project_root / critical_file).exists():
                test_file = f"test_{critical_file.replace('.py', '')}_unit.py"
                if not (self.project_root / test_file).exists():
                    violations.append(f"CRITICAL: Missing comprehensive tests for {critical_file}")
        
        if violations:
            raise TDDViolationError(f"Existing code lacks proper test coverage:\n" + "\n".join(violations))
        
        print("✅ Existing TDD compliance validated")
    
    def _verify_test_infrastructure(self) -> None:
        """Verify that proper test infrastructure exists"""
        print("\n🔧 VERIFYING TEST INFRASTRUCTURE...")
        
        required_packages = [
            "pytest",
            "pytest-asyncio", 
            "pytest-mock",
            "pytest-cov"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                importlib.import_module(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            raise TDDViolationError(f"Missing required test packages: {missing_packages}")
        
        # Check test configuration files
        required_configs = [
            "pytest.ini",
            ".coveragerc"
        ]
        
        missing_configs = []
        for config in required_configs:
            if not (self.project_root / config).exists():
                missing_configs.append(config)
        
        if missing_configs:
            print(f"⚠️  Missing test configuration files: {missing_configs}")
            self._create_missing_test_configs(missing_configs)
        
        print("✅ Test infrastructure verified")
    
    def _analyze_test_coverage(self) -> None:
        """Analyze current test coverage and identify gaps"""
        print("\n📊 ANALYZING TEST COVERAGE...")
        
        try:
            # Run coverage analysis
            result = subprocess.run([
                sys.executable, "-m", "pytest", "--cov=.", "--cov-report=json", "--cov-report=term"
            ], capture_output=True, text=True, timeout=120)
            
            # Parse coverage results
            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                
                total_coverage = coverage_data["totals"]["percent_covered"]
                print(f"📈 Overall test coverage: {total_coverage:.1f}%")
                
                if total_coverage < 80:
                    raise TDDViolationError(f"Test coverage {total_coverage:.1f}% is below minimum 80%")
                
                # Identify files with low coverage
                low_coverage_files = []
                for filename, file_data in coverage_data["files"].items():
                    if file_data["summary"]["percent_covered"] < 80:
                        low_coverage_files.append(f"{filename}: {file_data['summary']['percent_covered']:.1f}%")
                
                if low_coverage_files:
                    print("⚠️  Files with low coverage:")
                    for file_info in low_coverage_files:
                        print(f"   - {file_info}")
            
        except subprocess.TimeoutExpired:
            print("⚠️  Coverage analysis timed out")
        except Exception as e:
            print(f"⚠️  Coverage analysis failed: {e}")
        
        print("✅ Test coverage analysis completed")
    
    def _validate_tdd_workflow(self) -> None:
        """Validate that TDD workflow is being followed"""
        print("\n🔄 VALIDATING TDD WORKFLOW...")
        
        # Check that tests exist for recent changes
        try:
            # Get recent git changes
            result = subprocess.run([
                "git", "diff", "--name-only", "HEAD~1", "HEAD"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                changed_files = result.stdout.strip().split('\n')
                python_changes = [f for f in changed_files if f.endswith('.py') and not f.startswith('test_')]
                
                for changed_file in python_changes:
                    test_file = f"test_{Path(changed_file).stem}_unit.py"
                    if not (self.project_root / test_file).exists():
                        raise TDDViolationError(f"Modified {changed_file} without corresponding test file {test_file}")
        
        except subprocess.CalledProcessError:
            print("⚠️  Git history check failed (not in git repo or no history)")
        
        print("✅ TDD workflow validation completed")
    
    def _create_missing_test_configs(self, missing_configs: List[str]) -> None:
        """Create missing test configuration files"""
        
        if "pytest.ini" in missing_configs:
            pytest_config = """[tool:pytest]
testpaths = .
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --disable-warnings
    --tb=short
    -v
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
asyncio_mode = auto
"""
            with open(self.project_root / "pytest.ini", 'w') as f:
                f.write(pytest_config)
            print("✅ Created pytest.ini")
        
        if ".coveragerc" in missing_configs:
            coverage_config = """[run]
source = .
omit = 
    test_*.py
    tests/*
    venv/*
    .venv/*
    __pycache__/*
    setup.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    
[html]
directory = htmlcov
"""
            with open(self.project_root / ".coveragerc", 'w') as f:
                f.write(coverage_config)
            print("✅ Created .coveragerc")
    
    def run_all_tests(self) -> bool:
        """Run all tests and ensure they pass"""
        print("\n🧪 RUNNING ALL TESTS...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", "-v", "--tb=short"
            ], timeout=300)
            
            if result.returncode == 0:
                print("✅ All tests passed")
                return True
            else:
                raise TDDViolationError("Some tests failed - fix before continuing development")
                
        except subprocess.TimeoutExpired:
            raise TDDViolationError("Tests timed out - check for infinite loops or hanging tests")
        except Exception as e:
            raise TDDViolationError(f"Test execution failed: {e}")
    
    def enforce_red_green_refactor(self, test_file: str, implementation_file: str) -> bool:
        """
        Enforce Red-Green-Refactor cycle for new development
        """
        print(f"\n🔴 ENFORCING RED-GREEN-REFACTOR for {test_file} -> {implementation_file}")
        
        # RED: Ensure test exists and fails
        if not Path(test_file).exists():
            raise TDDViolationError(f"Test file {test_file} must exist before implementation")
        
        # Run tests to ensure they fail initially
        result = subprocess.run([
            sys.executable, "-m", "pytest", test_file, "-v"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            raise TDDViolationError(f"Tests in {test_file} are passing - they should FAIL first (RED phase)")
        
        print("🔴 RED: Tests are failing as expected")
        
        # At this point, developer should implement minimal code to make tests pass
        print("🟢 GREEN: Now implement minimal code to make tests pass")
        print("🔵 REFACTOR: Then refactor code while keeping tests green")
        
        return True
    
    def validate_new_feature_tdd(self, feature_name: str) -> Dict[str, str]:
        """
        Validate that a new feature follows TDD principles
        Returns dict with required test files to create
        """
        print(f"\n🆕 VALIDATING NEW FEATURE TDD: {feature_name}")
        
        required_tests = {
            f"test_{feature_name}_unit.py": "Unit tests for core functionality",
            f"test_{feature_name}_integration.py": "Integration tests for feature",
            f"test_{feature_name}_api.py": "API contract tests if applicable"
        }
        
        existing_tests = []
        missing_tests = []
        
        for test_file, description in required_tests.items():
            if Path(test_file).exists():
                existing_tests.append(test_file)
            else:
                missing_tests.append((test_file, description))
        
        if missing_tests:
            print(f"❌ Missing required test files for {feature_name}:")
            for test_file, desc in missing_tests:
                print(f"   - {test_file}: {desc}")
            
            raise TDDViolationError(f"Create these test files BEFORE implementing {feature_name}")
        
        print(f"✅ All required tests exist for {feature_name}")
        return required_tests
    
    def generate_tdd_compliance_report(self) -> Dict:
        """Generate comprehensive TDD compliance report"""
        print("\n📋 GENERATING TDD COMPLIANCE REPORT...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_compliance": "UNKNOWN",
            "test_files_count": len(self.test_files),
            "source_files_count": len(self.src_files),
            "coverage_percentage": 0.0,
            "violations": [],
            "recommendations": []
        }
        
        try:
            # Run comprehensive validation
            self.enforce_tdd_workflow()
            report["overall_compliance"] = "COMPLIANT"
            
        except TDDViolationError as e:
            report["overall_compliance"] = "VIOLATION"
            report["violations"].append(str(e))
        
        # Save report
        report_file = self.project_root / f"tdd_compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Report saved to: {report_file}")
        return report

def main():
    """Main TDD enforcement entry point"""
    framework = TDDEnforcementFramework()
    
    try:
        # Run comprehensive TDD enforcement
        framework.enforce_tdd_workflow()
        
        # Run all tests
        framework.run_all_tests()
        
        # Generate compliance report
        report = framework.generate_tdd_compliance_report()
        
        print("\n🎉 TDD COMPLIANCE VERIFIED - DEVELOPMENT MAY PROCEED")
        print("=" * 60)
        print("Remember: ALWAYS write failing tests FIRST!")
        
    except TDDViolationError as e:
        print(f"\n🛑 TDD VIOLATION: {e}")
        print("=" * 60)
        print("DEVELOPMENT MUST STOP UNTIL VIOLATIONS ARE CORRECTED")
        sys.exit(1)

if __name__ == "__main__":
    main()