# Phase 2 implementation design: first milestone 2A

Status: written design approved by the user on 2026-09-30. The user-supplied [Phase 2 contract](../../phase2-contract.md) is authoritative. The user selected the strict evidence gate: block saves until trustworthy evidence is available; use test evidence for Phase 2A. No Phase 2 application code has been implemented.

## Intent and scope

Make the backend authoritative for address versions, validation, confirmation, and persistence eligibility. The latest user request authorizes work on Phase 2 even though Phase 1's live-call acceptance remains unverified; retain that limitation in reports rather than treating it as a reason to reject backend development.

Follow the requested order. Implement 2A first as a deterministic domain package with Pydantic schemas and unit tests. Then proceed through validation, PostgreSQL, authenticated APIs, Bolna tools/webhooks, and product/security/reliability checks. Do not deploy or introduce distributed infrastructure. Do not start with Bolna function calling.

The current project contains the Phase 1 prompts, configuration, helper scripts, and tests. A local .env now exists; do not print, overwrite, or assume its contents. .env.example is currently absent. Python 3.11.3 is available; required Phase 2 packages are not installed in the inspected interpreter. Docker CLI exists; the Docker engine and PostgreSQL are not yet verified.

## Approach options

Recommended: a pure domain state machine, then a PostgreSQL-backed service with one transaction per state transition. The domain tests establish the business rules before voice or network dependencies exist.

Alternative: implement everything directly in FastAPI handlers. It reduces initial files but couples rules to HTTP and persistence, making state/concurrency behavior harder to test independently.

Alternative: connect Bolna first and grow a backend around its tool calls. This contradicts the required implementation order and retains critical decisions in the LLM. Do not use it.

## Domain boundaries

- Address candidate: nine nullable strict string fields; unknown fields rejected. Explicit null clears a field; omitted fields remain unchanged. Reject empty patches. Limit names/descriptions to 200 characters and house identifiers to 100. Candidate PIN remains a string; malformed digit counts can be retained for deterministic clarification in 2B, but never treated as valid. Reject control characters and overlong input rather than logging payloads.
- Version: immutable snapshot containing all nine fields and a positive version number. Raw customer values and normalized values stay distinguishable. Version 0 represents no candidate and is never eligible for confirmation or saving.
- Session: immutable customer/execution ownership linkage, current version, validated version, read-back reference, confirmed version, and state. Changes create a new snapshot while preserving historical snapshots.
- Validation result: belongs to a specific version, carries missing fields/conflicts and normalized representation. 2A consumes explicit test results at a trusted domain boundary; no public tool may declare arbitrary validation success. 2B supplies the real validator.
- Audit event: records operation, sequence/version references, and reason codes. Avoid copying full address values or secrets into general event metadata.

Proposed files: app/domain/address.py, app/domain/session.py, app/domain/errors.py, tests/unit/test_address.py, tests/unit/test_session.py, and pyproject.toml. Keep Phase 1 helper tests working. Add repository/API files only when their milestones need them.

## State transitions and invariants

Creation produces COLLECTING at version 0 with no validation, read-back, or confirmation.

Candidate update requires expected_version. A stale request fails without any state/history mutation. A changed patch creates current_version + 1, preserves unaffected values, and clears validated_version, read-back state, and confirmed_version. An identical patch is a no-op, so retries do not manufacture versions; a separate interrupted/rejected read-back event still clears read-back/confirmation even when values have not changed.

Validation may complete only for its requested current version. A stale in-flight result cannot validate a newer address. Invalid or failed validation clears eligibility and moves to clarification/error; it never defaults to success. A valid result pins the precise canonical snapshot for read-back. Normalization that changes the canonical content must be represented by an explicit versioned transition before that version is validated; no invisible mutation of a validated snapshot.

Read-back preparation binds a unique attempt reference to the validated version and exact rendered address. A completed read-back is distinct from merely returning text to the agent. Interruption invalidates that attempt. Confirmation must refer to the latest completed attempt for the exact current validated version and occur after completion. Refusal, uncertainty, or a correction cannot be represented as explicit approval.

Save eligibility independently checks a positive version and:

current_version == validated_version == confirmed_version

It additionally requires the corresponding accepted read-back/confirmation evidence. Domain eligibility does not itself mean a PostgreSQL write succeeded. In 2C, mark SAVED only after the transaction commits. Unique(source_session_id, source_version) makes repeated saves return the same record.

If a correction arrives after a saved version, retain the saved record as historical evidence, revoke its designation as the session's current accepted version, and collect/revalidate/reconfirm the new version. Never delete the audit trail or silently present the old address as the corrected one. The database milestone must implement these effects atomically.

## Confirmation evidence: strict policy selected

The contract's sample confirm request (version plus explicit_confirmation=true) is sufficient for version consistency but not sufficient to prove actual playback or customer speech. An authenticated LLM can still call it incorrectly. A server-issued read-back token alone also does not prove it was spoken.

Selected strict policy: domain confirmation requires read-back completion and a subsequent explicit customer-confirmation event from an independently trusted evidence adapter, bound to session, execution, version, and read-back attempt. The agent-facing tool requests confirmation; it cannot manufacture those evidence events. Unit tests use synthetic evidence from a test adapter. Without a suitable production evidence source, saving fails closed and the Bolna integration milestone remains incomplete. Test evidence must not be accepted by production confirmation routes or enabled through an agent-controlled flag.

Rejected alternative: authenticated agent-reported read-back and confirmation alone. This would preserve version checks but would not prevent false LLM confirmation; it is outside the selected design.

Evidence availability is not established. Current [Bolna tool documentation](https://www.bolna.ai/docs/tool-calling/custom-function-calls) describes parameters extracted by the LLM, and [webhook documentation](https://www.bolna.ai/docs/post-call/polling-call-status-webhooks) describes call-status execution payloads. Neither reviewed page establishes an independent completed-playback/explicit-consent signal. Do not invent that capability or treat a call-completed webhook as consent.

## Tests for 2A

Test strict field types and lengths, extra fields, null versus omission, immutable snapshots, version 0 guards, version increments, unaffected-field preservation, no-op patches, stale expected_version rejection, and validation results bound to a version.

Prove the required correction invariant: current=3, validated=3, confirmed=3 becomes current=4, validated=null, confirmed=null after a changed patch. Prove save eligibility rejects current=4, validated=4, confirmed=3. Also reject confirmation before validation, before completed read-back, after interrupted read-back, on the wrong read-back attempt, and with an uncertain/negative response.

Test that preparing text alone does not establish read-back completion, and that a no-change rejection/interrupt still invalidates the attempt. Ensure failed transitions leave no partial state changes. Domain tests cannot establish actual speech accuracy or real database isolation; later milestones must exercise those independently.

## Later milestone constraints carried forward

2B: conservative normalization, six ASCII canonical PIN digits, Unicode digit handling explicitly tested, authoritative/versioned PIN data provenance and coverage. Do not equate district with city or treat incomplete postal-city mappings as proof of a mismatch. Ambiguous/unavailable lookup fails to clarification or VALIDATION_ERROR; never silently overwrites customer geography.

2C: PostgreSQL/Alembic migrations, unique and foreign-key constraints, transactional optimistic concurrency (compare-and-update or locked row plus version check), immutable versions and validation attempts. Test against real PostgreSQL, including restart durability, concurrent update/save, and migration rollback. SQLite is not proof of PostgreSQL correctness.

2D: FastAPI with strict request schemas, service authentication and server-derived session authorization. A broad shared service secret plus arbitrary session_id is not sufficient ownership enforcement. Bind a scoped authenticated call principal to the stored execution/session/customer mapping; privileged session creation is separate from agent tools. Preserve the contract's distinct update/validate/confirm/save operations and add internal read-back/evidence operations as required by the chosen policy.

2E–2F: verify Bolna tool headers/context and call linkage using the actual account before configuring them. Webhook authentication is independent; deduplicate by authentic event ID if available, otherwise a documented stable event fingerprint. Handle out-of-order statuses without reverting a terminal call or changing address confirmation. Call lifecycle is not address acceptance.

2G–2J: reuse voice scenarios with database assertions; separate conversation_outcome, backend_outcome, and test_result. NOT_RUN remains the initial test_result. Exercise authentication/IDOR, input limits, rate limiting, secret/dependency scans, PII-safe logs, database least privilege, retention/deletion, encrypted backup/restore, reliability failures, migration/rollback and operational runbooks. Unverified infrastructure controls remain release blockers, not claimed features.

## Definition of completion

2A completion means only deterministic domain transitions and schema tests pass. It does not mean validation against live postal data, PostgreSQL persistence, authenticated API operation, or real voice integration is complete. All 22 Phase 2 acceptance criteria remain the final exit contract.

Next step after review of this written design: write the detailed 2A implementation plan, then implement and test it in this chat using the established direct-execution preference. Evidence policy is already decided and must not be asked again.
