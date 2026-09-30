# Demo postal integration report

## A. Uploaded CSV inspection

The original `C:\Users\palak\Downloads\pincodes.csv` was not modified. Its SHA-256 was rechecked after the call.

| Item | Observed result |
|---|---|
| Exact headers | PostOfficeName, Pincode, DistrictsName, City, State |
| Decoding | Strict UTF-8 with optional BOM |
| Rows read | 39,736 |
| Accepted | 39,733 |
| Rejected | 3, explicitly authorized demo-only exclusion |
| Unique accepted PINs | 23,915 |
| Malformed PIN | 1 row |
| Missing PIN / state / district / office | 2 rows for each reason; reasons overlap on the same two rows |
| Source kind | UNVERIFIED_OR_STALE |
| Import timestamp | 2026-09-30T07:59:00.468113Z |
| Official URL / ID / release date | null / null / null |
| trusted_runtime_ready | false |
| demo_runtime_ready | true during explicit demo mode |

Original SHA-256: `2b9fce4ed50cb98f1fde663970c378479c8569dea1ca2c816e37c56ef5bdd74e`.

Normalized records SHA-256: `4840bc2fb0ec65278d9076c376a480db32a12a578e3f0de5df677214698a86da`.

## B. Code changes

- Settings default ALLOW_UNVERIFIED_POSTAL_DATA=false. Explicit development/test modes may enable it; production startup rejects it. No API/tool input can change settings.
- Exact five-header demo importer preserves multiple offices/districts per PIN, optional City and original file bytes. Strict rejection remains default; the approved exclusion is explicit and counted.
- Provenance can honestly represent unknown official metadata for UNVERIFIED artifacts. No official freshness is fabricated. Existing official metadata requirements remain enforced.
- Runtime selector separates trusted and demo readiness. The demo directory permits validation without official freshness only in the explicit demo mode; production health remains false.
- Deterministic validation, normalization versioning, correction invalidation, evidence verification and save eligibility are unchanged. Tests exercise demo validation/readback and continued rejection of untrusted confirmation/save.

## C. Local verification

- Full pytest with real PostgreSQL: **192 passed +26 subtests**, latest run 5.98 seconds; one existing Starlette/httpx warning.
- Original unittest suite: **18 passed**.
- Actual importer run: **PASS**, with the counts and hashes above.
- Selected uploaded-data address mechanically validates as VALID locally, retaining UNVERIFIED_OR_STALE provenance and null release date.
- Initial full-suite failures were database connection timeouts because Docker was stopped. The existing service was restarted. A generated local runtime password exposed in a verbose failed-test traceback was rotated privately; Bolna credentials and the original .env were unchanged.

## D. Selected demo address

Selected CSV entry: Connaught Place, New Delhi, Delhi, PIN **110001**. Premise B-302 was synthetic. No building or private residence was asserted to exist. These fields are demo inputs from unverified data, not current official postal truth. Private selected-field note: `local-data/bolna/demo-postal/selected-demo-fields.json`.

The captured PIN in the live session **did not match** the selected demo PIN and **was absent** from the imported directory. The selected PIN itself is present and passed the local mechanical validation. We have not adjudicated whether the mismatch arose from caller speech, transcription or model extraction.

## E. Live call evidence

Exactly one call was placed. No manual session mutation or call retry occurred.

- Execution: `41a3009a-7ee3-4382-b0a8-260aedea96a9`.
- Session: `c74f6578-da85-4213-b37a-f6fcee8d05f0`.
- Scheduled: 2026-09-30 08:05:48 UTC / 13:35:48 IST.
- Provider final status: completed; duration **198 seconds**.
- Hosted tools/prompts were GET-verified before and during the call. The exact bound session passed public preflight at COLLECTING/version 0.

| Raw response time (UTC) | Tool | HTTP | Result / request ID |
|---|---|---|---|
| 08:06:14.214689 | update_address | 200 | v1; dcafd36b-e133-4d7c-8cb5-907a2bffe70a |
| 08:06:26.792160 | update_address | 200 | v2; 2cf26d71-4833-4fee-be41-8549e5a2b3b4 |
| 08:06:38.551243 | update_address | 200 | v3; fab97190-5902-4cb4-85b5-2618b0d2797c |
| 08:07:58.225275 | update_address | 200 | v4; 4a53396c-aaf8-4add-a04c-3b280782cd0a |
| 08:07:59.973550 | validate_address | 200 | NEEDS_CLARIFICATION / PINCODE_NOT_FOUND; ef14ff67-8779-4998-acef-affb7ccaf2f8 |
| 08:08:36.064917 | prepare_address_readback | 409 | ADDRESS_NOT_VALIDATED; 3be9d6b9-003a-49f8-820f-5925f0f6342b |

Raw execution logs were inspected, not just the empty summary tool_call_logs field. Final PostgreSQL state: current_version=4, validated_version=null, confirmed_version=null, status=NEEDS_CLARIFICATION, readback_attempt_id=null, readback attempts=0, trusted evidence=0, final saved addresses=0. conversation_outcome remains null.

## F. Path results

| Path | Result | Reason |
|---|---|---|
| LIVE_UPDATE_PATH | PASS | Four real HTTP 200 mutations, version 0→4 |
| LIVE_VALIDATION_PATH | FAIL | HTTP 200 carried a clarification result, not VALID; no validated version |
| LIVE_READBACK_PATH | FAIL | HTTP 409; no attempt created |
| LIVE_SPOKEN_READBACK | NOT_VERIFIED | No generated validated readback exists for comparison |
| LIVE_CONFIRMATION_PATH | BLOCKED | No independently trustworthy evidence; verifier unchanged |
| LIVE_SAVE_PATH | BLOCKED | No validated/confirmed eligible address; no final save |

The local development integration is implemented and tested. This single live call did **not** prove the requested validation/readback sequence because of the captured PIN mismatch. No second call was placed.

## G. Trust statement

The uploaded pincodes.csv was used only as **UNVERIFIED_OR_STALE development/demo postal data**. It is **NOT** accepted as authoritative current Department of Posts data. Production readiness remains false without verified official postal provenance/freshness and trustworthy confirmation evidence. No confirmation or save bypass was introduced.

## H. Restoration

Original Bolna configuration restored and GET-verified against all saved supplied editable fields/prompts. Tunnel stopped and process absence verified. The local backend was restarted with production defaults and the unverified flag disabled after the demo.

Cleanup was delayed by an automatic approval-review usage-limit failure. After the user's continuation, the provider status was fetched directly (the temporary tunnel URL had expired), then restoration and tunnel shutdown succeeded. Nothing remains blocked by that review failure.

Demo reproduction instructions are in [postal data setup](postal-data.md). Do not rerun a call without fresh authorization. [Redacted evidence](testing/demo-postal-evidence.json) includes import provenance, provider tool summaries, backend request/audit records, final session metadata and restoration status; it excludes full addresses, transcripts and credentials.
