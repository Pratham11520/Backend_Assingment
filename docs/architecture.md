# Architecture Notes

## Request flow
1. Receive webhook request.
2. Verify the HMAC-SHA256 signature before business logic.
3. Validate the payload.
4. Enforce message idempotency at the application and database layers.
5. Persist the message.
6. Expose health, analytics, metrics, and structured logs.

## Operational concerns
- Keep secrets in environment or a managed secret store.
- Prefer PostgreSQL for production workloads.
- Expose Prometheus metrics for monitoring.
