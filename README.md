# Address collection voice agent

## Assignment demo — current status

**Assignment implementation: COMPLETE. Production readiness: NOT READY.**

Run the complete deterministic demo (real FastAPI + PostgreSQL, simulated voice and clearly labelled synthetic evidence):

```powershell
.venv\Scripts\python.exe scripts/demo_end_to_end.py --verbose
```

No Bolna API calls, credits or tunnel are used. See [assignment demonstration and setup](docs/assignment-demo.md), [final report](docs/final-report.md), and [offline evidence](docs/testing/offline-e2e-evidence.json).

Verification: **197 tests + 26 subtests**, plus the separately run **18 original unittest checks** (already included in pytest). The offline flow demonstrates normalization, validation, correction, stale-evidence rejection, confirmation gates, committed save and idempotency. Final current/validated/confirmed version is 6.

Real Bolna authenticated tool dispatch and PostgreSQL candidate mutation were previously proven live. Successful validation/readback/confirmation/save here are offline results; evidence is SYNTHETIC and postal data UNVERIFIED_OR_STALE. Production's default verifier remains fail-closed, and production rejects the demo adapter and unverified postal opt-in.

The phase sections below are retained as historical documentation; their original counts, limitations and live status do not describe the current submission. Use the final report above for current status. Do not run further live-call commands: credits are exhausted and this submission requires no calls.

## Phase 2B — validation engine

The validation engine adds deterministic PIN conversion, required-field checks, conservative postal matching and raw-preserving normalization versions. A manual official-CSV importer and local directory are implemented. Synthetic checks pass; actual official-file ingestion remains unverified, so Phase 2B is not fully accepted. See the [Phase 2B report](docs/phase2b-report.md) and [postal data setup](docs/postal-data.md). No postal dataset or permissive fallback is bundled.

## Phase 2A — deterministic domain model

Phase 2A adds strict address schemas, immutable version history, validation-attempt binding, read-back and confirmation evidence checks, and independent save eligibility. It does not add an API, database, PIN dataset or live Bolna integration. [Phase 2A report](docs/phase2a-report.md) explains the implemented guarantees and remaining work.

From the project folder in PowerShell:

~~~powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e '.[dev]'
.venv\Scripts\python.exe -m pytest -q
~~~

The original Phase 1 unittest command below still works without these dependencies. Phase 2A has no server command and does not load .env.

The default evidence verifier rejects every reference. Synthetic evidence is available only in tests. A trusted future adapter must prove completed read-back and subsequent customer confirmation; an LLM-provided boolean, matching text digest, or authenticated tool call alone is insufficient. `record_saved` is a domain hook for a future committed database receipt; it writes nothing.

## Phase 1 prototype

A Bolna-hosted prototype for collecting and confirming Indian addresses in English, Hindi, and Hinglish. It handles corrections, missing details, number clarification, and full read-back through the prompt and uses Bolna's audio controls for interruption and silence.

**Status:** local prototype files and helper tests are available. No hosted agent or live voice behavior has been verified. Phase 1 is not complete.

## Scope and architecture

Customer phone → Bolna telephony → streaming STT → conversational LLM → streaming TTS → customer.

Address state is conceptual and held in conversation context. It is not a programmatic state store or guaranteed structured API output. Evaluation records separate conversation_outcome from test_result; unrun calls are NOT_RUN with null outcome.

There is no backend server, database, PIN geographical validation, permanent application persistence, maps/geocoding, CRM, authentication/dashboard, production retries, human transfer, or production analytics. Bolna may retain transcripts/audio: confirm account retention before live testing.

## Files

- [Shared system prompt](prompts/address_collector.md) and [Hindi guidance](prompts/address_collector.hi.md)
- [Agent configuration](config/agent.json) and [exact settings and sources](docs/bolna-configuration.md)
- [24 scripted scenarios](docs/testing/scenarios.md), [results](docs/testing/results.md), [20-call worksheet](docs/testing/manual-calls.md), [metrics](docs/testing/metrics.md)
- [Implementation report and remaining work](docs/phase1-report.md)

## Local checks

Requires Python 3.11 or newer; no external Python packages. From this folder in PowerShell:

~~~powershell
python -m unittest discover -s tests -v
python scripts/configure_agent.py
~~~

The second command validates the local configuration and prompt assembly only. It does not contact Bolna. Helpers work from other folders too when invoked with their absolute script paths.

## Account setup

Create/sign in to your [Bolna account](https://platform.bolna.ai), obtain an API key through its developer settings, and keep it local. Ensure the account has credits, the selected providers/voice, and a Plivo-compatible default outbound number. Do not paste keys into chat, commit them, or put them in frontend code.

For this PowerShell session, enter the key through a masked prompt:

~~~powershell
$bolnaSecret = Read-Host 'Bolna API key' -AsSecureString
$env:BOLNA_API_KEY = [System.Net.NetworkCredential]::new('', $bolnaSecret).Password
Remove-Variable bolnaSecret
~~~

[.env.example](.env.example) lists environment names with placeholders. Helpers do **not** automatically load .env files. .env files and local-data/ are ignored by Git if this folder is later made a repository.

Create one hosted agent only when ready:

~~~powershell
python scripts/configure_agent.py --execute
~~~

Save the returned ID in this session:

~~~powershell
$env:BOLNA_AGENT_ID = Read-Host 'Created Bolna agent ID'
~~~

Every configure --execute invocation creates a NEW agent. It does not update an existing one. Do not repeat after an uncertain response until checking the dashboard.

Open the new agent in Bolna and verify the applied settings against [configuration notes](docs/bolna-configuration.md), including English and Hindi language slots and both prompts. Inspect recording/transcript settings, minimize retention, and use synthetic test addresses. No recording-disabled claim has been verified for this account.

Initial selections: Sarvam saaras:v4 STT, OpenAI gpt-4.1, Sarvam bulbul:v3 Priya TTS, Plivo telephony. Speech recognition and voice are configured separately for en and hi. The prompt includes mixed-language behavior; actual Hinglish performance remains untested.

## Place one test call

Use a phone belonging to a consenting development tester. Set the recipient via a prompt so it is not embedded in a script:

~~~powershell
$testRecipient = Read-Host 'Consenting test phone number including + and country code'
python scripts/create_test_call.py --to $testRecipient
~~~

That is a dry-run: it validates inputs without a request. To make exactly one submission:

~~~powershell
python scripts/create_test_call.py --to $testRecipient --execute
~~~

The execution ID means submitted, not completed or address-confirmed. Inspect the call in Bolna's call history. Calls may cost credits. These helpers never retry automatically. On timeout, server failure, or missing identifier, check the account before manually trying again; the first request may already have succeeded.

Transport errors are deliberately summarized; raw provider bodies, headers, phone numbers, and credentials are not printed. Use the authenticated dashboard to investigate errors without publishing sensitive logs.

## Voice evaluation

1. Verify applied configuration and account data retention.
2. Run all 24 scripts, completing each [result record](docs/testing/results.md).
3. Listen for STT, TTS, timing and interruption errors; transcript inspection alone is insufficient.
4. Tune settings only from observed problems and rerun affected scenarios.
5. Conduct the 20 additional realistic calls in the worksheet.
6. Calculate metrics from observed counts and review every exit criterion.

Correct refusal can produce conversation_outcome=CUSTOMER_REFUSED and test_result=PASS. NOT_RUN is excluded from measured results. Never label a local helper test as a voice test.

## Known limitations

No external PIN validation, database, permanent application address storage, geocoding, retries, actual human transfer, or production analytics. Prompt-managed state can be wrong; there is no deterministic extraction/confirmation engine. Providers may retain data. Account compatibility, latency, one-check silence behavior, final-message interruption, numerals, spelling and multilingual switching require real calls. See the report for the current exit decision. Phase 2 must await review.

When finished, clear session values:

~~~powershell
Remove-Item Env:BOLNA_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:BOLNA_AGENT_ID -ErrorAction SilentlyContinue
Remove-Variable testRecipient -ErrorAction SilentlyContinue
~~~

