# API Examples

## Example payload

    {
      "message_id": "msg_123",
      "sender": "+919876543210",
      "recipient": "+919876543211",
      "timestamp": "2026-09-30T10:30:00Z",
      "text": "Hello"
    }

## Example query

    GET /messages?limit=20&offset=0

Use the project's authentication and validation rules for every production request.
