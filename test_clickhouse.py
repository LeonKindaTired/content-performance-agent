#!/usr/bin/env python3
"""
Test the ClickHouse tool directly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from tools.clickhouse_tool import get_clickhouse_tool

def test_clickhouse_tool():
    """Test the ClickHouse tool."""
    print("Testing ClickHouse tool...")
    tool = get_clickhouse_tool()

    # Check if using mock or real
    if tool.use_mock:
        print("Using mock data")
    else:
        print("Using real ClickHouse connection")
        if tool.test_connection():
            print("Connection successful")
        else:
            print("Connection failed")

    # Try to get content performance for SHOW-001
    try:
        data = tool.get_content_performance("SHOW-001")
        print(f"Retrieved {len(data)} episodes for SHOW-001")
        if data:
            print("First episode:", data[0])
            print("Last episode:", data[-1])
    except Exception as e:
        print(f"Error retrieving data: {e}")
        return False

    # Try to get content metadata
    try:
        metadata = tool.get_content_metadata("SHOW-001")
        print(f"Metadata: {metadata}")
    except Exception as e:
        print(f"Error retrieving metadata: {e}")
        return False

    return True

if __name__ == "__main__":
    success = test_clickhouse_tool()
    if success:
        print("\nTest passed!")
    else:
        print("\nTest failed!")
        sys.exit(1)