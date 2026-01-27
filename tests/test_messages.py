"""Tests for messages endpoint."""
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
    response = await client.post(
        "/webhook",
        content=body,
        headers={"Content-Type": "application/json", "X-Signature": sig}
    )
    assert response.status_code == 200, f"Seed failed: {response.text}"


@pytest.mark.asyncio
async def test_messages_list_basic(client: AsyncClient):
    """Test basic message listing."""
    # Seed data
    messages = [
        {"message_id": "msg1", "from": "+111", "to": "+999", "ts": "2025-01-01T10:00:00Z", "text": "A"},
        {"message_id": "msg2", "from": "+111", "to": "+999", "ts": "2025-01-01T11:00:00Z", "text": "B"},
        {"message_id": "msg3", "from": "+222", "to": "+999", "ts": "2025-01-01T12:00:00Z", "text": "C"},
    ]
    
    for msg in messages:
        await seed_message(client, msg)
    
    # Test basic list
    response = await client.get("/messages")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total"] == 3
    assert len(data["data"]) == 3
    assert data["limit"] == 50
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_messages_pagination(client: AsyncClient):
    """Test pagination."""
    # Seed data
    messages = [
        {"message_id": f"msg{i}", "from": "+111", "to": "+999", "ts": f"2025-01-01T{10+i:02d}:00:00Z", "text": str(i)}
        for i in range(5)
    ]
    
    for msg in messages:
        await seed_message(client, msg)
    
    # Test limit and offset
    response = await client.get("/messages?limit=2&offset=0")
    data = response.json()
    assert len(data["data"]) == 2
    assert data["total"] == 5
    assert data["data"][0]["message_id"] == "msg0"
    
    response = await client.get("/messages?limit=2&offset=2")
    data = response.json()
    assert len(data["data"]) == 2
    assert data["data"][0]["message_id"] == "msg2"


@pytest.mark.asyncio
async def test_messages_filter_by_from(client: AsyncClient):
    """Test filtering by from field."""
    # Seed data
    messages = [
        {"message_id": "msg1", "from": "+111", "to": "+999", "ts": "2025-01-01T10:00:00Z"},
        {"message_id": "msg2", "from": "+111", "to": "+999", "ts": "2025-01-01T11:00:00Z"},
        {"message_id": "msg3", "from": "+222", "to": "+999", "ts": "2025-01-01T12:00:00Z"},
    ]
    
    for msg in messages:
        await seed_message(client, msg)
    
    # Filter by from
    response = await client.get("/messages?from=+111")
    data = response.json()
    assert data["total"] == 2
    assert all(m["from"] == "+111" for m in data["data"])


@pytest.mark.asyncio
async def test_messages_filter_by_since(client: AsyncClient):
    """Test filtering by since timestamp."""
    # Seed data
    messages = [
        {"message_id": "msg1", "from": "+111", "to": "+999", "ts": "2025-01-01T10:00:00Z"},
        {"message_id": "msg2", "from": "+111", "to": "+999", "ts": "2025-01-01T11:00:00Z"},
        {"message_id": "msg3", "from": "+222", "to": "+999", "ts": "2025-01-01T12:00:00Z"},
    ]
    
    for msg in messages:
        await seed_message(client, msg)
    
    # Filter by since
    response = await client.get("/messages?since=2025-01-01T11:00:00Z")
    data = response.json()
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_messages_filter_by_q(client: AsyncClient):
    """Test text search with q parameter."""
    # Seed data
    messages = [
        {"message_id": "msg1", "from": "+111", "to": "+999", "ts": "2025-01-01T10:00:00Z", "text": "Hello"},
        {"message_id": "msg2", "from": "+111", "to": "+999", "ts": "2025-01-01T11:00:00Z", "text": "World"},
        {"message_id": "msg3", "from": "+222", "to": "+999", "ts": "2025-01-01T12:00:00Z", "text": "Hello World"},
    ]
    
    for msg in messages:
        await seed_message(client, msg)
    
    # Search for "Hello"
    response = await client.get("/messages?q=Hello")
    data = response.json()
    assert data["total"] == 2
