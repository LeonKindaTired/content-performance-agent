"""
ClickHouse tool for retrieving content performance data.
"""

from typing import Dict, List, Any, Optional
from clickhouse_connect import get_client
from clickhouse_connect.driver.exceptions import ClickHouseError
import os
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

# Mock data for demonstration when ClickHouse is not available
MOCK_EPISODE_DATA = {
    'SHOW-001': [  # Successful show
        {
            'content_id': 'SHOW-001',
            'episode_number': 1,
            'episode_date': '2023-02-01',
            'viewers': 10000,
            'unique_viewers': 8500,
            'watch_time_minutes': 400000,
            'completion_rate': 0.8,
            'returning_viewers': 4800,
            'new_viewers': 5200,
            'engagement_events': 80000
        },
        {
            'content_id': 'SHOW-001',
            'episode_number': 2,
            'episode_date': '2023-03-01',
            'viewers': 10500,
            'unique_viewers': 8925,
            'watch_time_minutes': 441000,
            'completion_rate': 0.82,
            'returning_viewers': 5100,
            'new_viewers': 5400,
            'engagement_events': 86100
        },
        {
            'content_id': 'SHOW-001',
            'episode_number': 3,
            'episode_date': '2023-04-01',
            'viewers': 11000,
            'unique_viewers': 9350,
            'watch_time_minutes': 484000,
            'completion_rate': 0.84,
            'returning_viewers': 5400,
            'new_viewers': 5600,
            'engagement_events': 92400
        },
        {
            'content_id': 'SHOW-001',
            'episode_number': 4,
            'episode_date': '2023-05-01',
            'viewers': 11500,
            'unique_viewers': 9775,
            'watch_time_minutes': 529000,
            'completion_rate': 0.86,
            'returning_viewers': 5700,
            'new_viewers': 5800,
            'engagement_events': 98900
        },
        {
            'content_id': 'SHOW-001',
            'episode_number': 5,
            'episode_date': '2023-06-01',
            'viewers': 12000,
            'unique_viewers': 10200,
            'watch_time_minutes': 576000,
            'completion_rate': 0.88,
            'returning_viewers': 6000,
            'new_viewers': 6000,
            'engagement_events': 105600
        },
        {
            'content_id': 'SHOW-001',
            'episode_number': 6,
            'episode_date': '2023-07-01',
            'viewers': 12500,
            'unique_viewers': 10625,
            'watch_time_minutes': 625000,
            'completion_rate': 0.9,
            'returning_viewers': 6300,
            'new_viewers': 6200,
            'engagement_events': 112500
        },
        {
            'content_id': 'SHOW-001',
            'episode_number': 7,
            'episode_date': '2023-08-01',
            'viewers': 13000,
            'unique_viewers': 11050,
            'watch_time_minutes': 676000,
            'completion_rate': 0.91,
            'returning_viewers': 6600,
            'new_viewers': 6400,
            'engagement_events': 118300
        },
        {
            'content_id': 'SHOW-001',
            'episode_number': 8,
            'episode_date': '2023-09-01',
            'viewers': 13500,
            'unique_viewers': 11475,
            'watch_time_minutes': 729000,
            'completion_rate': 0.92,
            'returning_viewers': 6900,
            'new_viewers': 6600,
            'engagement_events': 124200
        }
    ],
    'SHOW-007': [  # Acquisition strong, retention weak
        {
            'content_id': 'SHOW-007',
            'episode_number': 1,
            'episode_date': '2023-03-15',
            'viewers': 15000,
            'unique_viewers': 12000,
            'watch_time_minutes': 525000,
            'completion_rate': 0.7,
            'returning_viewers': 4200,
            'new_viewers': 10800,
            'engagement_events': 84000
        },
        {
            'content_id': 'SHOW-007',
            'episode_number': 2,
            'episode_date': '2023-04-15',
            'viewers': 13800,
            'unique_viewers': 11040,
            'watch_time_minutes': 441000,
            'completion_rate': 0.64,
            'returning_viewers': 3500,
            'new_viewers': 10300,
            'engagement_events': 73920
        },
        {
            'content_id': 'SHOW-007',
            'episode_number': 3,
            'episode_date': '2023-05-15',
            'viewers': 12600,
            'unique_viewers': 10080,
            'watch_time_minutes': 362880,
            'completion_rate': 0.58,
            'returning_viewers': 2900,
            'new_viewers': 9700,
            'engagement_events': 63504
        },
        {
            'content_id': 'SHOW-007',
            'episode_number': 4,
            'episode_date': '2023-06-15',
            'viewers': 11400,
            'unique_viewers': 9120,
            'watch_time_minutes': 290304,
            'completion_rate': 0.52,
            'returning_viewers': 2400,
            'new_viewers': 9000,
            'engagement_events': 52992
        },
        {
            'content_id': 'SHOW-007',
            'episode_number': 5,
            'episode_date': '2023-07-15',
            'viewers': 10200,
            'unique_viewers': 8160,
            'watch_time_minutes': 233472,
            'completion_rate': 0.46,
            'returning_viewers': 1900,
            'new_viewers': 8300,
            'engagement_events': 42336
        },
        {
            'content_id': 'SHOW-007',
            'episode_number': 6,
            'episode_date': '2023-08-15',
            'viewers': 9000,
            'unique_viewers': 7200,
            'watch_time_minutes': 181440,
            'completion_rate': 0.4,
            'returning_viewers': 1500,
            'new_viewers': 7500,
            'engagement_events': 31104
        },
        {
            'content_id': 'SHOW-007',
            'episode_number': 7,
            'episode_date': '2023-09-15',
            'viewers': 7800,
            'unique_viewers': 6240,
            'watch_time_minutes': 140256,
            'completion_rate': 0.34,
            'returning_viewers': 1100,
            'new_viewers': 6700,
            'engagement_events': 24192
        },
        {
            'content_id': 'SHOW-007',
            'episode_number': 8,
            'episode_date': '2023-10-15',
            'viewers': 6600,
            'unique_viewers': 5280,
            'watch_time_minutes': 104544,
            'completion_rate': 0.28,
            'returning_viewers': 800,
            'new_viewers': 5800,
            'engagement_events': 16896
        }
    ],
    'SHOW-042': [  # Failing show (declining retention with episode 3 drop-off)
        {
            'content_id': 'SHOW-042',
            'episode_number': 1,
            'episode_date': '2023-02-01',
            'viewers': 12000,
            'unique_viewers': 9840,
            'watch_time_minutes': 450000,
            'completion_rate': 0.75,
            'returning_viewers': 4500,
            'new_viewers': 7500,
            'engagement_events': 90000
        },
        {
            'content_id': 'SHOW-042',
            'episode_number': 2,
            'episode_date': '2023-03-01',
            'viewers': 11520,
            'unique_viewers': 9446,
            'watch_time_minutes': 414720,
            'completion_rate': 0.73,
            'returning_viewers': 4200,
            'new_viewers': 7320,
            'engagement_events': 84672
        },
        {
            'content_id': 'SHOW-042',
            'episode_number': 3,
            'episode_date': '2023-04-01',
            'viewers': 11040,
            'unique_viewers': 9053,
            'watch_time_minutes': 332640,
            'completion_rate': 0.5,  # Big drop at episode 3
            'returning_viewers': 2700,
            'new_viewers': 8340,
            'engagement_events': 55440
        },
        {
            'content_id': 'SHOW-042',
            'episode_number': 4,
            'episode_date': '2023-05-01',
            'viewers': 10560,
            'unique_viewers': 8659,
            'watch_time_minutes': 295680,
            'completion_rate': 0.58,
            'returning_viewers': 3100,
            'new_viewers': 7460,
            'engagement_events': 62496
        },
        {
            'content_id': 'SHOW-042',
            'episode_number': 5,
            'episode_date': '2023-06-01',
            'viewers': 10080,
            'unique_viewers': 8266,
            'watch_time_minutes': 262080,
            'completion_rate': 0.62,
            'returning_viewers': 3500,
            'new_viewers': 6580,
            'engagement_events': 69552
        },
        {
            'content_id': 'SHOW-042',
            'episode_number': 6,
            'episode_date': '2023-07-01',
            'viewers': 9600,
            'unique_viewers': 7872,
            'watch_time_minutes': 230400,
            'completion_rate': 0.66,
            'returning_viewers': 3900,
            'new_viewers': 5700,
            'engagement_events': 76608
        },
        {
            'content_id': 'SHOW-042',
            'episode_number': 7,
            'episode_date': '2023-08-01',
            'viewers': 9120,
            'unique_viewers': 7478,
            'watch_time_minutes': 205632,
            'completion_rate': 0.7,
            'returning_viewers': 4200,
            'new_viewers': 4920,
            'engagement_events': 80256
        },
        {
            'content_id': 'SHOW-042',
            'episode_number': 8,
            'episode_date': '2023-09-01',
            'viewers': 8640,
            'unique_viewers': 7085,
            'watch_time_minutes': 182784,
            'completion_rate': 0.74,
            'returning_viewers': 4500,
            'new_viewers': 4140,
            'engagement_events': 84672
        }
    ],
    'SHOW-999': [  # Insufficient evidence (low viewership)
        {
            'content_id': 'SHOW-999',
            'episode_number': 1,
            'episode_date': '2023-05-01',
            'viewers': 500,
            'unique_viewers': 375,
            'watch_time_minutes': 12000,
            'completion_rate': 0.6,
            'returning_viewers': 150,
            'new_viewers': 350,
            'engagement_events': 3000
        },
        {
            'content_id': 'SHOW-999',
            'episode_number': 2,
            'episode_date': '2023-06-01',
            'viewers': 450,
            'unique_viewers': 338,
            'watch_time_minutes': 9900,
            'completion_rate': 0.55,
            'returning_viewers': 120,
            'new_viewers': 330,
            'engagement_events': 2475
        }
    ]
}

MOCK_CONTENT_METADATA = {
    'SHOW-001': {
        'content_id': 'SHOW-001',
        'title': 'The Great Adventure',
        'content_type': 'series',
        'genre': 'Drama',
        'release_date': '2023-01-15',
        'total_episodes': 8
    },
    'SHOW-007': {
        'content_id': 'SHOW-007',
        'title': 'Mystery Manor',
        'content_type': 'series',
        'genre': 'Mystery',
        'release_date': '2023-03-01',
        'total_episodes': 8
    },
    'SHOW-042': {
        'content_id': 'SHOW-042',
        'title': 'Lost in Space',
        'content_type': 'series',
        'genre': 'Sci-Fi',
        'release_date': '2023-02-01',
        'total_episodes': 8
    },
    'SHOW-999': {
        'content_id': 'SHOW-999',
        'title': 'Short-lived Show',
        'content_type': 'series',
        'genre': 'Comedy',
        'release_date': '2023-05-01',
        'total_episodes': 2
    }
}

class ClickHouseTool:
    """
    Tool to query ClickHouse for content performance data.
    """

    def __init__(self):
        self.client = None
        self.use_mock = False
        self._initialize_client()

    def _initialize_client(self):
        """Initialize ClickHouse client from environment variables."""
        try:
            host = os.getenv('CLICKHOUSE_HOST', 'localhost')
            port = int(os.getenv('CLICKHOUSE_PORT', 8123))
            username = os.getenv('CLICKHOUSE_USER', 'default')
            password = os.getenv('CLICKHOUSE_PASSWORD', '')
            database = os.getenv('CLICKHOUSE_DATABASE', 'media_analytics')
            secure = os.getenv('CLICKHOUSE_SECURE', 'false').lower() == 'true'

            self.client = get_client(
                host=host,
                port=port,
                username=username,
                password=password,
                database=database,
                secure=secure
            )
            # Test connection
            self.client.ping()
            logger.info("ClickHouse client initialized successfully")
            self.use_mock = False
        except Exception as e:
            logger.warning(f"Failed to initialize ClickHouse client: {e}")
            logger.info("Falling back to mock data for demonstration")
            self.client = None
            self.use_mock = True

    def get_content_performance(
        self,
        content_id: str,
        date_range: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve episode performance data for a given content ID.
        Returns a list of dictionaries representing rows from episode_performance table.
        """
        # Use mock data if ClickHouse is not available
        if self.use_mock or not self.client:
            logger.info(f"Using mock data for content_id: {content_id}")
            mock_data = MOCK_EPISODE_DATA.get(content_id, [])

            # Apply date range filtering if provided (simplified for mock)
            if date_range and mock_data:
                start_date = date_range.get('start')
                end_date = date_range.get('end')
                if start_date or end_date:
                    filtered_data = []
                    for episode in mock_data:
                        episode_date = episode['episode_date']
                        if start_date and episode_date < start_date:
                            continue
                        if end_date and episode_date > end_date:
                            continue
                        filtered_data.append(episode)
                    return filtered_data

            return mock_data

        # Validate content_id format (basic)
        if not content_id or not isinstance(content_id, str):
            raise ValueError("Invalid content ID")

        # Prevent SQL injection by using parameterized query
        # ClickHouse client supports parameter substitution with ?
        query = """
            SELECT
                content_id,
                episode_number,
                episode_date,
                viewers,
                unique_viewers,
                watch_time_minutes,
                completion_rate,
                returning_viewers,
                new_viewers,
                engagement_events
            FROM episode_performance
            WHERE content_id = ?
            ORDER BY episode_number
        """

        params = [content_id]

        # Add date range filtering if provided
        if date_range:
            start_date = date_range.get('start')
            end_date = date_range.get('end')
            if start_date and end_date:
                query = query.replace("ORDER BY episode_number", "AND episode_date BETWEEN ? AND ? ORDER BY episode_number")
                params.extend([start_date, end_date])
            elif start_date:
                query = query.replace("ORDER BY episode_number", "AND episode_date >= ? ORDER BY episode_number")
                params.append(start_date)
            elif end_date:
                query = query.replace("ORDER BY episode_number", "AND episode_date <= ? ORDER BY episode_number")
                params.append(end_date)

        try:
            logger.info(f"Executing ClickHouse query for content_id: {content_id}")
            result = self.client.query(query, parameters=params)
            # Convert to list of dictionaries
            columns = result.column_names
            rows = []
            for row in result.result_rows:
                rows.append(dict(zip(columns, row)))
            logger.info(f"Retrieved {len(rows)} rows for content_id: {content_id}")
            return rows
        except ClickHouseError as e:
            logger.error(f"ClickHouse error: {e}")
            raise RuntimeError(f"Failed to retrieve data from ClickHouse: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error querying ClickHouse: {e}")
            raise RuntimeError(f"Unexpected error: {str(e)}")

    def get_content_metadata(self, content_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata for a content ID from content_catalog table.
        """
        # Use mock data if ClickHouse is not available
        if self.use_mock or not self.client:
            logger.info(f"Using mock metadata for content_id: {content_id}")
            return MOCK_CONTENT_METADATA.get(content_id)

        if not self.client:
            raise RuntimeError("ClickHouse client not initialized")

        query = """
            SELECT
                content_id,
                title,
                content_type,
                genre,
                release_date,
                total_episodes
            FROM content_catalog
            WHERE content_id = ?
        """

        try:
            result = self.client.query(query, parameters=[content_id])
            if result.result_rows:
                columns = result.column_names
                row = result.result_rows[0]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Error retrieving content metadata: {e}")
            return None

    def test_connection(self) -> bool:
        """Test the ClickHouse connection."""
        if self.use_mock or not self.client:
            return False  # Mock mode doesn't have a real connection
        try:
            self.client.ping()
            return True
        except Exception:
            return False

# Factory function for easy instantiation
def get_clickhouse_tool() -> ClickHouseTool:
    return ClickHouseTool()

# Example usage (for testing)
if __name__ == "__main__":
    tool = ClickHouseTool()
    if tool.test_connection():
        print("Connection successful")
        # Try to fetch a known content ID
        try:
            data = tool.get_content_performance("SHOW-001")
            print(f"Found {len(data)} episodes for SHOW-001")
            if data:
                print("First episode:", data[0])
        except Exception as e:
            print(f"Error fetching data: {e}")
    else:
        print("Connection failed")