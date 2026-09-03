"""
Integration tests for ClickHouse tool.
Tests the ClickHouse tool integration with mock data fallback.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tools.clickhouse_tool import get_clickhouse_tool, ClickHouseTool


class TestClickHouseToolIntegration(unittest.TestCase):
    """Integration tests for ClickHouse tool."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = get_clickhouse_tool()

    def test_tool_initialization(self):
        """Test that the tool initializes correctly."""
        self.assertIsInstance(self.tool, ClickHouseTool)
        # Should fall back to mock data since no ClickHouse is configured
        self.assertTrue(self.tool.use_mock)

    def test_get_content_performance_show_001(self):
        """Test retrieving performance data for SHOW-001 (successful show)."""
        data = self.tool.get_content_performance("SHOW-001")

        # Should return mock data for SHOW-001
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 8)  # 8 episodes

        # Check first episode
        first_episode = data[0]
        self.assertEqual(first_episode['content_id'], 'SHOW-001')
        self.assertEqual(first_episode['episode_number'], 1)
        self.assertEqual(first_episode['viewers'], 10000)
        self.assertEqual(first_episode['completion_rate'], 0.8)

        # Check that data is ordered by episode number
        episode_numbers = [ep['episode_number'] for ep in data]
        self.assertEqual(episode_numbers, list(range(1, 9)))

    def test_get_content_performance_show_042(self):
        """Test retrieving performance data for SHOW-042 (failing show)."""
        data = self.tool.get_content_performance("SHOW-042")

        # Should return mock data for SHOW-042
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 8)  # 8 episodes

        # Check the big drop at episode 3
        episode_3 = next((ep for ep in data if ep['episode_number'] == 3), None)
        self.assertIsNotNone(episode_3)
        self.assertEqual(episode_3['completion_rate'], 0.5)  # Big drop

        # Check episode 2 (before drop)
        episode_2 = next((ep for ep in data if ep['episode_number'] == 2), None)
        self.assertIsNotNone(episode_2)
        self.assertEqual(episode_2['completion_rate'], 0.73)

        # Check episode 4 (after drop)
        episode_4 = next((ep for ep in data if ep['episode_number'] == 4), None)
        self.assertIsNotNone(episode_4)
        self.assertEqual(episode_4['completion_rate'], 0.58)  # Recovering

    def test_get_content_performance_show_999(self):
        """Test retrieving performance data for SHOW-999 (insufficient evidence)."""
        data = self.tool.get_content_performance("SHOW-999")

        # Should return mock data for SHOW-999
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)  # Only 2 episodes

        # Check low viewership
        for episode in data:
            self.assertLess(episode['viewers'], 1000)  # Low viewership

    def test_get_content_performance_unknown_id(self):
        """Test retrieving performance data for unknown content ID."""
        data = self.tool.get_content_performance("UNKNOWN-SHOW")

        # Should return empty list for unknown ID (from mock data)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)

    def test_get_content_metadata(self):
        """Test retrieving content metadata."""
        # Test SHOW-001
        metadata = self.tool.get_content_metadata("SHOW-001")
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['content_id'], 'SHOW-001')
        self.assertEqual(metadata['title'], 'The Great Adventure')
        self.assertEqual(metadata['content_type'], 'series')
        self.assertEqual(metadata['genre'], 'Drama')

        # Test unknown ID
        unknown_metadata = self.tool.get_content_metadata("UNKNOWN-SHOW")
        self.assertIsNone(unknown_metadata)

    def test_test_connection_false_with_mock(self):
        """Test that connection test returns False when using mock data."""
        # Since we're using mock data, connection test should return False
        # (no actual ClickHouse connection)
        self.assertFalse(self.tool.test_connection())

    def test_date_range_filtering(self):
        """Test date range filtering in mock data."""
        # Test with date range that should return subset of data
        date_range = {
            'start': '2023-04-01',
            'end': '2023-06-01'
        }

        data = self.tool.get_content_performance("SHOW-001", date_range=date_range)

        # Should return episodes 3, 4, 5 (April, May, June)
        self.assertEqual(len(data), 3)
        episode_numbers = [ep['episode_number'] for ep in data]
        self.assertEqual(episode_numbers, [3, 4, 5])

        # Check specific episodes
        april_ep = data[0]  # Episode 3
        self.assertEqual(april_ep['episode_date'], '2023-04-01')
        self.assertEqual(april_ep['completion_rate'], 0.84)


if __name__ == '__main__':
    unittest.main()