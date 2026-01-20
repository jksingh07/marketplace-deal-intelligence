# Token Usage Tracking

## Overview

The system now tracks LLM token usage in two ways:

1. **Logging**: Token usage is logged at INFO level for each LLM call
2. **Metrics**: Token usage is aggregated in the metrics system for reporting

## How Token Tracking Works

### 1. Logging (Real-time)

Token usage is logged to the standard logger with INFO level. You'll see messages like:

```
Token usage: prompt=1234, completion=567, total=1801
```

This appears in your logs for every LLM API call.

### 2. Metrics (Aggregated)

Token usage is tracked in the metrics system as a histogram metric: `stage4.tokens_used`

## Where to See Token Usage

### Option 1: Quick Utility Script (Easiest)

Run the utility script from the project root:

```bash
python check_token_usage.py
```

This will show you:
- Total LLM calls
- Total tokens used
- Average tokens per call
- Min/Max/Median/P95/P99 statistics
- Related metrics (extractions, LLM usage rate)

### Option 2: In Your Code/Notebook

### In Code

```python
from common.metrics import get_metrics

# Get metrics collector
metrics = get_metrics()

# Get token usage statistics
token_stats = metrics.get_histogram_stats("stage4.tokens_used")

print(f"Total LLM calls: {token_stats['count']}")
print(f"Average tokens per call: {token_stats['avg']:.0f}")
print(f"Min tokens: {token_stats['min']}")
print(f"Max tokens: {token_stats['max']}")
print(f"P50 (median): {token_stats['p50']:.0f}")
print(f"P95: {token_stats['p95']:.0f}")
print(f"P99: {token_stats['p99']:.0f}")
```

### Get All Metrics

```python
from common.metrics import get_metrics

metrics = get_metrics()
all_metrics = metrics.get_all_metrics()

# Access token histogram
token_histogram = all_metrics['histograms'].get('stage4.tokens_used', {})
print(token_histogram)
```

### Example: Track Token Usage in a Batch

```python
from stage4.runner import run_stage4
from common.metrics import get_metrics

# Process some listings
listings = [...]  # your listings
for listing in listings:
    result = run_stage4(listing)

# After processing, check token usage
metrics = get_metrics()
token_stats = metrics.get_histogram_stats("stage4.tokens_used")

print(f"\nToken Usage Summary:")
print(f"  Total calls: {token_stats['count']}")
print(f"  Total tokens: {token_stats['count'] * token_stats['avg']:.0f}")
print(f"  Average per call: {token_stats['avg']:.0f}")
print(f"  Min: {token_stats['min']}")
print(f"  Max: {token_stats['max']}")
```

## Metrics Available

The following metrics are tracked for token usage:

- **`stage4.tokens_used`** (histogram): Total tokens used per LLM call
  - Includes prompt tokens + completion tokens
  - Tracked only when LLM is used (not in guardrails-only mode)

## Related Metrics

Other related metrics you might want to check:

- **`stage4.extractions_total`**: Total number of extractions
- **`stage4.extractions_with_llm`**: Number of extractions that used LLM
- **`stage4.extractions_guardrails_only`**: Number of guardrails-only extractions
- **`stage4.llm_latency`**: LLM call latency in milliseconds

## Quick Check in Notebook

Add this cell to your notebook to see token usage and costs:

```python
from common.metrics import get_metrics
from common.cost_tracker import get_cost_tracker

metrics = get_metrics()
cost_tracker = get_cost_tracker()
token_stats = metrics.get_histogram_stats("stage4.tokens_used")
cost_summary = cost_tracker.get_cost_summary()

if token_stats.get("count", 0) > 0:
    print(f"📊 Token Usage:")
    print(f"   Total calls: {token_stats['count']}")
    print(f"   Total tokens: {token_stats['count'] * token_stats['avg']:,.0f}")
    print(f"   Average per call: {token_stats['avg']:,.0f}")
    print(f"   Min: {token_stats['min']:,.0f} | Max: {token_stats['max']:,.0f}")
    print(f"   P95: {token_stats['p95']:,.0f} | P99: {token_stats['p99']:,.0f}")
    
    # Show costs
    if cost_summary["total_cost_usd"] > 0:
        print(f"\n💰 Cost Summary:")
        print(f"   Total cost: ${cost_summary['total_cost_usd']:.4f}")
        if cost_summary["model_breakdown"]:
            for model, breakdown in cost_summary["model_breakdown"].items():
                print(f"   {model}: ${breakdown['total_cost']:.4f} ({breakdown['calls']} calls)")
else:
    print("⚠️  No token usage data yet. Run some listings first.")
```

## Cumulative Usage (All Sessions)

To see **total usage across all notebook runs** (not just current session):

### Option 1: Human-Readable Summary Report (Recommended)

A markdown summary report is automatically generated at `.metrics/USAGE_SUMMARY.md`:

```bash
# View the report
cat .metrics/USAGE_SUMMARY.md

# Or regenerate it manually
python generate_usage_report.py
```

**The report includes**:
- Overall summary (total calls, tokens, costs)
- Cost breakdown by model
- Recent usage history (last 10 calls)
- Cost analysis (averages, cost per 1K tokens)
- Time range (first and last usage)

**Auto-updates**: The report is automatically regenerated after each LLM call.

### Option 2: Utility Script

```bash
python view_cumulative_usage.py
```

### Option 3: In Notebook

```python
from common.persistent_cost_tracker import get_persistent_tracker

persistent_tracker = get_persistent_tracker()
cumulative_stats = persistent_tracker.get_cumulative_stats()

print(f"Total calls (all time): {cumulative_stats['total_calls']:,}")
print(f"Total cost (all time): ${cumulative_stats['total_cost_usd']:.4f}")
```

**Storage**: Cumulative data is saved to `.metrics/usage_history.json` and persists across:
- Notebook kernel restarts
- Different notebook sessions
- Different Python processes

## Notes

- Token usage is only tracked when LLM is actually called (not in `skip_llm=True` mode)
- Token counts include both prompt and completion tokens
- **Session metrics** are stored in memory and reset when the process restarts
- **Cumulative metrics** are stored in `.metrics/usage_history.json` and persist forever
- In production, you'd typically export these metrics to Prometheus, DataDog, etc.
- **Real-time logging**: Check your console/logs for `Token usage: prompt=X, completion=Y, total=Z, model=MODEL` messages