# Phase 1 measurement guide

Status: unmeasured. No voice calls have run. Do not report zeros as evidence of accuracy or safety.

Keep scripted tests and the 20 realistic calls as separate cohorts. Within each cohort, report numerator / denominator and percentage. Exclude NOT_RUN cases. For incomplete evaluations, report observed counts and missing evidence separately; do not silently assume success. A denominator of zero is N/A.

| Metric | Numerator | Denominator |
|---|---|---|
| Address field accuracy | Correct final supplied fields after latest corrections | Supplied fields with ground truth in evaluated calls |
| PIN accuracy | Calls with the correct final PIN | Evaluated calls supplying a PIN |
| Correction success | Corrections reflected correctly in final state/read-back | Observed correction attempts |
| Interruption success | Interruptions where playback stops and the content is handled correctly | Observed interruption attempts |
| Redundant question rate | Collection questions asking for information already clearly provided | All collection questions |
| Hallucination rate | Introduced field claims unsupported by customer or trusted context | All introduced field claims |
| Confirmation completion | Calls with valid explicit approval after latest complete read-back | Eligible cooperative evaluated calls |

A field counts once per call for field accuracy; the latest explicit correction is ground truth. Compare semantic names using customer spelling, not a geographical lookup. Do not penalize a legitimate unknown optional field. Do count loss of a supplied optional field. Assess house/flat, building, area, city, and PIN separately too.
Count unsupported claims when introduced even if later corrected. Log field-level and conversation-level instances so repetition does not hide an error. A read-back clarification of genuinely uncertain data is not automatically a redundant question.

Eligible confirmation calls are cooperative calls with enough supplied identifying detail and an opportunity to finish; report exclusions (refusal, busy, human request, external disconnect) by count. Never exclude a cooperative agent failure merely to improve the completion rate.

Test pass rate uses test_result, not conversation_outcome: PASS / evaluated tests, with FAIL and PARTIAL counts shown separately. A correctly handled refusal can PASS. A call that claims ADDRESS_CONFIRMED without fresh full read-back must FAIL. PARTIAL_ADDRESS may PASS for an expected incomplete-address scenario.
An observed call disposition is separate from Bolna transport status. A platform "completed" execution does not mean ADDRESS_CONFIRMED.

Review stop latency in milliseconds from customer onset to agent audio cessation where an agreed recording is available; otherwise report a live observation and mark precise latency unmeasured. Naturalness rating is a separate subjective 1–5 score with a short reason.

Targets: no invented fields, no avoidable repeated questions, and very high numeric accuracy. No percentages or latency thresholds have yet been demonstrated. Every required scenario and exit behavior must have supporting evidence before declaring Phase 1 complete.

