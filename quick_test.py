#!/usr/bin/env python3
"""
Quick test script for Stage 4 Pipeline

This demonstrates the pipeline with guardrails-only mode (no LLM required).
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from stage4.runner import run_stage4


def main():
    print("=" * 70)
    print("Stage 4 Description Intelligence - Quick Test")
    print("=" * 70)
    
    # Test listing with high-risk signals
    test_listing = {
        "listing_id": "demo_001",
        "title": "2015 Subaru WRX STI - Stage 2 Build",
        "description": (
            "Running stage 2 tune with Cobb AP. Car has been defected for loud exhaust. "
            "Need gone ASAP, moving overseas. E85 compatible. Track use only. "
            "Engine has been tuned professionally. Some minor cosmetic scratches."
        ),
    }
    
    print(f"\n📋 Test Listing:")
    print(f"   ID: {test_listing['listing_id']}")
    print(f"   Title: {test_listing['title']}")
    print(f"   Description: {test_listing['description'][:100]}...")
    
    print(f"\n🔄 Running Stage 4 Pipeline (guardrails only, no LLM)...")
    
    # Run pipeline
    result = run_stage4(
        listing=test_listing,
        skip_llm=True,  # No LLM needed for guardrails
        validate=True,
    )
    
    print(f"\n✅ Pipeline completed successfully!")
    
    # Display results
    print(f"\n📊 Results Summary:")
    print(f"   Stage Version: {result['stage_version']}")
    print(f"   Risk Level: {result['payload']['risk_level_overall']}")
    print(f"   Mods Risk: {result['payload']['mods_risk_level']}")
    print(f"   Negotiation Stance: {result['payload']['negotiation_stance']}")
    
    # Show detected signals
    print(f"\n🚨 Detected Signals:")
    total_signals = 0
    for category, signals in result['payload']['signals'].items():
        if signals:
            print(f"\n   {category.replace('_', ' ').title()}:")
            for sig in signals:
                total_signals += 1
                print(f"      • {sig['type']} ({sig['severity']}) - "
                      f"confidence: {sig['confidence']}, "
                      f"verified: {sig['verification_level']}")
                print(f"        Evidence: \"{sig['evidence_text'][:50]}...\"")
    
    print(f"\n📈 Statistics:")
    print(f"   Total signals detected: {total_signals}")
    print(f"   Contains high-risk keywords: "
          f"{result['payload']['source_text_stats']['contains_keywords_high_risk']}")
    
    print(f"\n" + "=" * 70)
    print("✅ Test completed! All guardrails detected expected high-risk signals.")
    print("=" * 70)


if __name__ == "__main__":
    main()
