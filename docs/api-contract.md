# API Contract Summary

### POST /webhook
Authenticates and ingests a message.

### GET /messages
Returns paginated messages with optional sender, timestamp, and text filters.

### GET /stats
Returns aggregate message statistics.

### GET /health/live
Reports process liveness.

### GET /health/ready
Reports dependency readiness.

### GET /metrics
Exposes Prometheus metrics.
