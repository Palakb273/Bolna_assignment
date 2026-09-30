# Phase 1 implementation report

Date: 2026-09-30. Recommendation: **NOT COMPLETE — live validation pending**.

## A. What was built

Local Bolna agent configuration, a complete shared conversation prompt plus Hindi guidance, and minimal Python configuration/test-call helpers. Commands validate locally by default and require --execute for remote side effects. They make one submission, block redirects, sanitize failures, and print only returned UUID identifiers. No backend or address persistence service was built.

No hosted agent has been created in this session. The available environment has no Bolna credentials and no authorized recipient was supplied.

## B. Exact Bolna configuration

[Configuration notes](bolna-configuration.md) document STT, LLM, TTS, telephony, language slots, interruption, endpointing, silence, final-message handling, and source references. [agent.json](../config/agent.json) is the full machine-readable candidate. All hosted acceptance and applied settings remain unverified.

## C. Final agent prompt

Complete source: [address_collector.md](../prompts/address_collector.md). The Hindi slot adds [address_collector.hi.md](../prompts/address_collector.hi.md) after the same shared policy. Neither prompt has been tuned using real calls.

Rules cover all nine fields, multiple details per turn, non-invention, targeted questions, uncertain digits/names, latest-correction precedence, interrupted read-backs, explicit new confirmation, and polite exits.

## D. Testing results

Local automated checks: **18 PASS**, using Python 3.11.3 and unittest, with only the external HTTP boundary mocked. This checks request construction, prompt injection, input validation, no-call dry-runs, single submission, timeout behavior, redirection prevention, response parsing, and safe output. The initial run failed because the helper module was not yet implemented; the completed suite passed.

Real scripted calls: **24 NOT_RUN**, including all original 18. Every individual result and required error category appears in [results.md](testing/results.md). Additional realistic voice reviews: **20 NOT_RUN**, in [manual-calls.md](testing/manual-calls.md). All observed conversation_outcome values remain null. No live accuracy metric is available.

Local default configuration validation succeeds. Voice quality, address extraction, barge-in, language switching, and end-call behavior are not proven by these checks.

Independent review reran all 18 helper tests successfully and found no Critical/Important code defects. Two manual-test ambiguities were corrected: M16 now specifies B-302 and 500032; M20 requires a clean confirmation before interrupting the audible goodbye with a flat correction. No live result changed.

## E. Problems found

- Current Bolna pages disagree on Sarvam endpointing behavior. Its effect needs live verification.
- Public controls do not establish exactly one silence check. T15 must test the candidate 12s/20s timing.
- Hosted transcription/recording retention is distinct from application persistence and remains unknown for this account.
- No account credentials, default-number verification, participant, or call evidence is available.

These are documentation/setup limitations, not observed STT/TTS defects. No apartment-name, PIN-zero, or voice-pronunciation failure is claimed without a call.

## F. Changes made

Incorporated the user's two changes: NOT_RUN for unexecuted tests, and independent conversation_outcome/test_result fields throughout evaluation. Added native Hindi guidance and explicit per-language API configuration, retained shared correction policy across slots, and distinguished affirmative-with-correction from valid confirmation.

Selected documented current Sarvam models/voice. Added one-word interruption sensitivity, prompt-based termination, a neutral bilingual final message, and interruptible goodbye as candidate settings. No live tuning has occurred.

## G. Remaining risks and evidence needed

All voice exit criteria remain unverified: a real call, progressive collection, retention, natural questioning, interruption, corrections, numbers, English/Hindi/Hinglish, ambiguity handling, full read-back, explicit approval, refusal/busy/silence exits, and zero invented fields. Security files and synthetic fixtures are present; account credentials/retention access still require verification.

The conversation context is conceptual state, not a guaranteed structured output. A provider's completed call status cannot establish confirmed address. Account model availability and telephony must be checked. Speech overlap and silence require audible evidence.

No database, geographical PIN validation, maps/geocoding, production retry logic, actual human transfer, or production analytics are included.

## H. Recommendation and next action

Finish Bolna account setup locally, verify the deployed configuration and retention settings, then run the scripted scenarios and 20-call review with consenting testers. Fill in observed outcomes and independent test results, calculate metrics, and review failures before accepting Phase 1.

Phase 2 recommendations are provisional: investigate deterministic state/confirmation and geographical validation only after voice findings identify the actual needs. Do not start Phase 2 now.

## Implementation decisions

Work remains in the supplied project folder without Git commits: no repository metadata is present and Git inspection is unavailable in this environment. Hindi guidance is appended to the shared policy rather than maintained as a divergent second rule set. Endpointing and silence settings are marked unverified because documentation cannot substitute for audio evidence. These decisions and their costs are recorded in [execution ledger](implementation-progress.md).
