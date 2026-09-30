"""Small, secret-safe helpers for the Phase 1 hosted Bolna prototype."""

import copy
import json
import os
import re
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
API_ORIGIN = 'https://api.bolna.ai'
UUID_PATTERN = r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}'
UNKNOWN = 'Submission status unknown. Check Bolna call history/agents before retrying.'


def required_env(name: str) -> str:
    value = os.environ.get(name, '')
    if (not value or value != value.strip() or value.lower().startswith(('your_', 'replace_', '<'))
            or any(ord(char) < 33 or ord(char) > 126 for char in value)):
        raise ValueError(f'Set {name} to a valid value in your local environment.')
    return value


def build_agent_payload(config: dict, prompt: str, hindi_prompt: str = '') -> dict:
    """Insert shared policy and Hindi guidance into a validated config copy."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError('The system prompt must not be empty.')
    payload = copy.deepcopy(config)
    try:
        agent = payload['agent_config']
        tasks = agent['tasks']
        if len(tasks) != 1 or tasks[0]['task_type'] != 'conversation':
            raise ValueError('Use one conversation task for Phase 1.')
        tools = tasks[0]['tools_config']
        timing = tasks[0]['task_config']
        languages = tools['multilingual_config']['languages']
        if set(languages) != {'en', 'hi'} or tools['multilingual_config']['enabled'] is not True:
            raise ValueError('Configure enabled English and Hindi language entries.')
        if tools['multilingual_config']['active_language'] not in languages:
            raise ValueError('Active language must have a configuration.')
        if not 0 < timing['trigger_user_online_message_after'] < timing['hangup_after_silence'] < timing['call_terminate']:
            raise ValueError('Silence check must precede silence hangup and call timeout.')
        if timing['number_of_words_for_interruption'] < 1:
            raise ValueError('Interruption threshold must be positive.')
        for entry in [tools, *languages.values()]:
            synth = entry['synthesizer']
            if not synth['provider'] or not synth['provider_config']['voice_id']:
                raise ValueError('A synthesizer provider and voice are required.')
        for field in ['provider', 'model', 'language']:
            if not tools['transcriber'][field]:
                raise ValueError('Transcriber settings are incomplete.')
        for field in ['provider', 'model']:
            if not tools['llm_agent']['llm_config'][field]:
                raise ValueError('LLM settings are incomplete.')
        if agent.get('webhook_url') or agent.get('ingest_source_config') or agent.get('call_summary_enabled'):
            raise ValueError('Phase 1 does not enable webhooks, ingestion, or summaries.')
        if tools.get('api_tools'):
            raise ValueError('Phase 1 does not connect external tools.')
    except (KeyError, TypeError, IndexError, AttributeError):
        raise ValueError('Invalid agent configuration structure.') from None
    payload['agent_prompts'] = {'task_1': {'system_prompt': prompt}}
    languages['en']['system_prompt'] = prompt
    languages['hi']['system_prompt'] = prompt + ('\n\n' + hindi_prompt if hindi_prompt else '')
    return payload


def load_agent_payload() -> dict:
    try:
        config = json.loads((ROOT / 'config/agent.json').read_text(encoding='utf-8'))
        prompt = (ROOT / 'prompts/address_collector.md').read_text(encoding='utf-8')
        hindi = (ROOT / 'prompts/address_collector.hi.md').read_text(encoding='utf-8')
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ValueError('Cannot read the UTF-8 configuration and prompt files.') from None
    return build_agent_payload(config, prompt, hindi)


def build_call_payload(agent_id: str, recipient: str) -> dict:
    if not re.fullmatch(UUID_PATTERN, agent_id):
        raise ValueError('BOLNA_AGENT_ID must be a UUID returned by Bolna.')
    if not re.fullmatch(r'\+[1-9][0-9]{7,14}', recipient):
        raise ValueError('Recipient must be an E.164 phone number with country code, without spaces.')
    return {'agent_id': agent_id, 'recipient_phone_number': recipient}


class NoRedirect(HTTPRedirectHandler):
    """Do not forward authorization headers or repeat POSTs on redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def post_json(path: str, payload: dict, api_key: str) -> dict:
    if path not in {'/call', '/v2/agent'}:
        raise ValueError('Unsupported API path.')
    if not api_key or any(ord(char) < 33 or ord(char) > 126 for char in api_key):
        raise ValueError('Invalid API key format.')
    request = Request(API_ORIGIN + path, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                      headers={'Authorization': 'Bearer ' + api_key,
                               'Content-Type': 'application/json', 'Accept': 'application/json'},
                      method='POST')
    try:
        with build_opener(NoRedirect()).open(request, timeout=30) as response:
            if not 200 <= response.status < 300:
                raise RuntimeError('Unexpected HTTP response. ' + UNKNOWN)
            raw = response.read(1_048_577)
            if len(raw) > 1_048_576:
                raise RuntimeError('Response exceeded the size limit. ' + UNKNOWN)
    except HTTPError as error:
        status = error.code
        error.close()
        if 300 <= status < 400:
            raise RuntimeError('API redirect refused. ' + UNKNOWN) from None
        raise RuntimeError(f'Bolna returned HTTP {status}. ' + UNKNOWN) from None
    except (URLError, OSError, HTTPException):
        raise RuntimeError('API connection failed. ' + UNKNOWN) from None
    try:
        result = json.loads(raw.decode('utf-8'))
    except (ValueError, UnicodeError):
        raise RuntimeError('Invalid API response. ' + UNKNOWN) from None
    if not isinstance(result, dict):
        raise RuntimeError('Expected an API response object. ' + UNKNOWN)
    return result


def response_identifier(response: dict, key: str) -> str:
    value = response.get(key)
    if not isinstance(value, str) or not re.fullmatch(UUID_PATTERN, value):
        raise RuntimeError('Missing or invalid response identifier. ' + UNKNOWN)
    return value
