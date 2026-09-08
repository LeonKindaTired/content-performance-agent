"""
Content Performance Signal Agent (without Google ADK).
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import date, datetime


import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tools.clickhouse_tool import get_clickhouse_tool, ClickHouseTool
from analytics.data_quality import assess_data_quality, validate_content_id
from analytics.signals import aggregate_episode_data
from analytics.decision_policy import evaluate_decision, calculate_confidence, Recommendation
from agent.prompts import SYSTEM_INSTRUCTION, format_prompt

logger = logging.getLogger(__name__)

class ContentPerformanceAgent:
    """
    Agent that performs content performance analysis workflow:
    Content ID → ClickHouse → Data Validation → Signals → Decision Policy → Reasoning → Recommendation
    """

    def __init__(self):

        self._clickhouse_tool = get_clickhouse_tool()
        logger.info("ClickHouse tool initialized")

    def _validate_content_id(self, content_id: str) -> Dict[str, Any]:
        """
        Tool: Validate content ID format.
        """
        is_valid, error_msg = validate_content_id(content_id)
        return {
            "valid": is_valid,
            "error": error_msg if not is_valid else None
        }

    def _get_content_data(self, content_id: str, date_range: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Tool: Retrieve content performance data from ClickHouse.
        Returns raw episode data and metadata.
        """
        try:

            episodes = self._clickhouse_tool.get_content_performance(content_id, date_range)


            metadata = self._clickhouse_tool.get_content_metadata(content_id)

            return {
                "content_id": content_id,
                "episodes": episodes,
                "metadata": metadata,
                "retrieved_at": datetime.utcnow().isoformat() + "Z"
            }
        except Exception as e:
            logger.error(f"Error retrieving content data: {e}")
            return {
                "content_id": content_id,
                "error": str(e),
                "episodes": [],
                "metadata": None
            }

    def analyze_content(self, content_id: str) -> Dict[str, Any]:
        """
        Main analysis workflow.
        """
        logger.info(f"Starting analysis for content_id: {content_id}")


        validation = self._validate_content_id(content_id)
        if not validation["valid"]:
            return self._create_error_response(
                content_id,
                "INVALID_INPUT",
                validation["error"]
            )


        data_response = self._get_content_data(content_id)
        if "error" in data_response:
            return self._create_error_response(
                content_id,
                "DATA_RETRIEVAL_ERROR",
                data_response["error"]
            )

        episodes = data_response.get("episodes", [])
        metadata = data_response.get("metadata")

        if not episodes:
            return self._create_error_response(
                content_id,
                "NO_DATA_FOUND",
                f"No episode performance data found for content ID: {content_id}"
            )


        data_quality = assess_data_quality(episodes)


        aggregated = aggregate_episode_data(episodes)


        metrics_for_policy = {
            "total_viewers": aggregated.get("total_viewers", 0),
            "average_completion_rate": aggregated.get("average_completion_rate", 0.0),

        }

        signals_for_policy = {
            **aggregated,

            "retention_decay": aggregated.get("retention_decay", {"relative_decay": 0.0}),
            "drop_off_concentration": aggregated.get("drop_off_concentration"),
            "viewership_velocity": aggregated.get("viewership_velocity", 0.0),
            "engagement_velocity": aggregated.get("engagement_velocity", 0.0),
            "new_viewer_trend": aggregated.get("new_viewer_trend", 0.0),
            "returning_viewer_trend": aggregated.get("returning_viewer_trend", 0.0)
        }


        policy = self._get_decision_policy()
        decision_result = evaluate_decision(signals_for_policy, policy)
        recommendation = decision_result["recommendation"]
        decision_basis = decision_result["decision_basis"]


        confidence = calculate_confidence(data_quality, signals_for_policy, policy)


        evidence_for_reasoning = {
            "data_quality": data_quality,
            "metrics": metrics_for_policy,
            "signals": {
                "retention_decay": aggregated.get("retention_decay"),
                "drop_off_concentration": aggregated.get("drop_off_concentration"),
                "viewership_velocity": aggregated.get("viewership_velocity"),
                "engagement_velocity": aggregated.get("engagement_velocity"),
                "new_viewer_trend": aggregated.get("new_viewer_trend"),
                "returning_viewer_trend": aggregated.get("returning_viewer_trend"),
            }
        }


        analysis_result = {
            "content_id": content_id,
            "content_title": metadata.get("title") if metadata else None,
            "data_quality": data_quality,
            "metrics": metrics_for_policy,
            "signals": {
                "retention_decay": aggregated.get("retention_decay"),
                "drop_off_concentration": aggregated.get("drop_off_concentration"),
                "viewership_velocity": aggregated.get("viewership_velocity"),
                "engagement_velocity": aggregated.get("engagement_velocity"),
                "new_viewer_trend": aggregated.get("new_viewer_trend"),
                "returning_viewer_trend": aggregated.get("returning_viewer_trend"),
            },
            "deterministic_recommendation": recommendation,
            "deterministic_confidence": confidence,
            "decision_basis": decision_basis,
            "warnings": data_quality.get("warnings", []),
            "provenance": {
                "data_source": "ClickHouse",
                "retrieved_at": data_response.get("retrieved_at"),
                "clickhouse_query_id": None
            }
        }

        return analysis_result

    def _create_error_response(self, content_id: str, error_type: str, message: str) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "content_id": content_id,
            "error": {
                "type": error_type,
                "message": message
            },
            "recommendation": "INVESTIGATE",
            "confidence": 0.0,
            "data_quality": {"status": "ERROR"},
            "metrics": {},
            "signals": {},
            "warnings": [message]
        }

    def _get_decision_policy(self) -> Dict[str, Any]:
        """
        Load decision policy from environment variables or use defaults.
        In a production implementation, this would load from a config file.
        """

        return {
            "retention_positive_threshold": float(os.getenv('RETENTION_POS_THRESHOLD', '0.10')),
            "retention_negative_threshold": float(os.getenv('RETENTION_NEG_THRESHOLD', '-0.15')),
            "acquisition_positive_threshold": float(os.getenv('ACQUISITION_POS_THRESHOLD', '0.10')),
            "acquisition_negative_threshold": float(os.getenv('ACQUISITION_NEG_THRESHOLD', '-0.10')),
            "engagement_positive_threshold": float(os.getenv('ENGAGEMENT_POS_THRESHOLD', '0.10')),
            "engagement_negative_threshold": float(os.getenv('ENGAGEMENT_NEG_THRESHOLD', '-0.10')),
            "minimum_sample_size": int(os.getenv('MIN_SAMPLE_SIZE', '500'))
        }


def create_agent() -> ContentPerformanceAgent:
    return ContentPerformanceAgent()


if __name__ == "__main__":
    import asyncio

    async def test_agent():
        agent = create_agent()

        print("Testing validation tool:")
        validation_result = agent._validate_content_id("SHOW-042")
        print(json.dumps(validation_result, indent=2))


        print("\nTesting data retrieval:")
        try:
            data_result = agent._get_content_data("SHOW-042")
            print(f"Retrieved {len(data_result.get('episodes', []))} episodes")
            if data_result.get('episodes'):
                print("First episode:", json.dumps(data_result['episodes'][0], indent=2))
        except Exception as e:
            print(f"Data retrieval failed (expected if ClickHouse not running): {e}")


        print("\nTesting full analysis:")
        try:
            analysis_result = agent.analyze_content("SHOW-042")
            print(json.dumps(analysis_result, indent=2))
        except Exception as e:
            print(f"Analysis failed (expected if ClickHouse not running): {e}")


    asyncio.run(test_agent())