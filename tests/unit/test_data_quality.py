"""
Unit tests for the data quality module.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from analytics.data_quality import (
    validate_content_id,
    validate_episode_data,
    assess_data_quality
)

def test_validate_content_id():
    # Valid IDs
    assert validate_content_id("SHOW-001") == (True, "")
    assert validate_content_id("show_001") == (True, "")
    assert validate_content_id("SHOW001") == (True, "")
    assert validate_content_id("SHOW-001-EXTRA") == (True, "")

    # Invalid IDs
    assert validate_content_id("") == (False, "Content ID must be a non-empty string")
    assert validate_content_id(None) == (False, "Content ID must be a non-empty string")
    assert validate_content_id("SHOW@001") == (False, "Content ID contains invalid characters (only alphanumeric, hyphen, underscore allowed)")
    assert validate_content_id("A"*51) == (False, "Content ID too long (max 50 characters)")

def test_validate_episode_data():
    # Valid data
    valid_episodes = [
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
    is_valid, errors = validate_episode_data(valid_episodes)
    assert is_valid == True
    assert len(errors) == 0

    # Missing field
    missing_field = [
        {
            "content_id": "SHOW-001",
            "episode_number": 1,
            # missing episode_date
            "viewers": 10000,
            "unique_viewers": 8500,
            "completion_rate": 0.8,
            "returning_viewers": 4800,
            "new_viewers": 5200,
            "engagement_events": 80000
        }
    ]
    is_valid, errors = validate_episode_data(missing_field)
    assert is_valid == False
    assert any("episode_date" in err for err in errors)

    # Invalid completion rate
    invalid_rate = [
        {
            "content_id": "SHOW-001",
            "episode_number": 1,
            "episode_date": "2023-02-01",
            "viewers": 10000,
            "unique_viewers": 8500,
            "completion_rate": 1.5,  # > 1
            "returning_viewers": 4800,
            "new_viewers": 5200,
            "engagement_events": 80000
        }
    ]
    is_valid, errors = validate_episode_data(invalid_rate)
    assert is_valid == False
    assert any("completion_rate must be between 0 and 1" in err for err in errors)

    # Negative viewers
    negative_viewers = [
        {
            "content_id": "SHOW-001",
            "episode_number": 1,
            "episode_date": "2023-02-01",
            "viewers": -100,  # negative
            "unique_viewers": 8500,
            "completion_rate": 0.8,
            "returning_viewers": 4800,
            "new_viewers": 5200,
            "engagement_events": 80000
        }
    ]
    is_valid, errors = validate_episode_data(negative_viewers)
    assert is_valid == False
    assert any("viewers must be non-negative integer" in err for err in errors)

    # Logical inconsistency: unique > total
    inconsistent = [
        {
            "content_id": "SHOW-001",
            "episode_number": 1,
            "episode_date": "2023-02-01",
            "viewers": 10000,
            "unique_viewers": 12000,  # > viewers
            "completion_rate": 0.8,
            "returning_viewers": 4800,
            "new_viewers": 5200,
            "engagement_events": 80000
        }
    ]
    is_valid, errors = validate_episode_data(inconsistent)
    assert is_valid == False
    assert any("unique_viewers cannot exceed viewers" in err for err in errors)

    # Duplicate episode number
    duplicate = [
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
        },
        {
            "content_id": "SHOW-001",
            "episode_number": 1,  # duplicate
            "episode_date": "2023-03-01",
            "viewers": 11000,
            "unique_viewers": 9350,
            "completion_rate": 0.75,
            "returning_viewers": 4950,
            "new_viewers": 6050,
            "engagement_events": 82500
        }
    ]
    is_valid, errors = validate_episode_data(duplicate)
    assert is_valid == False
    assert any("duplicate episode number" in err for err in errors)

    # Missing episode (gap)
    missing_ep = [
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
        },
        {
            "content_id": "SHOW-001",
            "episode_number": 3,  # missing 2
            "episode_date": "2023-04-01",
            "viewers": 9000,
            "unique_viewers": 7650,
            "completion_rate": 0.75,
            "returning_viewers": 4050,
            "new_viewers": 4950,
            "engagement_events": 72000
        }
    ]
    is_valid, errors = validate_episode_data(missing_ep)
    assert is_valid == True  # Validation passes; missing episodes are a data quality warning
    assert len(errors) == 0

def test_assess_data_quality():
    # Sufficient data
    sufficient = [
        {
            "content_id": "SHOW-001",
            "episode_number": i,
            "episode_date": f"2023-02-{i*10:02d}",
            "viewers": 10000,
            "unique_viewers": 8500,
            "completion_rate": 0.8,
            "returning_viewers": 4800,
            "new_viewers": 5200,
            "engagement_events": 80000
        } for i in range(1, 9)  # 8 episodes
    ]
    result = assess_data_quality(sufficient)
    assert result["status"] == "SUFFICIENT"
    assert result["is_valid"] == True
    assert result["total_episodes"] == 8
    assert result["total_viewers"] == 80000

    # Insufficient sample (low viewers)
    low_viewers = [
        {
            "content_id": "SHOW-001",
            "episode_number": 1,
            "episode_date": "2023-02-01",
            "viewers": 40,  # very low
            "unique_viewers": 32,
            "completion_rate": 0.8,
            "returning_viewers": 19,
            "new_viewers": 21,
            "engagement_events": 320
        },
        {
            "content_id": "SHOW-001",
            "episode_number": 2,
            "episode_date": "2023-03-01",
            "viewers": 40,  # very low
            "unique_viewers": 32,
            "completion_rate": 0.7,
            "returning_viewers": 18,
            "new_viewers": 22,
            "engagement_events": 280
        }
    ]
    result_low = assess_data_quality(low_viewers)
    # Total viewers = 80 < 100 threshold, and we have 2 episodes
    assert result_low["status"] == "INSUFFICIENT_SAMPLE"

    # Invalid data
    invalid = [
        {
            "content_id": "SHOW-001",
            "episode_number": 1,
            "episode_date": "2023-02-01",
            "viewers": 10000,
            "unique_viewers": 8500,
            "completion_rate": 1.5,  # invalid
            "returning_viewers": 4800,
            "new_viewers": 5200,
            "engagement_events": 80000
        }
    ]
    result_invalid = assess_data_quality(invalid)
    assert result_invalid["status"] == "INVALID"
    assert result_invalid["is_valid"] == False
    assert len(result_invalid["errors"]) > 0

    # Missing episodes
    missing_ep = [
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
        },
        {
            "content_id": "SHOW-001",
            "episode_number": 3,
            "episode_date": "2023-04-01",
            "viewers": 9000,
            "unique_viewers": 7650,
            "completion_rate": 0.75,
            "returning_viewers": 4050,
            "new_viewers": 4950,
            "engagement_events": 72000
        }
    ]
    result_missing = assess_data_quality(missing_ep)
    assert result_missing["status"] == "SUFFICIENT"  # Still valid, but warnings should mention missing
    assert any("Missing episode numbers" in w for w in result_missing["warnings"])

if __name__ == "__main__":
    test_validate_content_id()
    test_validate_episode_data()
    test_assess_data_quality()
    print("All data quality tests passed!")