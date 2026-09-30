# Address Collector Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible Bolna-hosted address collection prototype and verify its behavior through documented voice tests.

**Architecture:** Bolna runs telephony → STT → conversational LLM → TTS. A prompt maintains conceptual per-call address state; small local Python commands configure the agent and initiate individual test calls. No application backend or permanent address store.

**Tech Stack:** Hosted Bolna API, Python 3.11+ standard library, JSON configuration, Markdown documentation, unittest with mocked HTTP.

**Spec:** `docs/superpowers/specs/2026-09-29-address-collector-design.md` (approved).

**Execution status (2026-09-30):** User authorized proceeding; implemented directly in this chat. Tasks 1–3 local deliverables are written; 18 helper tests pass. Task 4 live verification is pending account setup and a consenting test recipient. Detailed evidence and deviations are in `docs/implementation-progress.md`. Checkboxes below retain the original plan; they are not a claim that unrun live tasks passed.

## Global Constraints

- Correctness, context retention, interruption handling, and explicit confirmation take priority over brevity or cost.
- Do not build a backend, database, persistent address store, lookup service, geocoder, dashboard, authentication service, retry scheduler, queue, or production deployment.
- No application-managed permanent address persistence.
- Use synthetic addresses and consenting development participants.
- Do not print credentials, full request headers, or raw responses containing customer information.
- Local dry-run checks must not place calls.
- Phase 2 recommendations must follow observed evidence. Do not begin Phase 2.
- Account credentials and live-test participation are external dependencies, not reasons to leave local deliverables unfinished.

## Review Focus

1. A timeout after call submission may mean a call already started: never automatically retry (Task 2).
2. Provider error bodies or redirect responses may expose secrets: sanitize errors and reject redirects (Task 2).
3. “Yes, but the flat is 320” invalidates confirmation: apply the correction and repeat the full read-back (Tasks 1 and 3).
4. PIN zeros, Devanagari numbers, and pauses can be lost in speech: use targeted clarification and verify on voice calls (Tasks 1, 3, and 4).
5. A flat number may legitimately not exist: accept a customer-supplied identifying description or classify the conversation_outcome as PARTIAL_ADDRESS without invention (Tasks 1 and 3).

## File map

- `prompts/address_collector.md`: complete prompt, including conceptual state and terminal outcomes.
- `config/agent.json`: documented hosted-agent configuration, no secrets or real customer data.
- `scripts/bolna_common.py`: environment validation, payload assembly, safe single-attempt HTTP.
- `scripts/configure_agent.py`: configuration validation/dry-run and explicit agent creation.
- `scripts/create_test_call.py`: validation/dry-run and explicit single-call submission.
- `tests/test_helpers.py`: meaningful network-free helper tests.
- `.env.example`, `.gitignore`: placeholder settings and exclusions.
- `README.md`: setup and operation instructions.
- `docs/bolna-configuration.md`: exact settings, sources, account verification status, retention settings.
- `docs/testing/scenarios.md`: scripts and expected behavior.
- `docs/testing/results.md`: individual scenario results, with all required report fields.
- `docs/testing/manual-calls.md`: 20 realistic call cases and review fields.
- `docs/testing/metrics.md`: numerator/denominator definitions and unmeasured initial status.
- `docs/phase1-report.md`: implementation findings, evidence, gaps, and exit recommendation.

## Task 1: Prompt and current hosted configuration

**Files:** `prompts/address_collector.md`, `config/agent.json`, `docs/bolna-configuration.md`.

**Interfaces:** Produces UTF-8 prompt text and a JSON object matching the current hosted create-agent request schema. The helper will insert the prompt at the documented system-prompt location. Keep provider/model/voice selections as editable JSON values.

- [ ] Read current official hosted create/get-agent, call, STT, TTS, LLM, interruption, silence, hangup, and retention documentation through `https://www.bolna.ai/docs/llms.txt`. Record source URLs and retrieval date. Do not use open-source or deprecated API payloads as hosted API contracts.
- [ ] Select a documented Hindi/English-capable STT and TTS voice, a capable LLM, and supported telephony defaults. Record exact model IDs, voice ID, languages, endpointing, interruption threshold, silence timings, and call duration. Mark account acceptance as unverified until a live request succeeds. If a voice ID is account-specific, require it through environment configuration rather than inventing it.
- [ ] Write the complete prompt from the approved spec, including all nine fields, language switching, missing-field policy, spelling, numerical uncertainty, correction precedence, full read-back, and explicit confirmation. Include short English/Hindi/Hinglish examples and all seven conceptual outcomes. Refusal, busy, human request, and silence must terminate without false claims of saved information or connected systems.
- [ ] Review against these concrete traces: complete first response skips field-by-field questioning; “yes, but flat 320” requires another full read-back; five-digit PIN requires repetition; “no house number” does not invent one; uncertain Hindi digit transcription requires clarification. These are prompt reviews, not recorded voice-test passes.
- [ ] Validate that JSON parses and contains only documented fields, no webhooks/persistence integrations, and no credentials. Note any silence or hangup behavior requiring runtime verification.

## Task 2: Safe minimal developer helpers

**Files:** `scripts/bolna_common.py`, `scripts/configure_agent.py`, `scripts/create_test_call.py`, `tests/test_helpers.py`, `.env.example`, `.gitignore`.

**Interfaces:**

- `required_env(name: str) -> str`: reject missing, blank, and example-placeholder values without echoing values.
- `build_agent_payload(config: dict, prompt: str) -> dict`: assemble the Task 1 schema without mutating the input configuration.
- `build_call_payload(agent_id: str, recipient: str) -> dict`: validate agent ID and E.164 recipient; return the documented call payload with no invented customer context.
- `post_json(path: str, payload: dict, api_key: str) -> dict`: fixed documented HTTPS API origin, explicit timeout, no redirects or automatic retries, sanitized failure messages. Raise `RuntimeError` for transport/API/response failures.
- Each command exposes `main(argv: list[str] | None = None) -> int`, defaults to validation only, and requires `--execute` to send. Call command requires `--to`; account settings come from environment variables. Print validated status or an allowlisted response identifier, never full bodies.

- [ ] Write failing unittest cases: missing key raises ValueError without its contents; invalid recipient raises ValueError; input configuration remains unchanged; assembled payload contains the prompt at the documented location; valid call payload matches the documented schema.
- [ ] Write failing mocked-network tests: default invocation sends zero requests; execute sends exactly one request; HTTP 401 produces a sanitized error without sentinel secret/body text; timeout sends once and warns that submission status is unknown; redirects are rejected; malformed JSON and missing success identifiers fail safely; newline-containing identifiers are not printed.
- [ ] Run `python -m unittest discover -s tests -v` and confirm failures are caused by missing implementation.
- [ ] Implement the signatures above with argparse, json, os, pathlib, and urllib. Use explicit UTF-8 reads and paths relative to the script location. Do not add dotenv dependencies: document environment setup and treat `.env.example` as a template, not automatically loaded configuration.
- [ ] Add placeholder environment values required by verified configuration. Ignore `.env`, environment variants except `.env.example`, Python caches, and local recording/transcript artifacts.
- [ ] Run `python -m unittest discover -s tests -v`; require all tests to pass. Run both commands in default validation mode and verify no account request or call occurs. Check execution errors return nonzero exit status.

## Task 3: Evaluation kit and usable documentation

**Files:** README, configuration documentation, all four `docs/testing/` files, `docs/phase1-report.md`.

**Interfaces:** Uses the exact commands and configuration from Tasks 1–2. Result records contain Test ID, Scenario, Expected Behavior, Actual Behavior, `conversation_outcome`, `test_result`, STT Errors, LLM Errors, TTS Issues, Interruption Issues, Conversation Issues, and Notes. `conversation_outcome` is one of the seven call outcomes in the spec, or `null` when unobserved. Independently, `test_result` is `NOT_RUN`, `PASS`, `FAIL`, or `PARTIAL`. `PARTIAL` requires an executed test with incomplete evaluation or only some criteria demonstrated, with missing evidence explained; a demonstrated violation is `FAIL`. Correct refusal can be `CUSTOMER_REFUSED` plus `PASS`; `PARTIAL_ADDRESS` does not imply `PARTIAL`.

- [ ] Write T01–T18 directly from the user's brief, preserving each distinct scenario and expected result. Add T19 human request, T20 unavailable essential information, T21 disconnect, T22 affirmative with correction, T23 Devanagari/spoken zeros, and T24 legitimate no-number address. Supply synthetic utterances, correction timing, and expected final fields/outcomes.
- [ ] Create a results entry for every scenario. Initially set Actual Behavior to “Not run”, `conversation_outcome` to `null`, and `test_result` to `NOT_RUN`. Do not classify prompt review or helper tests as voice passes or infer actual outcomes from expected outcomes.
- [ ] Create 20 distinct manual call cases covering the requested speaking styles and conditions. Include ground truth, observed final fields, separate `conversation_outcome` and `test_result` fields with the same initial values as scripted results, redundant questions, unsupported fields, interruption behavior, confirmation quality, and naturalness notes.
- [ ] Copy metric definitions from the spec, retaining numerator and denominator counts and N/A for zero denominators. Mark all live metrics unmeasured initially. Exclude `NOT_RUN` entries from measured denominators. Base conversation metrics on observed call evidence and outcomes, and test pass rates on `test_result`; never substitute one field for the other. Report incomplete evaluations separately.
- [ ] Write README with exact PowerShell setup and dry-run/execute commands, agent creation, ID reuse, provider replacement, authorized test recipient setup, account/telephony prerequisites, and recording/retention inspection. Do not encourage pasting keys into chat.
- [ ] Write the implementation report with A–H sections requested by the user, referencing the full prompt and exact configuration. Separate verified helper results, proposed runtime settings, and unverified call behavior. Include every excluded production feature in limitations.
- [ ] Cross-check that every scripted test has a result entry, there are at least 20 manual cases, all seven metrics are defined, and documented commands match actual help output. Verify both result fields appear independently in scripted records, manual records, and the final report; every unexecuted case must have `test_result: NOT_RUN` and `conversation_outcome: null`. Rerun helper tests only if code/configuration changed.

## Task 4: Hosted verification and live voice evaluation

**Files:** Update configuration, prompt, configuration notes, results, manual-call worksheet, metrics, and implementation report as evidence arrives.

**Interfaces:** Uses Task 2 execute commands, consenting recipients, account access, and Task 3 evaluation records. No automated bulk calling or simulated human-review results.

- [ ] Determine whether required account settings are available without printing their values. If absent, finish all local work and request local environment setup and a test recipient; report live validation as blocked by those specific dependencies.
- [ ] Confirm account provider availability, phone configuration, credits, recording/transcript retention, and a consenting participant. Create the agent, retrieve its configuration through the current documented API, and compare applied settings with the local payload. Record safe agent identifier and any account-imposed differences.
- [ ] Conduct the 24 scripted scenarios with the participant and capture actual behavior. Inspect real audio for interruption stop, names, numerical rendering, and silence timing. Do not infer these properties from transcripts alone.
- [ ] Adjust prompt/settings only in response to observed problems; record changes and rerun affected scenarios. Preserve earlier failed results and configuration versions in notes.
- [ ] Conduct and document at least 20 realistic review calls after scripted testing, with the requested range of speaking styles. Calculate metrics from actual counts.
- [ ] Assess every original exit criterion. Recommend completion only if demonstrated; otherwise list exact failures or missing evidence and the next required tests. Do not start Phase 2.

## Review and handoff

- [ ] Before claiming local completion, run the helper suite and verify delivered files and documented commands.
- [ ] Review for fabricated API identifiers, secret exposure, accidental calls, unsupported retention claims, and fabricated test outcomes.
- [ ] Commit coherent work only if a valid Git repository is available. The current folder has no visible `.git`; do not imply a commit was made or create unrelated repository infrastructure.
- [ ] Deliver links to README, prompt, configuration, test results, and implementation report. State precisely whether local artifacts, hosted agent creation, and live exit criteria are complete.

Plan self-review: each spec section maps to Tasks 1–4; all five review-focus cases have assigned verification. No live account access or voice results are assumed. User approved proceeding with the requested result-field modifications; direct execution selected as recommended.
