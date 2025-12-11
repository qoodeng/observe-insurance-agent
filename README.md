# Observe Insurance Voice AI Agent

A backend for a Voice AI Claims Support Assistant built with FastAPI and Airtable, designed for integration with VAPI.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your Airtable credentials

# 3. Run the server
uvicorn app.main:app --reload
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AIRTABLE_API_KEY` | Your Airtable Personal Access Token |
| `AIRTABLE_BASE_ID` | Your Airtable Base ID (starts with `app`) |
| `AIRTABLE_TABLE_CLAIMS` | Claims table name (default: `Claims`) |
| `AIRTABLE_TABLE_INTERACTIONS` | Interactions table name (default: `Interactions`) |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/lookup-caller-data` | POST | Look up customer by phone number |
| `/log-call-summary` | POST | Log call outcome and sentiment |

## Airtable Schema

**Claims Table:**
- `Phone Number` (text) - normalized digits only
- `First Name` (text)
- `Last Name` (text)
- `Claim Status` (text) - "Approved", "Pending", or "Requires Documentation"

**Interactions Table:**
- `Caller Name` (text)
- `Call Summary` (long text)
- `Sentiment` (single select) - "Positive", "Neutral", or "Negative"

## Testing

```bash
# Test lookup
curl -X POST "http://127.0.0.1:8000/lookup-caller-data" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "5551234567"}'

# Test log
curl -X POST "http://127.0.0.1:8000/log-call-summary" \
  -H "Content-Type: application/json" \
  -d '{"caller_name": "John Smith", "summary": "Checked claim status", "sentiment": "Positive"}'
```

## Deployment

Deploy to Railway, Render, or any platform that supports Python. Set environment variables in the platform's dashboard.
