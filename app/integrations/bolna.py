import copy
from urllib.parse import urlparse

COLLECTION_POLICY = '''The backend tools are connected and authoritative. Immediately after the customer supplies any address component, call update_address before asking the next question or reading the address back. Do not wait for every field or final confirmation. Use version "0" for the initial update; use current_version from tool responses afterward. Construct changes_json as a JSON object with only customer-supplied fields. Never ask the customer for a version, JSON, session ID or execution ID. Session ownership is already bound by the tool configuration. Backend read-back, validation and save rules override any older conversational-only examples below.'''


def backend_prompt(text):
    text = text.replace('This is temporary conceptual state, not a database or external tool.',
                        'The backend maintains the versioned address state.')
    text = text.replace('No geographical validation is connected.',
                        'Use validate_address for geographical validation; it may report unavailable evidence.')
    if COLLECTION_POLICY not in text:
        text = COLLECTION_POLICY+'\n\n'+text
    return text if POLICY in text else text+'\n\n'+POLICY

POLICY = '''Backend address policy: use update_address for every supplied field and correction, preserving omitted fields. Never invent postal facts. Use validate_address and follow its next_action. Use returned current_version for subsequent tools. If version conflict occurs, get_address_session then retry with current facts. Read prepare_address_readback text exactly and completely, including all optional fields and each PIN digit. Any interruption, uncertainty, rejection, or "yes, but" correction invalidates read-back; call interrupt_address_readback and update/revalidate/reread as appropriate. A spoken yes is not permission to manufacture evidence. request_address_confirmation only requests evidence processing. Never claim the address was saved unless save_address returns backend_outcome ADDRESS_SAVED. If evidence or validation is unavailable, explain the limitation and offer human follow-up; do not claim success. Do not expose credentials. Preserve the customer's language and use language hi for Hindi/Hinglish read-back.'''


def build_tools(base_url, session_id, call_token):
    parsed = urlparse(base_url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('A public HTTPS backend origin is required.')
    if len(call_token) < 32 or any(ord(c) < 33 or ord(c) > 126 for c in call_token):
        raise ValueError('Valid session credential required.')
    descriptions = {
        'get_address_session': 'Get the current backend version and status after a conflict or uncertain response.',
        'update_address': 'Record only customer-supplied changes. changes_json is a JSON object using the nine address fields; omit unchanged fields, null explicitly clears.',
        'validate_address': 'Validate the current address; follow targeted next_action and use returned version after normalization.',
        'prepare_address_readback': 'Get the exact validated full read-back text. Speak it verbatim; language is en or hi.',
        'interrupt_address_readback': 'Invalidate consent after interruption, rejection, uncertainty or yes-but correction.',
        'request_address_confirmation': 'Request confirmation processing. This does not prove consent or authorize saving.',
        'save_address': 'Attempt guarded saving only after backend-confirmed evidence. Never claim saved on an error.'}
    tools = []
    for name, description in descriptions.items():
        properties = {'version': {'type':'string','description':'Exact current_version as decimal digits; use 0 initially.'}}
        # Bolna's legacy %-templates interpolate inside serialized JSON and break
        # on quotes in changes_json. Typed markers preserve strings until encoding.
        params = {'action':name, 'version':{'$var':'version'}}
        if name == 'update_address':
            properties['changes_json'] = {'type':'string','description':'JSON object with only supplied address changes. Allowed keys: house_flat, building, street, area, landmark, city, district, state, pincode. Values are strings or null to clear. Omit unknown fields. Convert clearly spoken PIN digits to a six-digit string. Do not invent state or district.'}
            params['changes_json'] = {'$var':'changes_json'}
        if name == 'prepare_address_readback':
            properties['language'] = {'type':'string','enum':['en','hi']}
            params['language'] = {'$var':'language'}
        tools.append({'name':name,'description':description, 'parameters':{'type':'object','properties':properties,
            'required':list(properties), 'additionalProperties':False}, 'key':'custom_task',
            'value':{'method':'POST','url':base_url.rstrip('/')+f'/v1/address-sessions/{session_id}/tool',
                     'api_token':'Bearer '+call_token,'headers':{'Content-Type':'application/json'},'param':params}})
    return tools


def merge_tools(payload, tools):
    result = copy.deepcopy(payload)
    config = result['agent_config']['tasks'][0]['tools_config']
    existing = config.get('api_tools') or {'tools':[], 'tools_params':{}}
    if not isinstance(existing, dict) or not isinstance(existing.get('tools', []), list):
        raise ValueError('Unsupported hosted tool configuration; use custom-function editor.')
    names = {t['name'] for t in tools}
    existing['tools'] = [t for t in existing.get('tools', []) if t.get('name') not in names] + [
        {k:v for k,v in t.items() if k not in ('key','value')} for t in tools]
    existing['tools_params'] = dict(existing.get('tools_params') or {}) | {t['name']:t['value'] for t in tools}
    config['api_tools'] = existing
    prompt = result.setdefault('agent_prompts', {}).setdefault('task_1', {})
    prompt['system_prompt'] = backend_prompt(prompt.get('system_prompt',''))
    for entry in (config.get('multilingual_config') or {}).get('languages', {}).values():
        entry['system_prompt'] = backend_prompt(entry.get('system_prompt',''))
    return result
