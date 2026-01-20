#!/usr/bin/env python3
"""
Generate a human-readable usage summary report.

Usage:
    python generate_usage_report.py
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from common.usage_report_generator import generate_usage_report


if __name__ == "__main__":
    report_path = generate_usage_report()
    print(f"✅ Usage report generated: {report_path}")
    print(f"\nOpen the file to view your cumulative usage and cost summary!")
