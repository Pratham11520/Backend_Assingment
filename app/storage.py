"""Database operations."""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Message


async def insert_message(session: AsyncSession, msg_data: dict) -> str:
    """
    Insert a message into the database.
    
    Returns:
        "created" if new message inserted
        "duplicate" if message_id already exists
    """
    try:
        # Check if message already exists
        result = await session.execute(
            select(Message).where(Message.message_id == msg_data["message_id"])
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return "duplicate"
        
        # Create a copy and add created_at timestamp
        from datetime import datetime
        data = dict(msg_data)
        data["created_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Insert new message
        new_message = Message(**data)
        session.add(new_message)
        await session.commit()
        return "created"
        
    except IntegrityError:
        await session.rollback()
        return "duplicate"
    except Exception as e:
        await session.rollback()
        raise e


async def get_messages(
    session: AsyncSession,
    limit: int,
    offset: int,
    from_msisdn: Optional[str] = None,
    since: Optional[str] = None,
    q: Optional[str] = None
) -> Tuple[List[Message], int]:
    """
    Retrieve messages with pagination and filters.
    
    Returns:
        Tuple of (messages list, total count)
    """
    # Build base query
    query = select(Message)
    
    # Apply filters
    if from_msisdn:
        query = query.where(Message.from_msisdn == from_msisdn)
    if since:
        query = query.where(Message.ts >= since)
    if q:
        query = query.where(Message.text.ilike(f"%{q}%"))
    
    # Get total count - build separate count query with same filters
    count_query = select(func.count(Message.message_id))
    if from_msisdn:
        count_query = count_query.where(Message.from_msisdn == from_msisdn)
    if since:
        count_query = count_query.where(Message.ts >= since)
    if q:
        count_query = count_query.where(Message.text.ilike(f"%{q}%"))
    
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()
    
    # Apply ordering and pagination
    query = query.order_by(Message.ts.asc(), Message.message_id.asc())
    query = query.limit(limit).offset(offset)
    
    # Execute query
    result = await session.execute(query)
    messages = result.scalars().all()
    
    return messages, total


async def get_stats(session: AsyncSession) -> Dict[str, Any]:
    """Get message statistics."""
    # Total messages
    total_result = await session.execute(select(func.count(Message.message_id)))
    total_messages = total_result.scalar_one()
    
    # Senders count
    senders_result = await session.execute(
        select(func.count(func.distinct(Message.from_msisdn)))
    )
    senders_count = senders_result.scalar_one()
    
    # Messages per sender (top 10, sorted by count desc)
    top_senders_result = await session.execute(
        select(
            Message.from_msisdn,
            func.count(Message.message_id).label("count")
        )
        .group_by(Message.from_msisdn)
        .order_by(desc("count"))
        .limit(10)
    )
    messages_per_sender = [
        {"from": row[0], "count": row[1]}
        for row in top_senders_result.all()
    ]
    
    # First and last message timestamps
    min_max_result = await session.execute(
        select(func.min(Message.ts), func.max(Message.ts))
    )
    first_ts, last_ts = min_max_result.one()
    
    return {
        "total_messages": total_messages,
        "senders_count": senders_count,
        "messages_per_sender": messages_per_sender,
        "first_message_ts": first_ts,
        "last_message_ts": last_ts,
    }
