#!/usr/bin/env python3
"""
End-to-end test of the Content Performance Signal Agent.
Tests the agent directly without making HTTP requests.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from agent.agent import ContentPerformanceAgent
import json

def test_content_analysis(content_id):
    """Test analysis for a specific content ID."""
    print(f"\n{'='*60}")
    print(f"Testing content analysis for: {content_id}")
    print('='*60)

    # Create agent instance
    agent = ContentPerformanceAgent()

    # Run analysis
    result = agent.analyze_content(content_id)

    # Check if there was an error
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False

    # Print results
    print(f"✅ Analysis successful!")
    print(f"Content ID: {result.get('content_id')}")
    print(f"Title: {result.get('content_title')}")
    print(f"Recommendation: {result.get('deterministic_recommendation')}")
    print(f"Confidence: {result.get('deterministic_confidence'):.2%}")

    # Print data quality
    data_quality = result.get('data_quality', {})
    print(f"Data Quality Status: {data_quality.get('status', 'unknown')}")
    if data_quality.get('warnings'):
        print(f"Warnings: {', '.join(data_quality['warnings'])}")

    # Print key signals
    signals = result.get('signals', {})
    print("\nKey Signals:")
    if signals.get('retention_decay'):
        rd = signals['retention_decay']
        if rd and rd.get('relative_decay') is not None:
            print(f"  Retention Change: {rd['relative_decay']:.2%}")

    if signals.get('drop_off_concentration'):
        doc = signals['drop_off_concentration']
        if doc and doc.get('episode') and doc.get('drop') is not None:
            print(f"  Largest Drop: {doc['drop']:.2%} at episode {doc['episode']}")

    if signals.get('viewership_velocity') is not None:
        print(f"  Viewership Velocity: {signals['viewership_velocity']:.2%}")

    if signals.get('engagement_velocity') is not None:
        print(f"  Engagement Velocity: {signals['engagement_velocity']:.2%}")

    # Print metrics
    metrics = result.get('metrics', {})
    print(f"\nMetrics:")
    print(f"  Total Viewers: {metrics.get('total_viewers', 0):,}")
    print(f"  Avg Completion Rate: {metrics.get('average_completion_rate', 0):.2%}")

    return True

def main():
    """Run end-to-end tests for all sample content IDs."""
    print("Starting End-to-End Test of Content Performance Signal Agent")
    print("Note: Using mock data (ClickHouse not required)")

    # Test all sample content IDs from the mock data
    test_ids = ["SHOW-001", "SHOW-007", "SHOW-042", "SHOW-999"]

    results = {}
    for content_id in test_ids:
        try:
            success = test_content_analysis(content_id)
            results[content_id] = success
        except Exception as e:
            print(f"❌ Failed to analyze {content_id}: {e}")
            results[content_id] = False

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    all_passed = True
    for content_id, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{content_id}: {status}")
        if not success:
            all_passed = False

    if all_passed:
        print("\n🎉 All tests passed! The agent is working correctly end-to-end.")
        return 0
    else:
        print("\n💥 Some tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())