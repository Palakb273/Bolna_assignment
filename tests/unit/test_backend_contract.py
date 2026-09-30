from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.api import create_app
from app.settings import Settings


def client():
    return TestClient(create_app(Settings(admin_token='a'*40)))


def test_liveness_and_unconfigured_readiness():
    c = client()
    assert c.get('/health/live').status_code == 200
    assert c.get('/health/ready').status_code == 503


def test_authentication_precedes_mutation():
    c = client()
    assert c.post('/v1/address-sessions', json={}).status_code == 401
    assert c.patch(f'/v1/address-sessions/{uuid4()}/candidate', json={}).status_code == 401


def test_errors_do_not_echo_inputs():
    c = client()
    r = c.post('/v1/address-sessions', headers={'Authorization': 'Bearer '+ 'a'*40},
               json={'unexpected': 'private customer text'})
    assert r.status_code == 422
    assert 'private customer text' not in r.text
