# Cost Tracking for LLM Usage

## Overview

The system now tracks **both token usage AND costs** for all LLM API calls. Costs are calculated based on:
- **Model used** (different models have different pricing)
- **Prompt tokens** (input tokens)
- **Completion tokens** (output tokens)

## How It Works

1. **Token Tracking**: Every LLM call records prompt tokens, completion tokens, and model name
2. **Cost Calculation**: Costs are calculated using current OpenAI pricing per model
3. **Aggregation**: Costs are aggregated by model and displayed in summaries

## Current Pricing (as of 2024)

The system includes pricing for common OpenAI models:

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| gpt-4o | $2.50 | $10.00 |
| gpt-4o-mini | $0.15 | $0.60 |
| gpt-4-turbo | $10.00 | $30.00 |
| gpt-4 | $30.00 | $60.00 |
| gpt-3.5-turbo | $0.50 | $1.50 |

*Note: Pricing is stored in `src/common/cost_calculator.py` and can be updated as OpenAI changes prices.*

## Viewing Costs

### In Your Notebook

```python
from common.cost_tracker import get_cost_tracker

cost_tracker = get_cost_tracker()
cost_summary = cost_tracker.get_cost_summary()

print(f"Total cost: ${cost_summary['total_cost_usd']:.4f}")
print(f"Total tokens: {cost_summary['total_tokens']:,}")

# Breakdown by model
for model, breakdown in cost_summary['model_breakdown'].items():
    print(f"{model}: ${breakdown['total_cost']:.4f} ({breakdown['calls']} calls)")
```

### Using the Utility Script

```bash
python check_token_usage.py
```

This now shows both token usage AND costs, including:
- Total cost across all calls
- Cost breakdown by model
- Average cost per call per model

## Cost Calculation Formula

For each API call:
```
Cost = (Prompt Tokens / 1,000,000) × Input Price + (Completion Tokens / 1,000,000) × Output Price
```

Example with `gpt-4o-mini`:
- 2,000 prompt tokens + 500 completion tokens
- Cost = (2,000 / 1,000,000) × $0.15 + (500 / 1,000,000) × $0.60
- Cost = $0.0003 + $0.0003 = **$0.0006**

## Features

✅ **Automatic tracking** - Costs are calculated automatically for every LLM call  
✅ **Model-specific pricing** - Different models use their correct pricing  
✅ **Aggregated reporting** - See totals and breakdowns by model  
✅ **Real-time updates** - Costs accumulate as you make more calls  
✅ **Unknown model handling** - Warns if a model doesn't have pricing data  

## Updating Pricing

If OpenAI changes pricing, update `src/common/cost_calculator.py`:

```python
OPENAI_PRICING = {
    "gpt-4o-mini": {
        "prompt": 0.15,      # Update these values
        "completion": 0.60
    },
    # ... other models
}
```

## Notes

- Costs are calculated in **USD**
- Pricing is per **1 million tokens**
- Costs are tracked per **Python process** (resets when kernel/process restarts)
- Unknown models show a warning but don't break the system
- Cost tracking works across your entire app (notebook, scripts, etc.)
