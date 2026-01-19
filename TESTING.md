# Testing Documentation

## Overview

Stage 4 has **66 unit tests** covering all core functionality:
- Schema validation (12 tests)
- Evidence verification (14 tests)
- Guardrail rules (21 tests)
- Idempotency (10 tests)
- Integration (9 tests via runner)

All tests pass and can run without LLM (no API key required).

---

## Quick Start

### Run All Tests

```bash
cd /Users/scopetech/Deal-Intelligence
python3 -m pytest tests/ -v
```

**Expected Output:**
```
========================= 66 passed in 0.30s =========================
```

### Run Specific Test File

```bash
# Guardrail rules
pytest tests/test_guardrails.py -v

# Evidence verification
pytest tests/test_evidence_verifier.py -v

# Schema validation
pytest tests/test_schema_validation.py -v

# Idempotency
pytest tests/test_idempotency.py -v
```

### Run Specific Test

```bash
pytest tests/test_guardrails.py::TestWriteoffDetection::test_write_off_detected -v
```

---

## Test Structure

### Test Organization

```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration (path setup)
├── test_schema_validation.py
├── test_evidence_verifier.py
├── test_guardrails.py
└── test_idempotency.py
```

### Test Configuration (`conftest.py`)

Sets up Python path to import `src/` modules:

```python
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))
```

---

## Test Suites

### 1. Schema Validation (`test_schema_validation.py`)

**Purpose:** Ensure outputs conform to JSON Schema contract.

**Tests:**
- ✅ Minimal valid output passes
- ✅ Missing required fields fail
- ✅ Invalid enum values fail
- ✅ Confidence out of range fails
- ✅ Empty evidence text fails
- ✅ Valid signals pass validation

**Key Test:**

```python
def test_minimal_valid_output_passes():
    output = create_minimal_valid_output(...)
    is_valid, errors = validate_stage4_output(output)
    assert is_valid
```

**Coverage:** All required fields, enum values, confidence ranges, nested structures.

---

### 2. Evidence Verification (`test_evidence_verifier.py`)

**Purpose:** Validate evidence checking prevents hallucinations.

**Test Categories:**

#### Evidence Existence

- ✅ Exact match evidence passes
- ✅ Case-insensitive matching works
- ✅ Whitespace normalization works
- ✅ Non-existent evidence rejected
- ✅ Partial word matching works

#### Signal Verification

- ✅ Signals with valid evidence pass
- ✅ Signals without evidence rejected
- ✅ Hallucinated evidence rejected

#### Explicit vs Inferred

- ✅ "write off" classified as explicit
- ✅ "defected" classified as explicit
- ✅ "needs love" classified as implicit
- ✅ "easy fix" classified as implicit

**Key Test:**

```python
def test_signal_with_hallucinated_evidence_rejected():
    signal = {
        "evidence_text": "this evidence does not exist",
        ...
    }
    original = "Perfect condition, no issues."
    result = verify_single_signal(signal, original)
    assert result is None  # Rejected
```

**Coverage:** Evidence matching, verification level classification, confidence adjustment.

---

### 3. Guardrail Rules (`test_guardrails.py`)

**Purpose:** Ensure guardrails detect high-risk patterns reliably.

**Test Categories:**

#### Write-Off Detection

- ✅ `write off` detected
- ✅ `written off` detected
- ✅ `repairable writeoff` detected
- ✅ `salvage` detected

#### Defect Detection

- ✅ `defected` detected
- ✅ `defect` detected
- ✅ `unregistered` detected
- ✅ `no rego` detected

#### Mechanical Issues

- ✅ `not running` detected
- ✅ `overheating` detected
- ✅ `engine knock` detected
- ✅ `head gasket` detected

#### Performance Mods

- ✅ `stage 2` detected
- ✅ `E85` detected
- ✅ `tuned` detected
- ✅ `turbo swap` detected
- ✅ `track car` detected

#### Clean Descriptions

- ✅ Clean text produces no false positives
- ✅ Similar words don't trigger false positives

**Key Test:**

```python
def test_write_off_detected():
    text = normalize_text("Car", "This is a write off.")
    signals = run_guardrails(text)
    assert any(s["type"] == "writeoff" for s in signals["accident_history"])
```

**Coverage:** All rule patterns, evidence extraction, signal properties (verified, high confidence).

---

### 4. Idempotency (`test_idempotency.py`)

**Purpose:** Ensure pipeline produces consistent outputs.

**Test Categories:**

#### Guardrail Idempotency

- ✅ Same input → same output
- ✅ Multiple runs → identical results
- ✅ Signal types stable across runs

#### Pipeline Idempotency

- ✅ Pipeline with skip_llm produces stable output
- ✅ Guardrails-only mode stable

#### Text Normalization

- ✅ Normalize text idempotent
- ✅ Whitespace handling stable

#### Derived Fields

- ✅ Risk level stable
- ✅ Mods risk level stable

**Key Test:**

```python
def test_pipeline_skip_llm_idempotent():
    result1 = run_stage4(listing, skip_llm=True)
    result2 = run_stage4(listing, skip_llm=True)
    assert result1["payload"]["signals"] == result2["payload"]["signals"]
```

**Coverage:** Text prep, guardrails, pipeline, derived fields, snapshot ID handling.

---

## Integration Testing

### Quick Test Script

```bash
python3 quick_test.py
```

**What it tests:**
- Full pipeline execution
- Guardrail detection on sample listing
- Risk level computation
- Signal output structure

**Sample output:**
```
✅ Pipeline completed successfully!
📊 Results Summary:
   Risk Level: high
   Mods Risk: high
🚨 Detected Signals:
   legality: defected (high)
   mods_performance: stage_2_or_higher (high)
```

---

## Notebook Testing

### POC Notebook (`notebooks/stage4_poc.ipynb`)

Interactive testing with step-by-step execution:

1. **Setup** - Import modules
2. **Load Data** - Sample listings
3. **Text Prep** - Normalize and split
4. **Guardrails** - Pattern detection
5. **Schema Validation** - Output validation
6. **Full Pipeline** - End-to-end execution
7. **Batch Processing** - Multiple listings
8. **Idempotency** - Consistency check

**To use:**
```bash
jupyter notebook notebooks/stage4_poc.ipynb
```

---

## Test Data

### Sample Listings

Located in `data_samples/raw_listing_examples/test_listingparse.json`

If file not found, notebook creates test data:
- High-risk listing (stage 2, defected, E85)
- Clean listing (no issues)
- Mechanical issues listing (not running, overheating)

### Test Fixtures

No external fixtures required - all tests are self-contained with inline test data.

---

## Running Tests

### Prerequisites

```bash
pip install -r requirements.txt
# Installs: pytest, jsonschema, pydantic, python-dotenv
```

### Command Options

```bash
# Verbose output
pytest tests/ -v

# Show print statements
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -x

# Show coverage (if pytest-cov installed)
pytest tests/ --cov=src

# Run specific pattern
pytest tests/ -k "guardrail"

# Parallel execution (if pytest-xdist installed)
pytest tests/ -n auto
```

---

## Test Coverage

### What's Tested

✅ **Schema validation** - All required fields, enums, types  
✅ **Evidence verification** - Exact matches, case-insensitivity, rejection logic  
✅ **Guardrail rules** - All high-risk patterns (write-off, defected, stage 2, etc.)  
✅ **Idempotency** - Text prep, guardrails, pipeline, derived fields  
✅ **Error handling** - Validation failures, missing fields, invalid enums  

### What's Not Tested (Future)

- LLM integration (requires API key, slow)
- Real-world listing data (manual testing)
- Performance benchmarks
- Concurrent processing

---

## Writing New Tests

### Test Template

```python
import pytest
from stage4.module_name import function_name

class TestFeatureName:
    def test_specific_behavior(self):
        """Test description."""
        # Arrange
        input_data = {...}
        
        # Act
        result = function_name(input_data)
        
        # Assert
        assert result == expected
```

### Best Practices

1. **One assertion per test** - Clear failure messages
2. **Descriptive names** - `test_write_off_detected` not `test_1`
3. **Isolated tests** - No shared state between tests
4. **Fast tests** - No API calls or file I/O if possible
5. **Test edge cases** - Empty strings, None values, boundary conditions

### Example: Adding Guardrail Test

```python
def test_new_pattern_detected():
    """Test that new pattern X is detected."""
    text = normalize_text("Title", "Description with pattern X here.")
    signals = run_guardrails(text)
    
    # Find signal in appropriate category
    category_signals = signals["appropriate_category"]
    assert any(s["type"] == "expected_signal_type" for s in category_signals)
    
    # Verify signal properties
    signal = next(s for s in category_signals if s["type"] == "expected_signal_type")
    assert signal["severity"] == "expected_severity"
    assert signal["verification_level"] == "verified"
    assert signal["confidence"] == 0.95
```

---

## Continuous Integration

### Recommended CI Setup

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```

**Requirements:**
- Python 3.9+
- All dependencies from `requirements.txt`
- No external services (tests are isolated)

---

## Debugging Failed Tests

### Common Issues

1. **Import Errors**
   ```bash
   # Check PYTHONPATH
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

2. **Schema Validation Failures**
   ```python
   # Print errors
   is_valid, errors = validate_stage4_output(output)
   if not is_valid:
       for error in errors:
           print(error)
   ```

3. **Evidence Not Found**
   ```python
   # Debug evidence matching
   from stage4.text_prep import check_evidence_exists
   print(check_evidence_exists(evidence, original_text))
   ```

### Running with Debugger

```python
import pdb; pdb.set_trace()  # Add breakpoint
```

Or use pytest debugging:
```bash
pytest tests/ --pdb  # Drop into debugger on failure
```

---

## Performance Testing

### Benchmarking (Manual)

```python
import time

start = time.time()
for _ in range(100):
    run_stage4(listing, skip_llm=True)
duration = time.time() - start
print(f"Average: {duration/100*1000:.1f}ms per listing")
```

**Expected:** < 20ms per listing (guardrails-only)

---

## Related Documentation

- **Architecture:** See `ARCHITECTURE.md`
- **Code Docs:** See `CODE_DOCUMENTATION.md`
- **Contributing:** See `CONTRIBUTING.md`
