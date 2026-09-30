"""Real PostgreSQL only. No SQLite substitute; opt in with TEST_DATABASE_URL."""
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from uuid import uuid4
import pytest
from sqlalchemy import select, func, event, insert, update
from sqlalchemy.exc import IntegrityError, ProgrammingError
from fastapi.testclient import TestClient
from app.database import make_engine, addresses, sessions, call_events, versions
from app.repository import Repository, ServiceError
from app.settings import Settings
from app.api import create_app
from app.domain.address import AddressChanges
from app.domain.session import update_candidate, record_validation
from app.domain.confirmation import prepare_readback, complete_readback, confirm_address
from test_validation_engine import SyntheticDirectory
from test_normalization_transition import provenance
from app.validation.engine import validate_address
from app.validation.models import ValidationPolicy

pytestmark = pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL'), reason='Real PostgreSQL not configured')


@pytest.fixture
def repo():
    engine = make_engine(os.environ['TEST_DATABASE_URL'])
    yield Repository(engine)
    engine.dispose()


def new(repo):
    return repo.create('customer-'+str(uuid4()), 'execution-'+str(uuid4()))


def test_demo_csv_validation_readback_keeps_confirmation_closed(repo,tmp_path):
    from test_demo_postal import fixture_csv
    cfg=Settings(app_env='development',allow_unverified_postal_data=True,
        postal_data_path=str(fixture_csv(tmp_path)),admin_token='a'*40,evidence_token='e'*40)
    client=TestClient(create_app(cfg,repository=repo))
    s,token=new(repo)
    base=f'/v1/address-sessions/{s.session_id}'
    auth={'Authorization':'Bearer '+token}
    response=client.patch(base+'/candidate',headers=auth,json={'expected_version':0,'changes':{
        'house_flat':'TEST-1','area':'Area','city':'City','pincode':'500032','state':'Example State'}})
    assert response.status_code==200
    response=client.post(base+'/validate',headers=auth,json={'expected_version':1})
    assert response.status_code==200 and response.json()['validated_version']==1
    state=repo.get(s.session_id,token)
    assert state.validation_attempts[-1].source.source_kind=='UNVERIFIED_OR_STALE'
    assert state.validation_attempts[-1].source.source_date is None
    assert client.post(base+'/readback',headers=auth,json={'expected_version':1}).status_code==200
    response=client.post(base+'/evidence',headers={'Authorization':'Bearer '+cfg.evidence_token},
        json={'expected_version':1,'kind':'READBACK_COMPLETED','reference':'untrusted-agent-assertion'})
    assert response.status_code==409 and response.json()['error']['code']=='EVIDENCE_UNAVAILABLE'
    assert client.post(base+'/save',headers=auth,json={'expected_version':1}).status_code==409
    response=client.patch(base+'/candidate',headers=auth,json={'expected_version':1,'changes':{'house_flat':'TEST-2'}})
    assert response.status_code==200 and response.json()['validated_version'] is None
    assert repo.get(s.session_id,token).readback is None


def test_rendered_bolna_mapping_reaches_postgres_without_losing_quotes(repo):
    import json
    from app.integrations.bolna import build_tools
    from test_bolna_tools import bolna_request_body
    s, token = new(repo)
    tool = next(t for t in build_tools('https://backend.example',s.session_id,token) if t['name']=='update_address')
    changes = {'house_flat':'TEST-1','building':'Example "North" Apartments'}
    body = bolna_request_body(tool['value']['param'],{'version':'0','changes_json':json.dumps(changes)})
    client = TestClient(create_app(Settings(),repository=repo))
    response = client.post(f'/v1/address-sessions/{s.session_id}/tool',
        headers={'Authorization':tool['value']['api_token']},json=body)
    assert response.status_code == 200
    assert response.json()['current_version'] == 1
    assert repo.get(s.session_id,token).versions[-1].raw.building == changes['building']


def confirmed(repo, verifier):
    s, token = new(repo)
    s = repo.mutate(s.session_id, token, 0, lambda s: update_candidate(s, 0, AddressChanges(
        house_flat='1', area='Locality', city='City', pincode='500032', state='Telangana')))
    s = repo.mutate(s.session_id, token, 1, lambda s: record_validation(s, validate_address(
        s.versions[-1], SyntheticDirectory(), ValidationPolicy(), date(2026, 9, 30), uuid4())))
    s = repo.mutate(s.session_id, token, 1, lambda s: prepare_readback(s, uuid4()))
    ref = verifier.issue(s, 'READBACK_COMPLETED', 1)
    s = repo.mutate(s.session_id, token, 1, lambda s: complete_readback(s, ref, verifier))
    ref = verifier.issue(s, 'CUSTOMER_CONFIRMED', 2)
    s = repo.mutate(s.session_id, token, 1, lambda s: confirm_address(s, 1, True, ref, verifier))
    return s, token


def test_actual_postgres_health_ownership_and_concurrency(repo):
    assert repo.ready()
    s, token = new(repo)
    with pytest.raises(ServiceError, match='FORBIDDEN'):
        repo.get(s.session_id, 'wrong credential')
    def change(value):
        try:
            return repo.mutate(s.session_id, token, 0, lambda s: update_candidate(s, 0, AddressChanges(house_flat=value))).current_version
        except ServiceError as exc:
            return exc.code
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(change, ['302', '320']))
    assert sorted(map(str, results)) == ['1', 'VERSION_CONFLICT']
    repo.engine.dispose()
    assert repo.get(s.session_id, token).current_version == 1


def test_database_foreign_keys_uniqueness_and_immutable_privileges(repo):
    s, token = new(repo)
    s = repo.mutate(s.session_id,token,0,lambda s:update_candidate(s,0,AddressChanges(house_flat='1')))
    row = dict(id=uuid4(),session_id=s.session_id,version=1,raw_address={},canonical_address={},field_origins=[],metadata={})
    with pytest.raises(IntegrityError):
        with repo.engine.begin() as conn:
            conn.execute(insert(versions).values(**row))
    row.update(id=uuid4(),session_id=uuid4())
    with pytest.raises(IntegrityError):
        with repo.engine.begin() as conn:
            conn.execute(insert(versions).values(**row))
    with pytest.raises(ProgrammingError):
        with repo.engine.begin() as conn:
            conn.execute(update(versions).where(versions.c.session_id==s.session_id).values(canonical_address={}))


def test_execution_binding_is_privileged_one_time_before_address_updates(repo):
    s, token = repo.create('link-'+str(uuid4()), 'pending-'+str(uuid4()))
    bound = repo.link_execution(s.session_id, 'real-'+str(uuid4()))
    assert bound.bolna_execution_id.startswith('real-')
    assert repo.get(s.session_id, token).bolna_execution_id == bound.bolna_execution_id
    with pytest.raises(ServiceError, match='EXECUTION_ALREADY_BOUND'):
        repo.link_execution(s.session_id, 'other')


def test_concurrent_save_idempotence_and_correction(repo, verifier):
    s, token = confirmed(repo, verifier)
    def save(_):
        return repo.mutate(s.session_id, token, 1, lambda s: s, save=True).current_saved_address_id
    with ThreadPoolExecutor(2) as pool:
        ids = list(pool.map(save, range(2)))
    assert ids[0] == ids[1]
    with repo.engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(addresses).where(addresses.c.source_session_id == s.session_id)).scalar() == 1
    assert repo.accepted_address(s.session_id, token)['canonical_address']['house_flat'] == '1'
    repo.mutate(s.session_id, token, 1, lambda s: update_candidate(s, 1, AddressChanges(house_flat='2')))
    with pytest.raises(ServiceError, match='ADDRESS_NOT_SAVED'):
        repo.accepted_address(s.session_id, token)


def test_save_commit_failure_rolls_back(repo, verifier):
    s, token = confirmed(repo, verifier)
    def fail(conn):
        raise RuntimeError('simulated commit failure')
    event.listen(repo.engine, 'commit', fail)
    try:
        with pytest.raises(RuntimeError):
            repo.mutate(s.session_id, token, 1, lambda s: s, save=True)
    finally:
        event.remove(repo.engine, 'commit', fail)
    assert repo.get(s.session_id, token).current_saved_address_id is None
    with repo.engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(addresses).where(addresses.c.source_session_id == s.session_id)).scalar() == 0


def test_api_workflow_security_and_webhooks(repo, verifier):
    cfg = Settings(admin_token='a'*40, webhook_token='w'*40, evidence_token='e'*40)
    app = create_app(cfg, repository=repo, directory=SyntheticDirectory(), evidence_verifier=verifier)
    c = TestClient(app)
    execution = 'execution-'+str(uuid4())
    created = c.post('/v1/address-sessions', headers={'Authorization':'Bearer '+cfg.admin_token},
        json={'customer_external_id':'test-'+str(uuid4()), 'bolna_execution_id':execution})
    assert created.status_code == 201
    sid, token = created.json()['session_id'], created.json()['call_token']
    base, auth = '/v1/address-sessions/'+sid, {'Authorization':'Bearer '+token}
    assert c.get(base, headers={'Authorization':'Bearer '+cfg.admin_token}).status_code == 403
    r = c.patch(base+'/candidate', headers=auth, json={'expected_version':0,'changes':{
        'house_flat':"1'; DROP TABLE customers;--",'area':'Area','city':'City','pincode':'५०००३२'}})
    assert r.status_code == 200
    assert c.post(base+'/validate', headers=auth,json={'expected_version':1}).json()['current_version'] == 2
    assert c.post(base+'/readback', headers=auth,json={'expected_version':2}).status_code == 200
    assert c.post(base+'/save',headers=auth,json={'expected_version':2}).status_code == 409
    assert c.post(base+'/evidence',headers=auth,json={'expected_version':2,'kind':'CUSTOMER_CONFIRMED','reference':'fake'}).status_code == 401
    for kind, seq in [('READBACK_COMPLETED',1),('CUSTOMER_CONFIRMED',2)]:
        s = repo.get(__import__('uuid').UUID(sid), token)
        ref = verifier.issue(s, kind, seq)
        r = c.post(base+'/evidence',headers={'Authorization':'Bearer '+cfg.evidence_token},
            json={'expected_version':2,'kind':kind,'reference':ref})
        assert r.status_code == 200
    assert c.post(base+'/save',headers=auth,json={'expected_version':2}).json()['backend_outcome'] == 'ADDRESS_SAVED'
    assert c.get(base+'/address',headers=auth).status_code == 200
    assert c.patch(base+'/candidate',headers=auth,json={'expected_version':2,'changes':{'house_flat':'320'}}).status_code == 200
    assert c.post(base+'/save',headers=auth,json={'expected_version':3}).status_code == 409
    wh = {'Authorization':'Bearer '+cfg.webhook_token}
    payload = {'execution_id':execution,'status':'completed','event_id':'done'}
    assert c.post('/v1/webhooks/bolna',headers=auth,json=payload).status_code == 401
    assert c.post('/v1/webhooks/bolna',headers=wh,json=payload).json()['duplicate'] is False
    assert c.post('/v1/webhooks/bolna',headers=wh,json=payload).json()['duplicate'] is True
    c.post('/v1/webhooks/bolna',headers=wh,json={'execution_id':execution,'status':'ringing'})
    with repo.engine.connect() as conn:
        assert conn.execute(select(sessions.c.call_status).where(sessions.c.bolna_execution_id == execution)).scalar() == 'completed'
    assert c.post('/v1/webhooks/bolna',headers=wh,json={'execution_id':'unknown','status':'completed'}).status_code == 404
    assert c.patch(base+'/candidate', headers=auth, content='{').status_code == 400
    assert c.patch(base+'/candidate', headers=auth, json={'expected_version':3,'changes':{'house_flat':'x'*101}}).status_code == 422
    assert c.patch(base+'/candidate', headers=auth, json={'expected_version':3,'changes':{'bogus':'private'}}).status_code == 422
