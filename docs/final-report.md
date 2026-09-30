# Final assignment report

Date: 2026-09-30

**ASSIGNMENT IMPLEMENTATION: COMPLETE**  
**PRODUCTION READINESS: NOT READY**

The requested deterministic offline demonstration completed through the actual FastAPI API and real PostgreSQL. No additional Bolna call, hosted-agent change or tunnel was used for this task.

## Verification

| Check | Actual result |
|---|---|
| Full suite with real PostgreSQL | 197 passed + 26 subtests; no skips; 7.07 seconds |
| Original unittest suite | 18 passed; included in pytest's total |
| Offline runner | PASS — OFFLINE_BOLNA_SIMULATION |
| Production rejects synthetic demo adapter | PASS |
| Production rejects unverified postal opt-in | PASS |
| Default evidence verifier fails closed | PASS |

One existing Starlette/httpx deprecation warning remains. Tests cover both canonical PIN input and spaced-digit normalization. See [evaluator guide](assignment-demo.md), [runner](../scripts/demo_end_to_end.py), and [integration test](../tests/integration/test_complete_address_workflow.py).

## Offline application and database evidence

Progressive collection advanced v0→v4. Real normalization created v5; validation/readback used v5. The correction created v6, revoked validation/confirmation/readback eligibility, and required new validation/readback. Stale version/evidence returned VERSION_CONFLICT or EVIDENCE_BINDING_MISMATCH. Premature save returned ADDRESS_NOT_CONFIRMED.

Correctly bound **SYNTHETIC** completion evidence followed by **SYNTHETIC** confirmation allowed a normal committed save. Final current_version = validated_version = confirmed_version = 6. Duplicate save returned the same record with one final-address row.

Session-scoped PostgreSQL counts: 1 session, 6 versions, 2 validations, 2 readbacks, 2 confirmation events, 1 address, 15 audit events. Exact session/source IDs, digests, request IDs and audit timeline are in [offline evidence](testing/offline-e2e-evidence.json). conversation_outcome=null; test_result=PASS. This is not a live voice outcome.

## Previously proven live behavior

Real Bolna selection, typed HTTP dispatch, authentication, execution/session ownership and PostgreSQL version mutations passed. The corrected mapping run reached v5, the demo postal call v4, and the last PIN-controlled call v3. The live validation/readback objective failed because the stored PIN differed from the intended demo input; no successful final live save is claimed.

Historical evidence remains unchanged: [typed live run](typed-live-report.md), [demo postal run](demo-postal-report.md), [controlled PIN run](pin-controlled-report.md). The [pre-offline report](pre-offline-final-report.md) preserves earlier status and test counts as historical results.

## Security invariants

No domain, authorization, ownership, typed transport or production confirmation rule was weakened. Every mutation in the demo uses normal HTTP routes and credentials. SQL verification is read-only. Synthetic issuance is local-only and cannot be enabled by a request; production construction and injection are rejected. The default verifier still rejects all evidence. Existing transaction/idempotency guards remain in use. No live-call session was edited.

## Remaining production dependencies

- The supplied postal CSV is UNVERIFIED_OR_STALE; its official identity/release date are unknown. It is explicitly development/demo-only. Three malformed records were excluded under prior authorization without changing the original.
- Independent production evidence of completed playback and subsequent customer confirmation is unavailable. Synthetic evidence demonstrates the software gates, not customer consent.
- Bolna credits are exhausted. No additional calls were made; this external constraint is not an application defect.
- No official postal validation, successful final live save, audio playback proof or adjudicated production conversation quality is claimed.

The assignment is ready to demonstrate using the offline command in the evaluator guide. Production readiness remains blocked by the dependencies above.
