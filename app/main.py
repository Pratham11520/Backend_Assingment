"""FastAPI application with webhook, messages, stats, health, and metrics endpoints."""
import time
import hmac
import hashlib
import uuid
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Header, Depends, Query, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.config import settings
from app.logging_utils import setup_logging, logger
from app.models import init_db, get_db, Message
from app.storage import insert_message, get_messages, get_stats as db_get_stats


# Setup logging
setup_logging(settings.LOG_LEVEL)

# Prometheus metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["path", "status"]
)

webhook_requests_total = Counter(
    "webhook_requests_total",
    "Webhook processing outcomes",
    ["result"]
)

request_latency_ms = Histogram(
    "request_latency_ms",
    "Request latency in milliseconds",
    buckets=[100, 500, float("inf")]
)


# Pydantic models
class WebhookMessage(BaseModel):
    """Webhook message payload schema."""
    message_id: str = Field(..., min_length=1)
    from_: str = Field(..., alias="from")
    to: str = Field(...)
    ts: str = Field(...)
    text: Optional[str] = Field(None, max_length=4096)

    @field_validator("from_", "to")
    @classmethod
    def validate_e164(cls, v: str) -> str:
        """Validate E.164 format."""
        if not v.startswith("+") or not v[1:].isdigit():
            raise ValueError("Must be in E.164 format (start with +, then digits only)")
        return v
    
    @field_validator("ts")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate ISO-8601 UTC timestamp."""
        if not v.endswith("Z"):
            raise ValueError("Must be ISO-8601 UTC string with Z suffix")
        return v


class MessageOut(BaseModel):
    """Message response schema."""
    message_id: str
    from_: str = Field(..., alias="from")
    to: str
    ts: str
    text: Optional[str]

    class Config:
        from_attributes = True
        populate_by_name = True


class MessagesResponse(BaseModel):
    """Messages list response."""
    data: List[MessageOut]
    total: int
    limit: int
    offset: int


class StatsResponse(BaseModel):
    """Statistics response."""
    total_messages: int
    senders_count: int
    messages_per_sender: List[dict]
    first_message_ts: Optional[str]
    last_message_ts: Optional[str]


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    logger.info("Database initialized")
    yield


# Create FastAPI app
app = FastAPI(title="Webhook API", lifespan=lifespan)


# Middleware for logging and metrics
@app.middleware("http")
async def logging_metrics_middleware(request: Request, call_next):
    """Log requests and record metrics."""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Store request_id in state
    request.state.request_id = request_id
    request.state.extra_log_fields = {}
    
    # Process request
    response = await call_next(request)
    
    # Calculate latency
    latency_ms = (time.time() - start_time) * 1000
    
    # Record metrics
    http_requests_total.labels(
        path=request.url.path,
        status=str(response.status_code)
    ).inc()
    request_latency_ms.observe(latency_ms)
    
    # Prepare log data
    log_data = {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "latency_ms": round(latency_ms, 2),
    }
    
    # Add extra fields from request state
    if hasattr(request.state, 'extra_log_fields'):
        log_data.update(request.state.extra_log_fields)
    
    # Log request
    logger.info(
        f"{request.method} {request.url.path} {response.status_code}",
        extra={"extra_fields": log_data}
    )
    
    return response


# HMAC verification dependency
async def verify_hmac_signature(
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature")
):
    """Verify HMAC signature of request body."""
    if not x_signature:
        webhook_requests_total.labels(result="invalid_signature").inc()
        request.state.extra_log_fields.update({
            "result": "invalid_signature",
            "message_id": None,
            "dup": False
        })
        raise HTTPException(status_code=401, detail="invalid signature")
    
    # Read raw body
    body = await request.body()
    
    # Compute expected signature
    expected_sig = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    if not hmac.compare_digest(expected_sig, x_signature):
        webhook_requests_total.labels(result="invalid_signature").inc()
        request.state.extra_log_fields.update({
            "result": "invalid_signature",
            "message_id": None,
            "dup": False
        })
        raise HTTPException(status_code=401, detail="invalid signature")


# Endpoints
@app.get("/health/live")
async def health_live():
    """Liveness probe - always returns 200."""
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready(db: AsyncSession = Depends(get_db)):
    """Readiness probe - checks DB and config."""
    # Check if WEBHOOK_SECRET is set
    if not settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="WEBHOOK_SECRET not set")
    
    # Check DB connection
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database not ready")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/webhook")
async def webhook(
    request: Request,
    message: WebhookMessage,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_hmac_signature)
):
    """Ingest webhook messages with HMAC verification and idempotency."""
    # Prepare data for DB
    msg_data = {
        "message_id": message.message_id,
        "from_msisdn": message.from_,
        "to_msisdn": message.to,
        "ts": message.ts,
        "text": message.text
    }
    
    # Insert message
    result = await insert_message(db, msg_data)
    
    # Record metrics
    webhook_requests_total.labels(result=result).inc()
    
    # Add to logs
    request.state.extra_log_fields.update({
        "message_id": message.message_id,
        "dup": result == "duplicate",
        "result": result
    })
    
    return {"status": "ok"}


@app.get("/messages", response_model=MessagesResponse)
async def list_messages(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    from_: Optional[str] = Query(None, alias="from"),
    since: Optional[str] = None,
    q: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List messages with pagination and filters."""
    messages, total = await get_messages(db, limit, offset, from_, since, q)
    
    # Convert to response models
    data = [
        MessageOut(
            message_id=m.message_id,
            from_=m.from_msisdn,
            to=m.to_msisdn,
            ts=m.ts,
            text=m.text
        )
        for m in messages
    ]
    
    return MessagesResponse(
        data=data,
        total=total,
        limit=limit,
        offset=offset
    )


@app.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get message statistics."""
    return await db_get_stats(db)
