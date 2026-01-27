# Lyftr AI Backend Assignment

Production-ready FastAPI webhook service with HMAC authentication, message persistence, and observability features.

## Setup Used
**Google Gemini 2.0 Experimental with Thinking** - Complete end-to-end implementation

## Features

- ✅ HMAC-SHA256 signature verification
- ✅ Idempotent message ingestion
- ✅ Paginated and filterable message listing
- ✅ Analytics endpoint
- ✅ Health probes (liveness & readiness)
- ✅ Prometheus metrics
- ✅ Structured JSON logging
- ✅ Docker & Docker Compose ready
- ✅ Comprehensive test suite

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- (Optional) Python 3.11+ for local development

### Run with Docker

```bash
# Start the service
make up

# View logs
make logs

# Stop the service
make down

# Run tests
make test
```

The API will be available at `http://localhost:8000`

### Run Locally (Development)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export WEBHOOK_SECRET="your-secret-here"
export DATABASE_URL="sqlite+aiosqlite:///./app.db"
export LOG_LEVEL="INFO"

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### POST /webhook

Ingest messages with HMAC verification.

**Request:**
```bash
# Compute signature
BODY='{"message_id":"m1","from":"+919876543210","to":"+14155550100","ts":"2025-01-15T10:00:00Z","text":"Hello"}'
SIGNATURE=$(echo -n "$BODY" | openssl dgst -sha256 -hmac "your-secret" | awk '{print $2}')

# Send request
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Signature: $SIGNATURE" \
  -d "$BODY"
```

**Response:**
```json
{"status": "ok"}
```

**Error Responses:**
- `401`: Invalid or missing signature
- `422`: Validation error (invalid phone format, timestamp, etc.)

### GET /messages

List messages with pagination and filters.

**Query Parameters:**
- `limit` (int, 1-100, default: 50): Number of messages to return
- `offset` (int, >=0, default: 0): Pagination offset
- `from` (string): Filter by sender phone number
- `since` (string): Filter by timestamp (ISO-8601)
- `q` (string): Search in message text

**Examples:**
```bash
# Basic listing
curl "http://localhost:8000/messages"

# Pagination
curl "http://localhost:8000/messages?limit=10&offset=20"

# Filter by sender
curl "http://localhost:8000/messages?from=+919876543210"

# Filter by timestamp
curl "http://localhost:8000/messages?since=2025-01-15T09:30:00Z"

# Text search
curl "http://localhost:8000/messages?q=Hello"

# Combined filters
curl "http://localhost:8000/messages?from=+919876543210&since=2025-01-15T09:30:00Z&limit=20"
```

**Response:**
```json
{
  "data": [
    {
      "message_id": "m1",
      "from": "+919876543210",
      "to": "+14155550100",
      "ts": "2025-01-15T10:00:00Z",
      "text": "Hello"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### GET /stats

Get message analytics.

**Example:**
```bash
curl "http://localhost:8000/stats"
```

**Response:**
```json
{
  "total_messages": 123,
  "senders_count": 10,
  "messages_per_sender": [
    {"from": "+919876543210", "count": 50},
    {"from": "+911234567890", "count": 30}
  ],
  "first_message_ts": "2025-01-10T09:00:00Z",
  "last_message_ts": "2025-01-15T10:00:00Z"
}
```

### GET /health/live

Liveness probe - always returns 200 when the service is running.

```bash
curl "http://localhost:8000/health/live"
```

### GET /health/ready

Readiness probe - returns 200 only when:
- Database is accessible
- `WEBHOOK_SECRET` is configured

```bash
curl "http://localhost:8000/health/ready"
```

### GET /metrics

Prometheus metrics endpoint.

```bash
curl "http://localhost:8000/metrics"
```

**Metrics Exposed:**
- `http_requests_total{path, status}`: Total HTTP requests by path and status
- `webhook_requests_total{result}`: Webhook outcomes (created, duplicate, invalid_signature)
- `request_latency_ms_bucket{le}`: Request latency histogram

## Design Decisions

### HMAC Verification

HMAC verification is implemented as a FastAPI dependency that:
1. Reads the raw request body
2. Computes HMAC-SHA256 using `WEBHOOK_SECRET`
3. Compares with the `X-Signature` header using constant-time comparison
4. Raises 401 on mismatch before any business logic executes

This ensures security-first design and prevents processing of unauthenticated requests.

### Idempotency

Idempotency is enforced through:
1. **Database-level**: `message_id` as PRIMARY KEY
2. **Application-level**: Check for existing message before insert
3. Both duplicate requests and unique constraint violations return `200 {"status": "ok"}`

This ensures exactly-once semantics even under retry scenarios.

### Pagination Contract

The `/messages` endpoint returns:
- `data`: Array of messages for the current page
- `total`: Total count matching the filters (ignoring limit/offset)
- `limit`: Echoed from request
- `offset`: Echoed from request

This allows clients to:
- Calculate total pages: `ceil(total / limit)`
- Build pagination UI with accurate page counts
- Navigate using offset-based pagination

Messages are ordered deterministically by `(ts ASC, message_id ASC)` to ensure consistent pagination.

### Stats & Metrics

**Stats Endpoint (`/stats`):**
- Computed on-demand using SQL aggregations
- Efficient for thousands of messages
- Returns top 10 senders sorted by message count

**Metrics Endpoint (`/metrics`):**
- Uses `prometheus_client` library
- Captures metrics via middleware (no per-endpoint logic)
- Provides both counters and histograms for latency analysis

### Logging

Structured JSON logs with custom `JSONFormatter`:
- One JSON object per line (jq-friendly)
- Includes: `ts`, `level`, `request_id`, `method`, `path`, `status`, `latency_ms`
- Webhook requests additionally log: `message_id`, `dup`, `result`
- Request ID is generated per-request for traceability

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, routes, middleware
│   ├── config.py            # Environment variable settings
│   ├── models.py            # SQLAlchemy models
│   ├── storage.py           # Database operations
│   └── logging_utils.py     # JSON logging setup
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_webhook.py      # Webhook tests
│   ├── test_messages.py     # Messages endpoint tests
│   └── test_stats.py        # Stats endpoint tests
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── README.md
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WEBHOOK_SECRET` | ✅ Yes | - | HMAC secret for signature verification |
| `DATABASE_URL` | No | `sqlite+aiosqlite:////data/app.db` | SQLite database URL |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Database Schema

```sql
CREATE TABLE messages (
    message_id TEXT PRIMARY KEY,
    from_msisdn TEXT NOT NULL,
    to_msisdn TEXT NOT NULL,
    ts TEXT NOT NULL,
    text TEXT,
    created_at TEXT NOT NULL
);
```

## Testing

Run tests with:
```bash
make test
```

Or locally:
```bash
pytest -v tests/
```

Test coverage includes:
- HMAC signature validation (valid, invalid, missing)
- Idempotency (duplicate message_id)
- Input validation (E.164 format, ISO-8601 timestamps)
- Pagination (limit, offset)
- Filtering (from, since, q)
- Stats computation
- Health probes

## Docker Configuration

The application uses:
- **Multi-stage build** (not implemented in this simple version, but recommended for production)
- **Small base image**: `python:3.11-slim`
- **Volume mount**: `/data` for SQLite persistence
- **Port mapping**: `8000:8000`

## Production Considerations

For production deployment, consider:
1. **Database**: Migrate to PostgreSQL or another production-grade RDBMS
2. **Secrets Management**: Use secret management service (AWS Secrets Manager, HashiCorp Vault)
3. **Logging**: Ship logs to centralized logging (ELK, Splunk, CloudWatch)
4. **Metrics**: Connect Prometheus to scrape `/metrics`
5. **Rate Limiting**: Add rate limiting middleware
6. **HTTPS**: Terminate TLS at load balancer or add to app
7. **Horizontal Scaling**: Deploy multiple instances behind load balancer
8. **Monitoring**: Add APM (Datadog, New Relic) for deeper observability

## License

MIT
