# Scripted test results

As of 2026-09-30: 24 NOT_RUN, 0 PASS, 0 FAIL, 0 PARTIAL. No real voice calls have been made. Automated helper checks are reported separately in the implementation report.

`conversation_outcome` records observed call disposition or null when unknown. `test_result` records NOT_RUN/PASS/FAIL/PARTIAL against expected behavior. A correctly handled refusal is CUSTOMER_REFUSED + PASS. PARTIAL_ADDRESS does not imply PARTIAL. Use FAIL for demonstrated violations; PARTIAL only for an executed case with incomplete evaluation, with missing evidence explained. No measured metric includes NOT_RUN entries.


## T01 — Simple happy path

| Field | Value |
|---|---|
| Test ID | T01 |
| Scenario | Simple happy path |
| Expected Behavior | No redundant questions; read every supplied field, PIN digit by digit, obtain explicit confirmation. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T02 — Gradual information

| Field | Value |
|---|---|
| Test ID | T02 |
| Scenario | Gradual information |
| Expected Behavior | Remember previous fields, ask only missing information; opening yes must not trigger success. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T03 — Everything immediately

| Field | Value |
|---|---|
| Test ID | T03 |
| Scenario | Everything immediately |
| Expected Behavior | Extract all six fields immediately and proceed to read-back; no second availability loop. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T04 — Missing PIN

| Field | Value |
|---|---|
| Test ID | T04 |
| Scenario | Missing PIN |
| Expected Behavior | Ask only for PIN; do not demand state, street or landmark. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T05 — Five-digit PIN

| Field | Value |
|---|---|
| Test ID | T05 |
| Scenario | Five-digit PIN |
| Expected Behavior | Reject incomplete PIN, do not append a guessed digit; accept six repeated digits. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T06 — PIN digit by digit

| Field | Value |
|---|---|
| Test ID | T06 |
| Scenario | PIN digit by digit |
| Expected Behavior | Preserve all repeated zeros and read digits individually. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T07 — Flat number variation

| Field | Value |
|---|---|
| Test ID | T07 |
| Scenario | Flat number variation |
| Expected Behavior | Normalize confidently or clarify just flat; never silently pick a conflicting value. Repeat with twelve-o-four and twelve hundred four as extra runs. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T08 — Correction mid-collection

| Field | Value |
|---|---|
| Test ID | T08 |
| Scenario | Correction mid-collection |
| Expected Behavior | Replace 302; never retain both values or discard the building. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T09 — Barge-in tower correction

| Field | Value |
|---|---|
| Test ID | T09 |
| Scenario | Barge-in tower correction |
| Expected Behavior | Audio stops; old queued speech does not resume; update tower, preserve building name, reread full address. Measure stop delay from interruption onset. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T10 — Hinglish

| Field | Value |
|---|---|
| Test ID | T10 |
| Scenario | Hinglish |
| Expected Behavior | Understand mixed speech and respond compatibly without forcing language selection. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T11 — Language switching

| Field | Value |
|---|---|
| Test ID | T11 |
| Scenario | Language switching |
| Expected Behavior | Switch naturally across turns without resetting the collected fields. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T12 — Difficult building name

| Field | Value |
|---|---|
| Test ID | T12 |
| Scenario | Difficult building name |
| Expected Behavior | Clarify genuine uncertainty, assemble spelled letters as words; no repeated spelling request once clear. If the first capture is clear, spelling is not mandatory. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T13 — Busy customer

| Field | Value |
|---|---|
| Test ID | T13 |
| Scenario | Busy customer |
| Expected Behavior | Acknowledge and terminate without collecting or scheduling/promising a callback. |
| Expected conversation outcome | CALLBACK_REQUIRED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T14 — Refusal

| Field | Value |
|---|---|
| Test ID | T14 |
| Scenario | Refusal |
| Expected Behavior | Thank and end without persuasion, follow-up pressure, or false persistence claims. |
| Expected conversation outcome | CUSTOMER_REFUSED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T15 — Silence

| Field | Value |
|---|---|
| Test ID | T15 |
| Scenario | Silence |
| Expected Behavior | One online check near the configured 12 seconds, then polite hangup near the configured 20 seconds; no looping. If runtime repeats checks or closes before the check, FAIL. Silence alone is not proof of transport failure. |
| Expected conversation outcome | PARTIAL_ADDRESS |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T16 — PIN correction at confirmation

| Field | Value |
|---|---|
| Test ID | T16 |
| Scenario | PIN correction at confirmation |
| Expected Behavior | Replace PIN without geography lookup or altering locality; reread everything and obtain new confirmation. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T17 — I already told you

| Field | Value |
|---|---|
| Test ID | T17 |
| Scenario | I already told you |
| Expected Behavior | Review context, acknowledge known details; ask for only genuinely missing PIN. If the agent redundantly asked an already supplied field, record that failure even if it recovers. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T18 — Uncertain confirmation

| Field | Value |
|---|---|
| Test ID | T18 |
| Scenario | Uncertain confirmation |
| Expected Behavior | No success or hangup after uncertainty; request a clear affirmative. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T19 — Human request

| Field | Value |
|---|---|
| Test ID | T19 |
| Scenario | Human request |
| Expected Behavior | Acknowledge, state transfer unavailable, end; no invented ticket or actual transfer. |
| Expected conversation outcome | NEEDS_HUMAN_REVIEW |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T20 — Essential detail unavailable

| Field | Value |
|---|---|
| Test ID | T20 |
| Scenario | Essential detail unavailable |
| Expected Behavior | Do not guess or confirm a complete address; no endless PIN loop. |
| Expected conversation outcome | PARTIAL_ADDRESS |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T21 — Disconnected call

| Field | Value |
|---|---|
| Test ID | T21 |
| Scenario | Disconnected call |
| Expected Behavior | Evaluator records actual disconnect and no final confirmation. Do not classify provider transport completion as address confirmation. |
| Expected conversation outcome | CALL_DROPPED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T22 — Yes followed by correction

| Field | Value |
|---|---|
| Test ID | T22 |
| Scenario | Yes followed by correction |
| Expected Behavior | Correction overrides the yes; no premature hangup. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T23 — Hindi digits and pauses

| Field | Value |
|---|---|
| Test ID | T23 |
| Scenario | Hindi digits and pauses |
| Expected Behavior | No dropped zeros, no premature turn at a digit pause. Targeted clarification is acceptable when uncertain. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

## T24 — No house number

| Field | Value |
|---|---|
| Test ID | T24 |
| Scenario | No house number |
| Expected Behavior | Accept explicit identifying alternative without inventing a number, preserve description and landmark, read all supplied details back. |
| Expected conversation outcome | ADDRESS_CONFIRMED |
| Actual Behavior | Not run |
| conversation_outcome | null |
| test_result | NOT_RUN |
| STT Errors | Not observed; test not run |
| LLM Errors | Not observed; test not run |
| TTS Issues | Not observed; test not run |
| Interruption Issues | Not observed; test not run |
| Conversation Issues | Not observed; test not run |
| Notes | Awaiting account setup and participant |
| Evidence / timestamp / agent version | None |

