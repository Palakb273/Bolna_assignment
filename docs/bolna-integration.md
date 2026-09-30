# Bolna integration

Latest live verification: **LIVE_TOOL_PATH PASS**. The corrected typed mapping produced five HTTP 200 address updates and a PostgreSQL version 0→5 transition in one authorized call. Original agent restored; tunnel stopped. See [corrected-mapping live report](typed-live-report.md). Postal validation and confirmation remain blocked independently.

Latest diagnostic: the model selected update_address, but legacy string interpolation of changes_json caused a pre-HTTP JSON parsing failure. The generator now uses Bolna's typed $var markers. Local transport/database regression tests pass; the corrected mapping has not had a live call. See [root-cause report](live-tool-debug-report.md). Always inspect the raw execution /log endpoint: an empty tool_call_logs summary can hide preparation failures.

Existing agent is preserved. Read-only authenticated GET succeeded during implementation; one conversation task was found and no tools were attached at that check. Do not recreate the agent.

Official references checked: [custom function guide](https://www.bolna.ai/docs/tool-calling/custom-function-calls), [webhooks and custom headers](https://www.bolna.ai/docs/post-call/polling-call-status-webhooks), [v2 update](https://www.bolna.ai/docs/api-reference/agent/v2/update), [call scheduling](https://www.bolna.ai/docs/api-reference/calls/make).

`app/integrations/bolna.py` generates seven custom functions with a fixed session URL and per-session credential outside LLM parameters. It also generates a tools/tools_params merge for the existing agent configuration. Hosted update acceptance and GET visibility passed in the authorized development test. The 10-second call made no address updates, so runtime substitution and tool invocation remain unverified. The original hosted configuration was restored afterward. Generated definitions and backups contain credentials and belong only in ignored local-data/bolna.

Set BOLNA_AGENT_ID, BOLNA_API_KEY and the newly provisioned BOLNA_CALL_TOKEN in the process environment. Generate definitions:

```powershell
.venv\Scripts\python.exe scripts/configure_backend_tools.py --backend-url https://YOUR_BACKEND --session-id SESSION_UUID
```

The default writes definitions without remote changes. Use a fresh session/output and `--execute` to fetch/back up the existing agent, preserve voice configuration, merge tools/prompts and PUT the existing ID. No remote mutation is retried automatically. Check the hosted agent after an ambiguous timeout before retrying. The integration is intended for a reserved single-call development agent; do not reuse static per-session tool credentials for concurrent customers. Provision isolated per-call credentials through a verified Bolna per-call configuration path before multi-call production deployment.

Configure webhook URL /v1/webhooks/bolna and a separate `Authorization: Bearer <BOLNA_WEBHOOK_TOKEN>` header in Bolna's webhook header settings. Do not put secrets in URLs. The backend authenticates that shared header; it does not claim a Bolna cryptographic signature. Consider provider IP allowlisting at the gateway. Callback stores only IDs/status/time, not transcripts. Absent event IDs use SHA-256(execution + status), deliberately collapsing repeated reports of the same lifecycle status. Terminal states never regress. This cannot prove conversation success or consent.

Production evidence is not available merely because custom tools/webhooks work. A future independent adapter must attest exact audio completion and subsequent explicit approval for the exact session/execution/version/attempt/digest and ordered event sequence. Never wire LLM tool output, generic call completion, or an unverified transcript interpretation into that trust boundary. Current default rejects every evidence reference. There is no runtime synthetic mode.

Treat “yes, but flat 320” as correction: invalidate read-back, patch, validate, read the complete new text, and wait for fresh trusted evidence. Hindi rendering retains customer spelling and speaks PIN digits separately; actual Hindi/Hinglish audio quality needs a live recording review.
