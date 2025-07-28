# Branch Protection Configuration

This document outlines the recommended branch protection rules for the AgentWriter repository.

## 🛡️ Master Branch Protection Rules

### Required Status Checks
```yaml
# These checks MUST pass before merging
required_status_checks:
  - "validate"           # Code syntax and basic validation
  - "test (3.10)"       # Unit tests on primary Python version
  - "quality"           # Code quality checks
  
# These are advisory - can be overridden by reviewers
advisory_status_checks:
  - "test (3.9)"        # Unit tests on older Python
  - "test (3.11)"       # Unit tests on newer Python  
  - "e2e-smoke"         # Basic E2E functionality
  - "e2e-full"          # Complete E2E suite
```

### Review Requirements
```yaml
required_reviews: 1
dismiss_stale_reviews: true
require_code_owner_reviews: false  # Set to true when CODEOWNERS exists
restrict_dismissals: false

# Allow these roles to override status checks
bypass_pull_request_allowances:
  - repository_admins
  - maintain_role_users  # For flaky test scenarios
```

### Additional Protections
```yaml
enforce_admins: false              # Admins can emergency merge
allow_force_pushes: false          # No force pushes to master
allow_deletions: false             # Can't delete master branch
require_linear_history: false      # Allow merge commits
require_signed_commits: false      # Optional for this project
```

## 🔧 Implementation Guide

### Option 1: GitHub UI Configuration
1. Go to **Settings** → **Branches** 
2. Click **Add rule** for `master` branch
3. Configure settings based on the rules above
4. Enable **"Restrict pushes that create files"** if needed

### Option 2: GitHub CLI Configuration
```bash
# Install GitHub CLI if not already installed
gh auth login

# Apply branch protection (requires admin permissions)
gh api repos/hoangvu71/AgentWriter/branches/master/protection \
  --method PUT \
  --input - << 'EOF'
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      {"context": "validate"},
      {"context": "test (3.10)"},
      {"context": "quality"}
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
```

### Option 3: Terraform Configuration
```hcl
resource "github_branch_protection" "master" {
  repository_id = "AgentWriter"
  pattern      = "master"

  required_status_checks {
    strict = true
    checks = [
      "validate",
      "test (3.10)", 
      "quality"
    ]
  }

  required_pull_request_reviews {
    required_approving_review_count = 1
    dismiss_stale_reviews          = true
  }

  enforce_admins = false
}
```

## 🚦 Merge Decision Matrix

| Test Status | Required Review | Action |
|------------|----------------|---------|
| ✅ All pass | ✅ Approved | **AUTO-MERGE** |
| ✅ Required pass, ⚠️ Advisory fail | ✅ Approved | **REVIEWER DISCRETION** |
| ❌ Required fail | ✅ Approved | **BLOCK MERGE** |
| ✅ All pass | ❌ No review | **BLOCK MERGE** |
| ⚠️ Flaky tests | ✅ Approved | **REVIEWER OVERRIDE** |

## 🎯 Test Categories

### 🟢 **Required Tests** (Must Pass)
- **validate**: Syntax, imports, basic code structure
- **test (3.10)**: Unit tests on primary Python version
- **quality**: Linting, formatting, basic security

**Rationale**: These represent core functionality that should never be broken.

### 🟡 **Advisory Tests** (Can Be Overridden)
- **test (3.9, 3.11)**: Compatibility testing on other Python versions
- **e2e-smoke**: Basic application startup and health
- **e2e-full**: Complete end-to-end testing including browser automation
- **security**: Comprehensive security scanning
- **docs**: Documentation validation

**Rationale**: These provide additional confidence but may be flaky or environmental.

## 👥 Team Roles & Permissions

### 🧑‍💻 **Developers (Contributors)**
- Can create branches and PRs
- Cannot merge their own PRs
- Must fix required test failures
- Can request reviewer help for advisory test failures

### 👨‍💼 **Maintainers (Reviewers)**
- Can approve and merge PRs
- Can override advisory test failures
- Should document reasons for overrides
- Create follow-up issues for deferred fixes

### 🏗️ **Admins (Repository Owners)**
- Can bypass all protections in emergencies
- Should follow standard process except for critical fixes
- Can modify branch protection rules

## 📝 Best Practices

### For PR Authors:
1. **Test locally first**: `pytest tests/` before creating PR
2. **Fix required tests**: Don't rely on reviewer overrides
3. **Explain advisory failures**: Help reviewers understand context
4. **Keep PRs focused**: Smaller changes = easier reviews

### For Reviewers:
1. **Check test relevance**: Are failures related to the changes?
2. **Document overrides**: Explain why you merged despite failures
3. **Create follow-up issues**: Track deferred test fixes
4. **Provide guidance**: Help authors understand and fix issues

### For the Team:
1. **Monitor flaky tests**: Regular cleanup of unreliable tests
2. **Update protection rules**: Adjust based on experience
3. **Review metrics**: Track merge success rates and failure patterns
4. **Communicate changes**: Announce policy updates clearly

## 🔄 Continuous Improvement

This policy should be reviewed and updated based on:
- **Test reliability metrics**: Adjust required vs advisory based on flakiness
- **Team feedback**: Developer and reviewer experience
- **Incident analysis**: Learn from issues that made it to production
- **Tool evolution**: New testing capabilities and CI/CD improvements

---

**Remember**: The goal is **working software delivered efficiently**. Rules should help, not hinder productivity.