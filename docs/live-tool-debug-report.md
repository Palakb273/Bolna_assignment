# Live Bolna tool-path investigation

**Root cause:** the diagnostic call selected `update_address` four times, but our legacy parameter template broke JSON serialization inside Bolna before HTTP dispatch. This is a payload-template defect, not a tool-selection failure. **Live test: FAIL** (version stayed 0). **Local fix: PASS** (181 tests +26 subtests). **Corrected live retest: NOT_RUN**; the one-call limit was respected.

## Root cause of the earlier 10-second call

Bolna execution `dcab69b3-4f1c-4bf1-b7f8-f05bf952c7ee` contains this non-address exchange: the assistant asked whether it was a good time, the caller answered “No,” and the assistant replied “No problem. Thank you.” The execution has zero tool_call_logs; telephony reports hangup_reason=end_call_tool and provider code 4010. There were no address facts for update_address to record. Ending the call respected the caller's availability response; this was not evidence of an HTTP failure.

The prior run verified hosted tool presence before scheduling, but did not retain an at-start snapshot. Its backend logging skipped early authorization failures. Therefore historical logs alone cannot prove all ten transport/configuration conditions retrospectively.

## Narrow changes

- Removed known English prototype statements denying backend/validation connectivity from the deployed prompt merge; preserved the saved original configuration.
- Made the collection instruction explicit: invoke update_address immediately after any supplied component, before asking another question. Listed all nine allowed changes_json keys and explained initial version 0. No test address is prefilled.
- Added request diagnostics for successful and rejected requests, limited to request ID, allowlisted tool name, HTTP status, UUID session ID, authenticated execution ID and error reason. Request bodies and credentials are excluded.
- Added exact supplied-field configuration checks, public nonmutating tool preflight, private snapshots, status evidence and verified restoration to the existing demo helper. Bolna-added default fields are allowed; supplied URLs, credentials, schemas and prompts must match.

Final verification: 181 tests and 26 subtests passed with real PostgreSQL, including early-rejection logging, prompt conflict, escaped JSON transport and a generated-payload-to-PostgreSQL version-1 transition. No architecture was added. One existing Starlette/httpx deprecation warning remains.

## Single diagnostic call

Execution: `c9d6e072-63f2-4797-97c8-468c7fdf35e6`.
Session: `a39f0eda-92c0-4846-9823-20efb689f730`.
Scheduled: 2026-09-30 05:14:32 UTC (10:44:32 IST).

One preflight-only run stopped before call creation because strict equality rejected provider-added defaults. Its original configuration was restored before the successful scheduling attempt. Exactly one call was submitted for this investigation.

Before scheduling, the deployed get_address_session URL and Authorization value returned HTTP 200 at version 0. That probe was nonmutating. Execution ownership was bound before the scheduled start. Model parameters contain neither session nor execution identity: session comes from the fixed URL and per-session bearer token; execution is bound server-side. An execution ID in each tool body is not required by this API.

The call completed after 118 seconds and was ended by the callee. Address speech was captured, but the session remained COLLECTING at version 0. No manual mutation was made to this call session. conversation_outcome remains null (not independently adjudicated); test_result is FAIL against the live mutation criterion.

## Exact failure evidence

The execution summary's tool_call_logs was empty. However, the separate [raw execution logs API](https://www.bolna.ai/docs/api-reference/executions/get_execution_raw_logs) returned four function responses named `custom_task_update_address`, at 05:15:02.738320, 05:15:14.318871, 05:15:24.675097 and 05:16:13.335181 UTC. All report:

`Expecting ',' delimiter: line 1 column 65 (char 64)`

The old mapping inserted `%(changes_json)s` inside serialized JSON without escaping the inner quotes. A synthetic local reproduction produced the identical error position. Bolna's [public request-construction source](https://github.com/bolna-ai/bolna/blob/master/bolna/helpers/function_calling_helpers.py) confirms this interpolation order. No HTTP response code exists for these attempts because construction failed first.

The generator now uses typed `{"$var":"changes_json"}` substitution, also for version/language, preserving values until JSON encoding. This path exists in the inspected public Bolna source. Hosted runtime compatibility of this correction remains unverified without another authorized call. The backend API and ownership design are unchanged.

## Ten checks

| Check | Evidence and conclusion |
|---|---|
| 1. Deployed tools | Pre-call snapshot contains all seven; in-progress checks at 05:14:51, 05:15:31 and 05:16:12 match every supplied tool/prompt field, as does final pre-restore check. |
| 2. Names/schemas | update_address appears in schema and prompt; raw logs resolve it as custom_task_update_address. The transport template failed. |
| 3. Public reachability | Deployed URL/header preflight returned 200; public session checks returned 200 throughout. Bolna-origin HTTP reachability cannot be directly proven because parsing failed before dispatch. |
| 4. Tunnel lifetime | Connected at 05:10:48; remained running through final 05:17:47 check, with no disconnect/error in its log; stopped afterward. |
| 5. Authentication | Hosted api_token matched expected Bearer value; preflight succeeded. No live auth rejection. |
| 6. Ownership | Fixed session URL/token matched the execution bound before start. Per-request execution ID is not required by this API. No live ownership rejection. |
| 7. Prompt trigger | Immediate-update instruction verified; four function attempts prove selection. |
| 8. Parameters | Version 0 is specified; all allowed address keys named. changes_json reached interpolation, where nested quotes broke JSON. |
| 9. Backend logs | No live update_address request or rejection arrived. Only our nonmutating preflight/status requests appear for this session. |
| 10. Provider logs | Four selected function attempts failed before HTTP. Empty summary tool_call_logs did not mean no selection. |

Original agent restoration was verified against all saved editable fields and prompts. The tunnel was stopped. No second diagnostic call was placed, and the corrected mapping was not left deployed.

Redacted evidence: [provider diagnostics](testing/live-tool-diagnostics.json). Private configuration snapshots, timestamped checks and logs remain in ignored local-data/bolna/debug-call and debug-one-call. Do not share configuration snapshots wholesale: they contain tokens.
