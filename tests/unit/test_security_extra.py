import logging
import json
from uuid import uuid4
from fastapi.testclient import TestClient
from app.api import create_app
from app.settings import Settings


def test_request_diagnostics_include_early_rejection_without_payload(caplog):
    c = TestClient(create_app(Settings()))
    sid = str(uuid4())
    with caplog.at_level(logging.INFO, logger='address_backend'):
        response = c.post('/v1/address-sessions/'+sid+'/tool', json={'action':'update_address','changes_json':'PRIVATE_ADDRESS'})
        assert response.status_code == 401
        response = c.post('/v1/address-sessions/'+sid+'/tool', headers={'Authorization':'Bearer '+'SECRET'*8},
                          json={'action':'update_address','version':False,'changes_json':'PRIVATE_ADDRESS'})
        assert response.status_code == 422
    records = [json.loads(r.message) for r in caplog.records if r.name == 'address_backend']
    assert [(r['status'], r['error_reason']) for r in records] == [(401,'UNAUTHORIZED'),(422,'INVALID_INPUT')]
    assert all(r['session_id'] == sid and r['request_id'] for r in records)
    assert records[-1]['tool_name'] == 'update_address'
    assert 'PRIVATE_ADDRESS' not in caplog.text and 'SECRET' not in caplog.text


def test_oversized_body_and_secret_safe_errors(caplog):
    c = TestClient(create_app(Settings(admin_token='a'*40)))
    auth = {'Authorization':'Bearer '+'private-token'*5}
    with caplog.at_level(logging.INFO, logger='address_backend'):
        assert c.patch('/v1/address-sessions/'+str(uuid4())+'/candidate', headers=auth, content='x'*65537).status_code == 413
        response = c.patch('/v1/address-sessions/'+str(uuid4())+'/candidate',headers=auth,
                           json={'expected_version':0,'changes':{'house_flat':'SECRET_CUSTOMER','extra':'invalid'}})
        assert response.status_code == 422
    assert 'SECRET_CUSTOMER' not in caplog.text+response.text
    assert 'private-token' not in caplog.text+response.text


def test_rate_limit_and_no_boolean_confirmation_route(monkeypatch):
    monkeypatch.setattr('app.api.rate_window', lambda: 0)
    c = TestClient(create_app(Settings()))
    auth = {'Authorization':'Bearer '+'x'*40}
    url = '/v1/address-sessions/'+str(uuid4())
    for _ in range(120):
        c.get(url,headers=auth)
    assert c.get(url,headers=auth).status_code == 429
    assert c.post(url+'/confirm',headers={'Authorization':'Bearer '+'y'*40},json={'confirmed':True}).status_code == 404
