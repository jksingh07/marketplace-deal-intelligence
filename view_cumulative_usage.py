#!/usr/bin/env python3
"""
View cumulative token usage and costs across all sessions.

Usage:
    python view_cumulative_usage.py
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from common.persistent_cost_tracker import get_persistent_tracker


def print_cumulative_usage():
    """Print cumulative usage statistics across all sessions."""
    tracker = get_persistent_tracker()
    stats = tracker.get_cumulative_stats()
    
    print("=" * 70)
    print("📊 CUMULATIVE LLM Usage & Cost (All Sessions)")
    print("=" * 70)
    
    if stats["total_calls"] == 0:
        print("\n⚠️  No usage data found.")
        print("   Usage data is stored in: .metrics/usage_history.json")
        print("   Run some listings through the pipeline to start tracking.")
        return
    
    print(f"\n📈 Total Summary (All Time):")
    print(f"   Total LLM calls: {stats['total_calls']:,}")
    print(f"   Total tokens: {stats['total_tokens']:,}")
    print(f"   Total prompt tokens: {stats['total_prompt_tokens']:,}")
    print(f"   Total completion tokens: {stats['total_completion_tokens']:,}")
    print(f"   Total cost: ${stats['total_cost_usd']:.4f}")
    
    if stats["first_record"] and stats["last_record"]:
        from datetime import datetime
        first = datetime.fromisoformat(stats["first_record"].replace('Z', '+00:00'))
        last = datetime.fromisoformat(stats["last_record"].replace('Z', '+00:00'))
        print(f"\n   First usage: {first.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Last usage: {last.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if stats["model_breakdown"]:
        print(f"\n💰 Cost Breakdown by Model:")
        for model, breakdown in sorted(stats["model_breakdown"].items()):
            avg_cost = breakdown['total_cost'] / breakdown['calls'] if breakdown['calls'] > 0 else 0
            avg_tokens = breakdown['total_tokens'] / breakdown['calls'] if breakdown['calls'] > 0 else 0
            print(f"\n   {model}:")
            print(f"      Calls: {breakdown['calls']:,}")
            print(f"      Total cost: ${breakdown['total_cost']:.4f}")
            print(f"      Average cost per call: ${avg_cost:.4f}")
            print(f"      Total tokens: {breakdown['total_tokens']:,}")
            print(f"      Average tokens per call: {avg_tokens:,.0f}")
            print(f"      Prompt tokens: {breakdown['prompt_tokens']:,}")
            print(f"      Completion tokens: {breakdown['completion_tokens']:,}")
    
    # Show recent usage
    recent = tracker.get_recent_usage(limit=5)
    if recent:
        print(f"\n📋 Recent Usage (Last 5 calls):")
        for i, record in enumerate(recent, 1):
            from datetime import datetime
            dt = datetime.fromisoformat(record.timestamp.replace('Z', '+00:00'))
            print(f"   {i}. {dt.strftime('%Y-%m-%d %H:%M:%S')} - {record.model}")
            print(f"      Tokens: {record.total_tokens:,} | Cost: ${record.cost_usd:.4f}")
    
    print(f"\n💾 Storage Location:")
    print(f"   {tracker.storage_path}")
    print(f"\n💡 Tip: This data persists across all notebook runs and sessions!")
    print("=" * 70)


if __name__ == "__main__":
    print_cumulative_usage()
