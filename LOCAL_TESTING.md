# Local Testing Guide for Lyftr AI Backend

## Quick Start (Windows)

### 1️⃣ Prerequisites Check

Open PowerShell and verify:
```powershell
# Check Docker
docker --version

# Check Docker Compose
docker compose version

# Navigate to project
cd C:\Users\HP\Downloads\backend
```

### 2️⃣ Build and Start

```powershell
# Option 1: Using Makefile
make up

# Option 2: Direct Docker Compose
docker compose up -d --build

# Check if running
docker compose ps
```

### 3️⃣ Test Health Endpoints

Open browser or use curl:
```powershell
# Liveness probe
curl http://localhost:8000/health/live

# Readiness probe  
curl http://localhost:8000/health/ready

# Both should return: {"status":"ok"} or {"status":"ready"}
```

### 4️⃣ Test Webhook with Valid Signature

Generate signatures first:
```powershell
python generate_signature.py
```

This will output curl commands with valid signatures. Copy and run them!

Example output:
```powershell
curl -X POST http://localhost:8000/webhook `
  -H "Content-Type: application/json" `
  -H "X-Signature: <COMPUTED_SIG>" `
  -d '{"message_id":"m1","from":"+919876543210","to":"+14155550100","ts":"2025-01-15T10:00:00Z","text":"Hello"}'
```

Expected response:
```json
{"status":"ok"}
```

### 5️⃣ Test Invalid Signature (Should Fail)

```powershell
curl -X POST http://localhost:8000/webhook `
  -H "Content-Type: application/json" `
  -H "X-Signature: invalid123" `
  -d '{"message_id":"test1","from":"+919876543210","to":"+14155550100","ts":"2025-01-15T10:00:00Z","text":"Test"}'
```

Expected response (401):
```json
{"detail":"invalid signature"}
```

### 6️⃣ Test Idempotency

Run the same valid webhook request twice. Both should return 200!

### 7️⃣ Test Message Listing

```powershell
# Get all messages
curl http://localhost:8000/messages

# With pagination
curl "http://localhost:8000/messages?limit=10&offset=0"

# With filters
curl "http://localhost:8000/messages?from=+919876543210"
curl "http://localhost:8000/messages?since=2025-01-15T10:30:00Z"
curl "http://localhost:8000/messages?q=Hello"
```

### 8️⃣ Test Stats

```powershell
curl http://localhost:8000/stats
```

Expected response:
```json
{
  "total_messages": 3,
  "senders_count": 2,
  "messages_per_sender": [...],
  "first_message_ts": "2025-01-15T10:00:00Z",
  "last_message_ts": "2025-01-15T12:00:00Z"
}
```

### 9️⃣ Test Metrics

```powershell
curl http://localhost:8000/metrics
```

Should see Prometheus format with:
- `http_requests_total`
- `webhook_requests_total`
- `request_latency_ms`

### 🔟 View Logs

```powershell
# View logs
make logs

# Or directly
docker compose logs api

# Should see JSON formatted logs
```

## Troubleshooting

### Port 8000 already in use?
```powershell
# Find and kill the process
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Docker not running?
- Start Docker Desktop
- Wait for it to fully start
- Try `docker ps` to verify

### Make command not found?
Just use `docker compose` commands directly (shown above)

## Stopping the Service

```powershell
# Stop and remove everything
make down

# Or
docker compose down -v
```

## 🎉 Success Checklist

- [x] Health endpoints return 200
- [x] Invalid signature returns 401
- [x] Valid webhook returns 200 and stores message
- [x] Duplicate message_id returns 200 (idempotent)
- [x] Messages endpoint returns paginated data
- [x] Stats endpoint returns analytics
- [x] Metrics endpoint returns Prometheus format
- [x] Logs are JSON formatted

**If all above pass, you're ready to submit!** ✅
