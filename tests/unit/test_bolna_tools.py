from uuid import uuid4
import json
import pytest
from app.integrations.bolna import build_tools, merge_tools


def bolna_request_body(template, values):
    """Exercise Bolna's public prepare_api_request substitution contract.

    Legacy formatting happens AFTER json.dumps, so JSON-valued strings must use
    typed $var substitution. Mirrors the two documented-by-source transport paths,
    not our configuration generator.
    """
    def markers(value):
        return isinstance(value, dict) and ('$var' in value or any(markers(v) for v in value.values()))
    def replace(value):
        if isinstance(value, dict):
            if set(value) == {'$var'}:
                return values[value['$var']]
            return {k:replace(v) for k,v in value.items()}
        return value
    if markers(template):
        return json.loads(json.dumps(replace(template)))
    return json.loads(json.dumps(template) % values)


@pytest.mark.parametrize('building', ['Example Apartments', 'Example "North" Apartments', 'इमारत', r'Example\Block'])
def test_bolna_payload_preserves_json_string_without_pre_http_parse_failure(building):
    tool = next(t for t in build_tools('https://backend.example', uuid4(), 'x'*40) if t['name']=='update_address')
    changes = json.dumps({'house_flat':'TEST-1','building':building},ensure_ascii=False)
    body = bolna_request_body(tool['value']['param'], {'version':'0','changes_json':changes})
    assert body == {'action':'update_address','version':'0','changes_json':changes}


def test_tools_have_fixed_ownership_and_no_evidence_endpoint():
    sid = uuid4()
    tools = build_tools('https://backend.example', sid, 'x'*40)
    assert {t['name'] for t in tools} >= {'update_address','validate_address','prepare_address_readback','save_address'}
    for t in tools:
        assert str(sid) in t['value']['url']
        assert 'session_id' not in t['parameters']['properties']
        assert t['value']['api_token'] == 'Bearer '+'x'*40
        assert '/evidence' not in t['value']['url']


def test_config_merge_preserves_voice_and_existing_tools():
    original = {'agent_config': {'tasks': [{'tools_config': {'synthesizer': {'provider':'sarvam'}}}]},
                'agent_prompts': {'task_1': {'system_prompt':'Existing instructions'}}}
    updated = merge_tools(original, build_tools('https://backend.example', uuid4(), 'x'*40))
    assert updated['agent_config']['tasks'][0]['tools_config']['synthesizer'] == {'provider':'sarvam'}
    assert 'api_tools' not in original['agent_config']['tasks'][0]['tools_config']


def test_refuses_insecure_backend_url():
    with pytest.raises(ValueError):
        build_tools('http://backend.example', uuid4(), 'x'*40)


def test_deployed_prompt_has_no_prototype_backend_conflict_and_fields_are_named():
    original = {'agent_config': {'tasks': [{'tools_config': {}}]}, 'agent_prompts': {'task_1': {
        'system_prompt': 'This is temporary conceptual state, not a database or external tool. No geographical validation is connected.'}}}
    tools = build_tools('https://backend.example', uuid4(), 'x'*40)
    updated = merge_tools(original, tools)
    prompt = updated['agent_prompts']['task_1']['system_prompt']
    assert 'not a database or external tool' not in prompt
    assert 'No geographical validation is connected' not in prompt
    assert 'before asking' in prompt
    update = next(t for t in tools if t['name'] == 'update_address')
    description = update['parameters']['properties']['changes_json']['description']
    for name in ('house_flat','building','street','area','landmark','city','district','state','pincode'):
        assert name in description
