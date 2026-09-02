"""
Unit tests for the agent module.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from agent.agent import ContentPerformanceAgent

class TestContentPerformanceAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ContentPerformanceAgent()
        # Mock the clickhouse_tool
        self.agent.clickhouse_tool = MagicMock()

    def test_validate_content_id_tool(self):
        # Test the tool method
        result = self.agent._validate_content_id("SHOW-001")
        self.assertTrue(result["valid"])
        self.assertIsNone(result["error"])

        result = self.agent._validate_content_id("INVALID@ID")
        self.assertFalse(result["valid"])
        self.assertIsNotNone(result["error"])

    @patch('agent.agent.assess_data_quality')
    @patch('agent.agent.aggregate_episode_data')
    def test_analyze_content_success(self, mock_aggregate, mock_assess):
        # Setup mocks
        mock_assess.return_value = {
            "status": "SUFFICIENT",
            "is_valid": True,
            "total_episodes": 8,
            "total_viewers": 5000,
            "missing_fields": [],
            "warnings": [],
            "errors": []
        }

        mock_aggregate.return_value = {
            "total_viewers": 5000,
            "average_completion_rate": 0.75,
            "first_episode_completion": 0.8,
            "latest_episode_completion": 0.7,
            "retention_decay": {"relative_decay": 0.125},
            "drop_off_concentration": {"episode": 3, "drop": -0.15, "share_of_total_decline": 0.6},
            "viewership_velocity": 0.05,
            "engagement_velocity": 0.02,
            "new_viewer_trend": 0.03,
            "returning_viewer_trend": 0.01,
            "raw_series": {}
        }

        # Mock clickhouse tool responses
        self.agent.clickhouse_tool.get_content_performance.return_value = [
            {
                "content_id": "SHOW-001",
                "episode_number": i,
                "episode_date": f"2023-02-{i*10:02d}",
                "viewers": 10000 - (i-1)*500,
                "unique_viewers": 8500,
                "completion_rate": 0.8 - (i-1)*0.01,
                "returning_viewers": 4800,
                "new_viewers": 5200,
                "engagement_events": 80000,
                "watch_time_minutes": 400000
            } for i in range(1, 9)
        ]
        self.agent.clickhouse_tool.get_content_metadata.return_value = {
            "content_id": "SHOW-001",
            "title": "Test Show",
            "content_type": "series",
            "genre": "Drama",
            "release_date": "2023-01-15",
            "total_episodes": 8
        }

        # Call the method
        result = self.agent.analyze_content("SHOW-001")

        # Assertions
        self.assertEqual(result["content_id"], "SHOW-001")
        self.assertEqual(result["content_title"], "Test Show")
        self.assertIn("deterministic_recommendation", result)
        self.assertIn("deterministic_confidence", result)
        self.assertIn("metrics", result)
        self.assertIn("signals", result)
        self.assertIn("data_quality", result)
        self.assertIn("warnings", result)
        self.assertIn("provenance", result)

        # Check that the recommendation is one of the expected values
        self.assertIn(result["deterministic_recommendation"],
                      ["RENEW", "PROMOTE", "REPOSITION", "RE-EDIT", "CANCEL", "INVESTIGATE"])

        # Check confidence is between 0 and 1
        self.assertGreaterEqual(result["deterministic_confidence"], 0.0)
        self.assertLessEqual(result["deterministic_confidence"], 1.0)

    def test_analyze_content_invalid_id(self):
        # Test with invalid content ID
        result = self.agent.analyze_content("INVALID@ID")
        self.assertIn("error", result)
        self.assertEqual(result["error"]["type"], "INVALID_INPUT")

    def test_analyze_content_no_data(self):
        # Mock clickhouse to return no episodes
        self.agent.clickhouse_tool.get_content_performance.return_value = []
        self.agent.clickhouse_tool.get_content_metadata.return_value = {
            "content_id": "SHOW-001",
            "title": "Test Show",
            "content_type": "series",
            "genre": "Drama",
            "release_date": "2023-01-15",
            "total_episodes": 8
        }

        result = self.agent.analyze_content("SHOW-001")
        self.assertIn("error", result)
        self.assertEqual(result["error"]["type"], "NO_DATA_FOUND")

if __name__ == '__main__':
    unittest.main()