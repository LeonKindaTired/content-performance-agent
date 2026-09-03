"""
End-to-end tests for API endpoints.
Tests the complete flow from HTTP request to response.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from api.main import app


class TestAPIEndpointsE2E(unittest.TestCase):
    """End-to-end tests for API endpoints."""

    def setUp(self):
        """Set up test client."""
        self.app = app
        self.client = TestClient(app)

    @patch('api.main.agent')
    def test_health_endpoint(self, mock_agent):
        """Test the health check endpoint."""
        # Mock the agent's ClickHouse tool
        mock_clickhouse_tool = MagicMock()
        mock_clickhouse_tool.test_connection.return_value = True
        mock_agent._clickhouse_tool = mock_clickhouse_tool

        # Make request
        response = self.client.get('/api/health')
        data = response.json()

        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['services']['clickhouse'], 'connected')
        self.assertEqual(data['services']['agent'], 'ready')

    @patch('api.main.agent')
    def test_health_endpoint_clickhouse_down(self, mock_agent):
        """Test health endpoint when ClickHouse is down."""
        # Mock the agent's ClickHouse tool to simulate failure
        mock_clickhouse_tool = MagicMock()
        mock_clickhouse_tool.test_connection.return_value = False
        mock_agent._clickhouse_tool = mock_clickhouse_tool

        # Make request
        response = self.client.get('/api/health')
        data = response.json()

        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'degraded')
        self.assertEqual(data['services']['clickhouse'], 'disconnected')
        self.assertEqual(data['services']['agent'], 'ready')

    @patch('api.main.agent')
    def test_analyze_endpoint_success(self, mock_agent):
        """Test successful analysis endpoint."""
        # Mock the agent's analyze_content method to return a sample result
        mock_agent.analyze_content.return_value = {
            'content_id': 'SHOW-042',
            'content_title': 'Lost in Space',
            'deterministic_recommendation': 'REPOSITION',
            'deterministic_confidence': 0.82,
            'decision_basis': {
                'acquisition': 'WEAK',
                'retention': 'DECLINING',
                'engagement': 'STABLE',
                'data_quality': 'SUFFICIENT'
            },
            'metrics': {
                'total_viewers': 18420,
                'average_completion_rate': 0.56
            },
            'signals': {
                'retention_decay': {'relative_decay': 0.39},
                'drop_off_concentration': {'episode': 3, 'drop': -0.18},
                'viewership_velocity': -0.12,
                'engagement_velocity': -0.09
            },
            'data_quality': {
                'status': 'SUFFICIENT',
                'sample_size': 18420,
                'missing_fields': [],
                'warnings': []
            },
            'warnings': [],
            'provenance': {
                'data_source': 'ClickHouse',
                'retrieved_at': '2023-09-03T10:00:00Z'
            }
        }

        # Make request
        response = self.client.post(
            '/api/analyze',
            json={'content_id': 'SHOW-042'}
        )
        data = response.json()

        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['content_id'], 'SHOW-042')
        self.assertEqual(data['recommendation'], 'REPOSITION')
        self.assertEqual(data['confidence'], 0.82)
        self.assertEqual(data['decision_basis']['acquisition'], 'WEAK')
        self.assertEqual(data['decision_basis']['retention'], 'DECLINING')
        self.assertEqual(data['metrics']['total_viewers'], 18420)
        self.assertEqual(data['signals']['drop_off_concentration']['episode'], 3)
        self.assertEqual(data['data_quality']['status'], 'SUFFICIENT')
        self.assertEqual(len(data['warnings']), 0)
        self.assertEqual(data['provenance']['data_source'], 'ClickHouse')

        # Verify agent method was called
        mock_agent.analyze_content.assert_called_once_with('SHOW-042')

    @patch('api.main.agent')
    def test_analyze_endpoint_invalid_id(self, mock_agent):
        """Test analysis endpoint with invalid content ID."""
        # Mock the agent's analyze_content method to return an error
        mock_agent.analyze_content.return_value = {
            'content_id': 'INVALID@ID!',
            'error': {
                'type': 'INVALID_INPUT',
                'message': 'Content ID contains invalid characters'
            },
            'recommendation': 'INVESTIGATE',
            'confidence': 0.0,
            'data_quality': {'status': 'ERROR'},
            'metrics': {},
            'signals': {},
            'warnings': ['Content ID contains invalid characters'],
            'provenance': {}
        }

        # Make request
        response = self.client.post(
            '/api/analyze',
            json={'content_id': 'INVALID@ID!'}
        )
        data = response.json()

        # Verify response (should be 400 Bad Request)
        self.assertEqual(response.status_code, 400)
        self.assertIn('detail', data)
        self.assertEqual(data['detail']['type'], 'INVALID_INPUT')

    @patch('api.main.agent')
    def test_analyze_endpoint_no_data(self, mock_agent):
        """Test analysis endpoint when no data is found."""
        # Mock the agent's analyze_content method to return no data error
        mock_agent.analyze_content.return_value = {
            'content_id': 'UNKNOWN-SHOW',
            'error': {
                'type': 'NO_DATA_FOUND',
                'message': 'No episode performance data found for content ID: UNKNOWN-SHOW'
            },
            'recommendation': 'INVESTIGATE',
            'confidence': 0.0,
            'data_quality': {'status': 'ERROR'},
            'metrics': {},
            'signals': {},
            'warnings': ['No episode performance data found for content ID: UNKNOWN-SHOW'],
            'provenance': {}
        }

        # Make request
        response = self.client.post(
            '/api/analyze',
            json={'content_id': 'UNKNOWN-SHOW'}
        )
        data = response.json()

        # Verify response (should be 400 Bad Request)
        self.assertEqual(response.status_code, 400)
        self.assertIn('detail', data)
        self.assertEqual(data['detail']['type'], 'NO_DATA_FOUND')

    @patch('api.main.agent')
    def test_analyze_endpoint_internal_error(self, mock_agent):
        """Test analysis endpoint when internal error occurs."""
        # Mock the agent's analyze_content method to raise an exception
        mock_agent.analyze_content.side_effect = Exception("Internal processing error")

        # Make request
        response = self.client.post(
            '/api/analyze',
            json={'content_id': 'SHOW-042'}
        )
        data = response.json()

        # Verify response (should be 500 Internal Server Error)
        self.assertEqual(response.status_code, 500)
        self.assertIn('detail', data)
        self.assertIn('Internal server error', data['detail'])

    def test_api_root_endpoint(self):
        """Test the API root endpoint."""
        response = self.client.get('/api/')
        data = response.json()

        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Content Performance Signal Agent API')
        self.assertEqual(data['version'], '0.1.0')
        self.assertEqual(data['docs'], '/api/docs')

    def test_frontend_served_at_root(self):
        """Test that the frontend is served at the root path."""
        response = self.client.get('/')
        # Should return HTML content
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.headers['content-type'])
        self.assertIn('Content Performance Signal Agent', response.text)


if __name__ == '__main__':
    unittest.main()