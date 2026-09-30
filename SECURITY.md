# Security Policy

## Reporting a vulnerability

Please do not disclose security vulnerabilities in a public issue. Contact the repository owner privately with a clear description, reproduction steps, affected component, and potential impact.

## Security practices

- Keep secrets out of source control.
- Verify webhook signatures before processing requests.
- Use constant-time comparison for signature checks.
- Validate and constrain externally supplied input.
- Use HTTPS in deployed environments.
- Review dependency updates regularly.
