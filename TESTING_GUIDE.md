# Stage 4 Testing Guide

## Quick Start

### Option 1: Run the Quick Test Script (Fastest)

```bash
python3 quick_test.py
```

This demonstrates guardrails-only mode (no LLM required) with a sample listing.

### Option 2: Run Full Test Suite

```bash
python3 -m pytest tests/ -v
```

All 66 tests should pass.

### Option 3: Use the Jupyter Notebook

```bash
jupyter notebook notebooks/stage4_poc.ipynb
```

Interactive demo with step-by-step pipeline execution.

---

## Testing Methods

### 1. Unit Tests (Automated)

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_guardrails.py -v

# Run specific test
pytest tests/test_guardrails.py::TestWriteoffDetection::test_write_off_detected -v
```

**Test Coverage:**
- `test_schema_validation.py` - 12 tests for JSON Schema validation
- `test_evidence_verifier.py` - 14 tests for evidence verification
- `test_guardrails.py` - 21 tests for guardrail rule detection
- `test_idempotency.py` - 10 tests for pipeline consistency

### 2. Quick Test Script (Manual)

```bash
python3 quick_test.py
```

Tests guardrails on a sample listing with:
- Stage 2 tune
- Defected status
- E85 compatibility
- Track use
- Urgent sale signals

### 3. Python REPL (Interactive)

```python
import sys
sys.path.insert(0, "src")

from stage4.runner import run_stage4

# Test with your own listing
listing = {
    "listing_id": "test_123",
    "title": "Your Title Here",
    "description": "Your description here..."
}

result = run_stage4(listing, skip_llm=True, validate=True)
print(result['payload']['risk_level_overall'])
print(result['payload']['signals'])
```

### 4. Notebook (Step-by-Step)

Open `notebooks/stage4_poc.ipynb` in Jupyter to see:
- Text preparation
- Guardrail detection
- Schema validation
- Full pipeline execution
- Batch processing
- Idempotency checks

---

## What Gets Tested

### Guardrail Rules (Always Active)

These patterns are detected **without LLM**:

**High-Risk Signals:**
- ✅ `write off` / `written off` → `writeoff`
- ✅ `defected` / `defect` → `defected`
- ✅ `not running` / `won't start` → `not_running`
- ✅ `stage 2` / `stage2` → `stage_2_or_higher`
- ✅ `E85` / `flex fuel` → `e85_flex_fuel`
- ✅ `track car` / `track use` → `track_use`
- ✅ `salvage` → `salvage_title`
- ✅ `overheating` → `engine_overheating`

**Medium-Risk Signals:**
- ✅ `tuned` / `tune` → `tuned`
- ✅ `firm price` → `firm_price`
- ✅ `no rego` → `no_rego`

### Schema Validation

Every output is validated against `contracts/stage4_description_intel.schema.json`:
- Required fields present
- Enum values valid
- Confidence scores in [0, 1]
- Evidence text non-empty

### Evidence Verification

All signals must have `evidence_text` that exists verbatim in the original text.
- ✅ Exact matches pass
- ✅ Case-insensitive matching works
- ❌ Hallucinated evidence rejected

### Idempotency

Running the same listing multiple times produces identical results:
- Same signal types
- Same risk levels
- Same derived fields

---

## Testing with LLM (Optional)

To test with LLM extraction:

1. **Set API Key:**
   ```bash
   export OPENAI_API_KEY="sk-your-key-here"
   ```

2. **Run with LLM:**
   ```python
   result = run_stage4(listing, skip_llm=False, validate=True)
   ```

3. **LLM provides:**
   - Richer signal extraction (cosmetic issues, maintenance claims)
   - Follow-up questions
   - Missing info detection
   - More nuanced verification levels

**Note:** Guardrails still run even with LLM enabled - they add signals but never remove them.

---

## Expected Test Outputs

### Guardrails-Only Mode (`skip_llm=True`)

```json
{
  "risk_level_overall": "high",
  "mods_risk_level": "high",
  "signals": {
    "legality": [{"type": "defected", "severity": "high", ...}],
    "mods_performance": [{"type": "stage_2_or_higher", ...}],
    ...
  }
}
```

### With LLM (`skip_llm=False`)

Additional fields populated:
- `maintenance.claims` - Service history claims
- `follow_up_questions` - Buyer questions to ask
- `missing_info` - What information is absent
- More detailed `cosmetic_issues` and `seller_behavior`

---

## Troubleshooting

### Import Errors

```bash
# Make sure src is in path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Missing Dependencies

```bash
pip install -r requirements.txt
```

### Schema Validation Failures

Check:
- All required fields present
- Enum values match schema exactly
- Confidence in [0, 1]
- Evidence text non-empty

---

## Next Steps

1. ✅ Run `quick_test.py` to see it in action
2. ✅ Run `pytest tests/ -v` to verify all tests pass
3. ✅ Open `notebooks/stage4_poc.ipynb` for interactive exploration
4. ✅ Try your own listing data with `run_stage4()`
