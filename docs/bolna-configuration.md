# Exact initial Bolna configuration

Prepared 2026-09-30. This is the local candidate, not a deployed or account-verified configuration. Source of truth: [agent.json](../config/agent.json). The helper injects [shared prompt](../prompts/address_collector.md) and [Hindi guidance](../prompts/address_collector.hi.md) into the base and per-language prompts.

| Component | Initial value |
|---|---|
| STT | sarvam / saaras:v4; stream=true |
| STT language | en base, hi override |
| LLM | openai / gpt-4.1; temperature=0.2; max_tokens=400; streaming simple_llm_agent |
| TTS | sarvam / bulbul:v3; Priya / priya; speed=0.95; buffer_size=150; streaming |
| TTS language | en base and English slot, hi Hindi slot |
| Telephony | plivo input/output, wav; account default outbound number |
| Multilingual | enabled; active_language=en; requested_or_auto_detected |
| Barge-in | number_of_words_for_interruption=1 |
| Turn timing | endpointing=500 ms; incremental_delay=500 ms |
| Silence | check_if_user_online=true; check at 12 seconds; hangup at 20 seconds |
| Duration cap | call_terminate=300 seconds |
| Ending | hangup_after_LLMCall=true with explicit completion conditions |
| Final message | English/Hindi variants; interruptible_hangup_message=true |
| Extras | backchanneling=false; ambient_noise=false; auto_reschedule=false; voicemail=false |
| Persistence integrations | no webhook, ingestion, database, tools, post-call extraction; call_summary_enabled=false |

These values are engineering starting points. The 400-token response budget allows full read-back; short questions are enforced through the prompt. Both language slots use the same multilingual voice identity, with the correct language setting.

## Sources and practical caveats

- [Hosted creation](https://www.bolna.ai/docs/api-reference/agent/v2/create): POST /v2/agent accepts agent_config and agent_prompts; success returns agent_id. GPT-4.1 is a supported listed model. Account/runtime acceptance is still required.
- [Call API](https://www.bolna.ai/docs/api-reference/calls/make): POST /call with agent_id and recipient_phone_number uses the account default number when sender is omitted; execution_id identifies submission.
- [Sarvam STT](https://www.bolna.ai/docs/sarvam-transcriber): selected model and plain en/hi codes come from this reference; audio rate/encoding follow telephony. Sarvam keyterm prompting is not connected through Bolna's keywords setting.
- [Sarvam TTS](https://www.bolna.ai/docs/sarvam-voice): bulbul:v3, Priya/priya and language are explicitly configured. Preview the voice in the actual account before calling.
- [Multilingual API](https://www.bolna.ai/docs/customizations/multilingual-config-reference): languages live in tools_config.multilingual_config. The helper copies the shared policy into both language prompts and appends native-script Hindi guidance; no state is intentionally reset.
- [Engine controls](https://www.bolna.ai/docs/agent-setup/engine-tab): short interruptions and timer behavior need acoustic verification. Its endpointing guidance excludes Sarvam from the slider list, while the Sarvam reference documents endpointing. We retain the Sarvam example's 500 ms, but its runtime effect is UNVERIFIED.
- [Prompt hangup](https://www.bolna.ai/docs/agent-setup/agent-tab): completion conditions are separate from spoken collection instructions. Do not assume saying goodbye disconnects a call.
- [System messages](https://www.bolna.ai/docs/customizations/auto-switch-multilingual-messages): English/Hindi online and final-message variants are configured.

The public timing controls do not establish a guaranteed one-check limit. T15 must verify exactly one prompt and a polite ending; if the hosted runtime repeats checks, Phase 1 fails that criterion until tuned or addressed with Bolna. The prompt cannot independently cancel queued audio. T09 must confirm actual playback stops. Also verify a last-second correction cancels goodbye and reopens confirmation. A neutral final message covers normal and silence exits; the more specific lost-connection wording is not claimed as a separately available runtime setting.

## Applied settings and data handling

| Account check | Actual state |
|---|---|
| Agent created and retrieved | Not attempted; credentials absent |
| Provider and voice availability | Unverified |
| Default outbound number and Plivo setup | Unverified |
| Recording enabled/disabled | Unknown; inspect account before first call |
| Transcript retention | Unknown account policy |
| Audio retention and deletion | Unknown account/provider policy |
| Live-call evidence | None |

[Bolna security documentation](https://www.bolna.ai/docs/concepts/security) describes recordings and transcripts in execution records; recording retention needs account/support confirmation. No local database does not imply no provider retention. Disable unnecessary recordings if possible; if recording is needed for QA, agree temporary retention and restrict access. Use synthetic addresses and consenting testers. Record actual settings in this table before live tests. There is no invented record=false flag in the payload.

To change providers, edit the base transcriber/synthesizer and relevant en/hi overrides together. Provider-specific fields must match the new provider's current docs. Re-run local validation, create a new test agent deliberately, and verify the applied configuration in the dashboard before placing calls. The helper intentionally does not modify or delete existing agents.

