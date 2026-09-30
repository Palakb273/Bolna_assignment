# Scripted voice scenarios

All addresses below are synthetic test combinations, including familiar place names. Do not use real customer information. Run T01–T24 with a consenting participant; the first 18 map to the supplied brief. No calls have been run.

Before each test: verify the deployed configuration, record safe agent/version identifiers and timestamp, start a fresh call, and have a second person evaluate the audible interaction. Confirm the full latest read-back only when instructed. Preserve failures even if a later turn recovers. Transcript review alone cannot establish TTS quality, audio cancellation, or silence timing.

For every test use the record in [results.md](results.md). Only set PASS when all expected behavior is observed. Expected outcomes below are test oracles, never observed results. Store any necessary short-lived raw evidence under ignored local-data/; agree retention first.

## T01 — Simple happy path

- Customer script: Say: “Flat 302, Galaxy Apartments, Gachibowli, Hyderabad, PIN 500032.” After full read-back say “Yes, correct.”
- Expected final fields: house_flat=302; building=Galaxy Apartments; area=Gachibowli; city=Hyderabad; pincode=500032; all other fields empty.
- Expected behavior: No redundant questions; read every supplied field, PIN digit by digit, obtain explicit confirmation.
- Expected conversation outcome: ADDRESS_CONFIRMED

## T02 — Gradual information

- Customer script: Say “Yes” to availability, then “302, Galaxy Apartments”, then “Gachibowli, Hyderabad”, then “500032”; confirm only after the full read-back.
- Expected final fields: Same as T01.
- Expected behavior: Remember previous fields, ask only missing information; opening yes must not trigger success.
- Expected conversation outcome: ADDRESS_CONFIRMED

## T03 — Everything immediately

- Customer script: Interrupt the greeting politely with “B-1204, Prestige High Fields, Financial District, Hyderabad, Telangana, 500032.” Confirm the completed read-back.
- Expected final fields: house_flat=B-1204; building=Prestige High Fields; area=Financial District; city=Hyderabad; state=Telangana; pincode=500032.
- Expected behavior: Extract all six fields immediately and proceed to read-back; no second availability loop.
- Expected conversation outcome: ADDRESS_CONFIRMED

## T04 — Missing PIN

- Customer script: Give T01 address without the PIN. Supply “500032” when asked, then confirm.
- Expected final fields: Same as T01.
- Expected behavior: Ask only for PIN; do not demand state, street or landmark.
- Expected conversation outcome: ADDRESS_CONFIRMED

## T05 — Five-digit PIN

- Customer script: Give T01 but say PIN “50003”. When asked to repeat, say “five zero zero zero three two”. Confirm.
- Expected final fields: Same as T01.
- Expected behavior: Reject incomplete PIN, do not append a guessed digit; accept six repeated digits.
- Expected conversation outcome: ADDRESS_CONFIRMED

## T06 — PIN digit by digit

- Customer script: Give T01 without PIN, then “five zero zero zero three two”. Confirm.
- Expected final fields: Same as T01.
- Expected behavior: Preserve all repeated zeros and read digits individually.
- Expected conversation outcome: ADDRESS_CONFIRMED

## T07 — Flat number variation

- Customer script: Use “B twelve zero four”, then T01's building, locality, city and PIN. If asked, clarify “B one two zero four”. Confirm.
- Expected final fields: house_flat=B-1204; remaining supplied fields same as T01.
- Expected behavior: Normalize confidently or clarify just flat; never silently pick a conflicting value. Repeat with twelve-o-four and twelve hundred four as extra runs.
- Expected conversation outcome: ADDRESS_CONFIRMED

## T08 — Correction mid-collection

- Customer script: Give “Flat 302, Galaxy Apartments”, then “Sorry, flat 320, Gachibowli, Hyderabad, PIN 500032.” Confirm.
- Expected final fields: house_flat=320; other supplied fields same as T01.
- Expected behavior: Replace 302; never retain both values or discard the building.
- Expected conversation outcome: ADDRESS_CONFIRMED

## T09 — Barge-in tower correction

- Customer script: Give “Flat 302, Tower B, Galaxy Apartments, Gachibowli, Hyderabad, 500032”. During read-back interrupt: “No, it's Tower C.” Then confirm only a new complete read-back.
- Expected final fields: house_flat=302; building=Tower C, Galaxy Apartments; remaining supplied fields same as T01.
- Expected behavior: Audio stops; old queued speech does not resume; update tower, preserve building name, reread full address. Measure stop delay from interruption onset.
- Expected conversation outcome: ADDRESS_CONFIRMED

## T10 — Hinglish

- Customer script: Say “Mera flat B-302 hai, Galaxy Apartments, Gachibowli mein.” Then “Hyderabad, PIN five zero zero zero three two.” Confirm “Haan sahi hai.”
- Expected final fields: house_flat=B-302; remaining supplied fields same as T01.
- Expected behavior: Understand mixed speech and respond compatibly without forcing language selection.
- Expected conversation outcome: ADDRESS_CONFIRMED

## T11 — Language switching

- Customer script: Say “मेरा फ्लैट तीन सौ दो है।” Then “Galaxy Apartments, Gachibowli, Hyderabad.” Then “पिन पाँच शून्य शून्य शून्य तीन दो।” Confirm “हाँ सही है।”
- Expected final fields: Same as T01.
- Expected behavior: Switch naturally across turns without resetting the collected fields.
- Expected conversation outcome: ADDRESS_CONFIRMED

## T12 — Difficult building name

- Customer script: Give “Flat 302, Rajapushpa Provincia, Gachibowli, Hyderabad, 500032”. Use an accent/noise that makes the name unclear. Repeat or spell R-A-J-A-P-U-S-H-P-A, P-R-O-V-I-N-C-I-A if asked, then confirm.
- Expected final fields: house_flat=302; building=Rajapushpa Provincia; remaining supplied fields same as T01.
- Expected behavior: Clarify genuine uncertainty, assemble spelled letters as words; no repeated spelling request once clear. If the first capture is clear, spelling is not mandatory.
- Expected conversation outcome: ADDRESS_CONFIRMED

## T13 — Busy customer

- Customer script: At greeting say “I'm busy, call later.”
- Expected final fields: No address fields required.
- Expected behavior: Acknowledge and terminate without collecting or scheduling/promising a callback.
- Expected conversation outcome: CALLBACK_REQUIRED

## T14 — Refusal

- Customer script: Say “I don't want to share my address.”
- Expected final fields: No address fields required.
- Expected behavior: Thank and end without persuasion, follow-up pressure, or false persistence claims.
- Expected conversation outcome: CUSTOMER_REFUSED

## T15 — Silence

- Customer script: Accept the call and remain silent for at least 25 seconds; note actual timing from last speech.
- Expected final fields: No address confirmed.
- Expected behavior: One online check near the configured 12 seconds, then polite hangup near the configured 20 seconds; no looping. If runtime repeats checks or closes before the check, FAIL. Silence alone is not proof of transport failure.
- Expected conversation outcome: PARTIAL_ADDRESS

## T16 — PIN correction at confirmation

- Customer script: Give T01, then during confirmation say “No, PIN is 500084.” Confirm only after another full read-back.
- Expected final fields: house_flat=302; building=Galaxy Apartments; area=Gachibowli; city=Hyderabad; pincode=500084.
- Expected behavior: Replace PIN without geography lookup or altering locality; reread everything and obtain new confirmation.
- Expected conversation outcome: ADDRESS_CONFIRMED

## T17 — I already told you

- Customer script: Give T01 without PIN. At the next question say “I already told you the flat, building and city.” Then provide PIN when requested.
- Expected final fields: Same as T01 after PIN supplied.
- Expected behavior: Review context, acknowledge known details; ask for only genuinely missing PIN. If the agent redundantly asked an already supplied field, record that failure even if it recovers.
- Expected conversation outcome: ADDRESS_CONFIRMED

## T18 — Uncertain confirmation

- Customer script: Give T01; after full read-back say “I think so.” Only on explicit follow-up say “Yes, correct.”
- Expected final fields: Same as T01.
- Expected behavior: No success or hangup after uncertainty; request a clear affirmative.
- Expected conversation outcome: ADDRESS_CONFIRMED

## T19 — Human request

- Customer script: Say “Can I talk to a person instead?”
- Expected final fields: No address fields required.
- Expected behavior: Acknowledge, state transfer unavailable, end; no invented ticket or actual transfer.
- Expected conversation outcome: NEEDS_HUMAN_REVIEW

## T20 — Essential detail unavailable

- Customer script: Give T01 without PIN, say “I don't know it and can't find it.” Agree to stop if asked.
- Expected final fields: house_flat=302; building=Galaxy Apartments; area=Gachibowli; city=Hyderabad; pincode empty.
- Expected behavior: Do not guess or confirm a complete address; no endless PIN loop.
- Expected conversation outcome: PARTIAL_ADDRESS

## T21 — Disconnected call

- Customer script: Supply “Flat 302” and then hang up the phone before any full read-back.
- Expected final fields: house_flat=302 if heard; other fields empty.
- Expected behavior: Evaluator records actual disconnect and no final confirmation. Do not classify provider transport completion as address confirmation.
- Expected conversation outcome: CALL_DROPPED

## T22 — Yes followed by correction

- Customer script: Give T01 and answer full read-back: “Yes, but the flat is 320.” Confirm only after full corrected read-back.
- Expected final fields: house_flat=320; remaining supplied fields same as T01.
- Expected behavior: Correction overrides the yes; no premature hangup.
- Expected conversation outcome: ADDRESS_CONFIRMED

## T23 — Hindi digits and pauses

- Customer script: Give T01 without PIN. Say “पाँच, शून्य, शून्य, शून्य, तीन, दो” with pauses of about half a second; verify any displayed ५०००३२ maps to 500032. Confirm.
- Expected final fields: Same as T01.
- Expected behavior: No dropped zeros, no premature turn at a digit pause. Targeted clarification is acceptable when uncertain.
- Expected conversation outcome: ADDRESS_CONFIRMED

## T24 — No house number

- Customer script: Say “My house has no number. It's the blue house beside Example School, Example Lane, Example Colony, Hyderabad, 500032.” Confirm if full description is read back.
- Expected final fields: house_flat empty; building=blue house (or house description retained verbatim); street=Example Lane; area=Example Colony; landmark=beside Example School; city=Hyderabad; pincode=500032.
- Expected behavior: Accept explicit identifying alternative without inventing a number, preserve description and landmark, read all supplied details back.
- Expected conversation outcome: ADDRESS_CONFIRMED

