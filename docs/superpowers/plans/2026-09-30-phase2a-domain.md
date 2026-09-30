# Phase 2A Domain and Confirmation Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Establish deterministic address versions and save eligibility with a strict read-back/confirmation evidence gate, proven by unit tests before backend or voice integration.

**Architecture:** Immutable domain objects and pure transitions separate candidate updates, validation results, read-back attempts, confirmation, and persistence eligibility. A trusted evidence-verifier interface defaults to rejecting all evidence; synthetic implementations exist only in tests. No HTTP routes, PostgreSQL implementation, PIN lookup, or Bolna changes in this milestone.

**Tech Stack:** Python 3.11+, Pydantic 2, pytest, Python standard library.

**Spec:** `docs/superpowers/specs/2026-09-30-phase2-domain-design.md` (approved); original contract `docs/phase2-contract.md`.

**Execution:** Direct implementation in this chat, preserving the user's established preference. Approved and implemented. Phase 2A tests and independent review passed; see docs/phase2a-report.md and docs/phase2a-progress.md for evidence and remaining integration work.

## Global Constraints

- Do not start with Bolna function calling.
- Candidate PIN remains a string; malformed digit counts can be retained for deterministic clarification in 2B, but never treated as valid.
- Explicit null clears a field; omitted fields remain unchanged.
- Version 0 represents no candidate and is never eligible for confirmation or saving.
- Test evidence must not be accepted by production confirmation routes or enabled through an agent-controlled flag.
- Domain eligibility does not itself mean a PostgreSQL write succeeded.
- A local .env now exists; do not print, overwrite, or assume its contents.
- Keep conversation_outcome, backend_outcome, and test_result distinct; unexecuted integration tests remain NOT_RUN.
- No actual validation, durable persistence, authentication, audio proof, or production readiness is claimed by synthetic domain tests.

## Review Focus

1. A frozen object containing a mutable dictionary is not immutable: use immutable nested models and tuples, and test old snapshots cannot change (Tasks 1–2).
2. Revalidation of an unchanged address must revoke earlier read-back/confirmation, not merely compare equal version integers (Tasks 2–3).
3. Evidence replay across sessions, executions, versions, or read-back attempts must fail without partial state mutation (Task 3).
4. A model-controlled trusted=true flag or matching text token must not bypass evidence verification (Task 3).
5. An interruption or rejection without changed field values must invalidate consent, including after a saved version (Tasks 3–4).

## Files and boundaries

- `pyproject.toml`: packaging, Python floor, Pydantic dependency, pytest development dependency and test discovery.
- `app/__init__.py`, `app/domain/__init__.py`: package markers.
- `app/domain/address.py`: strict Address/AddressChanges schemas, immutable AddressVersion and deterministic read-back rendering.
- `app/domain/errors.py`: DomainError with stable code and safe messages, no address values in errors.
- `app/domain/session.py`: immutable Session, ValidationResult, AuditEvent, and pure version/validation transitions.
- `app/domain/confirmation.py`: evidence protocol, fail-closed verifier, read-back lifecycle, confirmation and save eligibility.
- `tests/unit/test_address.py`, `test_session.py`, `test_confirmation.py`: behavioral tests.
- `tests/unit/conftest.py`: synthetic validation/evidence fixtures; never shipped as application functionality.
- `README.md`: additive Phase 2A setup and scope.
- `docs/phase2a-report.md`: verified unit results, limitations, and next milestone.
- `docs/phase2a-progress.md`: task ledger and explicit rulings.

## Task 1: Address schemas and immutable snapshots

**Interfaces:** `Address` has the nine nullable string fields in the contract. `AddressChanges` has the same fields and distinguishes omitted from explicitly null through Pydantic's supplied-field tracking. `AddressVersion(version: int, raw: Address, canonical: Address)` is immutable. `apply_changes(address: Address, changes: AddressChanges) -> Address` returns a validated replacement. `render_readback(address: Address) -> str` includes every nonempty canonical field in schema order, with PIN digits separated by commas. `DomainError(code: str)` exposes a stable code without raw input.

- [x] Create project-local virtual environment and pyproject dependency metadata. Install only Pydantic 2 and pytest plus packaging requirements into it. Pin the resolved direct dependency versions after installation. If network approval is required, request it normally; do not change the global interpreter. Verify the existing 18 helper tests first using their current unittest command.
- [x] Write failing schema tests before the domain implementation. Cases: string preservation (including Hindi and leading zeros), integer/bool rejection, extra field rejection, house length 100 accepted/101 rejected, description length 200 accepted/201 rejected, PIN candidate length limit 32, empty patch rejection, and explicit null versus omission.

```python
base = Address(house_flat="302", building="Galaxy Apartments")
assert apply_changes(base, AddressChanges(house_flat=None)).house_flat is None
assert apply_changes(base, AddressChanges(house_flat=None)).building == "Galaxy Apartments"
assert base.house_flat == "302"
```

- [x] Verify failure with `.venv\Scripts\python.exe -m pytest tests/unit/test_address.py -q`; missing schema implementation is the expected initial failure.
- [x] Implement strict, extra-forbidden, frozen schemas. Use tuples for collections in snapshots. Reject Unicode control/surrogate characters (categories Cc/Cs); preserve ordinary Unicode names and joiners. Reject blank non-null strings; require null to clear. Do not add geographic normalization or speculative flat-number conversion. Suppress input values in rendered validation errors.
- [x] Add and run read-back tests: every supplied optional field survives rendering; nulls are omitted; PIN 500032 appears as `5, 0, 0, 0, 3, 2`; old snapshots reject mutation. English rendering is a deterministic 2A artifact, not a claim of multilingual TTS verification.
- [x] Require the address tests and original helper suite to pass. Record commands/results and resolved dependency versions in the ledger.

## Task 2: Versioned sessions and validation boundaries

**Interfaces:** `Session` is an immutable aggregate with session_id, customer_id, bolna_execution_id, status, versions tuple, current_version, validated_version, validation_attempt_id, confirmed_version, readback, saved_references tuple, and audit_events tuple. `AuditEvent` contains event sequence, operation, version and safe reason/reference IDs only. `ValidationResult` contains version, attempt_id, status (VALID/NEEDS_CLARIFICATION/VALIDATION_ERROR), canonical address, missing_fields tuple, and conflict codes tuple. IDs are UUIDs except customer/execution external identifiers, which are bounded nonblank strings.

Functions: `create_session(session_id: UUID, customer_id: str, execution_id: str) -> Session`; `update_candidate(session: Session, expected_version: int, changes: AddressChanges) -> Session`; `record_validation(session: Session, result: ValidationResult) -> Session`. No validator adapter callable from the LLM is added.

- [x] Write failing tests for version-0 creation and guards, changed patch increment, unchanged-field retention, identical patch no-op, stale expected_version rejection, rejected operation leaving the original aggregate unchanged, and immutable historical snapshots.
- [x] Run `.venv\Scripts\python.exe -m pytest tests/unit/test_session.py -q`; verify failures correspond to unimplemented transitions.
- [x] Implement pure transitions. Start COLLECTING at 0. Changed patch creates CANDIDATE_UPDATED and clears validation, read-back and confirmation; identical patch returns unchanged state. All version arguments are strict nonnegative integers, never bools. Ownership identifiers have no update operation.
- [x] Add tests for valid validation to READY_FOR_READBACK, missing/conflict to NEEDS_CLARIFICATION, failure to VALIDATION_ERROR, and stale in-flight validation rejection. Revalidation invalidates all earlier read-back/confirmation even if the version does not change. An exact duplicate attempt/result is idempotent; reuse of an attempt ID with different content is rejected.
- [x] Implement validation recording at a trusted internal boundary. Reject a VALID result whose canonical address differs from the current canonical snapshot; normalization must first create an explicit version through the update transition. Record each distinct accepted validation attempt and safe audit event. This consumes synthetic validator results in 2A; it does not claim postal validation exists.
- [x] Run all unit tests plus the original helper tests; require zero failures and record results.

## Task 3: Strict read-back and confirmation evidence

**Interfaces:** `ReadbackAttempt` binds UUID id, session/execution, positive version, validation_attempt_id, rendered_text and SHA-256 digest, plus completion/confirmation evidence references. A read-back reference alone grants no permission.

`EvidenceVerifier.verify(reference: str) -> VerifiedEvidence` is a process-injected trusted interface. `VerifiedEvidence` is immutable and contains evidence_id, kind (READBACK_COMPLETED/CUSTOMER_CONFIRMED), session_id, execution_id, version, validation_attempt_id, readback_id, text_digest and source_sequence (positive integer). The verifier must establish provenance before returning it; the domain checks binding and order. `RejectAllEvidenceVerifier` is the default and always raises EVIDENCE_UNAVAILABLE. There is no trusted boolean or test-mode request field.

Functions: `prepare_readback(session: Session, attempt_id: UUID) -> Session`; `complete_readback(session: Session, evidence_reference: str, verifier: EvidenceVerifier) -> Session`; `confirm_address(session: Session, version: int, explicit_confirmation: bool, evidence_reference: str, verifier: EvidenceVerifier) -> Session`; `invalidate_readback(session: Session, reason: Literal['INTERRUPTED', 'REJECTED', 'UNCERTAIN']) -> Session`. The verifier argument defaults to RejectAllEvidenceVerifier, never a permissive adapter.

- [x] Write failing tests that preparing read-back produces the complete canonical text/digest but not completion, and default verification rejects arbitrary strings, agent booleans, and matching text hashes. Add a synthetic verifier solely in tests/unit/conftest.py with explicit fixtures; do not export it from app.
- [x] Run the confirmation test file and observe failures before implementing.
- [x] Implement preparation for the exact validated current version only; each fresh attempt clears prior confirmation. Apply verified playback completion to WAITING_CONFIRMATION, then verified customer confirmation to CONFIRMED. Require explicit_confirmation to be the literal boolean True, and confirmation source_sequence strictly later than completion.
- [x] Test wrong session, execution, version, attempt, validation attempt, text digest, evidence kind and event ordering. Reject evidence replay under different bindings. Exact repeated confirmation for the same accepted evidence is idempotent. Failed transitions cannot change any field or append a success audit event.
- [x] Test interruption/rejection/uncertainty both before and after completion/confirmation, with no field changes. These revoke read-back/confirmation and require a newly prepared completed attempt before another confirmation. Keep still-valid address validation; move to READY_FOR_READBACK until a correction changes it.
- [x] Verify no fake adapter or request-controlled trust option exists in application code. Run the complete unit and helper suites; record evidence in the ledger.

## Task 4: Save eligibility, correction regression, and handoff

**Interfaces:** `require_save_eligible(session: Session) -> AddressVersion` independently checks current/validated/confirmed equality, positive version, current validation attempt, completed latest read-back, and its accepted subsequent confirmation evidence. It does not persist anything. `SavedReference` holds address_id, source_version and accepted evidence references. `record_saved(session: Session, address_id: UUID, version: int) -> Session` is an internal hook for a future repository to call only after committed persistence; it rechecks eligibility and is idempotent for the same receipt. No public save endpoint exists in 2A.

- [x] Write failing tests for every save guard, including a deliberately constructed inconsistent aggregate with current=4, validated=4, confirmed=3. The guard must reject it independently rather than rely on earlier transitions having been correct.
- [x] Add the contract's exact correction regression using valid transitions and synthetic evidence:

```python
assert (s.current_version, s.validated_version, s.confirmed_version) == (3, 3, 3)
changed = update_candidate(s, 3, AddressChanges(house_flat="320"))
assert (changed.current_version, changed.validated_version, changed.confirmed_version) == (4, None, None)
with pytest.raises(DomainError):
    require_save_eligible(changed)
```

- [x] Run these tests and verify failure, then implement eligibility and receipt recording. A save receipt does not bypass validation/evidence. Repeated identical receipt does not duplicate history; a conflicting address ID for the same session/version fails.
- [x] Test correction and interruption after a recorded saved reference. Preserve historical reference but make current acceptance unavailable immediately; require new evidence before current eligibility is restored. Record that actual atomic database supersession is a 2C obligation.
- [x] Add README setup/run instructions and docs/phase2a-report.md with scope, results, strict evidence trust boundary and later milestones. Preserve local .env and Phase 1 artifacts. Mark real PostgreSQL, PIN-data, API and live-Bolna checks NOT_RUN rather than PASS.
- [x] Run `.venv\Scripts\python.exe -m pytest -q` over all tests, including the original unittest-style helper tests. Also run `python -m unittest discover -s tests -v` to verify Phase 1's documented command still works. Record exact pass/fail counts.
- [x] Request one independent read-only review of all Phase 2A changes under the established review workflow. Fix substantive findings with reproducing tests before claiming completion. Do not create a repository, commit, push, or deploy merely for workflow bookkeeping if Git remains unavailable.
- [x] Deliver links to the implementation and report. Claim only 2A completion when tests pass; preserve all remaining 2B–2J acceptance work. Synthetic evidence proves state-machine behavior, not real customer consent.

## Self-review

Coverage: Task 1 covers strict candidate data and immutability; Task 2 covers versioning and validation attempt binding; Task 3 covers the approved evidence policy and interruption; Task 4 independently enforces save guards and post-save invalidation. All five review-focus cases have assigned tests. Future PostgreSQL/API concurrency and external evidence authenticity remain explicit integration obligations, not purported guarantees of an in-process type system.

Implementation details resolved here: candidate PIN maximum 32 characters; blank strings rejected rather than implicitly cleared; no-op updates keep the version; revalidation revokes consent; default verifier rejects all; fake evidence lives only in tests. These narrow decisions preserve the approved contract.
