# Controlled PIN live retest — 2026-09-30

Exactly one call was submitted. No manual candidate changes or retry calls occurred. Only the temporary hosted prompt was hardened; application/domain code and typed transport were unchanged.

| Path | Result |
|---|---|
| LIVE_UPDATE_PATH | PASS |
| LIVE_PIN_CAPTURE | FAIL |
| LIVE_VALIDATION_PATH | FAIL |
| LIVE_READBACK_PATH | FAIL |
| LIVE_SPOKEN_READBACK | NOT_VERIFIED |
| LIVE_CONFIRMATION_PATH | BLOCKED |
| LIVE_SAVE_PATH | BLOCKED |

## Preflight
Full PostgreSQL-backed suite: 192 tests and 26 subtests passed (one existing deprecation warning). PostgreSQL healthy. Explicit demo directory loaded; 19 records for intended PIN; pure local validation VALID. Source remains UNVERIFIED_OR_STALE, development/demo only. No selected address/PIN was prefilled in the session or hosted prompt.

Original hosted configuration backed up privately. Temporary generic PIN-only confirmation instructions were inserted into the main and multilingual prompts. All supplied editable fields were GET-verified, allowing provider-added fields. Both public get_address_session probes returned HTTP 200; execution-bound session was COLLECTING at version 0 before scheduled start.

## Call and backend evidence
- Execution: da9c3c74-74a9-48ae-8c18-b56e3bb398fb
- Session: b50f8418-25ab-4e32-896b-2cbf83f59ab9
- Scheduled: 2026-09-30 10:50:14 UTC
- Final provider status: completed; duration: 300 seconds
- Intended PIN: 110001; final PostgreSQL candidate PIN: 201016
- current_version: 3; validated_version: null
- Final validation: NEEDS_CLARIFICATION / PINCODE_NOT_FOUND
- Readback attempt ID/digest: null; attempts: 0
- Trusted evidence: 0; saved addresses: 0
- conversation_outcome: null; test_result: FAIL

Raw execution logs show five update_address requests/responses and two validate_address requests/responses. Backend diagnostics independently record all seven with HTTP 200 and the correct authenticated execution/session binding. Three updates advanced versions; two later updates made no version change. No prepare_address_readback request appeared. No transport, authentication, ownership, schema rejection or backend failure was observed.

Version timeline (UTC, PostgreSQL audit):
- 10:48:13: session created, v0
- 10:48:14: execution bound, v0
- 10:51:41: update, v1
- 10:52:03: update, v2
- 10:52:24: update, v3
- 10:52:35 and 10:54:14: validation at v3, PINCODE_NOT_FOUND

## Failure attribution
The first incorrect PIN was already present in the transcriber response at 10:52:13 as 201016. The model sent 201016 in its next update. Thus the initial model extraction matched available STT text; the intended-input mismatch arose at or before transcription. Caller speech versus STT error remains UNKNOWN because audio was not independently reviewed.

A later transcriber response at 10:54:34 contains 301301; the subsequent update at 10:54:52 contains no PIN field, leaving 201016 stored. This establishes that the later transcribed digit sequence was not persisted, but its conversational meaning was not independently adjudicated. PIN-only confirmation compliance is not independently established. Prompt deployment alone does not prove compliance.

The failed validation target was the wrong captured PIN, not the locally verified intended input. This does not establish a postal-directory loading failure. No validated version existed, so the readback success criterion could not be met.

## Cleanup and limits
Original hosted configuration restored and GET-verified at 10:56:47 UTC. Tunnel process remained alive through terminal call status, was stopped, and absence verified. Local backend restored to production defaults (demo_runtime_ready=false); PostgreSQL retained. No second call placed.

Confirmation/save guards remain unchanged. No production readiness, official postal validation, or end-to-end success claimed.

Safe request IDs, raw tool diagnostics and PIN-only evidence: [pin-controlled-evidence.json](testing/pin-controlled-evidence.json). Full transcripts, addresses, credentials and private configuration snapshots are excluded.
