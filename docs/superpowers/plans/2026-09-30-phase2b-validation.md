# Phase 2B Validation Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Implement deterministic completeness, PIN and official postal validation without weakening address-version or confirmation integrity.

**Architecture:** A pure validator consumes immutable snapshots and an injected local postal directory. Shared immutable metadata connects normalization proposals and validation history to the existing domain. A manual importer creates verifiable versioned reference artifacts.

**Tech Stack:** Existing Python 3.11+, Pydantic 2.13.5, pytest 9.1.1; standard-library CSV, JSON, hashing, dates and Unicode. No new runtime dependency planned.

**Spec:** docs/superpowers/specs/2026-09-30-phase2b-validation-design.md; approved review docs/phase2b-design-review.md; original docs/phase2b-proposed-design.txt.

**Execution:** Preserve direct implementation in this chat, with one final independent read-only review. Execution approved. Tasks 1–4 implemented and tested; Task 5 integration checks pass, independent review blocked by usage limit, official-file ingestion blocked. See docs/phase2b-progress.md.

## Global Constraints

- Scope is Phase 2B only; preserve the strict Phase 2A evidence gate.
- Never read or modify .env.
- Keep test_result separate from conversation_outcome and backend_outcome.
- No database, API, Bolna, deployment, scheduler or network-per-validation implementation.
- Unicode decimal conversion plus ASCII spaces only; no O-to-zero or fuzzy geographic correction.
- Default source maximum age 90 days, explicit injected evaluation date and versioned policy.
- Preserve raw customer data, immutable historical versions and origin metadata.
- Real ingestion remains NOT_RUN until an actual official file is imported and verified.
- Use the existing workspace. If Git remains unavailable, record progress/results in docs/phase2b-progress.md instead of inventing commits or creating a repository.

## Review Focus

1. A PIN correction must discard old derived state while preserving customer state (Task 2).
2. A customer claim equal to a derived value changes provenance and must create a version (Task 2).
3. Fresh import timestamps cannot conceal stale source dates, and partial corrupt imports cannot become ready (Task 3).
4. Unknown district evidence is not proof of disagreement; city/office mismatch is not conflict (Task 4).
5. Same-version foreign proposals or late results cannot bypass snapshot binding or revoke/restore the wrong session's eligibility (Tasks 2 and 5).

## File map

- app/domain/validation_metadata.py: origins, provenance, policy/result metadata and normalization proposal value objects.
- app/domain/address.py: snapshot origins and normalization provenance.
- app/domain/session.py: normalization transition, customer correction origin handling and richer ValidationResult history.
- app/validation/models.py: ValidationPolicy, PostalRecord, PostalLookupResult and directory readiness.
- app/validation/normalization.py and required_fields.py: pure local rules.
- app/validation/postal_directory.py: protocol, immutable local loader/index and safe errors.
- app/validation/engine.py: ordered orchestration and structured outcomes.
- scripts/import_postal_data.py: manual official CSV ingestion CLI.
- tests/unit/test_pincode_normalization.py, test_required_fields.py, test_normalization_transition.py, test_postal_directory.py, test_validation_engine.py, test_validation_provenance.py: behavior tests.
- tests/fixtures/postal/: explicitly synthetic good/bad CSV/JSON fixtures.
- docs/postal-data.md, docs/phase2b-report.md, docs/phase2b-progress.md, README.md, data/postal/README.md: usage, evidence and limitations.

## Task 1: Local normalization and completeness

**Interfaces:** normalize_pincode(value: str | None) -> PinNormalization (canonical: str | None, reason_codes: tuple[str, ...], changed: bool); missing_required_fields(address: Address) -> tuple[AddressField, ...]. ValidationPolicy defaults: version urban-v1, max_source_age_days 90. Immutable supporting types follow FrozenModel conventions.

- [x] Run baseline `.venv\Scripts\python.exe -m pytest -q`; record actual results in the ledger (prior baseline 108 passed, 26 subtests).
- [x] Write tests before implementation: 500032 unchanged; 500 032 and ५०००३२ become 500032; 50003/5000327 wrong length; 500O32, superscripts, hyphen and zero-width text invalid. Missing PIN is PINCODE_REQUIRED. Normalizing a normalized PIN produces changed=False.
- [x] Write completeness tests: house_flat='Sharma Medical Store', area/city/PIN satisfy completeness; building alone and landmark alone do not; missing fields return stable house_flat, area, city, pincode order.
- [x] Run the two new test files and observe missing implementation failures.
- [x] Implement the signatures in normalization.py and required_fields.py plus immutable PinNormalization and ValidationPolicy models. Use unicodedata.decimal without compatibility normalization.
- [x] Rerun those tests and the full suite; record red/green evidence. Commit only if a usable repository exists and workflow allows it.

## Task 2: Versioned normalization and origin history

**Interfaces:** NormalizationProposal carries proposal_id, base_version, base_snapshot: AddressVersion, canonical: Address, origins and metadata specified in the spec. apply_normalization(session: Session, expected_version: int, proposal: NormalizationProposal) -> Session lives in session.py. It is a trusted internal operation, never an agent request schema. Extend ValidationResult with immutable metadata defaults to preserve Phase 2A synthetic test construction.

- [x] Add failing tests for raw Unicode PIN preservation, canonical ASCII PIN at new version, unchanged old snapshot, cleared consent/save eligibility, stale and same-version wrong-snapshot proposals, immutable nested origins, and rejection of no-change proposals.
- [x] Add tests for PIN correction removing POSTAL_DATA state; preserving CUSTOMER state; explicit state in the same patch winning; equal-value explicit customer state creating a new provenance-bearing version. Unaffected fields/origins survive.
- [x] Run `... -m pytest tests/unit/test_normalization_transition.py -q` and verify failures.
- [x] Implement shared metadata types, snapshot origins and apply_normalization. Bind proposal to complete current snapshot and policy metadata; validate replacement objects instead of unvalidated model copies. Add CANONICAL_NORMALIZED audit operation with reference IDs, no address payload.
- [x] Update update_candidate to record supplied fields as customer-origin and invalidate dependent derived state on changed PIN. Extend validation history metadata while retaining attempt reuse checks and canonical equality checks. Do not relax confirmation/save guards.
- [x] Run normalization-transition tests and the complete existing suite; record results.

## Task 3: Versioned postal import and local lookup

**Interfaces:** PostalDirectory.lookup_pincode(pincode: str) -> PostalLookupResult; load_directory(path: Path, policy: ValidationPolicy, as_of: date) -> LocalPostalDirectory with readiness/error codes; import_csv(source: Path, output: Path, provenance_inputs: ImportMetadata) -> PostalDataProvenance. ImportMetadata supplies trusted official identity/release/import metadata; content hashes are computed, never accepted as substitutes for origin verification.

- [x] Write fixtures/tests for duplicate PIN offices, duplicate rows, header BOM, missing/duplicate headers, invalid UTF-8, malformed late row, invalid PIN/state/district, artifact tampering and conflicting existing output. Assert failed imports publish no usable artifact and failed directories never return permissive matches.
- [x] Write provenance tests for stable normalized digest despite row ordering, original-byte digest, immutable source metadata, age90 accepted/age91 rejected, future dates rejected, reimported stale data still stale and production loader rejecting SYNTHETIC artifacts.
- [x] Run the new postal/provenance tests before implementation and observe expected failures.
- [x] Implement CSV validation and stable normalized-record artifact serialization. Write only after complete validation; use exclusive output creation or safe atomic publication without overwriting a different existing artifact. Build a private immutable PIN index retaining all records.
- [x] Implement readiness/error models and lookup failures with safe reason codes. Check both hash integrity and required provenance on load; freshness uses source release date and injected date. Keep synthetic directory construction confined to test fixtures/injection.
- [x] Add the manual CLI with explicit input/output/resource/release metadata arguments and document invocation, expected columns, hash algorithm, trusted-operator boundary and no runtime downloads.
- [x] Run postal/provenance tests and full suite; record results.

## Task 4: Pure validation engine

**Interfaces:** validate_address(snapshot: AddressVersion, directory: PostalDirectory, policy: ValidationPolicy, as_of: date, attempt_id: UUID) -> ValidationResult | NormalizationProposal. Caller supplies attempt_id so evaluation is deterministic. Result includes canonical snapshot, codes, conflicts, warnings, origins, policy identity and postal provenance. Proposal IDs may use supplied attempt_id.

- [x] Write tests for required fields and malformed PIN without lookup; known/unknown PIN; matching/conflicting state; exact/explicit alias comparison; any matching district; missing district evidence; multiple districts; conflicting states; unavailable/corrupt/stale directory; sanitized lookup exception. Assert no failure returns VALID.
- [x] Write tests that unrelated city/office and area/office strings remain accepted completeness values with explicit unverified warnings. Missing state proposes a derivation only for unanimous reference state. Conflict must not silently rewrite supplied state.
- [x] Write normalization tests: Unicode/space PIN proposes exact bound changes; combined PIN+state canonical changes create one proposal; after application validation converges to VALID; conflicts prevent automatic proposal application. Metadata persists in recorded results and participates in duplicate-attempt equality.
- [x] Run `... -m pytest tests/unit/test_validation_engine.py -q` and observe failures.
- [x] Implement ordered stages and status/action priority specified in the spec. Compare geographic strings conservatively without altering customer spelling. Pin all codes in enums/literals or validated constants; exclude freeform customer values from error messages.
- [x] Run new engine tests and full suite; record results.

## Task 5: Integration, actual import verification and handoff

**Interfaces:** Use Tasks 2–4 APIs without an HTTP/application-service shortcut or trust flag.

- [x] Add regression tests establishing v3 with prior evidence, applying a normalization proposal to reach v4, asserting raw preservation and null validation/confirmation/readback, and then recording only the v4 result. Add a pending v3 validation followed by customer v4 correction; late VALID v3 must raise ADDRESS_VERSION_CHANGED and leave state untouched.
- [x] Run new regression tests before any needed integration changes, implement only necessary fixes, and rerun. Ensure default evidence verifier still blocks real confirmation/save eligibility.
- [ ] Acquire an actual official Department of Posts release using the documented source (no credentials in outputs). Verify resource identity/date and source schema; run importer, load and sample lookups with recorded checksums and counts. If inaccessible, record the precise limitation and NOT_RUN real-ingestion status; never replace it with synthetic success. Adjust explicit source-column mapping only on evidence and add representative synthetic schema tests.
- [x] Write docs/postal-data.md and docs/phase2b-report.md covering policy defaults, completeness limits, origins, official provenance, import command, dataset freshness, status/action meanings and deferred milestones. Update README and data/postal/README.md. Keep bulky acquired artifacts in ignored local-data with report metadata.
- [x] Run `.venv\Scripts\python.exe -m pytest -q` and `python -m unittest discover -s tests -v`; verify documented importer help and setup imports. Record exact counts and distinguish synthetic tests from actual import evidence.
- [ ] Obtain one independent read-only review; fix substantive findings with reproducing tests and rerun affected/full checks. Do not read .env or perform live voice calls.
- [ ] Deliver report and implementation links. Claim Phase 2B complete only when required checks including real import are evidenced; otherwise state implemented scope and remaining blocker. Phase 2C is next; Phase 2 overall remains incomplete.

## Self-review

All seven approved review points have explicit interfaces and tests. Task 1 owns deterministic text/completeness rules; Task 2 owns raw/origin/version integrity; Task 3 owns postal integrity/provenance/freshness; Task 4 owns conservative matching and status decisions; Task 5 owns stale-result regressions and real-data evidence. Five review-focus cases are assigned above. No code, database or live integration work is claimed by this plan.
