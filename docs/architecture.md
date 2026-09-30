# Architecture

Bolna owns telephony, speech recognition/synthesis, turn-taking and tool invocation. FastAPI owns authentication, session ownership and orchestration. Immutable domain transitions own address versions, normalization, validation binding and confirmation eligibility. The pure validator uses a versioned local postal directory. SQLAlchemy persists state and separate historical projections in PostgreSQL.

Every mutation locks the customer row then the session row, compares expected_version, applies domain transitions, appends histories, updates the session aggregate and commits atomically. Customer locking serializes final-address supersession across sessions. The version comparison is optimistic concurrency; row locks protect the comparison and transaction. No success response is returned before commit. SQLAlchemy uses bound parameters and hides SQL parameter logging.

Tables: customers, address_sessions, address_versions, validation_attempts, readback_attempts, confirmation_events, addresses, call_events and audit_events. Sessions store the complete immutable aggregate for lossless rehydration; separate tables support audit/querying. Version/validation/evidence/audit projections are append-only to the restricted runtime role. Read-back lifecycle rows and accepted-address supersession timestamps can change. Constraints enforce unique session/version and accepted record uniqueness; migrations bind projections to existing versions.

Credentials: admin creates sessions; a cryptographically random four-hour per-session token is returned once and stored as SHA-256. It binds the caller to the stored customer/execution/session. The admin token does not grant tool access. Webhook and evidence-adapter credentials are separate. No public input accepts a Session, ValidationResult, NormalizationProposal or VerifiedEvidence object.

The evidence interface remains default-deny. Trusted adapter requests supply opaque references, resolved by server-injected verifier code. No production adapter currently proves exact playback and subsequent customer consent. Tests inject synthetic evidence exclusively in the test process. A completed call never implies address confirmation.

Single-process rate limiting is a development safeguard; deploy gateway limits for distributed service instances. No frontend, queue, Redis or microservice is required.
