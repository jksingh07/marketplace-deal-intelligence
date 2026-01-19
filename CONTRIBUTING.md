# Contributing Guide

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- (Optional) OpenAI API key for LLM testing

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Deal-Intelligence
   ```

2. **Create and activate virtual environment:**
   ```bash
   # Create virtual environment
   python3 -m venv .venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source .venv/bin/activate
   # On Windows:
   # .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Verify installation:**
   ```bash
   python quick_test.py
   # Should run successfully
   ```

5. **Run tests:**
   ```bash
   pytest tests/ -v
   # All 66 tests should pass
   ```

**Note:** After activating the virtual environment, you can use `python` and `pytest` directly (no need for `python3` or `python3 -m pytest`).

---

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

Follow the existing code style:
- **PEP 8** formatting
- **Type hints** on all functions
- **Docstrings** for all public functions/classes
- **Snake_case** for variables/functions
- **PascalCase** for classes

### 3. Test Your Changes

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_guardrails.py -v

# Run quick test script
python3 quick_test.py
```

**Ensure all tests pass before committing.**

### 4. Update Documentation

If you add features or change behavior:
- Update `CODE_DOCUMENTATION.md` if adding new modules/functions
- Update `ARCHITECTURE.md` if changing system design
- Update `TESTING.md` if adding new tests

### 5. Commit Changes

Use descriptive commit messages:

```bash
git commit -m "feat: add new guardrail rule for pattern X"
git commit -m "fix: correct evidence verification for case-insensitive matches"
git commit -m "docs: update CODE_DOCUMENTATION.md with new API"
```

**Commit message format:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `style:` - Formatting, no logic change

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Create a PR with:
- Description of changes
- Link to related issue (if any)
- Test results showing all tests pass

---

## Code Standards

### Python Style

Follow **PEP 8** with these guidelines:

```python
# Good
def extract_signals(text: str, category: str) -> List[Dict[str, Any]]:
    """Extract signals from text."""
    signals = []
    # ...
    return signals

# Bad
def extractSignals(text,category):  # No type hints, wrong naming
    signals=[]
    return signals
```

### Type Hints

Always include type hints for Python 3.9 compatibility:

```python
# Use typing module (not | syntax)
from typing import Dict, List, Optional, Tuple

def example(
    text: str,
    optional: Optional[int] = None,
) -> Tuple[bool, List[str]]:
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is invalid
    """
```

---

## Adding New Features

### Adding Guardrail Rules

**Location:** `src/stage4/guardrails.py`

**Steps:**

1. **Add rule pattern:**
   ```python
   NEW_RULES = [
       (r'\bnew_pattern\b', 'signal_type', 'category', 'severity'),
   ]
   
   ALL_RULES = ALL_RULES + NEW_RULES
   ```

2. **Ensure signal type exists in schema:**
   - Check `contracts/stage4_description_intel.schema.json`
   - Add enum value if new type

3. **Add test:**
   ```python
   def test_new_pattern_detected():
       text = normalize_text("Title", "Description with new_pattern")
       signals = run_guardrails(text)
       assert any(s["type"] == "signal_type" for s in signals["category"])
   ```

4. **Run tests:**
   ```bash
   pytest tests/test_guardrails.py -v
   ```

### Adding Derived Fields

**Location:** `src/stage4/derived_fields.py`

**Steps:**

1. **Add computation function:**
   ```python
   def compute_new_field(signals: Dict, ...) -> str:
       """Compute new field from signals."""
       # Deterministic logic
       return "value"
   ```

2. **Add to `compute_derived_fields()`:**
   ```python
   return {
       ...
       "new_field": compute_new_field(signals, ...),
   }
   ```

3. **Update schema** if new field is required:
   - `contracts/stage4_description_intel.schema.json`

4. **Add test** for new computation

### Adding LLM Extraction Features

**Location:** `src/stage4/llm_extractor.py` and `stages/stage4_description_intel/prompts/extractor_prompt.md`

**Steps:**

1. **Update prompt template** with new extraction requirements
2. **Ensure enum values** match schema
3. **Test with sample listings** (manual testing required)
4. **Update documentation** with new signal types

---

## Testing Requirements

### Before Submitting PR

- ✅ All existing tests pass
- ✅ New features have tests
- ✅ No test warnings or errors
- ✅ Quick test script runs successfully

### Test Coverage

Aim for:
- **Guardrails:** Test all new patterns
- **Evidence verification:** Test edge cases
- **Schema validation:** Test new fields/enums
- **Idempotency:** Test new computations are deterministic

### Writing Good Tests

```python
def test_feature_behavior():
    """Clear description of what is tested."""
    # Arrange: Set up test data
    input_data = {...}
    expected = {...}
    
    # Act: Execute function
    result = function_under_test(input_data)
    
    # Assert: Verify result
    assert result == expected
    assert result["field"] == expected["field"]
```

---

## Code Review Guidelines

### What Reviewers Look For

1. **Functionality**
   - Does it work as intended?
   - Edge cases handled?
   - Error handling appropriate?

2. **Code Quality**
   - Follows style guide?
   - Type hints present?
   - Docstrings clear?

3. **Testing**
   - Tests cover new code?
   - All tests pass?
   - Tests are clear and maintainable?

4. **Documentation**
   - Code is self-documenting?
   - Docs updated if needed?
   - Comments explain "why" not "what"?

5. **Architecture**
   - Follows existing patterns?
   - Doesn't break contracts?
   - Idempotent if required?

---

## Breaking Changes

### Schema Changes

**DO NOT** change `contracts/stage4_description_intel.schema.json` without:
1. Discussion in PR
2. Version bump in `contracts/VERSION.md`
3. Update all dependent code
4. Migration plan if breaking

### API Changes

**DO NOT** change function signatures without:
1. Deprecation notice
2. Backward compatibility period
3. Update all call sites
4. Update documentation

---

## Project Structure

### Where to Put Code

```
src/
├── config.py              # Configuration constants
├── common/models.py       # Shared models/enums
└── stage4/
    ├── runner.py          # Main entry point
    ├── text_prep.py       # Text utilities
    ├── guardrails.py      # Rule-based detection
    ├── llm_extractor.py   # LLM integration
    ├── evidence_verifier.py
    ├── merger.py
    ├── derived_fields.py
    └── schema_validator.py
```

### Where to Put Tests

```
tests/
├── test_schema_validation.py
├── test_evidence_verifier.py
├── test_guardrails.py
└── test_idempotency.py
```

**Match test file to module name:** `test_guardrails.py` tests `guardrails.py`

---

## Questions?

- **Architecture questions:** See `ARCHITECTURE.md`
- **Code questions:** See `CODE_DOCUMENTATION.md`
- **Testing questions:** See `TESTING.md`
- **General questions:** Open an issue or discussion

---

## Golden Rules

When contributing, remember:

1. **Pure Functions** - Same inputs → same outputs
2. **Idempotent** - Re-running is safe
3. **Evidence Required** - All signals need evidence_text
4. **Schema-Valid** - Outputs always match contract
5. **Tested** - New code has tests

---

## Thank You!

Contributions are welcome and appreciated. Thank you for helping improve Stage 4 Description Intelligence!
