"""Tests for webhook endpoint."""
import hmac
import hashlib
import json
import pytest
from httpx import AsyncClient


def compute_signature(body: str, secret: str = "testsecret") -> str:
    """Compute HMAC-SHA256 signature."""
    return hmac.new(
        secret.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()


@pytest.mark.asyncio
async def test_webhook_invalid_signature(client: AsyncClient):
    """Test webhook with invalid signature returns 401."""
    payload = {
        "message_id": "m1",
        "from": "+1234567890",
        "to": "+0987654321",
        "ts": "2025-01-01T10:00:00Z",
        "text": "Hello"
    }
    
    response = await client.post(
        "/webhook",
        json=payload,
        headers={"X-Signature": "invalid"}
    )
    
    assert response.status_code == 401
    assert response.json() == {"detail": "invalid signature"}


@pytest.mark.asyncio
async def test_webhook_success(client: AsyncClient):
    """Test successful webhook message insertion."""
    payload = {
        "message_id": "m1",
        "from": "+1234567890",
        "to": "+0987654321",
        "ts": "2025-01-01T10:00:00Z",
        "text": "Hello"
    }
    
    body = json.dumps(payload)
    sig = compute_signature(body)
    
    response = await client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": sig
        }
    )
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_webhook_idempotency(client: AsyncClient):
    """Test that duplicate messages return 200 without inserting."""
    payload = {
        "message_id": "m_dup",
        "from": "+111",
        "to": "+222",
        "ts": "2025-01-01T12:00:00Z",
        "text": "Duplicate test"
    }
    
    body = json.dumps(payload)
    sig = compute_signature(body)
    
    # First request
    response1 = await client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": sig
        }
    )
    assert response1.status_code == 200
    
    # Duplicate request
    response2 = await client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": sig
        }
    )
    assert response2.status_code == 200
    assert response2.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_webhook_validation_error(client: AsyncClient):
    """Test validation errors return 422."""
    payload = {
        "message_id": "m2",
        "from": "invalid_phone",  # Invalid E.164 format
        "to": "+0987654321",
        "ts": "2025-01-01T10:00:00Z"
    }
    
    body = json.dumps(payload)
    sig = compute_signature(body)
    
    response = await client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": sig
        }
    )
    
    assert response.status_code == 422
