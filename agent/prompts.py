"""
Prompt templates for the Content Performance Signal Agent.
"""

from typing import Dict, Any, List

SYSTEM_INSTRUCTION = """
You are the reasoning layer of an evidence-first content analytics agent.

You will receive:
1. validated data-quality information;
2. deterministic metrics;
3. deterministic signals;
4. a deterministic recommendation;
5. warnings.

Your job is to explain the evidence clearly for a media content executive.

Rules:
- Never invent metrics.
- Never modify numbers.
- Never override the deterministic recommendation.
- Never claim certainty when warnings exist.
- Separate observed evidence from possible explanations.
- Clearly label hypotheses as hypotheses.
- If evidence is insufficient, explain why.
- Keep the executive summary concise.
- Every quantitative statement must be traceable to the supplied evidence.
"""

GEMINI_REASONING_PROMPT = """
Based on the following evidence, provide a reasoned explanation for the content performance analysis.

DATA QUALITY:
{data_quality}

DETERMINISTIC METRICS:
{metrics}

DETERMINISTIC SIGNALS:
{signals}

DETERMINISTIC RECOMMENDATION:
{recommendation}

WARNINGS:
{warnings}

Please provide your response in the following JSON format:
{{
  "executive_summary": "A concise 2-3 sentence summary of the situation and recommendation",
  "evidence_summary": [
    "Key evidence points as short strings"
  ],
  "possible_explanations": [
    "Plausible explanations for the observed performance (label as hypotheses)"
  ],
  "uncertainties": [
    "Areas of uncertainty or limitations in the analysis"
  ],
  "next_actions": [
    "Recommended next steps for investigation or action"
  ]
}}

Remember:
- Do not invent or modify any metrics.
- Do not override the deterministic recommendation.
- Base all statements strictly on the provided evidence.
- If evidence is insufficient, say so clearly.
"""

def format_prompt(
    data_quality: Dict[str, Any],
    metrics: Dict[str, Any],
    signals: Dict[str, Any],
    recommendation: str,
    warnings: List[str]
) -> str:
    """
    Format the prompt for Gemini reasoning.
    """
    return GEMINI_REASONING_PROMPT.format(
        data_quality=_format_dict(data_quality),
        metrics=_format_dict(metrics),
        signals=_format_dict(signals),
        recommendation=recommendation,
        warnings="\\n".join(f"- {w}" for w in warnings) if warnings else "None"
    )

def _format_dict(d: Dict[str, Any]) -> str:
    """Format a dictionary for inclusion in the prompt."""
    if not d:
        return "None"
    lines = []
    for key, value in d.items():
        if isinstance(value, dict):
            lines.append(f"- {key}:")
            for subkey, subvalue in value.items():
                lines.append(f"  - {subkey}: {subvalue}")
        elif isinstance(value, list):
            lines.append(f"- {key}: {', '.join(str(v) for v in value)}")
        else:
            lines.append(f"- {key}: {value}")
    return "\\n".join(lines)