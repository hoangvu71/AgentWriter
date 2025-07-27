#!/usr/bin/env python3
"""
Install and configure pre-commit hooks for TDD enforcement
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr.strip() if e.stderr else str(e)}")
        return False

def check_git_repo():
    """Check if we're in a git repository"""
    try:
        subprocess.run(['git', 'rev-parse', '--git-dir'], 
                      check=True, capture_output=True, text=True)
        print("✅ Git repository detected")
        return True
    except subprocess.CalledProcessError:
        print("❌ Not in a git repository. Initialize git first:")
        print("   git init")
        return False

def install_pre_commit():
    """Install pre-commit package"""
    print("🚀 Installing Pre-commit Hooks for TDD Enforcement")
    print("=" * 60)
    
    # Check if pre-commit is already installed
    try:
        result = subprocess.run(['pre-commit', '--version'], 
                              capture_output=True, text=True)
        print(f"✅ pre-commit already installed: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        pass
    
    # Install pre-commit
    install_commands = [
        "pip install pre-commit",
        "pip install black isort flake8 mypy bandit"  # Ensure all tools are available
    ]
    
    for command in install_commands:
        if not run_command(command, f"Installing {command.split()[-1]}"):
            return False
    
    return True

def setup_git_hooks():
    """Install git hooks"""
    if not run_command("pre-commit install", "Installing pre-commit git hooks"):
        return False
    
    if not run_command("pre-commit install --hook-type pre-push", "Installing pre-push hooks"):
        return False
    
    return True

def test_hooks():
    """Test the installed hooks"""
    print("\n🧪 Testing Pre-commit Hooks")
    print("-" * 40)
    
    # Run hooks on all files to test
    if not run_command("pre-commit run --all-files", "Testing hooks on all files"):
        print("⚠️  Some hooks may have made changes or found issues")
        print("   This is normal for the first run")
        print("   Review the changes and commit them if acceptable")
        return False
    
    print("✅ All hooks passed successfully")
    return True

def create_tdd_commit_msg_template():
    """Create commit message template that enforces TDD documentation"""
    template_content = """# TDD Commit Message Template
# 
# Subject line: Brief description of changes
# 
# TDD Compliance Checklist:
# [ ] Tests were written BEFORE implementation (RED phase)
# [ ] Minimal code written to make tests pass (GREEN phase) 
# [ ] Code refactored while keeping tests passing (REFACTOR phase)
# [ ] All tests pass with coverage >= 80%
# [ ] No code exists without corresponding tests
# 
# Detailed description:
# - What was implemented?
# - Which tests were written first?
# - How does this follow TDD principles?
# 
# Breaking changes: None / Describe any breaking changes
# 
# Related issues: Fixes #123, Closes #456
"""
    
    template_path = Path('.gitmessage')
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    # Configure git to use the template
    run_command("git config commit.template .gitmessage", 
                "Setting up TDD commit message template")
    
    print("✅ TDD commit message template created")
    print("   Use 'git commit' (without -m) to use the template")

def main():
    """Main installation process"""
    print("🎯 TDD Pre-commit Hooks Installation")
    print("=" * 60)
    
    # Check prerequisites
    if not check_git_repo():
        sys.exit(1)
    
    # Install pre-commit
    if not install_pre_commit():
        print("❌ Failed to install pre-commit")
        sys.exit(1)
    
    # Set up git hooks
    if not setup_git_hooks():
        print("❌ Failed to set up git hooks")
        sys.exit(1)
    
    # Create TDD commit template
    create_tdd_commit_msg_template()
    
    # Test hooks
    print("\n🧪 TESTING HOOKS")
    print("-" * 40)
    test_result = test_hooks()
    
    print("\n🎉 INSTALLATION COMPLETE")
    print("=" * 60)
    print("✅ Pre-commit hooks installed successfully")
    print("✅ TDD enforcement is now active")
    print("✅ All commits will be validated for TDD compliance")
    
    print("\n📋 WHAT HAPPENS NOW:")
    print("-" * 40)
    print("• Every commit will run TDD compliance checks")
    print("• Code formatting and linting will be automatic")
    print("• Tests must pass before commits are allowed")
    print("• Security scans will detect hardcoded credentials")
    print("• Missing test files will block commits")
    
    print("\n🔄 TDD WORKFLOW REMINDER:")
    print("-" * 40)
    print("1. RED: Write failing tests first")
    print("2. GREEN: Write minimal code to pass tests")
    print("3. REFACTOR: Improve code while keeping tests passing")
    print("4. COMMIT: Hooks will validate TDD compliance")
    
    print("\n⚠️  TROUBLESHOOTING:")
    print("-" * 40)
    print("• If hooks fail: Review the output and fix issues")
    print("• To skip hooks (emergency): git commit --no-verify")
    print("• To update hooks: pre-commit autoupdate")
    print("• To run hooks manually: pre-commit run --all-files")
    
    if not test_result:
        print("\n🔍 NEXT STEPS:")
        print("-" * 40)
        print("1. Review any changes made by the hooks")
        print("2. Add and commit the changes: git add . && git commit -m 'Setup TDD pre-commit hooks'")
        print("3. Future commits will be automatically validated")

if __name__ == "__main__":
    main()