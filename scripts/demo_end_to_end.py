"""OFFLINE_BOLNA_SIMULATION: real API/PostgreSQL; SYNTHETIC voice evidence only."""
import argparse
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from fastapi.testclient import TestClient
from sqlalchemy import select, func, text
from app.api import create_app
from app.settings import Settings
from app.demo_evidence import SyntheticDemoEvidenceVerifier
from app.domain.session import Session
from app.database import make_engine, sessions, versions, validations, readbacks, confirmations, addresses, audit


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run_demo(database_url, postal_path, *, emit=print, pin_input='1 1 0 0 0 1'):
    """All mutations use authenticated HTTP routes; SQL below is read-only."""
    cfg = Settings(database_url=database_url, app_env='development',
        allow_unverified_postal_data=True, postal_data_path=str(postal_path),
        admin_token=secrets.token_urlsafe(40), evidence_token=secrets.token_urlsafe(40))
    verifier = SyntheticDemoEvidenceVerifier(cfg.app_env)
    app = create_app(cfg, evidence_verifier=verifier)
    engine = make_engine(database_url)
    timeline = []
    requests = []
    emit('=' * 64)
    emit('BOLNA ADDRESS COLLECTOR - OFFLINE_BOLNA_SIMULATION')
    emit('Real FastAPI + PostgreSQL | SYNTHETIC evidence | no voice/network call')
    emit('Postal source: UNVERIFIED_OR_STALE - development/demo only')
    emit('=' * 64)
    sid = None
    def state():
        with engine.connect() as db:
            return Session.model_validate_json(json.dumps(db.execute(select(sessions.c.state).where(sessions.c.id == sid)).scalar_one()))
    def step(label, observed):
        timeline.append({'event':label, 'version':observed['current_version']})
        emit(f"[PASS] {label:43} v{observed['current_version']}")
    try:
        with engine.connect() as db:
            require(db.execute(text('SELECT 1')).scalar_one() == 1, 'PostgreSQL unavailable')
        emit('[PASS] PostgreSQL connected')
        with TestClient(app) as client:
            def request(path, body, credential, expected=200):
                response = client.post(path, json=body, headers={'Authorization':'Bearer '+credential})
                value = response.json()
                reason = (value.get('error') or {}).get('code')
                requests.append({'request_id':response.headers.get('x-request-id'),
                    'operation':body.get('action') or path.rsplit('/',1)[-1],
                    'http_status':response.status_code, 'reason':reason})
                require(response.status_code == expected, f'Unexpected HTTP {response.status_code}: {reason or "response mismatch"}')
                return value
            health = client.get('/health/ready').json()
            require(health['demo_runtime_ready'] and not health['trusted_runtime_ready'], 'Demo directory unavailable')
            execution = 'OFFLINE_BOLNA_SIMULATION-'+str(uuid4())
            first = request('/v1/address-sessions', {'customer_external_id':execution,
                'bolna_execution_id':'pending-'+str(uuid4())}, cfg.admin_token, 201)
            sid = UUID(first['session_id']); token = first['call_token']
            base = '/v1/address-sessions/'+str(sid)
            current = request(base+'/execution', {'bolna_execution_id':execution}, cfg.admin_token)
            require(current['current_version']==0, 'Session not pristine')
            step('Session created and execution bound', current)
            def tool(name, changes=None, expected=200):
                nonlocal current
                body={'action':name,'version':str(current['current_version'])}
                if changes is not None: body['changes_json']=json.dumps(changes)
                result=request(base+'/tool',body,token,expected)
                if expected==200: current=result
                return result
            for label,change in [('Premise supplied',{'house_flat':'B-302'}),
                ('Area supplied',{'area':'Connaught Place'}),
                ('City/state supplied',{'city':'New Delhi','state':'Delhi'}),
                ('PIN supplied',{'pincode':pin_input})]:
                before=current['current_version']; tool('update_address',change)
                require(current['current_version']==before+1,'Progressive version mismatch')
                step(label,current)
            def validate():
                tool('validate_address')
                require(current['validation']['status']=='VALID' and current['validated_version']==current['current_version'], 'Address not VALID')
                require(state().validation_attempts[-1].source.source_kind=='UNVERIFIED_OR_STALE','Incorrect source trust')
                step('Validated with demo postal data',current)
            validate()
            normalization_observed = any(x.operation=='CANONICAL_NORMALIZED' for x in state().audit_events)
            require(state().versions[-1].canonical.pincode=='110001','Canonical PIN mismatch')
            def readback():
                tool('prepare_address_readback')
                rb=state().readback
                require(str(rb.id)==current['readback_id'] and rb.rendered_text==current['text'], 'Readback response mismatch')
                require(rb.text_digest==sha256(rb.rendered_text.encode()).hexdigest(), 'Digest mismatch')
                require(rb.version==current['current_version'] and rb.validation_attempt_id==state().validation_attempt_id, 'Readback binding mismatch')
                step('Readback generated (TEXT ONLY)', current)
                emit('Generated offline readback: '+rb.rendered_text)
                return rb
            old=readback()
            old_completion=verifier.issue(old,'READBACK_COMPLETED',1)
            old_confirmation=verifier.issue(old,'CUSTOMER_CONFIRMED',2)
            emit('--- CUSTOMER CORRECTION: Actually the flat is B-320 ---')
            prior=current['current_version']; tool('update_address',{'house_flat':'B-320'})
            require(current['current_version']==prior+1 and current['validated_version'] is None
                and current['confirmed_version'] is None and state().readback is None,'Correction failed to invalidate prior acceptance')
            step('Correction; prior acceptance invalidated', current)
            stale_version=request(base+'/evidence',{'expected_version':prior,'kind':'CUSTOMER_CONFIRMED',
                'reference':old_confirmation},cfg.evidence_token,409)
            require(stale_version['error']['code']=='VERSION_CONFLICT','Old version was not rejected')
            step('Old version confirmation rejected',current)
            validate(); new=readback()
            require(old.id!=new.id and old.text_digest!=new.text_digest and old.version!=new.version,'Readback reused after correction')
            stale=request(base+'/evidence',{'expected_version':current['current_version'],
                'kind':'READBACK_COMPLETED','reference':old_completion},cfg.evidence_token,409)
            require(stale['error']['code']=='EVIDENCE_BINDING_MISMATCH','Stale binding not rejected')
            step('Old readback evidence rejected',current)
            premature=tool('save_address',expected=409)
            require(premature['error']['code']=='ADDRESS_NOT_CONFIRMED','Premature save guard mismatch')
            step('Premature save rejected',current)
            for kind,sequence in [('READBACK_COMPLETED',3),('CUSTOMER_CONFIRMED',4)]:
                if kind == 'CUSTOMER_CONFIRMED':
                    rejected=request(base+'/evidence',{'expected_version':current['current_version'],
                        'kind':kind,'reference':old_confirmation},cfg.evidence_token,409)
                    require(rejected['error']['code']=='EVIDENCE_BINDING_MISMATCH',
                        'Old confirmation accepted for corrected readback')
                    step('Stale confirmation binding rejected',current)
                reference=verifier.issue(new,kind,sequence)
                current=request(base+'/evidence',{'expected_version':current['current_version'],
                    'kind':kind,'reference':reference},cfg.evidence_token)
                step('SYNTHETIC '+kind,current)
            require(current['confirmed_version']==current['current_version'],'Confirmation mismatch')
            saved=tool('save_address');step('Address committed to PostgreSQL',current)
            duplicate=tool('save_address');step('Duplicate save idempotent',current)
            require(saved['address_id']==duplicate['address_id'],'Duplicate save changed ID')
            accepted=client.get(base+'/address',headers={'Authorization':'Bearer '+token})
            require(accepted.status_code==200,'Saved-address API unavailable')
            final=state()
            require(final.current_version==final.validated_version==final.confirmed_version,'Final version mismatch')
            with engine.connect() as db:
                counts={table.name:db.execute(select(func.count()).select_from(table).where(
                    (table.c.id==sid) if table is sessions else
                    (table.c.source_session_id==sid) if table is addresses else (table.c.session_id==sid))).scalar_one()
                    for table in (sessions,versions,validations,readbacks,confirmations,addresses,audit)}
                row=db.execute(select(addresses).where(addresses.c.source_session_id==sid)).mappings().one()
            require(counts['addresses']==1 and str(row['id'])==saved['address_id'],'Final row missing/duplicated')
            require(row['source_version']==final.current_version and row['canonical_address']['house_flat']=='B-320','Saved correction mismatch')
            result={'mode':'OFFLINE_BOLNA_SIMULATION','evidence_source':'SYNTHETIC',
                'postal_source':'UNVERIFIED_OR_STALE','test_result':'PASS','conversation_outcome':None,
                'completed_at':datetime.now(timezone.utc).isoformat(),'session_id':str(sid),'execution_id':execution,
                'current_version':final.current_version,'validated_version':final.validated_version,
                'confirmed_version':final.confirmed_version,'normalization_observed':normalization_observed,
                'stale_reason':stale['error']['code'],'old_version_reason':stale_version['error']['code'],
                'premature_save_reason':premature['error']['code'],'address_id':saved['address_id'],
                'duplicate_address_id':duplicate['address_id'],'source_session_id':str(row['source_session_id']),
                'source_version':row['source_version'],'counts':counts,'timeline':timeline,'requests':requests,
                'readbacks':[{'id':str(r.id),'validation_attempt_id':str(r.validation_attempt_id),
                    'version':r.version,'text_digest':r.text_digest,'rendered_text':r.rendered_text} for r in (old,new)],
                'audit':[{'operation':e.operation,'version':e.version,'sequence':e.sequence} for e in final.audit_events]}
            emit('FINAL: current = validated = confirmed = '+str(final.current_version))
            emit('Session-scoped database counts: '+json.dumps(counts))
            emit('source_session_id: '+str(sid)+'; source_version: '+str(row['source_version']))
            emit('[PASS] OFFLINE_BOLNA_SIMULATION complete; production consent/audio NOT proven')
            return result
    finally:
        engine.dispose()
        app.state.repository.engine.dispose()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verbose',action='store_true')
    parser.add_argument('--postal-data',type=Path,default=ROOT/'local-data/postal/demo-pincodes.json')
    parser.add_argument('--output',type=Path,default=ROOT/'local-data/offline-demo/evidence.json')
    args=parser.parse_args()
    if os.getenv('APP_ENV')=='production':
        raise SystemExit('Offline demo refuses APP_ENV=production. Use a development database/environment.')
    values={}
    local=ROOT/'local-data/development.env'
    if local.exists():
        values=dict(line.split('=',1) for line in local.read_text().splitlines() if '=' in line)
    url=os.getenv('DATABASE_URL') or values.get('DATABASE_URL','')
    if not url:
        raise SystemExit('Configure a development DATABASE_URL or run scripts/init_local_config.py first.')
    try:
        result=run_demo(url,args.postal_data)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
        if args.verbose:
            print('Actual database audit:')
            for event in result['audit']: print(f"  {event['sequence']:2} {event['operation']:24} v{event['version']}")
        print('Sanitized evidence: '+str(args.output.resolve()))
    except Exception:
        raise SystemExit('Offline demo FAILED. Verify development PostgreSQL/migrations and demo postal data. Sensitive details withheld.') from None


if __name__=='__main__':
    main()

