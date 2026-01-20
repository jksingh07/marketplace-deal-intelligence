"""
Usage Report Generator

Generates human-readable summary reports of token usage and costs.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional

from common.persistent_cost_tracker import get_persistent_tracker


def generate_usage_report(output_path: Optional[Path] = None) -> Path:
    """
    Generate a markdown report of cumulative usage and costs.
    
    Args:
        output_path: Path to write the report (defaults to .metrics/USAGE_SUMMARY.md)
        
    Returns:
        Path to the generated report file
    """
    if output_path is None:
        project_root = Path(__file__).parent.parent.parent
        metrics_dir = project_root / ".metrics"
        metrics_dir.mkdir(exist_ok=True)
        output_path = metrics_dir / "USAGE_SUMMARY.md"
    
    tracker = get_persistent_tracker()
    stats = tracker.get_cumulative_stats()
    recent = tracker.get_recent_usage(limit=10)
    
    # Generate report content
    report_lines = []
    
    # Header
    report_lines.append("# LLM Usage & Cost Summary")
    report_lines.append("")
    report_lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    
    if stats["total_calls"] == 0:
        report_lines.append("## ⚠️ No Usage Data Yet")
        report_lines.append("")
        report_lines.append("No LLM API calls have been recorded yet.")
        report_lines.append("")
        report_lines.append("Usage data will appear here once you start running listings through the pipeline.")
    else:
        # Overall Summary
        report_lines.append("## 📊 Overall Summary")
        report_lines.append("")
        report_lines.append("| Metric | Value |")
        report_lines.append("|--------|-------|")
        report_lines.append(f"| **Total LLM Calls** | {stats['total_calls']:,} |")
        report_lines.append(f"| **Total Tokens** | {stats['total_tokens']:,} |")
        report_lines.append(f"| **Total Prompt Tokens** | {stats['total_prompt_tokens']:,} |")
        report_lines.append(f"| **Total Completion Tokens** | {stats['total_completion_tokens']:,} |")
        report_lines.append(f"| **Total Cost (USD)** | ${stats['total_cost_usd']:.4f} |")
        report_lines.append("")
        
        # Time Range
        if stats["first_record"] and stats["last_record"]:
            first = datetime.fromisoformat(stats["first_record"].replace('Z', '+00:00'))
            last = datetime.fromisoformat(stats["last_record"].replace('Z', '+00:00'))
            report_lines.append("### 📅 Time Range")
            report_lines.append("")
            report_lines.append(f"- **First Usage**: {first.strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append(f"- **Last Usage**: {last.strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("")
        
        # Model Breakdown
        if stats["model_breakdown"]:
            report_lines.append("## 💰 Cost Breakdown by Model")
            report_lines.append("")
            
            for model, breakdown in sorted(stats["model_breakdown"].items()):
                avg_cost = breakdown['total_cost'] / breakdown['calls'] if breakdown['calls'] > 0 else 0
                avg_tokens = breakdown['total_tokens'] / breakdown['calls'] if breakdown['calls'] > 0 else 0
                
                report_lines.append(f"### {model}")
                report_lines.append("")
                report_lines.append("| Metric | Value |")
                report_lines.append("|--------|-------|")
                report_lines.append(f"| Calls | {breakdown['calls']:,} |")
                report_lines.append(f"| Total Cost | ${breakdown['total_cost']:.4f} |")
                report_lines.append(f"| Average Cost per Call | ${avg_cost:.4f} |")
                report_lines.append(f"| Total Tokens | {breakdown['total_tokens']:,} |")
                report_lines.append(f"| Average Tokens per Call | {avg_tokens:,.0f} |")
                report_lines.append(f"| Prompt Tokens | {breakdown['prompt_tokens']:,} |")
                report_lines.append(f"| Completion Tokens | {breakdown['completion_tokens']:,} |")
                report_lines.append("")
        
        # Recent Usage
        if recent:
            report_lines.append("## 📋 Recent Usage (Last 10 Calls)")
            report_lines.append("")
            report_lines.append("| # | Timestamp | Model | Tokens | Cost |")
            report_lines.append("|---|-----------|-------|--------|------|")
            
            for i, record in enumerate(recent, 1):
                dt = datetime.fromisoformat(record.timestamp.replace('Z', '+00:00'))
                report_lines.append(
                    f"| {i} | {dt.strftime('%Y-%m-%d %H:%M:%S')} | {record.model} | "
                    f"{record.total_tokens:,} | ${record.cost_usd:.4f} |"
                )
            report_lines.append("")
        
        # Cost Analysis
        if stats["total_calls"] > 0:
            avg_cost_per_call = stats['total_cost_usd'] / stats['total_calls']
            avg_tokens_per_call = stats['total_tokens'] / stats['total_calls']
            
            report_lines.append("## 📈 Cost Analysis")
            report_lines.append("")
            report_lines.append("| Metric | Value |")
            report_lines.append("|--------|-------|")
            report_lines.append(f"| Average Cost per Call | ${avg_cost_per_call:.4f} |")
            report_lines.append(f"| Average Tokens per Call | {avg_tokens_per_call:,.0f} |")
            
            if stats['total_tokens'] > 0:
                cost_per_1k_tokens = (stats['total_cost_usd'] / stats['total_tokens']) * 1000
                report_lines.append(f"| Cost per 1,000 Tokens | ${cost_per_1k_tokens:.4f} |")
            report_lines.append("")
    
    # Footer
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 📝 Notes")
    report_lines.append("")
    report_lines.append("- This report is automatically generated from `.metrics/usage_history.json`")
    report_lines.append("- Data persists across all notebook runs and kernel restarts")
    report_lines.append("- To regenerate this report, run: `python generate_usage_report.py`")
    report_lines.append("- To view raw data, see: `.metrics/usage_history.json`")
    report_lines.append("")
    report_lines.append(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    # Write to file
    output_path.write_text('\n'.join(report_lines))
    
    return output_path


def update_usage_report() -> Path:
    """
    Update the usage report (convenience function).
    
    Returns:
        Path to the updated report file
    """
    return generate_usage_report()
