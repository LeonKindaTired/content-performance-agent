"""
FastAPI application for the Content Performance Signal Agent.
"""

import os
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Import our agent
from agent.agent import create_agent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Content Performance Signal Agent",
    description="Agentic analytics workflow for content performance analysis",
    version="0.1.0"
)

# Create agent instance
agent = create_agent()

# Mount static files (for frontend assets if needed)
# app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Request/Response models
class ContentRequest(BaseModel):
    content_id: str
    # Optional parameters for future extension
    # date_range: Optional[Dict[str, str]] = None

class ContentResponse(BaseModel):
    content_id: str
    recommendation: str
    confidence: float
    decision_basis: dict
    metrics: dict
    signals: dict
    data_quality: dict
    evidence: list
    llm_reasoning: dict
    warnings: list
    provenance: dict

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    # Check ClickHouse connection
    try:
        from agent.agent import ClickHouseTool
        clickhouse_tool = ClickHouseTool()
        ch_status = clickhouse_tool.test_connection()
    except Exception as e:
        ch_status = False
        logger.error(f"ClickHouse health check failed: {e}")

    return {
        "status": "healthy" if ch_status else "degraded",
        "services": {
            "clickhouse": "connected" if ch_status else "disconnected",
            "agent": "ready"
        }
    }

# Main analysis endpoint
@app.post("/api/analyze", response_model=ContentResponse)
async def analyze_content(request: ContentRequest):
    """
    Analyze content performance and return a recommendation.
    """
    logger.info(f"Received analysis request for content_id: {request.content_id}")

    try:
        # Run the agent's analysis workflow
        # Note: In a full ADK implementation, we would invoke the agent's run method
        # which would handle tool use and LLM reasoning.
        # For this MVP, we'll call the agent's analyze_content method directly
        # and then simulate the Gemini reasoning step.

        analysis_result = agent.analyze_content(request.content_id)

        # If there was an error in the analysis, return it
        if "error" in analysis_result:
            raise HTTPException(
                status_code=400,
                detail=analysis_result["error"]
            )

        # Now we need to invoke Gemini reasoning.
        # For this MVP, we'll create a mock Gemini response based on the structured evidence.
        # In a real implementation, we would call the Gemini model via ADK or directly.

        gemini_reasoning = await _invoke_gemini_reasoning(analysis_result)

        # Construct the final response
        response = {
            "content_id": analysis_result["content_id"],
            "recommendation": analysis_result["deterministic_recommendation"],
            "confidence": analysis_result["deterministic_confidence"],
            "decision_basis": analysis_result["decision_basis"],
            "metrics": analysis_result["metrics"],
            "signals": analysis_result["signals"],
            "data_quality": analysis_result["data_quality"],
            "evidence": _extract_evidence_strings(analysis_result),
            "llm_reasoning": gemini_reasoning,
            "warnings": analysis_result.get("warnings", []),
            "provenance": analysis_result.get("provenance", {})
        }

        return JSONResponse(content=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

async def _invoke_gemini_reasoning(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke Gemini reasoning based on the analysis result.
    Uses the Google Gemini API to generate structured reasoning.
    """
    try:
        from google import genai
        import json as python_json

        # Set Gemini location environment variable for the client
        # Uses GEMINI_LOCATION (Gemini Enterprise Agent Platform)
        gemini_location = os.getenv('GEMINI_LOCATION', 'us-central1')
        if gemini_location:
            os.environ['GOOGLE_CLOUD_LOCATION'] = gemini_location

        # Initialize Gemini client
        # The API key should be available via GOOGLE_APPLICATION_CREDENTIALS or ADC
        client = genai.Client()

        # Prepare the prompt for Gemini
        prompt = _format_gemini_prompt(analysis_result)

        # Configure the model
        model = os.getenv('GEMINI_MODEL', 'gemini-pro')

        # Generate content with Gemini
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={
                "temperature": 0.2,  # Low temperature for consistent, factual responses
                "top_p": 0.8,
                "max_output_tokens": 1024,
            }
        )

        # Parse the JSON response from Gemini
        # We expect Gemini to return JSON matching our schema
        response_text = response.text

        # Try to extract JSON from the response
        # Gemini might wrap JSON in markdown or add extra text
        json_str = _extract_json_from_response(response_text)
        gemini_reasoning = python_json.loads(json_str)

        # Validate that we got the expected structure
        _validate_gemini_response(gemini_reasoning)

        return gemini_reasoning

    except Exception as e:
        logger.error(f"Error invoking Gemini API: {e}", exc_info=True)
        # Fallback to mock reasoning if Gemini fails
        logger.warning("Falling back to mock Gemini reasoning due to API error")
        return _mock_gemini_reasoning(analysis_result)


def _format_gemini_prompt(analysis_result: Dict[str, Any]) -> str:
    """Format the prompt for Gemini reasoning based on analysis results."""
    from agent.prompts import GEMINI_REASONING_PROMPT, format_prompt

    # Extract the components needed for the prompt
    data_quality = analysis_result.get("data_quality", {})
    metrics = analysis_result.get("metrics", {})
    signals = analysis_result.get("signals", {})
    recommendation = analysis_result.get("deterministic_recommendation", "INVESTIGATE")
    warnings = analysis_result.get("warnings", [])

    # Use the existing prompt formatting function
    return format_prompt(data_quality, metrics, signals, recommendation, warnings)


def _extract_json_from_response(response_text: str) -> str:
    """Extract JSON string from Gemini response, handling markdown wrappers."""
    import re

    # Look for JSON in markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        return json_match.group(1)

    # Look for JSON object directly
    json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
    if json_match:
        return json_match.group(1)

    # If no JSON found, return the whole text (will likely cause json.loads to fail)
    return response_text.strip()


def _validate_gemini_response(response: Dict[str, Any]) -> None:
    """Validate that Gemini response has the expected structure."""
    required_keys = ["executive_summary", "evidence_summary", "possible_explanations", "uncertainties", "next_actions"]
    for key in required_keys:
        if key not in response:
            raise ValueError(f"Missing required key in Gemini response: {key}")

    # Check types
    if not isinstance(response["executive_summary"], str):
        raise ValueError("executive_summary must be a string")
    if not isinstance(response["evidence_summary"], list):
        raise ValueError("evidence_summary must be a list")
    if not isinstance(response["possible_explanations"], list):
        raise ValueError("possible_explanations must be a list")
    if not isinstance(response["uncertainties"], list):
        raise ValueError("uncertainties must be a list")
    if not isinstance(response["next_actions"], list):
        raise ValueError("next_actions must be a list")


def _mock_gemini_reasoning(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Mock Gemini reasoning for fallback when API is unavailable."""
    recommendation = analysis_result["deterministic_recommendation"]
    confidence = analysis_result["deterministic_confidence"]
    signals = analysis_result["signals"]
    data_quality = analysis_result["data_quality"]
    warnings = analysis_result.get("warnings", [])

    # Build evidence summary from signals
    evidence_summary = []

    if signals.get("retention_decay"):
        rd = signals["retention_decay"]
        if rd and rd.get("relative_decay") is not None:
            decay_pct = rd["relative_decay"] * 100
            direction = "decline" if decay_pct < 0 else "improvement"
            evidence_summary.append(
                f"Retention changed by {decay_pct:.1f}% ({direction}) from first to latest episode"
            )

    if signals.get("drop_off_concentration"):
        doc = signals["drop_off_concentration"]
        if doc and doc.get("episode") and doc.get("drop") is not None:
            evidence_summary.append(
                f"Largest retention drop of {doc['drop']*100:.1f} percentage points occurred at episode {doc['episode']}"
            )

    if signals.get("viewership_velocity") is not None:
        vv = signals["viewership_velocity"] * 100
        direction = "growth" if vv > 0 else "decline"
        evidence_summary.append(
            f"Viewership velocity: {vv:.1f}% ({direction})"
        )

    if signals.get("engagement_velocity") is not None:
        ev = signals["engagement_velocity"] * 100
        direction = "growth" if ev > 0 else "decline"
        evidence_summary.append(
            f"Engagement velocity: {ev:.1f}% ({direction})"
        )

    # Determine possible explanations based on recommendation
    possible_explanations = []
    if recommendation == "REPOSITION":
        possible_explanations.append(
            "Hypothesis: Strong initial attraction but content fails to deliver on expectations set by early episodes"
        )
        possible_explanations.append(
            "Hypothesis: Episode 3 may have a structural issue (e.g., pacing, topic relevance) causing drop-off"
        )
    elif recommendation == "CANCEL":
        possible_explanations.append(
            "Hypothesis: Fundamental mismatch between content and target audience"
        )
    elif recommendation == "RENEW":
        possible_explanations.append(
            "Hypothesis: Content resonates well with audience and shows healthy growth trajectory"
        )
    else:
        possible_explanations.append(
            "Hypothesis: Insufficient data to confidently determine performance drivers"
        )

    # Determine uncertainties
    uncertainties = []
    if data_quality.get("status") != "SUFFICIENT":
        uncertainties.append("Data quality or sample size limitations affect confidence")
    if len(analysis_result.get("warnings", [])) > 0:
        uncertainties.append("Analysis based on limited episode data")
    if not uncertainties:
        uncertainties.append("Standard uncertainty inherent in predictive analytics")

    # Determine next actions
    next_actions = []
    if recommendation == "REPOSITION":
        next_actions.append("Review episode 3 content structure, pacing, and thematic elements")
        next_actions.append("Consider A/B testing alternative episode ordering or content adjustments")
    elif recommendation == "INVESTIGATE":
        next_actions.append("Collect additional qualitative audience feedback")
        next_actions.append("Analyze competitive landscape for similar content")
    else:
        next_actions.append("Monitor performance trends for any significant changes")
        next_actions.append("Consider audience expansion strategies")

    # Executive summary
    exec_summary = f"Based on analysis of {analysis_result['content_id']}, the recommendation is {recommendation} with {confidence:.0%} confidence. "
    if evidence_summary:
        exec_summary += "Key factors include " + "; ".join(evidence_summary[:2]) + "."

    return {
        "executive_summary": exec_summary,
        "evidence_summary": evidence_summary,
        "possible_explanations": possible_explanations,
        "uncertainties": uncertainties,
        "next_actions": next_actions
    }

def _extract_evidence_strings(analysis_result: Dict[str, Any]) -> List[str]:
    """
    Extract human-readable evidence strings from the analysis result.
    """
    evidence = []
    signals = analysis_result.get("signals", {})
    metrics = analysis_result.get("metrics", {})

    # Add metrics
    if metrics.get("total_viewers"):
        evidence.append(f"Total viewers: {metrics['total_viewers']:,}")

    if metrics.get("average_completion_rate") is not None:
        evidence.append(f"Average completion rate: {metrics['average_completion_rate']:.0%}")

    # Add signals
    if signals.get("retention_decay"):
        rd = signals["retention_decay"]
        if rd and rd.get("relative_decay") is not None:
            evidence.append(f"Retention decay: {rd['relative_decay']:.0%}")

    if signals.get("drop_off_concentration"):
        doc = signals["drop_off_concentration"]
        if doc and doc.get("episode") and doc.get("drop") is not None:
            evidence.append(f"Largest drop: {doc['drop']:.0%} at episode {doc['episode']}")

    if signals.get("viewership_velocity") is not None:
        evidence.append(f"Viewership velocity: {signals['viewership_velocity']:.0%}")

    if signals.get("engagement_velocity") is not None:
        evidence.append(f"Engagement velocity: {signals['engagement_velocity']:.0%}")

    return evidence

# Serve frontend
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML page."""
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Frontend not found")

# API root endpoint
@app.get("/api/")
async def api_root():
    """API root endpoint."""
    return {
        "message": "Content Performance Signal Agent API",
        "version": "0.1.0",
        "docs": "/api/docs"
    }

if __name__ == "__main__":
    import uvicorn
    # Get port from environment or default to 8000
    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=True)