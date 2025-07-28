# Pull Request Template

## 📋 Description
Brief description of the changes in this PR.

## 🧪 Testing Checklist

**Before requesting review, please ensure:**

- [ ] All CI tests pass locally: `pytest tests/`
- [ ] New code has appropriate test coverage
- [ ] No new linting errors: `flake8 src/`
- [ ] Documentation updated if needed

**If tests are failing:**

- [ ] I have investigated the failing tests
- [ ] The failures are related to my changes (not pre-existing)
- [ ] I have fixed the test failures OR explained why they should be ignored

## 🔧 Test Failure Resolution

**If your PR has failing CI tests, please:**

1. **Check the CI failure details** in the Actions tab
2. **Run tests locally** to reproduce the issue
3. **Fix the underlying issue** that caused the test failure
4. **Update tests** if your change intentionally modifies behavior
5. **Ask for help** in comments if you're unsure about a failure

### Common Test Failure Types:

- **❌ Unit Test Failure**: Fix the code bug or update test expectations
- **⚠️ Flaky Test**: Comment explaining the intermittent nature, reviewer will decide
- **📦 Dependency Issue**: Update requirements.txt or installation instructions
- **🚀 E2E Timeout**: May need reviewer input on acceptable performance changes

## 🎯 Reviewer Notes

**For reviewers:**

- **✅ All tests passing**: Ready for standard review process
- **⚠️ Some tests failing**: 
  - Check if failures are related to PR changes
  - Determine if failures are acceptable (flaky tests, minor issues)
  - Guide author on fixes needed or approve with exceptions
- **❌ Many tests failing**: Likely needs author attention before review

### Reviewer Override Guidelines:

You may merge PRs with failing tests when:
- [ ] Failures are demonstrably flaky/environmental
- [ ] Failures are in non-critical test areas
- [ ] Core functionality is verified to work
- [ ] Follow-up issue is created to address failures

## 📝 Additional Notes

Add any additional context, screenshots, or information that would help reviewers understand and test your changes.

---

**Remember**: The goal is working software. Tests are there to help us, not block us unnecessarily. When in doubt, discuss in the PR comments!