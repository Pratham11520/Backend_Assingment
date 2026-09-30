# Engineering Checklist

## API
- Validate request payloads.
- Verify webhook signatures before processing.
- Preserve idempotency guarantees.
- Keep pagination bounded.

## Reliability
- Maintain liveness and readiness probes.
- Track latency and request outcomes.
- Keep structured logs useful for debugging.

## Deployment
- Keep secrets outside source control.
- Use PostgreSQL for production workloads.
- Run tests before deployment.
- Keep container and dependency versions reproducible.
