"""
Unit tests for the decision policy module.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from analytics.decision_policy import (
    evaluate_decision,
    calculate_confidence,
    Recommendation
)

def test_evaluate_decision():
    # Default policy thresholds
    policy = {
        "retention_positive_threshold": 0.10,
        "retention_negative_threshold": -0.15,
        "acquisition_positive_threshold": 0.10,
        "acquisition_negative_threshold": -0.10,
        "engagement_positive_threshold": 0.10,
        "engagement_negative_threshold": -0.10,
        "minimum_sample_size": 500
    }

    # Test healthy content -> RENEW
    signals_healthy = {
        "total_viewers": 1000,
        "retention_decay": {"relative_decay": 0.12},  # positive (>0.10)
        "drop_off_concentration": None,  # no major drops
        "viewership_velocity": 0.12,  # positive (>0.10)
        "engagement_velocity": 0.12,  # positive (>0.10)
        "new_viewer_trend": 0.02,
        "returning_viewer_trend": 0.01
    }
    result = evaluate_decision(signals_healthy, policy)
    assert result["recommendation"] == Recommendation.RENEW
    assert result["decision_basis"]["retention"] == "POSITIVE"
    assert result["decision_basis"]["acquisition"] == "POSITIVE"
    assert result["decision_basis"]["engagement"] == "POSITIVE"

    # Test strong acquisition, weak retention -> REPOSITION
    signals_reposition = {
        "total_viewers": 1000,
        "retention_decay": {"relative_decay": -0.20},  # negative (< -0.15)
        "drop_off_concentration": {"episode": 3, "drop": -0.25, "share_of_total_decline": 0.6},
        "viewership_velocity": 0.15,  # positive (>0.10)
        "engagement_velocity": -0.02,
        "new_viewer_trend": 0.1,
        "returning_viewer_trend": -0.01
    }
    result = evaluate_decision(signals_reposition, policy)
    assert result["recommendation"] == Recommendation.REPOSITION
    assert result["decision_basis"]["retention"] == "NEGATIVE"
    assert result["decision_basis"]["acquisition"] == "POSITIVE"

    # Test weak acquisition, strong retention -> PROMOTE
    signals_promote = {
        "total_viewers": 1000,
        "retention_decay": {"relative_decay": 0.12},  # positive (>0.10)
        "drop_off_concentration": None,
        "viewership_velocity": -0.12,  # negative (< -0.10)
        "engagement_velocity": 0.08,  # neutral (between -0.10 and 0.10)
        "new_viewer_trend": -0.1,
        "returning_viewer_trend": 0.05
    }
    result = evaluate_decision(signals_promote, policy)
    assert result["recommendation"] == Recommendation.PROMOTE
    assert result["decision_basis"]["retention"] == "POSITIVE"
    assert result["decision_basis"]["acquisition"] == "NEGATIVE"
    # Note: engagement is neutral, but rule only checks acquisition and retention for this case

    # Test broad underperformance -> CANCEL
    signals_cancel = {
        "total_viewers": 1000,
        "retention_decay": {"relative_decay": -0.20},  # negative
        "drop_off_concentration": {"episode": 2, "drop": -0.18, "share_of_total_decline": 0.5},
        "viewership_velocity": -0.15,  # negative
        "engagement_velocity": -0.12,  # negative
        "new_viewer_trend": -0.1,
        "returning_viewer_trend": -0.05
    }
    result = evaluate_decision(signals_cancel, policy)
    assert result["recommendation"] == Recommendation.CANCEL
    assert result["decision_basis"]["retention"] == "NEGATIVE"
    assert result["decision_basis"]["acquisition"] == "NEGATIVE"
    assert result["decision_basis"]["engagement"] == "NEGATIVE"

    # Test insufficient sample -> INVESTIGATE
    signals_insufficient = {
        "total_viewers": 100,  # below minimum_sample_size of 500
        "retention_decay": {"relative_decay": 0.0},
        "drop_off_concentration": None,
        "viewership_velocity": 0.0,
        "engagement_velocity": 0.0,
        "new_viewer_trend": 0.0,
        "returning_viewer_trend": 0.0
    }
    result = evaluate_decision(signals_insufficient, policy)
    assert result["recommendation"] == Recommendation.INVESTIGATE
    assert result["decision_basis"]["data_quality"] == "INSUFFICIENT_SAMPLE"

    # Test mixed signals -> INVESTIGATE (default)
    signals_mixed = {
        "total_viewers": 1000,
        "retention_decay": {"relative_decay": 0.05},  # neutral
        "drop_off_concentration": None,
        "viewership_velocity": -0.05,  # neutral
        "engagement_velocity": 0.0,  # neutral
        "new_viewer_trend": 0.0,
        "returning_viewer_trend": 0.0
    }
    result = evaluate_decision(signals_mixed, policy)
    assert result["recommendation"] == Recommendation.INVESTIGATE

def test_calculate_confidence():
    policy = {
        "minimum_sample_size": 500
    }

    # High confidence case
    data_quality_high = {
        "status": "SUFFICIENT",
        "total_episodes": 8,
        "total_viewers": 5000
    }
    signals_high = {
        "total_viewers": 5000,
        "retention_decay": {"relative_decay": 0.1},
        "drop_off_concentration": {"episode": 3, "drop": -0.15, "share_of_total_decline": 0.5},
        "viewership_velocity": 0.1,
        "engagement_velocity": 0.05,
        "new_viewer_trend": 0.05,
        "returning_viewer_trend": 0.02
    }
    confidence = calculate_confidence(data_quality_high, signals_high, policy)
    assert 0.8 <= confidence <= 1.0  # Should be high

    # Low confidence case
    data_quality_low = {
        "status": "INSUFFICIENT_SAMPLE",
        "total_episodes": 2,
        "total_viewers": 100
    }
    signals_low = {
        "total_viewers": 100,
        "retention_decay": {"relative_decay": 0.01},
        "drop_off_concentration": None,
        "viewership_velocity": 0.01,
        "engagement_velocity": 0.0,
        "new_viewer_trend": 0.0,
        "returning_viewer_trend": 0.0
    }
    confidence_low = calculate_confidence(data_quality_low, signals_low, policy)
    assert 0.0 <= confidence_low <= 0.5  # Should be low

    # Edge case: zero viewers
    data_quality_zero = {
        "status": "INSUFFICIENT_SAMPLE",
        "total_episodes": 1,
        "total_viewers": 0
    }
    signals_zero = {
        "total_viewers": 0,
        "retention_decay": {"relative_decay": 0.0},
        "drop_off_concentration": None,
        "viewership_velocity": 0.0,
        "engagement_velocity": 0.0,
        "new_viewer_trend": 0.0,
        "returning_viewer_trend": 0.0
    }
    confidence_zero = calculate_confidence(data_quality_zero, signals_zero, policy)
    assert confidence_zero == 0.0  # Should be zero due to no data

if __name__ == "__main__":
    test_evaluate_decision()
    test_calculate_confidence()
    print("All decision policy tests passed!")