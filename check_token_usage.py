#!/usr/bin/env python3
"""
Quick utility to check current token usage and costs from metrics.

Usage:
    python check_token_usage.py
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from common.metrics import get_metrics
from common.cost_tracker import get_cost_tracker


def print_token_usage():
    """Print current token usage statistics and costs."""
    metrics = get_metrics()
    cost_tracker = get_cost_tracker()
    
    token_stats = metrics.get_histogram_stats("stage4.tokens_used")
    cost_summary = cost_tracker.get_cost_summary()
    model_breakdown = cost_tracker.get_model_breakdown()
    
    print("=" * 70)
    print("📊 LLM Token Usage & Cost Statistics")
    print("=" * 70)
    
    if token_stats.get("count", 0) == 0:
        print("\n⚠️  No token usage data yet.")
        print("   Run some listings through the pipeline to see token usage.")
        print("\n   Example:")
        print("   ```python")
        print("   from stage4.runner import run_stage4")
        print("   result = run_stage4(listing)")
        print("   ```")
        return
    
    count = token_stats["count"]
    avg = token_stats["avg"]
    total_tokens = count * avg
    
    print(f"\n📈 Summary:")
    print(f"   Total LLM calls: {count}")
    print(f"   Total tokens used: {total_tokens:,.0f}")
    print(f"   Average per call: {avg:,.0f} tokens")
    
    # Cost information
    if cost_summary["total_cost_usd"] > 0:
        print(f"\n💰 Cost Summary:")
        print(f"   Total cost: ${cost_summary['total_cost_usd']:.4f}")
        print(f"   Total prompt tokens: {cost_summary['total_prompt_tokens']:,}")
        print(f"   Total completion tokens: {cost_summary['total_completion_tokens']:,}")
        
        if cost_summary["model_breakdown"]:
            print(f"\n   Cost by Model:")
            for model, breakdown in cost_summary["model_breakdown"].items():
                print(f"      {model}:")
                print(f"         Calls: {breakdown['calls']}")
                print(f"         Cost: ${breakdown['total_cost']:.4f}")
                print(f"         Tokens: {breakdown['prompt_tokens']:,} prompt + {breakdown['completion_tokens']:,} completion")
        
        if cost_summary["unknown_models"]:
            print(f"\n   ⚠️  Unknown models (no pricing data): {', '.join(cost_summary['unknown_models'])}")
    
    print(f"\n📊 Distribution:")
    print(f"   Minimum: {token_stats['min']:,.0f} tokens")
    print(f"   Maximum: {token_stats['max']:,.0f} tokens")
    print(f"   Median (P50): {token_stats['p50']:,.0f} tokens")
    print(f"   P95: {token_stats['p95']:,.0f} tokens")
    print(f"   P99: {token_stats['p99']:,.0f} tokens")
    
    # Show related metrics
    extractions_total = metrics.get_counter("stage4.extractions_total")
    extractions_with_llm = metrics.get_counter("stage4.extractions_with_llm")
    extractions_guardrails_only = metrics.get_counter("stage4.extractions_guardrails_only")
    
    print(f"\n🔍 Related Metrics:")
    print(f"   Total extractions: {extractions_total:.0f}")
    print(f"   With LLM: {extractions_with_llm:.0f}")
    print(f"   Guardrails only: {extractions_guardrails_only:.0f}")
    
    if extractions_with_llm > 0:
        llm_percentage = (extractions_with_llm / extractions_total) * 100 if extractions_total > 0 else 0
        print(f"   LLM usage rate: {llm_percentage:.1f}%")
    
    print("\n" + "=" * 70)
    print("💡 Tip: Token usage is logged in real-time at INFO level")
    print("   Look for: 'Token usage: prompt=X, completion=Y, total=Z, model=MODEL'")
    print("=" * 70)


if __name__ == "__main__":
    print_token_usage()
