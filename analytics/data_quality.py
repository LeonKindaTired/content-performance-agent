"""
Data quality engine for validating content performance data.
"""

from typing import List, Dict, Any, Tuple
import re

def validate_content_id(content_id: str) -> Tuple[bool, str]:
    """
    Validate content ID.
    Rules: non-empty, alphanumeric and hyphens only, reasonable length.
    """
    if not content_id or not isinstance(content_id, str):
        return False, "Content ID must be a non-empty string"

    if len(content_id) > 50:
        return False, "Content ID too long (max 50 characters)"

    # Allow alphanumeric, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', content_id):
        return False, "Content ID contains invalid characters (only alphanumeric, hyphen, underscore allowed)"

    return True, ""

def validate_episode_data(episodes: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Validate episode performance data.
    Returns (is_valid, list_of_errors)
    """
    errors = []

    if not episodes:
        errors.append("No episode data provided")
        return False, errors

    # Check for required fields in each episode
    required_fields = ['content_id', 'episode_number', 'episode_date',
                      'viewers', 'unique_viewers', 'completion_rate',
                      'returning_viewers', 'new_viewers', 'engagement_events']

    seen_episodes = set()

    for i, ep in enumerate(episodes):
        # Check required fields
        for field in required_fields:
            if field not in ep:
                errors.append(f"Episode {i+1}: missing required field '{field}'")
            elif ep[field] is None:
                errors.append(f"Episode {i+1}: field '{field}' is null")

        # Validate data types and ranges
        if 'episode_number' in ep and ep['episode_number'] is not None:
            if not isinstance(ep['episode_number'], int) or ep['episode_number'] <= 0:
                errors.append(f"Episode {i+1}: episode_number must be positive integer")

        if 'completion_rate' in ep and ep['completion_rate'] is not None:
            if not isinstance(ep['completion_rate'], (int, float)):
                errors.append(f"Episode {i+1}: completion_rate must be numeric")
            else:
                rate = float(ep['completion_rate'])
                if rate < 0 or rate > 1:
                    errors.append(f"Episode {i+1}: completion_rate must be between 0 and 1, got {rate}")

        # Check for negative counts where inappropriate
        count_fields = ['viewers', 'unique_viewers', 'returning_viewers', 'new_viewers', 'engagement_events']
        for field in count_fields:
            if field in ep and ep[field] is not None:
                if not isinstance(ep[field], int) or ep[field] < 0:
                    errors.append(f"Episode {i+1}: {field} must be non-negative integer")

        # Check logical consistency: unique_viewers <= viewers
        if 'viewers' in ep and 'unique_viewers' in ep:
            if ep['viewers'] is not None and ep['unique_viewers'] is not None:
                if ep['unique_viewers'] > ep['viewers']:
                    errors.append(f"Episode {i+1}: unique_viewers cannot exceed viewers")

        # Check logical consistency: returning + new = viewers (approximately)
        if 'returning_viewers' in ep and 'new_viewers' in ep and 'viewers' in ep:
            if all(ep[f] is not None for f in ['returning_viewers', 'new_viewers', 'viewers']):
                total = ep['returning_viewers'] + ep['new_viewers']
                if total != ep['viewers']:
                    errors.append(f"Episode {i+1}: returning_viewers + new_viewers ({total}) does not equal viewers ({ep['viewers']})")

        # Check for duplicate episode numbers
        ep_num = ep.get('episode_number')
        if ep_num is not None:
            if ep_num in seen_episodes:
                errors.append(f"Episode {i+1}: duplicate episode number {ep_num}")
            else:
                seen_episodes.add(ep_num)

    is_valid = len(errors) == 0
    return is_valid, errors

def assess_data_quality(episodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Assess overall data quality and return a status object.
    """
    is_valid, errors = validate_episode_data(episodes)

    # Additional quality metrics
    total_episodes = len(episodes)
    total_viewers = sum(ep.get('viewers', 0) for ep in episodes if ep.get('viewers') is not None)

    # Determine status
    if not is_valid:
        status = "INVALID"
    elif total_episodes < 2:
        status = "INSUFFICIENT_EPISODES"
    elif total_viewers < 100:  # Arbitrary threshold for insufficient sample
        status = "INSUFFICIENT_SAMPLE"
    else:
        status = "SUFFICIENT"

    # Collect warnings (non-fatal issues)
    warnings = []
    if total_episodes < 5:
        warnings.append(f"Limited episode data ({total_episodes} episodes)")

    # Check for missing episodes (gaps in sequence)
    seen_episodes = set()
    for ep in episodes:
        ep_num = ep.get('episode_number')
        if ep_num is not None:
            seen_episodes.add(ep_num)
    if seen_episodes:
        max_ep = max(seen_episodes)
        expected = set(range(1, max_ep + 1))
        missing = expected - seen_episodes
        if missing:
            warnings.append(f"Missing episode numbers: {sorted(missing)}")

    # Check for missing values in non-required fields (if we had more)
    missing_fields = []
    # For simplicity, we'll check the required fields again
    required = ['content_id', 'episode_number', 'episode_date', 'viewers',
               'unique_viewers', 'completion_rate', 'returning_viewers',
               'new_viewers', 'engagement_events']
    for field in required:
        if any(ep.get(field) is None for ep in episodes):
            missing_fields.append(field)

    return {
        "status": status,
        "is_valid": is_valid,
        "total_episodes": total_episodes,
        "total_viewers": total_viewers,
        "missing_fields": missing_fields,
        "warnings": warnings,
        "errors": errors
    }

# Example usage
if __name__ == "__main__":
    # Test with sample data
    test_episodes = [
        {
            "content_id": "SHOW-001",
            "episode_number": 1,
            "episode_date": "2023-02-01",
            "viewers": 10000,
            "unique_viewers": 8500,
            "completion_rate": 0.8,
            "returning_viewers": 4800,
            "new_viewers": 5200,
            "engagement_events": 80000
        }
    ]
    print(assess_data_quality(test_episodes))