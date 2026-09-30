# Twenty realistic review calls

Run these 20 additional calls after scripted testing. All are currently NOT_RUN. Synthetic ground truth and baseline scripts are in [scenarios.md](scenarios.md); changes below modify that ground truth. Do not write real participant phone numbers here.

For each case, evaluate correctness and naturalness, not merely whether it ended. Rate naturalness 1–5 with a reason. Record speech overlap duration where measurable, optional-field retention, hallucinated fields, and each unnecessary question. Use null for unobserved outcomes and do not turn missing evidence into PASS.

## M01 — Fast English

- Script / ground truth: T01, including the following variation.
- Variation: Speak quickly but naturally, retaining every zero.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M02 — Slow English

- Script / ground truth: T02, including the following variation.
- Variation: Use one-second pauses between address components.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M03 — Hindi

- Script / ground truth: T11, including the following variation.
- Variation: Speak Hindi throughout; give city/building names unchanged.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M04 — Hinglish

- Script / ground truth: T10, including the following variation.
- Variation: Mix Hindi and English within sentences.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M05 — Regional English accent

- Script / ground truth: T01, including the following variation.
- Variation: Participant uses their normal regional accent; do not imitate stereotypes.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M06 — Regional Hindi accent

- Script / ground truth: T11, including the following variation.
- Variation: Participant speaks in their normal Hindi accent.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M07 — Background noise

- Script / ground truth: T01, including the following variation.
- Variation: Use moderate ambient household noise; no real personal audio.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M08 — Speakerphone

- Script / ground truth: T02, including the following variation.
- Variation: Use speakerphone at a normal distance.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M09 — Quick interruption

- Script / ground truth: T09, including the following variation.
- Variation: Interrupt after the first incorrect tower word.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M10 — Long interruption

- Script / ground truth: T09, including the following variation.
- Variation: Interrupt with the tower correction plus a long explanation; verify no overlap.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M11 — Flat correction

- Script / ground truth: T08, including the following variation.
- Variation: Change only the flat number.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M12 — PIN correction

- Script / ground truth: T16, including the following variation.
- Variation: Change only the PIN at read-back.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M13 — Apartment spelling

- Script / ground truth: T12, including the following variation.
- Variation: Spell the name only when clarification is needed.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M14 — Street name

- Script / ground truth: T24, including the following variation.
- Variation: Speak the street name clearly, then correct Example Lane to Sample Road before confirmation.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M15 — Complex flat

- Script / ground truth: T07, including the following variation.
- Variation: Use B twelve-o-four.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M16 — Mixed numerals

- Script / ground truth: T23, including the following variation.
- Variation: Say “B, तीन शून्य दो” for the flat and “पाँच शून्य शून्य शून्य तीन दो” for the PIN. Expected final house_flat=B-302 and pincode=500032; remaining supplied fields match T23.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M17 — Repeated zeros

- Script / ground truth: T06, including the following variation.
- Variation: Read PIN digits with natural pauses.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M18 — Optional landmark

- Script / ground truth: T01, including the following variation.
- Variation: Add “opposite Example Library” and verify it survives full read-back.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M19 — Hesitant approval

- Script / ground truth: T18, including the following variation.
- Variation: Say “maybe” then clear confirmation only on explicit follow-up.
- Expected behavior: all baseline criteria plus accurate handling of this speaking condition.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution

## M20 — Late correction

- Script / ground truth: T01 initially; after the correction, house_flat=320 and all other supplied fields remain as in T01.
- Variation: After the first complete read-back say “Yes, correct.” Wait until the agent's goodbye is audible, then interrupt: “Actually, flat 320.” Confirm again only after a fresh complete corrected read-back.
- Expected behavior: interrupt audible goodbye, cancel pending hangup, replace 302 with 320, repeat the full updated address, and obtain a new explicit confirmation before ending. Record FAIL if the call ends before the correction can be handled.
- Actual behavior: Not run
- conversation_outcome: null
- test_result: NOT_RUN
- Observed final fields / correct supplied fields / total supplied fields: unmeasured
- PIN correct / PIN supplied: unmeasured
- Successful corrections / attempts: unmeasured
- Successful interruptions / attempts / stop delay: unmeasured
- Redundant questions / collection questions: unmeasured
- Unsupported fields / introduced fields: unmeasured
- Valid final confirmation / eligible cooperative call: unmeasured
- STT errors: unobserved
- LLM errors: unobserved
- TTS issues: unobserved
- Interruption issues: unobserved
- Conversation issues / context retention: unobserved
- Naturalness rating and reason: unmeasured
- Notes / evidence reference / timestamp / configuration version: awaiting execution
