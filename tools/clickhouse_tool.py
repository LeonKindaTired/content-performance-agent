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

class ClickHouseTool:
    """
    Tool to query ClickHouse for content performance data.
    """

    def __init__(self):
        self.client = None
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
        except Exception as e:
            logger.error(f"Failed to initialize ClickHouse client: {e}")
            self.client = None

    def get_content_performance(
        self,
        content_id: str,
        date_range: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve episode performance data for a given content ID.
        Returns a list of dictionaries representing rows from episode_performance table.
        """
        if not self.client:
            raise RuntimeError("ClickHouse client not initialized")

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
        if not self.client:
            return False
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