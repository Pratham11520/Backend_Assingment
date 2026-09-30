# Security Notes

- Verify request signatures with constant-time comparison.
- Never commit webhook secrets or database credentials.
- Validate all externally supplied fields.
- Use HTTPS in deployed environments.
- Centralize and protect production logs because request metadata can contain sensitive information.
