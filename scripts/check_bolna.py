import json
from uuid import UUID
import httpx
from private_bolna_env import load_bolna_keys
from bolna_common import required_env


def main():
    try:
        load_bolna_keys()
        agent = UUID(required_env('BOLNA_AGENT_ID'))
        key = required_env('BOLNA_API_KEY')
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            response = client.get(f'https://api.bolna.ai/v2/agent/{agent}', headers={'Authorization':'Bearer '+key})
            if response.status_code != 200:
                print(json.dumps({'agent_access':'FAIL','http_status':response.status_code}))
                return
            data = response.json()
            print(json.dumps({'agent_access':'PASS','task_count':len(data.get('tasks',[])),
                'tools_present':bool(data.get('tasks',[{}])[0].get('tools_config',{}).get('api_tools'))}))
    except (ValueError, OSError):
        print('Bolna credentials unavailable or invalid; no values displayed.')
    except httpx.HTTPError:
        print('Bolna network check failed; no response body or credentials displayed.')
        raise SystemExit(2)


if __name__ == '__main__':
    main()
