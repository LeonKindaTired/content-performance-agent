"""
Content Performance Signal Agent using Google ADK.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import date, datetime

from google.adk.agents import Agent
from google.adk.tools import BaseTool, FunctionTool
from google.adk.models import Gemini

# Import our modules
from content_performance_signal_agent.tools.clickhouse_tool import get_clickhouse_tool, ClickHouseTool
from content_performance_signal_agent.analytics.data_quality import assess_data_quality, validate_content_id
from content_performance_signal_agent.analytics.signals import aggregate_episode_data
from content_performance_signal_agent.analytics.decision_policy import evaluate_decision, calculate_confidence, Recommendation
from content_performance_signal_agent.agent.prompts import SYSTEM_INSTRUCTION, format_prompt

logger = logging.getLogger(__name__)

class ContentPerformanceAgent(Agent):
    """
    Agent that performs content performance analysis workflow:
    Content ID → ClickHouse → Data Validation → Signals → Decision Policy → Gemini Reasoning → Recommendation
    """

    def __init__(self):
        # Initialize ClickHouse tool
        ContentPerformanceAgent._clickhouse_tool = get_clickhouse_tool()
        print("Initializing ClickHouse tool")

        # Define the tools this agent can use
        tools = [
            FunctionTool(
                func=self._get_content_data,
                
            ),
            FunctionTool(
                func=self._validate_content_id,
                
            )
        ]

        # Initialize the Gemini model
        # Note: In ADK, we typically specify the model in the agent configuration
        # We'll rely on environment variables for the Gemini model
        super().__init__(
            name="content_performance_agent",
            description="Analyzes content performance data to provide evidence-based recommendations",
            instruction=SYSTEM_INSTRUCTION,
            tools=tools,
            # The model will be set via environment variables or ADK configuration
            # For Gemini, we can use: model="gemini-pro"
            # But ADK handles this differently; we'll let the runtime configure it
        )

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
            # Get episode performance data
            episodes = ContentPerformanceAgent._clickhouse_tool.get_content_performance(content_id, date_range)

            # Get content metadata
            metadata = ContentPerformanceAgent._clickhouse_tool.get_content_metadata(content_id)

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
        This is not an ADK tool but the core logic that the agent will execute.
        In ADK, we might override the run method or use this as a helper.
        """
        logger.info(f"Starting analysis for content_id: {content_id}")

        # Step 1: Validate input
        validation = self._validate_content_id(content_id)
        if not validation["valid"]:
            return self._create_error_response(
                content_id,
                "INVALID_INPUT",
                validation["error"]
            )

        # Step 2: Retrieve data from ClickHouse
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

        # Step 3: Validate data quality
        data_quality = assess_data_quality(episodes)

        # Step 4: Compute deterministic signals and metrics
        aggregated = aggregate_episode_data(episodes)

        # Prepare metrics for decision policy
        metrics_for_policy = {
            "total_viewers": aggregated.get("total_viewers", 0),
            "average_completion_rate": aggregated.get("average_completion_rate", 0.0),
            # Add other metrics as needed
        }
        # Merge aggregated signals into the metrics dict for policy evaluation
        signals_for_policy = {
            **aggregated,
            # Ensure we have the expected signal names
            "retention_decay": aggregated.get("retention_decay", {"relative_decay": 0.0}),
            "drop_off_concentration": aggregated.get("drop_off_concentration"),
            "viewership_velocity": aggregated.get("viewership_velocity", 0.0),
            "engagement_velocity": aggregated.get("engagement_velocity", 0.0),
            "new_viewer_trend": aggregated.get("new_viewer_trend", 0.0),
            "returning_viewer_trend": aggregated.get("returning_viewer_trend", 0.0)
        }

        # Step 5: Apply decision policy
        # Load policy from environment or config (for now, use defaults)
        policy = self._get_decision_policy()
        decision_result = evaluate_decision(signals_for_policy, policy)
        recommendation = decision_result["recommendation"]
        decision_basis = decision_result["decision_basis"]

        # Step 6: Calculate confidence
        confidence = calculate_confidence(data_quality, signals_for_policy, policy)

        # Step 7: Prepare evidence for Gemini
        # Structure evidence as expected by the prompt
        evidence_for_gemini = {
            "data_quality": data_quality,
            "metrics": metrics_for_policy,
            "signals": {
                "retention_decay": aggregated.get("retention_decay"),
                "drop_off_concentration": aggregated.get("drop_off_concentration"),
                "viewership_velocity": aggregated.get("viewership_velocity"),
                "engagement_velocity": aggregated.get("engagement_velocity"),
                "new_viewer_trend": aggregated.get("new_viewer_trend"),
                "returning_viewer_trend": aggregated.get("returning_viewer_trend"),
                # Add raw series for transparency if needed
            }
        }

        # Step 8: Invoke Gemini reasoning (this will be done by the ADK agent runtime)
        # We'll return the structured input for Gemini, and the agent's run method
        # will handle the LLM call.
        # For now, we'll simulate what the agent should return before LLM processing.

        # Step 9: Return structured pre-LLM output (the ADK will handle the LLM call)
        # In a full ADK implementation, we would return this to the agent's run_loop
        # which would then invoke the LLM with the prompt.
        # However, for simplicity in this MVP, we'll assume the agent's tools are used
        # and the LLM reasoning is invoked separately.

        # Let's return the analysis results up to the point before LLM reasoning
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
                "clickhouse_query_id": None  # We could extract this from query metadata
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
            "recommendation": "INVESTIGATE",  # Safe default
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
        # For MVP, we'll use hardcoded defaults matching the spec examples
        return {
            "retention_positive_threshold": float(os.getenv('RETENTION_POS_THRESHOLD', '0.10')),
            "retention_negative_threshold": float(os.getenv('RETENTION_NEG_THRESHOLD', '-0.15')),
            "acquisition_positive_threshold": float(os.getenv('ACQUISITION_POS_THRESHOLD', '0.10')),
            "acquisition_negative_threshold": float(os.getenv('ACQUISITION_NEG_THRESHOLD', '-0.10')),
            "engagement_positive_threshold": float(os.getenv('ENGAGEMENT_POS_THRESHOLD', '0.10')),
            "engagement_negative_threshold": float(os.getenv('ENGAGEMENT_NEG_THRESHOLD', '-0.10')),
            "minimum_sample_size": int(os.getenv('MIN_SAMPLE_SIZE', '500'))
        }

# For ADK, we need to expose the agent instance
# The ADK framework will discover and instantiate the agent
def create_agent() -> ContentPerformanceAgent:
    return ContentPerformanceAgent()

# If this file is run directly, test the agent
if __name__ == "__main__":
    import asyncio

    async def test_agent():
        agent = create_agent()
        # Test validation tool
        print("Testing validation tool:")
        validation_result = agent._validate_content_id("SHOW-042")
        print(json.dumps(validation_result, indent=2))

        # Test data retrieval (requires ClickHouse running)
        print("\nTesting data retrieval:")
        try:
            data_result = agent._get_content_data("SHOW-042")
            print(f"Retrieved {len(data_result.get('episodes', []))} episodes")
            if data_result.get('episodes'):
                print("First episode:", json.dumps(data_result['episodes'][0], indent=2))
        except Exception as e:
            print(f"Data retrieval failed (expected if ClickHouse not running): {e}")

        # Test full analysis (will fail without ClickHouse)
        print("\nTesting full analysis:")
        try:
            analysis_result = agent.analyze_content("SHOW-042")
            print(json.dumps(analysis_result, indent=2))
        except Exception as e:
            print(f"Analysis failed (expected if ClickHouse not running): {e}")

    # Run the test
    asyncio.run(test_agent())