"""Tests for stats endpoint."""
import hmac
import hashlib
import json
import pytest
from httpx import AsyncClient


def sign(data: dict, secret: str = "testsecret") -> str:
    """Helper to sign message data."""
    body = json.dumps(data)
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()


async def seed_message(client: AsyncClient, msg: dict):
    """Helper to seed a message via webhook."""
    body = json.dumps(msg)
    sig = sign(msg)
    await client.post(
        "/webhook",
        content=body,
        headers={"Content-Type": "application/json", "X-Signature": sig}
    )


@pytest.mark.asyncio
async def test_stats_basic(client: AsyncClient):
    """Test basic stats computation."""
    # Seed data
    messages = [
        {"message_id": "s1", "from": "+A", "to": "+Z", "ts": "2025-01-01T10:00:00Z"},
        {"message_id": "s2", "from": "+A", "to": "+Z", "ts": "2025-01-02T10:00:00Z"},
        {"message_id": "s3", "from": "+B", "to": "+Z", "ts": "2025-01-03T10:00:00Z"},
    ]
    
    for msg in messages:
        await seed_message(client, msg)
    
    # Get stats
    response = await client.get("/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_messages"] == 3
    assert data["senders_count"] == 2
    assert data["first_message_ts"] == "2025-01-01T10:00:00Z"
    assert data["last_message_ts"] == "2025-01-03T10:00:00Z"
    
    # Check messages per sender
    assert len(data["messages_per_sender"]) == 2
    assert data["messages_per_sender"][0]["from"] == "+A"
    assert data["messages_per_sender"][0]["count"] == 2
    assert data["messages_per_sender"][1]["from"] == "+B"
    assert data["messages_per_sender"][1]["count"] == 1


@pytest.mark.asyncio
async def test_stats_empty(client: AsyncClient):
    """Test stats with no messages."""
    response = await client.get("/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_messages"] == 0
    assert data["senders_count"] == 0
    assert data["messages_per_sender"] == []
    assert data["first_message_ts"] is None
    assert data["last_message_ts"] is None
