# Phase 1: Bolna address collection voice prototype

Status: approved by the user on 2026-09-30. Implementation has not started.

## Purpose and scope

Demonstrate that a Bolna-hosted voice agent can naturally collect and confirm an Indian address in English, Hindi, and Hinglish. Correctness, context retention, interruption handling, and explicit confirmation take priority over brevity or cost. The supplied Phase 1 brief is the acceptance contract.

Build one hosted agent, a versioned prompt and configuration, minimal Python developer scripts, and evaluation documents. Do not build a backend, database, persistent address store, lookup service, geocoder, dashboard, authentication service, retry scheduler, queue, or production deployment.

## Architecture

Customer phone → Bolna telephony → streaming STT → conversational LLM → streaming TTS → customer.

Bolna manages the live audio pipeline. Local scripts configure the agent and initiate developer test calls; they are not a running backend. The prompt maintains conceptual address state within the call's conversation context. This is not a deterministic application state store or a guaranteed structured extraction API.

Prefer hosted Bolna over dashboard-only manual configuration because versioned configuration is reproducible. Avoid self-hosting because it adds infrastructure outside Phase 1.

## Conversation contract

Open with: “Hi, I'm calling to confirm your address. Is now a good time?” Accept address details volunteered immediately without repeating the availability question or discarding fields.

Conceptually track house_flat, building, street, area, landmark, city, district, state, and pincode. Track unresolved ambiguity and whether the latest full address has been read back and explicitly confirmed. Never speak internal JSON or outcome codes to the customer.

For ordinary urban addresses, seek a house/flat identifier, locality, city, and six-digit PIN. Ask one short question at a time, or two closely related fields. Building, street, landmark, state, and district are contextual; do not mechanically require them. If no house number exists, clarify an alternative identifying description without inventing a number. If essential information remains unavailable, end with a partial outcome rather than claiming success.

Extract all volunteered fields. Preserve exact names unless the customer supplies a correction. Do not infer state, locality, landmarks, or PIN from geographical knowledge. Retain unaffected fields when one value changes. An ambiguous correction requires a targeted clarification.

Mirror the customer's language and allow switching. Normalize spoken numbers only when clear. Preserve meaningful flat prefixes and separators. Ask for digit-by-digit repetition for uncertain numbers; accept PIN format only as exactly six digits, without geographical validation. Ask for repetition or spelling of difficult names when needed.

Read every collected field back, including optional fields supplied by the customer. Speak PIN digits separately. A clear affirmative after a completed full read-back confirms the current address. Hesitation, partial acknowledgments, and agreement to an earlier clarification do not establish final confirmation. Any correction invalidates prior confirmation and requires another full read-back and fresh explicit approval.

Barge-in must interrupt audio playback, not merely be requested in the prompt. Listen to the interruption, apply corrections, and resume with the corrected state. Verify that stale queued speech does not continue.

Busy → CALLBACK_REQUIRED; refusal → CUSTOMER_REFUSED; explicit human request → NEEDS_HUMAN_REVIEW. End politely without promising an actual callback, saved record, or transfer. Prolonged silence permits one check followed by polite termination. Distinguish incomplete collection, transport disconnection, and agent failure as PARTIAL_ADDRESS, CALL_DROPPED, and AGENT_ERROR in evaluation. Successful conversational confirmation is ADDRESS_CONFIRMED. These are conceptual evaluation outcomes, not a persistence system.

## Provider and runtime configuration

Select a currently supported multilingual STT suitable for Indian English/Hindi, a capable instruction-following LLM, and a natural English/Hindi TTS voice. Verify current hosted API documentation and account availability before fixing exact provider/model/voice identifiers. Do not copy deprecated v1 examples into an assumed v2 payload.

Keep STT, LLM, TTS, language, telephony, endpointing, interruption sensitivity, silence timing, and maximum call duration configurable. Record exact initial values and any tuning changes in the implementation documentation. Prefer the account's easiest available development phone setup.

Tune endpointing for digit sequences and natural pauses. Enable interruption and test short corrections such as “No.” Configure one silence check and bounded termination using supported runtime controls. Document any behavior the runtime cannot guarantee instead of implying the prompt alone enforces it.

## Files and responsibilities

- README.md: setup, architecture, selected providers, commands, testing, limitations, and data handling.
- prompts/address_collector.md: complete final system prompt.
- config/: versioned hosted-agent configuration with no credentials or real customer data.
- scripts/: minimal agent configuration and test-call helpers, using environment variables and explicit target phone input.
- .env.example and .gitignore: placeholder settings and secret exclusions.
- tests/: focused automated checks for helper request construction, configuration validation, error handling, and secret-safe output.
- docs/testing/: at least 18 scripted scenarios, a 20-call manual worksheet, metric definitions, and results.
- docs/phase1-report.md: implementation/configuration references, verified results, problems, changes, risks, and exit recommendation.

Use Python standard-library functionality where sufficient. Helpers must validate required settings, handle API errors and timeouts, avoid automatically retrying a call-creation request that might already have succeeded, and print only safe identifiers/status. Do not print credentials, full request headers, or raw responses containing customer information. Local dry-run checks must not place calls.

## Data handling

No application-managed permanent address persistence. Use synthetic addresses and consenting development participants. Do not commit secrets, real phone numbers, recordings, transcripts, or real addresses. Confirm Bolna/provider recording and transcript retention settings before live tests; hosted retention is separate from the absence of a local database. Record the actual settings and limitations, without claiming zero retention unless verified.

## Validation

Automated checks establish that helpers behave correctly; they do not prove speech quality or real conversation success.

Run all 18 supplied scenarios: happy path, gradual collection, complete first response, missing PIN, five-digit PIN, spoken PIN digits, flat-number variation, correction, interruption, Hinglish, language switching, difficult name, busy customer, refusal, silence, correction during confirmation, frustration, and uncertain confirmation. Add human request, unresolvable missing information, and disconnection coverage.

Each result includes ID, scenario, expected and actual behavior, conversation_outcome, test_result, STT errors, LLM errors, TTS issues, interruption issues, conversation issues, and notes.

Keep these two fields independent:

- `conversation_outcome`: what happened in the call. Allowed values are `ADDRESS_CONFIRMED`, `CUSTOMER_REFUSED`, `CALLBACK_REQUIRED`, `PARTIAL_ADDRESS`, `CALL_DROPPED`, and `NEEDS_HUMAN_REVIEW`, plus `AGENT_ERROR`. Use `null` when no outcome has been observed, including before execution; do not invent an outcome from the expected behavior.
- `test_result`: whether observed behavior met the scenario's expectations. Allowed values are `NOT_RUN`, `PASS`, `FAIL`, and `PARTIAL`. Initially use `NOT_RUN` and Actual Behavior “Not run.” Use `PARTIAL` only after execution when evaluation is incomplete or only some criteria have been demonstrated; explain the missing evidence. A demonstrated violation is `FAIL`.

For example, a correctly handled refusal has `conversation_outcome: CUSTOMER_REFUSED` and `test_result: PASS`. An address confirmed without the required full read-back may have `conversation_outcome: ADDRESS_CONFIRMED` but `test_result: FAIL`. A partial address is a conversation outcome, not automatically a partial test result. Apply this separation to scripted results, manual-call records, metrics, and the final report.

After scripted testing, run at least 20 realistic voice calls across fast/slow English, Hindi, Hinglish, regional accents, noise, speakerphone, short/long interruptions, corrections, difficult names, and complex flat numbers. Use a synthetic expected address as ground truth and record outcomes without unnecessary personal data.

Measure field accuracy (correct supplied fields / supplied fields), PIN accuracy (correct final PIN / calls supplying PIN), correction success (correct applied corrections / correction attempts), interruption success (playback stops and interruption handled / interruption attempts), redundant questions (questions asking known information / collection questions), hallucinations (unsupported introduced fields / introduced fields), and confirmation completion (explicit valid confirmations / eligible cooperative calls). Mark zero denominators as not applicable; report counts alongside percentages. Record observed interruption delay where measurable.

## Completion and dependencies

Local artifacts can be completed without live account access. A working hosted agent requires an available Bolna account/API key, compatible providers/voice, sufficient account access/credits, configured telephony, and an authorized test recipient. Keys must be supplied through local environment configuration, not chat.

Phase 1 remains incomplete until real voice calling and every exit criterion in the brief have been demonstrated, with results for all scenarios and at least 20 realistic review calls. Do not manufacture results, claim deployment from a configuration file, or substitute automated helper tests for call evidence.

Phase 2 recommendations must follow observed evidence. Do not begin Phase 2.
