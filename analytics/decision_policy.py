"""
Deterministic decision policy for content performance recommendations.
"""

from typing import Dict, Any, Literal, Optional
from enum import Enum

class Recommendation(str, Enum):
    RENEW = "RENEW"
    PROMOTE = "PROMOTE"
    REPOSITION = "REPOSITION"
    RE_EDIT = "RE-EDIT"
    CANCEL = "CANCEL"
    INVESTIGATE = "INVESTIGATE"

def classify_signal(value: float, positive_threshold: float, negative_threshold: float) -> Literal["positive", "negative", "neutral"]:
    """
    Classify a signal value as positive, negative, or neutral based on thresholds.
    """
    if value > positive_threshold:
        return "positive"
    elif value < negative_threshold:
        return "negative"
    else:
        return "neutral"

def evaluate_decision(
    signals: Dict[str, Any],
    policy: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate the decision policy based on signals.
    Returns a dictionary with recommendation and decision basis.
    """
    # Extract policy thresholds with defaults
    retention_pos = policy.get('retention_positive_threshold', 0.10)
    retention_neg = policy.get('retention_negative_threshold', -0.15)
    acquisition_pos = policy.get('acquisition_positive_threshold', 0.10)
    acquisition_neg = policy.get('acquisition_negative_threshold', -0.10)
    engagement_pos = policy.get('engagement_positive_threshold', 0.10)
    engagement_neg = policy.get('engagement_negative_threshold', -0.10)
    min_sample_size = policy.get('minimum_sample_size', 500)

    # Extract signals (with fallback to neutral if missing)
    retention_signal = signals.get('retention_decay', {}).get('relative_decay', 0.0)
    # For retention change, we might use the largest drop or average change
    # Using largest drop as a proxy for retention volatility (negative is bad)
    drop_off = signals.get('drop_off_concentration')
    retention_change_signal = drop_off['drop'] if drop_off else 0.0  # Negative values indicate drops

    acquisition_signal = signals.get('viewership_velocity', 0.0)
    engagement_signal = signals.get('engagement_velocity', 0.0)
    new_viewer_signal = signals.get('new_viewer_trend', 0.0)
    returning_viewer_signal = signals.get('returning_viewer_trend', 0.0)

    # Classify each dimension
    retention_class = classify_signal(retention_signal, retention_pos, retention_neg)
    # For retention change, we invert because negative drop is bad
    retention_change_class = classify_signal(retention_change_signal, retention_neg, retention_pos)  # Note: swapped thresholds
    acquisition_class = classify_signal(acquisition_signal, acquisition_pos, acquisition_neg)
    engagement_class = classify_signal(engagement_signal, engagement_pos, engagement_neg)
    new_viewer_class = classify_signal(new_viewer_signal, acquisition_pos, acquisition_neg)  # Reuse acquisition thresholds for simplicity
    returning_viewer_class = classify_signal(returning_viewer_signal, engagement_pos, engagement_neg)  # Reuse engagement thresholds

    # For simplicity in this MVP, we'll use a rule-based approach similar to the spec example
    # We'll focus on the three main dimensions: acquisition, retention, engagement
    # Using the classified signals above

    # Check for insufficient evidence first
    total_viewers = signals.get('total_viewers', 0)
    if total_viewers < min_sample_size:
        return {
            "recommendation": Recommendation.INVESTIGATE,
            "decision_basis": {
                "acquisition": "INSUFFICIENT_DATA",
                "retention": "INSUFFICIENT_DATA",
                "engagement": "INSUFFICIENT_DATA",
                "data_quality": "INSUFFICIENT_SAMPLE"
            }
        }

    # Apply rule system from spec
    # healthy_content: retention positive AND acquisition positive AND engagement positive -> RENEW
    if (retention_class == "positive" and
        acquisition_class == "positive" and
        engagement_class == "positive"):
        return {
            "recommendation": Recommendation.RENEW,
            "decision_basis": {
                "acquisition": acquisition_class.upper(),
                "retention": retention_class.upper(),
                "engagement": engagement_class.upper(),
                "data_quality": "SUFFICIENT"
            }
        }

    # strong_acquisition_weak_retention: acquisition positive AND retention negative -> REPOSITION
    if acquisition_class == "positive" and retention_class == "negative":
        return {
            "recommendation": Recommendation.REPOSITION,
            "decision_basis": {
                "acquisition": acquisition_class.upper(),
                "retention": retention_class.upper(),
                "engagement": engagement_class.upper(),
                "data_quality": "SUFFICIENT"
            }
        }

    # weak_acquisition_strong_retention: acquisition negative AND retention positive -> PROMOTE
    if acquisition_class == "negative" and retention_class == "positive":
        return {
            "recommendation": Recommendation.PROMOTE,
            "decision_basis": {
                "acquisition": acquisition_class.upper(),
                "retention": retention_class.upper(),
                "engagement": engagement_class.upper(),
                "data_quality": "SUFFICIENT"
            }
        }

    # broad_underperformance: acquisition negative AND retention negative AND engagement negative -> CANCEL
    if (acquisition_class == "negative" and
        retention_class == "negative" and
        engagement_class == "negative"):
        return {
            "recommendation": Recommendation.CANCEL,
            "decision_basis": {
                "acquisition": acquisition_class.upper(),
                "retention": retention_class.upper(),
                "engagement": engagement_class.upper(),
                "data_quality": "SUFFICIENT"
            }
        }

    # Default to INVESTIGATE for mixed or ambiguous cases
    return {
        "recommendation": Recommendation.INVESTIGATE,
        "decision_basis": {
            "acquisition": acquisition_class.upper(),
            "retention": retention_class.upper(),
            "engagement": engagement_class.upper(),
            "data_quality": "SUFFICIENT"
        }
    }

def calculate_confidence(
    data_quality: Dict[str, Any],
    signals: Dict[str, Any],
    policy: Dict[str, Any]
) -> float:
    """
    Calculate deterministic confidence score.
    Based on data completeness, sample sufficiency, signal strength, and agreement.
    """
    # Data quality score (0-1)
    dq_status = data_quality.get('status', 'INVALID')
    if dq_status == 'SUFFICIENT':
        dq_score = 1.0
    elif dq_status == 'INSUFFICIENT_SAMPLE':
        dq_score = 0.5
    else:
        dq_score = 0.0

    # Sample score (0-1) based on total viewers relative to minimum
    min_sample = policy.get('minimum_sample_size', 500)
    total_viewers = signals.get('total_viewers', 0)
    # If no viewers, confidence is zero
    if total_viewers == 0:
        return 0.0
    sample_score = min(1.0, total_viewers / min_sample) if min_sample > 0 else 0.0

    # Signal strength score (0-1) based on magnitude of key signals
    # We'll use absolute values of retention decay, viewership velocity, engagement velocity
    retention_strength = min(1.0, abs(signals.get('retention_decay', {}).get('relative_decay', 0.0)) * 5)  # Scale factor
    acquisition_strength = min(1.0, abs(signals.get('viewership_velocity', 0.0)) * 5)
    engagement_strength = min(1.0, abs(signals.get('engagement_velocity', 0.0)) * 5)
    signal_strength = (retention_strength + acquisition_strength + engagement_strength) / 3

    # Signal agreement score (0-1) - how consistent the signals are
    # For simplicity, we'll check if retention, acquisition, engagement all point same direction (all positive or all negative)
    signals_list = [
        signals.get('retention_decay', {}).get('relative_decay', 0.0),
        signals.get('viewership_velocity', 0.0),
        signals.get('engagement_velocity', 0.0)
    ]
    positive_count = sum(1 for s in signals_list if s > 0.01)  # Small epsilon to avoid noise
    negative_count = sum(1 for s in signals_list if s < -0.01)
    total_nonzero = positive_count + negative_count
    if total_nonzero == 0:
        agreement_score = 0.5  # Neutral
    else:
        # Agreement is high if all non-zero signals point same direction
        agreement_score = max(positive_count, negative_count) / total_nonzero if total_nonzero > 0 else 0.5

    # Combine scores with weights (these are demo-policy parameters)
    confidence = (
        0.30 * dq_score +
        0.25 * sample_score +
        0.25 * signal_strength +
        0.20 * agreement_score
    )

    # Clamp to [0, 1]
    return max(0.0, min(1.0, confidence))

# Example usage
if __name__ == "__main__":
    # Mock signals for testing
    test_signals = {
        "total_viewers": 12000,
        "retention_decay": {"relative_decay": -0.25},
        "drop_off_concentration": {"episode": 3, "drop": -0.18, "share_of_total_decline": 0.46},
        "viewership_velocity": -0.1,
        "engagement_velocity": -0.05,
        "new_viewer_trend": -0.15,
        "returning_viewer_trend": -0.05
    }
    test_dq = {"status": "SUFFICIENT", "total_episodes": 8, "total_viewers": 12000}
    test_policy = {
        "retention_positive_threshold": 0.10,
        "retention_negative_threshold": -0.15,
        "acquisition_positive_threshold": 0.10,
        "acquisition_negative_threshold": -0.10,
        "engagement_positive_threshold": 0.10,
        "engagement_negative_threshold": -0.10,
        "minimum_sample_size": 500
    }
    decision = evaluate_decision(test_signals, test_policy)
    confidence = calculate_confidence(test_dq, test_signals, test_policy)
    print("Decision:", decision)
    print("Confidence:", confidence)