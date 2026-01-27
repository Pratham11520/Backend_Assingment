"""
HMAC Signature Generator for Webhook Testing
Usage: python generate_signature.py
"""
import hmac
import hashlib
import json

# Configuration
SECRET = "testsecret"

# Sample payloads
payloads = {
    "m1": {
        "message_id": "m1",
        "from": "+919876543210",
        "to": "+14155550100",
        "ts": "2025-01-15T10:00:00Z",
        "text": "Hello"
    },
    "m2": {
        "message_id": "m2",
        "from": "+919876543210",
        "to": "+14155550100",
        "ts": "2025-01-15T11:00:00Z",
        "text": "Second message"
    },
    "m3": {
        "message_id": "m3",
        "from": "+911234567890",
        "to": "+14155550100",
        "ts": "2025-01-15T12:00:00Z",
        "text": "Third message"
    }
}


def generate_signature(payload_dict, secret=SECRET):
    """Generate HMAC-SHA256 signature for a payload."""
    # Convert to JSON string (compact, no spaces)
    body = json.dumps(payload_dict, separators=(',', ':'))
    
    # Compute HMAC
    signature = hmac.new(
        secret.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return body, signature


if __name__ == "__main__":
    print("=" * 70)
    print("HMAC Signature Generator for Webhook Testing")
    print("=" * 70)
    
    for msg_id, payload in payloads.items():
        body, sig = generate_signature(payload)
        
        print(f"\n[{msg_id}]")
        print(f"Body: {body}")
        print(f"Signature: {sig}")
        print(f"\nCurl command (Windows PowerShell):")
        print(f'curl -X POST http://localhost:8000/webhook `')
        print(f'  -H "Content-Type: application/json" `')
        print(f'  -H "X-Signature: {sig}" `')
        print(f"  -d '{body}'")
        print("-" * 70)
    
    print("\n✓ Copy and paste the curl commands above to test your webhook!")
