# Content Performance Signal Agent

An agentic analytics workflow for media and entertainment content performance analysis.

## Overview

This agent takes a content ID and performs an automated workflow:
1. Retrieves real performance data from ClickHouse
2. Validates data quality
3. Computes deterministic signals
4. Applies a decision policy
5. Uses Gemini to explain the evidence
6. Returns a structured recommendation

## Project Structure

```
.
├── agent/              # ADK agent implementation
├── analytics/          # Deterministic signal engine, data quality, decision policy
├── api/                # FastAPI application
├── data/               # Database schema
├── frontend/           # (Optional) Minimal UI
├── scripts/            # Data seeding and utilities
├── tests/              # Unit and integration tests
└── tools/              # ClickHouse tool and other integrations
```

## Setup

1. Clone the repository
2. Install dependencies: `pip install -e .`
3. Configure environment variables (see `.env.example`)
4. Set up ClickHouse database and seed with sample data:
   ```bash
   python scripts/seed_clickhouse.py
   ```
5. Run the API server:
   ```bash
   uvicorn api.main:app --reload
   ```
6. Visit `http://localhost:8000/docs` for API documentation

## Environment Variables

See `.env.example` for required variables:
- ClickHouse connection details
- Google Cloud project and credentials
- Application settings

## Usage

Send a POST request to `/analyze` with a JSON body:
```json
{
  "content_id": "SHOW-042"
}
```

The agent will return a structured analysis including recommendation, confidence, evidence, and Gemini-powered reasoning.

## Testing

Run unit tests:
```bash
pytest tests/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.