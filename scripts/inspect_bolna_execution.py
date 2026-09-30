"""Read-only raw-log diagnostics. Never emits transcript, arguments or credentials."""
import argparse
import ast
import json
import re
from pathlib import Path
import httpx
from private_bolna_env import load_bolna_keys
from bolna_common import required_env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    args = parser.parse_args()
    marker = json.loads((args.run_dir/'active-demo.json').read_text())
    load_bolna_keys()
    try:
        response = httpx.get('https://api.bolna.ai/executions/'+marker['execution_id']+'/log',
            headers={'Authorization':'Bearer '+required_env('BOLNA_API_KEY')},timeout=30)
        response.raise_for_status()
        rows = response.json()['data']
    except (httpx.HTTPError,ValueError,KeyError):
        raise SystemExit('Raw-log retrieval failed; response body withheld.') from None
    safe = []
    for row in rows:
        if row.get('component') not in ('warning','function_call'):
            continue
        name = row.get('tool_name')
        allowed = {'get_address_session','update_address','validate_address','prepare_address_readback',
                   'interrupt_address_readback','request_address_confirmation','save_address'}
        if name not in allowed | {'custom_task_'+x for x in allowed}:
            name = None
        match = re.search(r"Expecting ',' delimiter: line [0-9]+ column [0-9]+ \(char [0-9]+\)",str(row.get('data','')))
        item = {'timestamp':row.get('created_at'),'execution_id':marker['execution_id'],
            'session_id':marker['session_id'],'tool_name':name,
            'component':row['component'],'direction':row.get('type'),
            'error_reason':match.group() if match else None}
        data = row.get('data')
        if isinstance(data,str) and len(data) <= 65536:
            try:
                data = json.loads(data)
            except (ValueError,TypeError):
                try:
                    data = ast.literal_eval(data)
                except (ValueError,SyntaxError):
                    data = None
        if isinstance(data,dict):
            status = data.get('status')
            if status in ('COLLECTING','VALID','VALIDATION_ERROR','NEEDS_CLARIFICATION','CONFIRMED','SAVED'):
                item['response_state'] = status
            if type(data.get('current_version')) is int:
                item['response_version'] = data['current_version']
            error = data.get('error')
            code = error.get('code') if isinstance(error,dict) else None
            if isinstance(code,str) and re.fullmatch(r'[A-Z_]{1,60}',code):
                item['error_reason'] = code
        if row['component']=='warning' and not item['error_reason']:
            item['error_reason']='DETAILS_WITHHELD'
        safe.append(item)
    (args.run_dir/'provider-diagnostics.json').write_text(json.dumps(safe,indent=2),encoding='utf-8')
    print(json.dumps(safe))


if __name__ == '__main__':
    main()
