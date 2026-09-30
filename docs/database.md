# Database Notes

The message table uses `message_id` as the primary key. Messages retain sender, recipient, timestamp, text, and creation time.

For production scale, PostgreSQL is preferred over SQLite. Indexes should be evaluated against real query patterns for sender, timestamp, and text-search workloads.
