# Implementation and verification report

Latest update: [demo postal integration](demo-postal-report.md) adds explicit development-only UNVERIFIED_OR_STALE data, with production startup protection. Local tests pass (192 +26 subtests). The single demo call updated v0→v4 but did not validate due to a captured PIN mismatch; readback was correctly blocked. Agent restored and tunnel stopped.

Latest result: [corrected-mapping live report](typed-live-report.md) records **LIVE_TOOL_PATH PASS**, with five real Bolna HTTP 200 mutations, version 0→5 and independently checked PostgreSQL rows. Original agent restored and tunnel stopped. This supersedes the earlier live-retest NOT_RUN status below; production validation/confirmation remain blocked.

Update: [live tool-path investigation](live-tool-debug-report.md) identified a pre-HTTP JSON template failure on four update_address attempts. The correction is locally tested (181 tests +26 subtests); the single diagnostic live call failed the version-change criterion. Original agent restored, tunnel stopped. Corrected live retest NOT_RUN.

Date: 2026-09-30. Overall acceptance: PARTIAL. The backend is implemented and tested; a production successful-save voice demonstration remains BLOCKED.

## Delivered

- FastAPI endpoints, strict request schemas, per-session authorization and separate privileged/webhook/evidence credentials.
- PostgreSQL 17 schema, Alembic migrations, restricted runtime role, immutable histories, concurrency locks, idempotent committed saves and supersession on correction.
- Deterministic field/PIN normalization, source provenance and freshness gates, conservative postal matching, exact English/Hindi read-back and version/attempt-bound confirmation evidence.
- Seven Bolna function definitions, existing-agent configuration backup/update/restore, authenticated webhook ingestion and a reserved single-call development runner.
- Docker development setup, redacted logs, health checks, operating instructions and test coverage.

## Measured checks

| Check | Result | Evidence / limit |
|---|---|---|
| Full suite with actual PostgreSQL | PASS | 174 tests and 26 subtests; latest run 8.18 seconds |
| Original helper unittest suite | PASS | 18 tests; included in full suite, not additional coverage |
| Migration upgrade/downgrade/upgrade | PASS | Separate disposable PostgreSQL database |
| Database restart durability | PASS | Persisted marker survived actual container restart |
| Concurrent writes/saves and failed-commit rollback | PASS | Real PostgreSQL integration tests |
| API save with synthetic evidence/data | PASS | Test-only injected evidence and directory; does not prove production consent |
| Existing hosted agent tools update | PASS | PUT accepted; tools visible on subsequent GET |
| Authorized live call submission | PASS | One execution scheduled and bound to backend session |
| Live conversation and tool invocation | PARTIAL | Provider final status completed, duration 10 seconds; backend remained COLLECTING at version 0 with no address updates |
| Official postal import | BLOCKED | No CSV supplied or independently verified; synthetic data excluded |
| Production playback/confirmation adapter | BLOCKED | Default verifier rejects all evidence |
| Independent final review | NOT_RUN | Reviewer unavailable because of usage limit; self-review is not independent review |
| Optional backend Docker image | NOT_RUN | API tested in local Python environment against containerized PostgreSQL |

One dependency warning remains: Starlette deprecates its httpx TestClient path. Tests pass; this is not a production request failure.

The single authorized call first reported call-disconnected, then completed. The provider returned no error or termination reason in the checked fields. This does not establish why it ended or whether voice/tool behavior was correct. conversation_outcome remains null. No second call was placed. The original agent configuration was restored and a fresh GET confirmed no tools attached, matching its pre-test state. The temporary tunnel was stopped; PostgreSQL and the loopback backend remain available locally.

## Acceptance boundaries

conversation_outcome is separate from test_result. An unrun scenario remains NOT_RUN with a null conversation outcome. A completed provider execution alone does not prove a correct conversation, read-back or consent.

Production readiness fails closed without verified, fresh postal data. Saving additionally requires independently trustworthy completed playback and later explicit confirmation for the exact current version and attempt. Neither authenticated LLM reports nor generic webhooks can satisfy this gate. No permissive runtime evidence mode was added.

Static per-session agent tool configuration is reserved for this single-call development test. Concurrent production calls require verified per-call isolation. Local in-process rate limiting needs a shared gateway equivalent for multiple workers. Retention, recovery, deployment TLS and source restrictions require operational configuration.

See [operations](operations.md), [API](api.md), [postal setup](postal-data.md), [Bolna integration](bolna-integration.md), [security](security.md), and [testing](testing.md). Private credentials, hosted backups and call artifacts are under ignored local-data; the original .env was not modified.
