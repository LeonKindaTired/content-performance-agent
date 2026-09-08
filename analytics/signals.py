"""
Deterministic signal engine for content performance analytics.
"""

from typing import List, Dict, Any, Optional
import statistics
import math

EPSILON = 1e-10


def safe_divide(numerator: float, denominator: float) -> float:
    """Avoid division by zero."""
    if abs(denominator) < EPSILON:
        return 0.0
    return numerator / denominator


def compute_completion_rate(completed_viewers: float, eligible_viewers: float) -> float:
    """
    Signal 1: Episode completion rate.
    completion_i = completed_viewers_i / eligible_viewers_i
    """
    return safe_divide(completed_viewers, eligible_viewers)


def compute_retention_change(completion_current: float, completion_previous: float) -> float:
    """
    Signal 2: Episode retention change.
    retention_change_i = completion_rate_i - completion_rate_(i-1)
    """
    return completion_current - completion_previous


def compute_overall_retention_decay(completion_rates: List[float]) -> Dict[str, Any]:
    """
    Signal 3: Overall retention decay.
    Uses both first-to-latest relative decay and largest consecutive episode drop.
    """
    if len(completion_rates) < 2:
        return {
            "relative_decay": None,
            "largest_drop": None,
            "first_completion": completion_rates[0] if completion_rates else None,
            "latest_completion": completion_rates[-1] if completion_rates else None
        }

    first = completion_rates[0]
    latest = completion_rates[-1]
    relative_decay = safe_divide((first - latest), max(first, EPSILON))


    changes = [completion_rates[i] - completion_rates[i-1] for i in range(1, len(completion_rates))]
    largest_drop = min(changes) if changes else 0.0

    return {
        "relative_decay": relative_decay,
        "largest_drop": largest_drop,
        "first_completion": first,
        "latest_completion": latest
    }


def compute_drop_off_concentration(completion_rates: List[float]) -> Optional[Dict[str, Any]]:
    """
    Signal 4: Drop-off concentration.
    Identify the episode with the largest negative retention change.
    Returns dict with episode number (1-indexed), drop value, and share of total decline.
    """
    if len(completion_rates) < 2:
        return None

    changes = [completion_rates[i] - completion_rates[i-1] for i in range(1, len(completion_rates))]
    if not changes:
        return None


    min_change = min(changes)
    if min_change >= 0:
        return None

    min_index = changes.index(min_change)
    episode_number = min_index + 2


    total_decline = sum([c for c in changes if c < 0])
    if total_decline == 0:
        share = 0.0
    else:
        share = safe_divide(abs(min_change), abs(total_decline))

    return {
        "episode": episode_number,
        "drop": min_change,
        "share_of_total_decline": share
    }


def compute_viewership_velocity(
    viewers_previous: float,
    viewers_recent: float
) -> float:
    """
    Signal 5: Viewership velocity.
    velocity = (recent_period_average - previous_period_average) / max(previous_period_average, epsilon)
    """
    return safe_divide((viewers_recent - viewers_previous), max(viewers_previous, EPSILON))


def compute_engagement_velocity(
    engagement_previous: float,
    engagement_recent: float
) -> float:
    """
    Signal 6: Engagement velocity (using normalized engagement rate).
    """
    return safe_divide((engagement_recent - engagement_previous), max(engagement_previous, EPSILON))


def compute_new_viewer_trend(
    new_viewers_previous: float,
    new_viewers_recent: float
) -> float:
    """
    Signal 7: New viewer trend.
    """
    return safe_divide((new_viewers_recent - new_viewers_previous), max(new_viewers_previous, EPSILON))


def compute_returning_viewer_trend(
    returning_previous: float,
    returning_recent: float
) -> float:
    """
    Signal 8: Returning viewer trend.
    """
    return safe_divide((returning_recent - returning_previous), max(returning_previous, EPSILON))


def compute_anomaly_z_score(
    current: float,
    historical: List[float]
) -> Optional[float]:
    """
    Signal 9: Anomaly score using z-score.
    z = (current - mean) / stddev
    Returns None if insufficient data or zero stddev.
    """
    if len(historical) < 2:
        return None
    mean = statistics.mean(historical)
    stdev = statistics.stdev(historical) if len(historical) >= 2 else 0.0
    if stdev < EPSILON:
        return None
    return (current - mean) / stdev


def aggregate_episode_data(episodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate raw episode data into useful metrics for signaling.
    Expects episodes sorted by episode_number.
    Returns a dictionary with aggregated metrics and time series.
    """
    if not episodes:
        return {}


    completion_rates = [ep.get('completion_rate', 0.0) for ep in episodes]
    viewers = [ep.get('viewers', 0) for ep in episodes]
    unique_viewers = [ep.get('unique_viewers', 0) for ep in episodes]
    returning_viewers = [ep.get('returning_viewers', 0) for ep in episodes]
    new_viewers = [ep.get('new_viewers', 0) for ep in episodes]
    engagement_events = [ep.get('engagement_events', 0) for ep in episodes]
    watch_time_minutes = [ep.get('watch_time_minutes', 0.0) for ep in episodes]


    total_viewers = sum(viewers)
    avg_completion = statistics.mean(completion_rates) if completion_rates else 0.0


    split_idx = len(episodes) // 2
    if split_idx == 0:

        prev_viewers = sum(viewers) if viewers else 0
        recent_viewers = 0
        prev_engagement = sum(engagement_events) if engagement_events else 0
        recent_engagement = 0
        prev_new = sum(new_viewers) if new_viewers else 0
        recent_new = 0
        prev_returning = sum(returning_viewers) if returning_viewers else 0
        recent_returning = 0
    else:
        prev_viewers = sum(viewers[:split_idx])
        recent_viewers = sum(viewers[split_idx:])
        prev_engagement = sum(engagement_events[:split_idx])
        recent_engagement = sum(engagement_events[split_idx:])
        prev_new = sum(new_viewers[:split_idx])
        recent_new = sum(new_viewers[split_idx:])
        prev_returning = sum(returning_viewers[:split_idx])
        recent_returning = sum(returning_viewers[split_idx:])


    retention_decay = compute_overall_retention_decay(completion_rates)
    drop_off = compute_drop_off_concentration(completion_rates)

    return {
        "total_viewers": total_viewers,
        "average_completion_rate": avg_completion,
        "first_episode_completion": completion_rates[0] if completion_rates else None,
        "latest_episode_completion": completion_rates[-1] if completion_rates else None,
        "retention_decay": retention_decay,
        "drop_off_concentration": drop_off,
        "viewership_velocity": compute_viewership_velocity(prev_viewers, recent_viewers),
        "engagement_velocity": compute_engagement_velocity(prev_engagement, recent_engagement),
        "new_viewer_trend": compute_new_viewer_trend(prev_new, recent_new),
        "returning_viewer_trend": compute_returning_viewer_trend(prev_returning, recent_returning),
        "raw_series": {
            "completion_rates": completion_rates,
            "viewers": viewers,
            "unique_viewers": unique_viewers,
            "returning_viewers": returning_viewers,
            "new_viewers": new_viewers,
            "engagement_events": engagement_events,
            "watch_time_minutes": watch_time_minutes
        }
    }



if __name__ == "__main__":

    test_completion = [0.8, 0.75, 0.7, 0.65, 0.6]
    print("Retention decay:", compute_overall_retention_decay(test_completion))
    print("Drop off concentration:", compute_drop_off_concentration(test_completion))