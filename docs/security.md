# Security and trust boundaries

Environment-only credentials; existing .env is not overwritten. The user explicitly authorized private loading of only BOLNA_API_KEY/BOLNA_AGENT_ID for verification. Generated local credentials are separate in ignored local-data/development.env. Never attach or publish that directory, hosted-agent backups, or test session tokens.

The API uses admin-only provisioning, hashed expiring per-session call credentials and separate webhook/evidence secrets. Session IDs alone do not confer access. Session ownership and expected version are checked inside transactions. The LLM cannot supply customer/execution ownership changes or submit a verified-evidence object. Use HTTPS and protect host/proxy logs. The public docs expose schema, not stored data or secrets.

The database runtime role is NOSUPERUSER/NOCREATEDB/NOCREATEROLE, with SELECT/INSERT and narrowly scoped UPDATE; no DELETE or DDL. Historical projection updates are revoked. Migrations use a separate owner role. Local database/backend ports bind to loopback. Docker runtime runs as an unprivileged user. Production additionally requires managed secret storage, encrypted storage/backups, TLS to PostgreSQL as appropriate, retention/deletion policy and network restrictions.

Requests are capped at 64 KiB, address fields retain strict bounds and unknown-field rejection. A 120/minute per-credential in-process limit protects basic use, with bounded bucket storage. This is not a distributed abuse-control guarantee; use gateway rate limits before public production exposure. Invalid arbitrary tokens can create buckets, so gateway IP limits remain necessary.

Structured logs include request/operation/status/latency and transition IDs/version/reasons, not authorization, addresses or transcripts. Avoid enabling SQL parameters, proxy body logging, debug tracebacks or verbose HTTP client logging. Postal source text is validated; arbitrary metadata is not copied from webhook payloads.

Synthetic tests verify selected authentication, ownership, malformed-input, SQL-injection-text, stale/replay, rollback, logging and database privilege cases. They are not an independent penetration test. The earlier independent reviewer was blocked by its usage limit; no independent security-review pass is claimed.
