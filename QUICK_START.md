# 🚀 LOCAL VERIFICATION GUIDE (Without Docker)

## ⚠️ Docker Not Detected

Docker is not installed on your system. You have two options:

### Option A: Install Docker Desktop (Recommended for Assignment Submission)
1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop/
2. Install and restart your computer
3. Come back to this guide after Docker is running

### Option B: Run Locally with Python (Quick Testing)

## 🐍 Running Without Docker (Python Direct)

### Step 1: Set Environment Variables

```powershell
# Set environment variables for this session
$env:WEBHOOK_SECRET="testsecret"
$env:DATABASE_URL="sqlite+aiosqlite:///./app.db"
$env:LOG_LEVEL="INFO"
```

### Step 2: Install Dependencies (if not done)

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install requirements (if needed)
pip install -r requirements.txt
```

### Step 3: Start the Application

```powershell
# Run with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 4: Test in a NEW PowerShell Window

Keep the server running in the first window, open a NEW window:

```powershell
# Navigate to project
cd C:\Users\HP\Downloads\backend

# Test health endpoints
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

Expected: Both return 200 OK

### Step 5: Generate Test Signatures

In the new window:
```powershell
python generate_signature.py
```

Copy the curl commands from the output.

### Step 6: Test Webhook

Use the curl commands from generate_signature.py output:

```powershell
# Example (use the actual signature from generate_signature.py)
curl -X POST http://localhost:8000/webhook `
  -H "Content-Type: application/json" `
  -H "X-Signature: YOUR_SIGNATURE_HERE" `
  -d '{\"message_id\":\"m1\",\"from\":\"+919876543210\",\"to\":\"+14155550100\",\"ts\":\"2025-01-15T10:00:00Z\",\"text\":\"Hello\"}'
```

Expected: `{"status":"ok"}`

### Step 7: Test Invalid Signature (Should Fail)

```powershell
curl -X POST http://localhost:8000/webhook `
  -H "Content-Type: application/json" `
  -H "X-Signature: invalid123" `
  -d '{\"message_id\":\"m1\",\"from\":\"+919876543210\",\"to\":\"+14155550100\",\"ts\":\"2025-01-15T10:00:00Z\",\"text\":\"Hello\"}'
```

Expected: 401 error with `{"detail":"invalid signature"}`

### Step 8: Test Other Endpoints

```powershell
# Get messages
curl http://localhost:8000/messages

# Get stats
curl http://localhost:8000/stats

# Get metrics
curl http://localhost:8000/metrics
```

### Step 9: Stop the Server

In the first PowerShell window, press `Ctrl+C`

---

## 📸 PROOF FOR SUBMISSION

Take screenshots of:

1. ✅ Server running (uvicorn output)
2. ✅ Health checks returning 200
3. ✅ Invalid signature returning 401
4. ✅ Valid webhook returning 200
5. ✅ Messages endpoint returning data
6. ✅ Stats endpoint showing analytics
7. ✅ Metrics endpoint showing Prometheus format

---

## 🔧 For Assignment Submission - YOU NEED DOCKER

**IMPORTANT**: While local testing with Python works, the assignment requires Docker for submission:

> "What We Will Actually Run (Evaluation Script Outline)"
> ```bash
> make up
> curl http://localhost:8000/health/ready
> ```

### Install Docker Desktop:
1. Go to: https://www.docker.com/products/docker-desktop/
2. Download Windows version
3. Install (requires restart)
4. Verify: `docker --version`
5. Then use: `make up`

---

## ✅ Quick Verification Checklist

Without Docker (Local Python):
- [ ] Server starts with uvicorn
- [ ] `/health/live` returns 200
- [ ] `/health/ready` returns 200
- [ ] Invalid signature → 401
- [ ] Valid signature → 200
- [ ] Messages endpoint works
- [ ] Stats endpoint works
- [ ] Metrics endpoint works

With Docker (For Submission):
- [ ] `docker --version` works
- [ ] `make up` starts service
- [ ] All endpoints work at http://localhost:8000
- [ ] `make down` stops service cleanly

---

## 🆘 Troubleshooting

### "curl not recognized"
Alternative: Open browser to `http://localhost:8000/health/live`

### Port 8000 in use
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID_HERE> /F
```

### Import errors
```powershell
pip install -r requirements.txt
```
