# Corrected Bolna mapping: single-call verification

**LIVE_TOOL_PATH = PASS.** Five actual Bolna-origin update_address requests returned HTTP 200 and advanced the bound PostgreSQL session from version 0 to 5. Exactly one call was submitted; no manual candidate mutation or call retry occurred. Date: 2026-09-30.

## A. Pre-call verification

- Full PostgreSQL-backed suite: 181 tests +26 subtests PASS; one existing Starlette/httpx deprecation warning.
- User-specified realistic nested JSON passed typed substitution, final JSON serialization and backend schema validation without losing fields.
- Original hosted configuration backed up privately. Temporary corrected configuration GET matched every supplied editable field, including names, URLs, credentials, schemas, prompts and typed variable mappings; provider-added fields allowed.
- Public tunnel connected at 05:28:50 UTC. Exact bound-session get_address_session returned 200 at 05:29:21.819 UTC: COLLECTING/version 0, execution bound server-side. Bound preflight request ID: `da339e1f-82f1-4c5a-a355-baac8629e07d`.
- Bolna assigns execution ID on call submission, so the call was scheduled two minutes ahead and bound/checked before its scheduled start. No ownership changes were made during the conversation.

## B. Call metadata

| Field | Value |
|---|---|
| Execution ID | b5a143b4-6d55-4915-8b69-06b5844db49b |
| Session ID | 2a2377e6-8f91-4170-b2f6-4781ff203f49 |
| Scheduled start | 05:31:21 UTC / 11:01:21 IST |
| Final provider status | completed |
| Duration | 268 seconds |
| Hangup reason | end_call_tool |
| conversation_outcome | null; not independently adjudicated |

## C. Raw Bolna tool evidence

The raw /executions/{id}/log endpoint recorded five custom_task_update_address request/response pairs with returned versions 1–5, two validate_address attempts, one prepare_address_readback, one request_address_confirmation, and one provider end_call. No JSON-construction error recurred. The summary tool_call_logs field was empty, so it was not used to determine success.

## D. Backend request evidence

Every row below has the exact session and authenticated execution binding listed above. Preflight requests were nonmutating and are excluded.

| Tool | HTTP | Reason / result | Request ID |
|---|---|---|---|
| update_address | 200 | version 1 | 261c340a-c374-4c50-a2dc-1ab621c3cf0a |
| update_address | 200 | version 2 | 15fc7db2-9467-4edf-85c1-6511a471fa25 |
| update_address | 200 | version 3 | a9e76c67-3579-4032-92fd-08bdec94b580 |
| update_address | 200 | version 4 | 80c7e131-195c-4a8d-83e4-dd3a1ed42b64 |
| validate_address | 503 | POSTAL_DATA_UNAVAILABLE | be05d98c-77a9-4711-b605-15fb547e5f94 |
| update_address | 200 | version 5 | 484ee72b-ab6e-4818-9155-29642f208794 |
| validate_address | 503 | POSTAL_DATA_UNAVAILABLE | d05910e9-c73b-4d17-987e-ab404d0cd710 |
| prepare_address_readback | 409 | ADDRESS_NOT_VALIDATED | e6919d0b-7db8-4ab8-8bd2-f0b9e97357c2 |
| request_address_confirmation | 200 | Waiting only; no confirmation recorded | 21057b40-60fa-4d22-9f12-d5cd6b68a947 |

For the two 503 responses, request middleware logged the generic BACKEND_UNAVAILABLE label; the same request IDs' domain audit events and session response identify the specific cause as POSTAL_DATA_UNAVAILABLE. These are validation-dependency failures, not authentication, ownership, payload, version-conflict or database failures.

## E. Session version timeline

Times below are provider raw response timestamps, except the bound preflight.

| UTC | Version | Observation |
|---|---|---|
| 05:29:21.819 | 0 | Bound preflight, COLLECTING |
| 05:31:45.878 | 1 | First update returned |
| 05:32:05.867 | 2 | Second update returned |
| 05:32:17.503 | 3 | Third update returned |
| 05:34:14.552 | 4 | Fourth update returned |
| 05:34:49.744 | 5 | Fifth update returned |
| 05:36:39.792 | 5 | Final read-only session poll, VALIDATION_ERROR |

An independent read-only PostgreSQL query confirmed current_version=5, five stored address-version rows and the exact execution binding. validated_version and confirmed_version remained null.

## F. LIVE_TOOL_PATH result

**PASS**, limited to real tool dispatch and committed candidate mutation. Both raw provider responses and backend request/audit evidence establish the 0→1 transition. No production confirmation or final saved-address success is claimed.

## G. Failure cause

No failure of the requested mutation criterion. The corrected typed mapping eliminated the observed legacy JSON interpolation failure. Later validation was blocked by missing official postal data; read-back correctly rejected an unvalidated address.

## H. Restoration verification

Original agent restored after call completion. A fresh GET matched every saved supplied editable field and prompt, allowing provider defaults. The temporary tunnel was then stopped and process absence verified. No second call was placed. The corrected definitions remain in the local generator, not deployed over the restored original agent.

## I. Remaining blockers

Verified official postal data and trustworthy independent playback/confirmation evidence are still unavailable. Neither was bypassed. The agent attempted downstream read-back despite validation failure; the backend rejected it. Overall conversation quality was not adjudicated and conversation_outcome remains null.

[Redacted machine-readable evidence](testing/typed-live-evidence.json) contains raw-tool summaries, every scoped backend request/audit entry, safe session polls and the PostgreSQL check. It excludes addresses, transcripts, credentials and tokens.
