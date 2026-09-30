"""Update an existing reserved development agent; dry-run default. No .env loading."""
import argparse
import json
from pathlib import Path
from uuid import UUID, uuid4
import httpx
from bolna_common import required_env
from app.integrations.bolna import build_tools, merge_tools


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--backend-url', required=True)
    p.add_argument('--session-id', type=UUID, required=True)
    p.add_argument('--execute', action='store_true')
    args = p.parse_args()
    try:
        agent_id = UUID(required_env('BOLNA_AGENT_ID'))
        tools = build_tools(args.backend_url, args.session_id, required_env('BOLNA_CALL_TOKEN'))
        root = Path('local-data/bolna')
        root.mkdir(parents=True, exist_ok=True)
        tool_path = root/f'tools-{args.session_id}.json'
        with tool_path.open('x', encoding='utf-8') as f:
            json.dump(tools, f, ensure_ascii=False, indent=2)
        if not args.execute:
            print('Tool definitions written to ignored local-data/bolna. Contains session credential; keep private. No remote changes.')
            return
        with httpx.Client(timeout=30, follow_redirects=False, headers={'Authorization':'Bearer '+required_env('BOLNA_API_KEY')}) as c:
            url = f'https://api.bolna.ai/v2/agent/{agent_id}'
            response = c.get(url)
            response.raise_for_status()
            original = response.json()
            if 'tasks' not in original:
                raise ValueError('Unexpected agent response; no update sent.')
            allowed = ('agent_name','agent_welcome_message','agent_type','tasks','webhook_url','ingest_source_config','calling_guardrails','call_summary_enabled')
            payload = {'agent_config':{k:original[k] for k in allowed if k in original},
                       'agent_prompts':original.get('agent_prompts',{})}
            with (root/f'backup-{agent_id}-{uuid4()}.json').open('x',encoding='utf-8') as f:
                json.dump(payload,f,ensure_ascii=False)
            updated = merge_tools(payload, tools)
            result = c.put(url,json=updated)
            result.raise_for_status()
            print('Existing agent update accepted. Hosted tool behavior still requires a live test. Configure separate webhook headers in the dashboard.')
    except (ValueError, OSError, httpx.HTTPError):
        raise SystemExit('Configuration failed; check required environment and hosted configuration. If a PUT timed out, inspect the agent before retrying. No response body or credential logged.') from None


if __name__ == '__main__':
    main()
