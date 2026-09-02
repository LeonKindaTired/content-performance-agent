"""
Unit tests for the signals module.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from analytics.signals import (
    compute_completion_rate,
    compute_retention_change,
    compute_overall_retention_decay,
    compute_drop_off_concentration,
    compute_viewership_velocity,
    compute_engagement_velocity,
    compute_new_viewer_trend,
    compute_returning_viewer_trend,
    compute_anomaly_z_score,
    aggregate_episode_data
)

def test_completion_rate():
    assert compute_completion_rate(80, 100) == 0.8
    assert compute_completion_rate(0, 100) == 0.0
    assert compute_completion_rate(100, 100) == 1.0
    # Edge case: zero eligible viewers
    assert compute_completion_rate(50, 0) == 0.0

def test_retention_change():
    assert abs(compute_retention_change(0.8, 0.7) - 0.1) < 1e-9
    assert abs(compute_retention_change(0.6, 0.8) - (-0.2)) < 1e-9
    assert abs(compute_retention_change(0.7, 0.7) - 0.0) < 1e-9

def test_overall_retention_decay():
    # Test normal case
    rates = [0.8, 0.75, 0.7, 0.65]
    result = compute_overall_retention_decay(rates)
    assert abs(result["relative_decay"] - 0.1875) < 1e-9
    assert abs(result["largest_drop"] - (-0.05)) < 1e-9
    assert result["first_completion"] == 0.8
    assert result["latest_completion"] == 0.65

    # Test single episode
    result_single = compute_overall_retention_decay([0.8])
    assert result_single["relative_decay"] is None
    assert result_single["largest_drop"] is None
    assert result_single["first_completion"] == 0.8
    assert result_single["latest_completion"] == 0.8

    # Test empty list
    result_empty = compute_overall_retention_decay([])
    assert result_empty["relative_decay"] is None
    assert result_empty["largest_drop"] is None
    assert result_empty["first_completion"] is None
    assert result_empty["latest_completion"] is None

def test_drop_off_concentration():
    # Test with clear drop
    rates = [0.9, 0.8, 0.5, 0.6]  # Big drop from 0.8 to 0.5
    result = compute_drop_off_concentration(rates)
    assert result is not None
    assert result["episode"] == 3  # Drop between episode 2 and 3
    assert abs(result["drop"] - (-0.3)) < 1e-9
    # Total decline: -0.1 (0.9->0.8) + -0.3 (0.8->0.5) + 0.1 (0.5->0.6) = -0.3
    # Share of total decline: 0.3 / 0.3 = 1.0 (only considering negative changes)
    # Actually, we sum only negative changes: -0.1 + -0.3 = -0.4
    # Share = 0.3 / 0.4 = 0.75
    assert abs(result["share_of_total_decline"] - 0.75) < 0.001

    # Test no negative changes
    rates_increasing = [0.5, 0.6, 0.7]
    result_none = compute_drop_off_concentration(rates_increasing)
    assert result_none is None

    # Test insufficient data
    assert compute_drop_off_concentration([0.5]) is None
    assert compute_drop_off_concentration([]) is None

def test_viewership_velocity():
    assert abs(compute_viewership_velocity(100, 120) - 0.2) < 1e-9
    assert abs(compute_viewership_velocity(120, 100) - (-0.16666666666666666)) < 1e-9
    # When previous is zero, we use epsilon, so result is (100-0)/epsilon = 100 / 1e-10 = 1e12
    result = compute_viewership_velocity(0, 100)
    assert result > 1e10  # Should be a large number
    # Test zero denominator with zero numerator
    assert compute_viewership_velocity(0, 0) == 0.0  # (0-0)/max(0, epsilon) = 0/epsilon = 0

def test_aggregate_episode_data():
    episodes = [
        {
            "content_id": "SHOW-001",
            "episode_number": 1,
            "episode_date": "2023-02-01",
            "viewers": 10000,
            "unique_viewers": 8500,
            "completion_rate": 0.8,
            "returning_viewers": 4800,
            "new_viewers": 5200,
            "engagement_events": 80000,
            "watch_time_minutes": 400000
        },
        {
            "content_id": "SHOW-001",
            "episode_number": 2,
            "episode_date": "2023-03-01",
            "viewers": 11000,
            "unique_viewers": 9350,
            "completion_rate": 0.75,
            "returning_viewers": 4950,
            "new_viewers": 6050,
            "engagement_events": 82500,
            "watch_time_minutes": 412500
        }
    ]
    aggregated = aggregate_episode_data(episodes)
    assert aggregated["total_viewers"] == 21000
    assert abs(aggregated["average_completion_rate"] - 0.775) < 1e-9
    assert aggregated["first_episode_completion"] == 0.8
    assert aggregated["latest_episode_completion"] == 0.75
    # Retention decay: (0.8-0.75)/0.8 = 0.0625
    assert abs(aggregated["retention_decay"]["relative_decay"] - 0.0625) < 1e-9
    # Drop off: change is -0.05, so largest drop -0.05
    assert abs(aggregated["drop_off_concentration"]["drop"] - (-0.05)) < 1e-9
    assert aggregated["drop_off_concentration"]["episode"] == 2
    # Viewership velocity: (11000-10000)/10000 = 0.1
    assert abs(aggregated["viewership_velocity"] - 0.1) < 1e-9
    # Engagement velocity: (82500-80000)/80000 = 0.03125
    assert abs(aggregated["engagement_velocity"] - 0.03125) < 1e-9

if __name__ == "__main__":
    test_completion_rate()
    test_retention_change()
    test_overall_retention_decay()
    test_drop_off_concentration()
    test_viewership_velocity()
    test_aggregate_episode_data()
    print("All tests passed!")