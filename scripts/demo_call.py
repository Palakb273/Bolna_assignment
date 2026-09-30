"""One authorized development call. Keeps tokens/backups private; never retries POST."""
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4
import httpx
from private_bolna_env import load_bolna_keys
from bolna_common import required_env, build_call_payload
from app.integrations.bolna import build_tools, merge_tools

ROOT = Path('local-data/bolna')


def supplied_fields_match(expected, actual):
    """Bolna adds defaults; every field supplied by us must still match."""
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and supplied_fields_match(v,actual[k]) for k,v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual,list) and len(expected)==len(actual) and all(supplied_fields_match(a,b) for a,b in zip(expected,actual))
    return expected == actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['start','status','restore'])
    parser.add_argument('--backend-url')
    parser.add_argument('--to')
    parser.add_argument('--run-dir', type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.run_dir
    root.mkdir(parents=True,exist_ok=True)
    marker = root/'active-demo.json'
    try:
        load_bolna_keys()
        agent = UUID(required_env('BOLNA_AGENT_ID'))
        local = dict(line.split('=',1) for line in Path('local-data/development.env').read_text().splitlines() if '=' in line)
        with httpx.Client(timeout=30, follow_redirects=False) as c:
            bolna_headers = {'Authorization':'Bearer '+required_env('BOLNA_API_KEY')}
            agent_url = f'https://api.bolna.ai/v2/agent/{agent}'
            if args.operation == 'start':
                if marker.exists():
                    raise ValueError('Existing demo marker; inspect status/restore before a new call.')
                call = build_call_payload(str(agent), args.to or '')
                # Validate URL before sending privileged credentials.
                build_tools(args.backend_url or '',uuid4(),'x'*40)
                c.get(args.backend_url+'/health/live').raise_for_status()
                raw = c.get(agent_url,headers=bolna_headers)
                raw.raise_for_status()
                current = raw.json()
                fields = ('agent_name','agent_welcome_message','agent_type','tasks','webhook_url','ingest_source_config','calling_guardrails','call_summary_enabled')
                original = {'agent_config':{k:current[k] for k in fields if k in current},'agent_prompts':current.get('agent_prompts',{})}
                if not original['agent_config'].get('tasks'):
                    raise ValueError('Unexpected agent shape.')
                admin = {'Authorization':'Bearer '+local['BOLNA_SERVICE_TOKEN']}
                response = c.post(args.backend_url+'/v1/address-sessions',headers=admin,json={
                    'customer_external_id':'demo-'+str(uuid4()),'bolna_execution_id':'pending-'+str(uuid4())})
                response.raise_for_status()
                session = response.json()
                info = {'agent_id':str(agent),'backend_url':args.backend_url,'session_id':session['session_id'],
                    'call_token':session['call_token'],'original':original,'stage':'PREPARED'}
                marker.write_text(json.dumps(info),encoding='utf-8')
                updated = merge_tools(original,build_tools(args.backend_url,UUID(session['session_id']),session['call_token']))
                (root/'deployed-payload.json').write_text(json.dumps(updated),encoding='utf-8')
                result = c.put(agent_url,headers=bolna_headers,json=updated)
                result.raise_for_status()
                info['stage']='AGENT_UPDATED'
                marker.write_text(json.dumps(info),encoding='utf-8')
                verify = c.get(agent_url,headers=bolna_headers)
                verify.raise_for_status()
                hosted = verify.json()
                (root/'hosted-before-call.json').write_text(json.dumps(hosted),encoding='utf-8')
                wanted = updated['agent_config']['tasks'][0]['tools_config']['api_tools']
                if not supplied_fields_match(updated['agent_config'],hosted) or not supplied_fields_match(updated['agent_prompts'],hosted.get('agent_prompts')):
                    raise ValueError('Hosted editable fields differ after update.')
                # Exercise the deployed URL/header/template without mutating the call session.
                params = wanted['tools_params']['get_address_session']
                probe = c.post(params['url'],headers={'Authorization':params['api_token']},
                               json={'action':'get_address_session','version':'0'})
                probe.raise_for_status()
                if probe.json()['current_version'] != 0 or probe.json()['status'] != 'COLLECTING':
                    raise ValueError('Session was not pristine before call.')
                info['preflight_request_id'] = probe.headers.get('x-request-id')
                call['scheduled_at']=(datetime.now(timezone.utc)+timedelta(minutes=2)).isoformat()
                result=c.post('https://api.bolna.ai/call',headers=bolna_headers,json=call)
                result.raise_for_status()
                execution=str(UUID(result.json()['execution_id']))
                info.update(execution_id=execution,stage='CALL_SCHEDULED')
                marker.write_text(json.dumps(info),encoding='utf-8')
                linked=c.post(args.backend_url+f"/v1/address-sessions/{session['session_id']}/execution",headers=admin,
                              json={'bolna_execution_id':execution})
                linked.raise_for_status()
                bound_probe = c.post(params['url'],headers={'Authorization':params['api_token']},
                                     json={'action':'get_address_session','version':'0'})
                bound_probe.raise_for_status()
                if bound_probe.json()['current_version'] != 0 or bound_probe.json()['status'] != 'COLLECTING':
                    raise ValueError('Bound session was not pristine before scheduled start.')
                info['bound_preflight_request_id'] = bound_probe.headers.get('x-request-id')
                info['scheduled_at'] = call['scheduled_at']
                info['bound_preflight_at'] = datetime.now(timezone.utc).isoformat()
                info['stage']='LINKED'
                marker.write_text(json.dumps(info),encoding='utf-8')
                print(json.dumps({'call_submission':'PASS','execution_id':execution,'session_id':session['session_id'],
                                  'scheduled_at':call['scheduled_at'],'note':'Development call. Evaluate each path from evidence; no production trust claimed.'}))
            else:
                info=json.loads(marker.read_text())
                if args.operation == 'restore':
                    result=c.put(agent_url,headers=bolna_headers,json=info['original'])
                    result.raise_for_status()
                    restored = c.get(agent_url,headers=bolna_headers)
                    restored.raise_for_status()
                    raw = restored.json()
                    if not supplied_fields_match(info['original']['agent_config'],raw) or not supplied_fields_match(info['original']['agent_prompts'],raw.get('agent_prompts')):
                        raise ValueError('Restoration verification mismatch.')
                    info['stage']='RESTORED'
                    info['restoration_verified_at']=datetime.now(timezone.utc).isoformat()
                    marker.write_text(json.dumps(info),encoding='utf-8')
                    print('Original hosted agent configuration restored; private demo marker retained for audit.')
                    return
                result=c.get('https://api.bolna.ai/executions/'+info['execution_id'],headers=bolna_headers)
                result.raise_for_status()
                data=result.json()
                hosted = c.get(agent_url,headers=bolna_headers)
                hosted.raise_for_status()
                wanted = json.loads((root/'deployed-payload.json').read_text()) if (root/'deployed-payload.json').exists() else None
                visible = hosted.json()
                if wanted:
                    config_matches = supplied_fields_match(wanted['agent_config'],visible) and supplied_fields_match(wanted['agent_prompts'],visible.get('agent_prompts'))
                else:
                    config_matches = None
                state=c.get(info['backend_url']+f"/v1/address-sessions/{info['session_id']}",
                            headers={'Authorization':'Bearer '+info['call_token']})
                state.raise_for_status()
                summary={'call_status':data.get('status'),'session':state.json(),
                         'conversation_outcome':None,'backend_outcome':state.json().get('status'),'test_result':'PARTIAL'}
                summary.update(checked_at=datetime.now(timezone.utc).isoformat(),duration=data.get('conversation_duration'),
                    tool_call_count=len(data.get('tool_call_logs') or []),
                    tool_log_shapes=[{k:type(v).__name__ for k,v in x.items()} for x in (data.get('tool_call_logs') or [])],
                    hosted_configuration_matches=config_matches,public_session_http_status=state.status_code,
                    hangup_by=(data.get('telephony_data') or {}).get('hangup_by'),
                    hangup_reason=(data.get('telephony_data') or {}).get('hangup_reason'))
                (root/'demo-result.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
                with (root/'checks.jsonl').open('a',encoding='utf-8') as f:
                    f.write(json.dumps(summary)+'\n')
                print(json.dumps(summary))
    except (httpx.HTTPError,ValueError,KeyError,OSError):
        print('Demo operation failed. No secrets or response bodies displayed. Inspect private stage marker and hosted call history before retrying any mutation.')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
