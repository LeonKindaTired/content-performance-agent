#!/usr/bin/env python3
"""
Test ClickHouse connection with the same parameters as in .env
"""

import os
from clickhouse_connect import get_client
from clickhouse_connect.driver.exceptions import ClickHouseError

def test_connection():
    try:
        host = os.getenv('CLICKHOUSE_HOST', 'localhost')
        port = int(os.getenv('CLICKHOUSE_PORT', 8123))
        username = os.getenv('CLICKHOUSE_USER', 'default')
        password = os.getenv('CLICKHOUSE_PASSWORD', '')
        database = os.getenv('CLICKHOUSE_DATABASE', 'media_analytics')
        secure = os.getenv('CLICKHOUSE_SECURE', 'false').lower() == 'true'

        print(f"Connecting to {host}:{port} as {username} (secure={secure})")
        client = get_client(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            secure=secure
        )
        # Test connection
        client.ping()
        print("Connection successful")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()