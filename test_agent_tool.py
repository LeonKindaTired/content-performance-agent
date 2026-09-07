#!/usr/bin/env python3
"""
Test the agent's ClickHouse tool state.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from agent.agent import ContentPerformanceAgent

def test_agent_tool():
    """Test the agent's ClickHouse tool."""
    print("Creating agent...")
    agent = ContentPerformanceAgent()
    tool = agent._clickhouse_tool
    print(f"Tool use_mock: {tool.use_mock}")
    print(f"Tool client is None: {tool.client is None}")
    if tool.client is not None:
        print("Client is not None, trying to ping...")
        try:
            tool.client.ping()
            print("Ping succeeded")
        except Exception as e:
            print(f"Ping failed: {e}")
    else:
        print("Client is None")
    # Test the test_connection method
    status = tool.test_connection()
    print(f"test_connection returned: {status}")

if __name__ == "__main__":
    test_agent_tool()