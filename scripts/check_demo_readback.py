"""Read-only comparison of stored readback and provider text; outputs no address/transcript."""
import argparse
import json
import re
from pathlib import Path
from uuid import UUID
import httpx
from sqlalchemy import select,func
from app.database import make_engine,sessions,addresses,readbacks
from private_bolna_env import load_bolna_keys
from bolna_common import required_env


def normalized(text):
    return ' '.join(text.split())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,required=True)
    args=parser.parse_args()
    info=json.loads((args.run_dir/'active-demo.json').read_text())
    values=dict(line.split('=',1) for line in Path('local-data/development.env').read_text().splitlines() if '=' in line)
    engine=make_engine(values['DATABASE_URL'])
    try:
        with engine.connect() as c:
            state=c.execute(select(sessions.c.state).where(sessions.c.id==UUID(info['session_id']))).scalar_one()
            saved=c.execute(select(func.count()).select_from(addresses).where(addresses.c.source_session_id==UUID(info['session_id']))).scalar_one()
            attempts=c.execute(select(func.count()).select_from(readbacks).where(readbacks.c.session_id==UUID(info['session_id']))).scalar_one()
        load_bolna_keys()
        headers={'Authorization':'Bearer '+required_env('BOLNA_API_KEY')}
        with httpx.Client(timeout=30) as client:
            result=client.get('https://api.bolna.ai/executions/'+info['execution_id'],headers=headers)
            result.raise_for_status()
            log=client.get('https://api.bolna.ai/executions/'+info['execution_id']+'/log',headers=headers)
            log.raise_for_status()
        data=result.json()
        rows=log.json()['data']
        rb=state.get('readback') or {}
        expected=normalized(rb.get('rendered_text',''))
        transcript=data.get('transcript') or ''
        parts=re.split(r'(?:^|\n)(assistant|user):\s*',transcript)
        assistant=' '.join(parts[i+1] for i in range(1,len(parts)-1,2) if parts[i]=='assistant')
        synth=' '.join(r['data'] for r in rows if r.get('component')=='synthesizer' and r.get('type')=='request' and isinstance(r.get('data'),str))
        exact=bool(expected and expected in normalized(assistant))
        latest=(state.get('validation_attempts') or [{}])[-1]
        output={'execution_id':info['execution_id'],'session_id':info['session_id'],
            'current_version':state['current_version'],'validated_version':state.get('validated_version'),
            'confirmed_version':state.get('confirmed_version'),'status':state['status'],
            'validation_status':latest.get('status'),'source_kind':(latest.get('source') or {}).get('source_kind'),
            'readback_attempt_id':rb.get('id'),'readback_version':rb.get('version'),'readback_digest':rb.get('text_digest'),
            'readback_attempt_count':attempts,'saved_address_count':saved,'trusted_evidence_count':len(state.get('evidence_history',[])),
            'assistant_transcript_exact_readback':exact,'synthesizer_input_contains_readback':bool(expected and expected in normalized(synth)),
            'LIVE_SPOKEN_READBACK':'PASS' if exact else 'NOT_VERIFIED','conversation_outcome':None}
        (args.run_dir/'readback-evidence.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
        print(json.dumps(output))
    except Exception:
        raise SystemExit('Readback evidence inspection failed; sensitive details withheld.') from None


if __name__=='__main__':
    main()
