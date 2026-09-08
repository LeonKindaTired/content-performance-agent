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


MOCK_EPISODE_DATA = {
    'SHOW-001': [
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
        }
    ],
    'SHOW-007': [
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
            'watch_time_minutes': 453600,
            'completion_rate': 0.64,
            'returning_viewers': 3542,
            'new_viewers': 10258,
            'engagement_events': 70560
        },
        {
            'content_id': 'SHOW-007',
            'episode_number': 3,
            'episode_date': '2023-05-15',
            'viewers': 12696,
            'unique_viewers': 10157,
            'watch_time_minutes': 381024,
            'completion_rate': 0.58,
            'returning_viewers': 2926,
            'new_viewers': 9770,
            'engagement_events': 57154
        },
        {
            'content_id': 'SHOW-007',
            'episode_number': 4,
            'episode_date': '2023-06-15',
            'viewers': 11680,
            'unique_viewers': 9344,
            'watch_time_minutes': 319440,
            'completion_rate': 0.52,
            'returning_viewers': 2419,
            'new_viewers': 9261,
            'engagement_events': 43747
        },
        {
            'content_id': 'SHOW-007',
            'episode_number': 5,
            'episode_date': '2023-07-15',
            'viewers': 10746,
            'unique_viewers': 8597,
            'watch_time_minutes': 267408,
            'completion_rate': 0.46,
            'returning_viewers': 1995,
            'new_viewers': 8751,
            'engagement_events': 32341
        },
        {
            'content_id': 'SHOW-007',
            'episode_number': 6,
            'episode_date': '2023-08-15',
            'viewers': 9886,
            'unique_viewers': 7909,
            'watch_time_minutes': 223344,
            'completion_rate': 0.40,
            'returning_viewers': 1644,
            'new_viewers': 8242,
            'engagement_events': 23125
        },
        {
            'content_id': 'SHOW-007',
            'episode_number': 7,
            'episode_date': '2023-09-15',
            'viewers': 9095,
            'unique_viewers': 7276,
            'watch_time_minutes': 185856,
            'completion_rate': 0.34,
            'returning_viewers': 1349,
            'new_viewers': 6746,
            'engagement_events': 15896
        },
        {
            'content_id': 'SHOW-007',
            'episode_number': 8,
            'episode_date': '2023-10-15',
            'viewers': 8367,
            'unique_viewers': 6694,
            'watch_time_minutes': 153792,
            'completion_rate': 0.28,
            'returning_viewers': 1095,
            'new_viewers': 6272,
            'engagement_events': 10407
        }
    ],
    'SHOW-042': [
        {
            'content_id': 'SHOW-042',
            'episode_number': 1,
            'episode_date': '2023-02-01',
            'viewers': 12000,
            'unique_viewers': 9840,
            'watch_time_minutes': 432000,
            'completion_rate': 0.75,
            'returning_viewers': 4500,
            'new_viewers': 7500,
            'engagement_events': 86400
        },
        {
            'content_id': 'SHOW-042',
            'episode_number': 2,
            'episode_date': '2023-03-01',
            'viewers': 11520,
            'unique_viewers': 9446,
            'watch_time_minutes': 414720,
            'completion_rate': 0.73,
            'returning_viewers': 4222,
            'new_viewers': 7298,
            'engagement_events': 82944
        },
        {
            'content_id': 'SHOW-042',
            'episode_number': 3,
            'episode_date': '2023-04-01',
            'viewers': 11059,
            'unique_viewers': 9068,
            'watch_time_minutes': 398124,
            'completion_rate': 0.5,
            'returning_viewers': 2765,
            'new_viewers': 8294,
            'engagement_events': 59718
        },
        {
            'content_id': 'SHOW-042',
            'episode_number': 4,
            'episode_date': '2023-05-01',
            'viewers': 10617,
            'unique_viewers': 8706,
            'watch_time_minutes': 382400,
            'completion_rate': 0.58,
            'returning_viewers': 3079,
            'new_viewers': 7538,
            'engagement_events': 57341
        },
        {
            'content_id': 'SHOW-042',
            'episode_number': 5,
            'episode_date': '2023-06-01',
            'viewers': 10194,
            'unique_viewers': 8359,
            'watch_time_minutes': 367104,
            'completion_rate': 0.56,
            'returning_viewers': 2868,
            'new_viewers': 7326,
            'engagement_events': 55066
        },
        {
            'content_id': 'SHOW-042',
            'episode_number': 6,
            'episode_date': '2023-07-01',
            'viewers': 9786,
            'unique_viewers': 8025,
            'watch_time_minutes': 352220,
            'completion_rate': 0.54,
            'returning_viewers': 2667,
            'new_viewers': 7119,
            'engagement_events': 52891
        },
        {
            'content_id': 'SHOW-042',
            'episode_number': 7,
            'episode_date': '2023-08-01',
            'viewers': 9395,
            'unique_viewers': 7704,
            'watch_time_minutes': 337740,
            'completion_rate': 0.52,
            'returning_viewers': 2475,
            'new_viewers': 6920,
            'engagement_events': 50810
        },
        {
            'content_id': 'SHOW-042',
            'episode_number': 8,
            'episode_date': '2023-09-01',
            'viewers': 9019,
            'unique_viewers': 7396,
            'watch_time_minutes': 323830,
            'completion_rate': 0.50,
            'returning_viewers': 2291,
            'new_viewers': 6728,
            'engagement_events': 48816
        }
    ],
    'SHOW-999': [
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
            'engagement_events': 2000
        },
        {
            'content_id': 'SHOW-999',
            'episode_number': 2,
            'episode_date': '2023-06-01',
            'viewers': 450,
            'unique_viewers': 338,
            'watch_time_minutes': 10800,
            'completion_rate': 0.55,
            'returning_viewers': 124,
            'new_viewers': 326,
            'engagement_events': 1485
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
    def __init__(self):
        self.use_mock = os.getenv('USE_MOCK_DATA', 'false').lower() == 'true'
        self.client = None
        if not self.use_mock:
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

                self.client.ping()
                logger.info("ClickHouse client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize ClickHouse client: {e}. Falling back to mock data.")
                self.use_mock = True
                self.client = None
        else:
            logger.info("Using mock data for ClickHouse tool")

    def test_connection(self) -> bool:
        """Test ClickHouse connection. Returns True if connected, False otherwise."""
        if self.use_mock or self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"ClickHouse connection test failed: {e}")
            return False

    def get_content_performance(self, content_id: str, date_range: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Retrieve episode performance data for a content ID."""
        if self.use_mock:
            return self._get_mock_content_performance(content_id, date_range)


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
        """
        params = [content_id]

        if date_range:
            if 'start' in date_range:
                query += " AND episode_date >= ?"
                params.append(date_range['start'])
            if 'end' in date_range:
                query += " AND episode_date <= ?"
                params.append(date_range['end'])

        query += " ORDER BY episode_number"

        try:
            result = self.client.query(query, parameters=params)

            columns = result.column_names
            rows = result.result_rows
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
            return data
        except Exception as e:
            logger.error(f"Error querying ClickHouse for content performance: {e}")
            return []

    def get_content_metadata(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve content metadata for a content ID."""
        if self.use_mock:
            return MOCK_CONTENT_METADATA.get(content_id)

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
                row = result.result_rows[0]
                columns = result.column_names
                return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Error querying ClickHouse for content metadata: {e}")
            return None


    def _get_mock_content_performance(self, content_id: str, date_range: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        data = MOCK_EPISODE_DATA.get(content_id, [])
        if not date_range:
            return data


        filtered = []
        start_str = date_range.get('start')
        end_str = date_range.get('end')

        for episode in data:
            ep_date = episode['episode_date']
            if start_str and ep_date < start_str:
                continue
            if end_str and ep_date > end_str:
                continue
            filtered.append(episode)
        return sorted(filtered, key=lambda x: x['episode_number'])


def get_clickhouse_tool() -> ClickHouseTool:
    """Factory function to get ClickHouse tool instance."""
    return ClickHouseTool()