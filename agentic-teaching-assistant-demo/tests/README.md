# AgenticTA Test Suite

## Quick Start

```bash
# Fast feedback loop (unit tests only, ~5s)
make test

# Full validation (unit + integration, ~17s)
make test-all

# With coverage report
make test-cov
```

## Test Organization

### Unit Tests (Always Run)
- ✅ **Fast** (~5 seconds)
- ✅ **No external dependencies**
- ✅ **Reliable** (well-mocked)

Files:
- `test_llm_client.py` - LLM module tests
- `test_errors.py` - Error handling tests
- `test_user_cleanup.py` - User data cleanup tests
- `test_chapter_generation.py` - Chapter parsing tests

### Integration Tests (Optional)
- ⏱️ **Slower** (~12 seconds additional)
- 🔗 **Tests real workflows**
- 🎯 **Use for pre-release validation**

Files:
- `test_integration.py` - Full pipeline tests

Marked with: `@pytest.mark.integration`

### Slow Tests (Optional)
- 🐌 **Slowest** (50+ PDFs processing)
- 📊 **Load/stress testing**
- 🚀 **Use before major releases**

Marked with: `@pytest.mark.slow`

---

## Development Workflow

### 🚀 Rapid Development Mode
```bash
# Only run fast unit tests
make test

# Or even faster - just LLM module
make test-llm
```

**Use when:**
- Actively coding/iterating
- Testing specific functions
- Need quick feedback (<5s)

---

### 🔍 Pre-Commit Mode
```bash
# Run unit tests only
make test
```

**Use when:**
- About to commit changes
- Changed specific modules
- Want reasonable confidence

---

### 🎯 Pre-Release Mode
```bash
# Full test suite
make test-all

# Or with coverage
make test-cov
```

**Use when:**
- Before pushing to main
- Before deploying
- Before creating PR

---

## Running Specific Tests

```bash
# Inside container (make shell)
pytest tests/test_llm_client.py -v           # One file
pytest tests/test_llm_client.py::test_name   # One test
pytest -m "not slow"                          # Skip slow tests
pytest -k "llm"                               # Tests matching "llm"
```

---

## Test Markers

We use pytest markers to categorize tests:

```python
@pytest.mark.integration  # Integration test (slower)
@pytest.mark.slow         # Very slow test (load testing)
@pytest.mark.unit         # Unit test (default, fast)
```

---

## Adding New Tests

### For New Features
**Add unit tests** (fast, always run):
```python
# tests/test_my_feature.py
def test_my_feature():
    """Fast, isolated test."""
    assert my_function() == expected
```

### For Bug Fixes
**Add regression test**:
```python
def test_bug_123_fixed():
    """Ensure bug #123 doesn't come back."""
    # Test the specific scenario that was broken
```

### For Full Workflows
**Add integration test** (opt-in):
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow():
    """Test complete user journey."""
    # This runs only with `make test-all`
```

---

## Disabling Tests Temporarily

Sometimes during rapid refactoring, you want to temporarily disable tests:

```python
@pytest.mark.skip(reason="Refactoring in progress")
def test_old_behavior():
    pass

# Or conditionally
@pytest.mark.skipif(FEATURE_FLAG, reason="Feature disabled")
def test_new_feature():
    pass
```

---

## CI/CD Recommendations

```yaml
# Fast PR checks (on every commit)
- run: make test        # Unit tests only

# Nightly builds (full validation)
- run: make test-all    # All tests

# Release pipeline
- run: make test-cov    # With coverage report
```

---

## Current Test Stats

- **Total Tests**: 35
- **Unit Tests**: 22 (fast, ~5s)
- **Integration Tests**: 13 (slower, +12s)
- **Coverage**: 34%
- **Run Time**: 5s (unit) / 17s (all)

---

## Philosophy

> "Tests are tools, not rules. Use what helps, skip what slows you down."

- **Early stage**: Favor unit tests, skip integration
- **Stable features**: Add integration tests for confidence
- **Before release**: Run everything

You're in control! 🎮
