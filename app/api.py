import hashlib
import hmac
import json
import logging
import time
from collections import OrderedDict
from datetime import date, datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Literal
from uuid import UUID, uuid4
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from .settings import Settings
from .database import make_engine
from .repository import Repository, ServiceError
from .domain.address import AddressChanges, NormalizationProposal
from .domain.session import update_candidate, record_validation, apply_normalization
from .domain.confirmation import (prepare_readback, complete_readback, confirm_address,
    invalidate_readback, RejectAllEvidenceVerifier)
from .domain.errors import DomainError
from .validation.models import ValidationPolicy
from .validation.postal_directory import load_directory
from .validation.demo_postal import select_directory
from .validation.engine import validate_address
from .observability import request_id as request_id_context

logger = logging.getLogger('address_backend')


def rate_window():
    return int(time.monotonic() // 60)


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)


class CreateSession(Input):
    customer_external_id: str = Field(min_length=1, max_length=200, pattern=r'^[A-Za-z0-9_.:-]+$')
    bolna_execution_id: str = Field(min_length=1, max_length=200, pattern=r'^[A-Za-z0-9_.:-]+$')
    name: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, pattern=r'^\+[1-9][0-9]{7,14}$')


class VersionRequest(Input):
    expected_version: StrictInt = Field(ge=0)


class LinkExecutionRequest(Input):
    bolna_execution_id: str = Field(min_length=1, max_length=200, pattern=r'^[A-Za-z0-9_.:-]+$')


class CandidateRequest(VersionRequest):
    changes: AddressChanges


class ReadbackRequest(VersionRequest):
    language: Literal['en','hi'] = 'en'


class EvidenceRequest(VersionRequest):
    reference: str = Field(min_length=1, max_length=500)
    kind: Literal['READBACK_COMPLETED', 'CUSTOMER_CONFIRMED']


class InterruptRequest(VersionRequest):
    reason: Literal['INTERRUPTED', 'REJECTED', 'UNCERTAIN']


class ToolRequest(Input):
    action: Literal['get_address_session','update_address','validate_address','prepare_address_readback',
                    'interrupt_address_readback','request_address_confirmation','save_address']
    version: str = Field(pattern=r'^[0-9]{1,9}$')
    changes_json: str | None = Field(default=None, max_length=6000)
    language: Literal['en','hi'] = 'en'


def view(state):
    result = {'session_id': str(state.session_id), 'status': state.status,
        'current_version': state.current_version, 'validated_version': state.validated_version,
        'confirmed_version': state.confirmed_version}
    if state.validation_attempts:
        v = state.validation_attempts[-1]
        result['validation'] = {'status': v.status, 'reason_codes': v.reason_codes,
            'missing_fields': v.missing_fields, 'conflicts': v.conflicts, 'warnings': v.warnings, 'next_action': v.next_action}
    return result


def create_app(settings=None, *, repository=None, directory=None, evidence_verifier=None):
    settings = settings or Settings.from_env()
    if settings.app_env == 'production' and getattr(evidence_verifier, 'nonproduction_only', False):
        raise ValueError('Synthetic demo evidence is forbidden in production')
    repo = repository or (Repository(make_engine(settings.database_url)) if settings.database_url else None)
    policy = ValidationPolicy(max_source_age_days=settings.max_postal_source_age_days)
    directory = directory if directory is not None else select_directory(settings, policy, date.today())
    verifier = evidence_verifier or RejectAllEvidenceVerifier()
    app = FastAPI(title='Address collection backend', version='1.0.0')
    app.state.repository = repo
    buckets, bucket_lock = OrderedDict(), Lock()

    def require_repo():
        if repo is None:
            raise ServiceError('BACKEND_UNAVAILABLE', 503)
        return repo

    def token(request):
        return request.state.token

    def secret_matches(value, secret):
        return len(secret) >= 32 and hmac.compare_digest(value, secret)

    @app.middleware('http')
    async def guard(request: Request, call_next):
        request_id = request.state.diagnostic_id
        request_id_context.set(request_id)
        path = request.url.path
        credential = request.headers.get('authorization', '')
        request.state.token = credential[7:] if credential.startswith('Bearer ') else ''
        if path.startswith('/v1/'):
            if not request.state.token:
                return JSONResponse({'error': {'code': 'UNAUTHORIZED'}, 'request_id': request_id}, status_code=401)
            needed = None
            if path == '/v1/address-sessions' and request.method == 'POST':
                needed = settings.admin_token
            elif path.endswith('/execution'):
                needed = settings.admin_token
            elif path == '/v1/webhooks/bolna':
                needed = settings.webhook_token
            elif path.endswith('/evidence'):
                needed = settings.evidence_token
            if needed is not None and not secret_matches(request.state.token, needed):
                return JSONResponse({'error': {'code': 'UNAUTHORIZED'}, 'request_id': request_id}, status_code=401)
            key = hashlib.sha256(request.state.token.encode()).hexdigest()
            minute = rate_window()
            with bucket_lock:
                previous, count = buckets.get(key, (minute, 0))
                count = count + 1 if previous == minute else 1
                buckets[key] = (minute, count)
                buckets.move_to_end(key)
                while len(buckets) > 10000:
                    buckets.popitem(last=False)
            if count > 120:
                return JSONResponse({'error': {'code': 'RATE_LIMITED'}}, status_code=429)
            chunks, size = [], 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > 65536:
                    return JSONResponse({'error': {'code': 'REQUEST_TOO_LARGE'}}, status_code=413)
                chunks.append(chunk)
            request._body = b''.join(chunks)
            if request._body:
                try:
                    parsed_body = json.loads(request._body)
                    if isinstance(parsed_body, dict) and parsed_body.get('action') in ToolRequest.model_fields['action'].annotation.__args__:
                        request.state.tool_name = parsed_body['action']
                except (ValueError, UnicodeError):
                    return JSONResponse({'error': {'code': 'MALFORMED_REQUEST'}}, status_code=400)
        try:
            response = await call_next(request)
        except Exception:
            response = JSONResponse({'error': {'code': 'BACKEND_UNAVAILABLE'}}, status_code=503)
        response.headers['X-Request-ID'] = request_id
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.middleware('http')
    async def request_diagnostics(request: Request, call_next):
        request.state.diagnostic_id = str(uuid4())
        request.state.tool_name = None
        request.state.execution_id = None
        request.state.error_reason = None
        session_id = None
        parts = request.url.path.split('/')
        if len(parts) >= 4 and parts[1:3] == ['v1', 'address-sessions']:
            try:
                session_id = str(UUID(parts[3]))
            except ValueError:
                pass
        response = await call_next(request)
        reason = request.state.error_reason
        if reason is None and response.status_code >= 400:
            reason = {400:'MALFORMED_REQUEST',401:'UNAUTHORIZED',403:'FORBIDDEN',404:'NOT_FOUND',
                      409:'STATE_CONFLICT',413:'REQUEST_TOO_LARGE',422:'INVALID_INPUT',
                      429:'RATE_LIMITED',503:'BACKEND_UNAVAILABLE'}.get(response.status_code, 'REQUEST_FAILED')
        response.headers['X-Request-ID'] = request.state.diagnostic_id
        response.headers['Cache-Control'] = 'no-store'
        logger.info(json.dumps({'request_id': request.state.diagnostic_id,
            'tool_name': request.state.tool_name, 'status': response.status_code,
            'session_id': session_id, 'execution_id': request.state.execution_id, 'error_reason': reason}))
        return response

    @app.exception_handler(ServiceError)
    async def service_error(request, exc):
        request.state.error_reason = exc.code
        return JSONResponse({'error': {'code': exc.code}}, status_code=exc.status)

    @app.exception_handler(DomainError)
    async def domain_error(request, exc):
        code = 'VERSION_CONFLICT' if exc.code == 'ADDRESS_VERSION_CHANGED' else exc.code
        request.state.error_reason = code
        return JSONResponse({'error': {'code': code}}, status_code=409)

    @app.exception_handler(RequestValidationError)
    async def input_error(request, exc):
        malformed = any(e['type'] == 'json_invalid' for e in exc.errors())
        return JSONResponse({'error': {'code': 'MALFORMED_REQUEST' if malformed else 'INVALID_INPUT'}}, status_code=400 if malformed else 422)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        return JSONResponse({'error': {'code': 'STATE_CONFLICT' if isinstance(exc, IntegrityError) else 'BACKEND_UNAVAILABLE'}},
                            status_code=409 if isinstance(exc, IntegrityError) else 503)

    @app.get('/health/live')
    def live():
        return {'live': True}

    @app.get('/health/ready')
    def ready():
        try:
            # Reload to recheck source age rather than cache a once-ready stale dataset forever.
            postal = select_directory(settings, policy, date.today())
            backend_ok = bool(repo and repo.ready() and len(settings.admin_token) >= 32)
            trusted = bool(backend_ok and postal.trusted_runtime_ready)
            demo = bool(backend_ok and postal.demo_runtime_ready)
            ok = trusted
        except Exception:
            ok = False
            trusted = demo = False
        return JSONResponse({'ready': ok,'trusted_runtime_ready':trusted,'demo_runtime_ready':demo}, status_code=200 if ok else 503)

    @app.post('/v1/address-sessions', status_code=201)
    def create(body: CreateSession):
        state, credential = require_repo().create(body.customer_external_id, body.bolna_execution_id, body.name, body.phone)
        return view(state) | {'call_token': credential, 'token_ttl_seconds': 14400}

    @app.get('/v1/address-sessions/{session_id}')
    def get_session(session_id: UUID, request: Request):
        return view(require_repo().get(session_id, token(request)))

    @app.post('/v1/address-sessions/{session_id}/execution')
    def link_execution(session_id: UUID, body: LinkExecutionRequest):
        return view(require_repo().link_execution(session_id, body.bolna_execution_id))

    @app.patch('/v1/address-sessions/{session_id}/candidate')
    def patch(session_id: UUID, body: CandidateRequest, request: Request):
        return view(require_repo().mutate(session_id, token(request), body.expected_version,
            lambda s: update_candidate(s, body.expected_version, body.changes)))

    @app.post('/v1/address-sessions/{session_id}/validate')
    def validate(session_id: UUID, body: VersionRequest, request: Request):
        def operation(s):
            if not s.versions:
                raise ServiceError('ADDRESS_INCOMPLETE', 422)
            for _ in range(2):
                outcome = validate_address(s.versions[-1], directory, policy, date.today(), uuid4())
                if isinstance(outcome, NormalizationProposal):
                    outcome = NormalizationProposal(**(outcome.model_dump() | {'session_id': s.session_id}))
                    s = apply_normalization(s, s.current_version, outcome)
                else:
                    return record_validation(s, outcome)
            raise ServiceError('VALIDATION_ERROR', 503)
        s = require_repo().mutate(session_id, token(request), body.expected_version, operation)
        return JSONResponse(view(s), status_code=503 if s.status == 'VALIDATION_ERROR' else 200)

    @app.post('/v1/address-sessions/{session_id}/readback')
    def readback(session_id: UUID, body: ReadbackRequest, request: Request):
        s = require_repo().mutate(session_id, token(request), body.expected_version, lambda s: prepare_readback(s, uuid4(), body.language))
        return view(s) | {'readback_id': str(s.readback.id), 'text': s.readback.rendered_text, 'text_digest': s.readback.text_digest}

    @app.post('/v1/address-sessions/{session_id}/interrupt')
    def interrupt(session_id: UUID, body: InterruptRequest, request: Request):
        return view(require_repo().mutate(session_id, token(request), body.expected_version,
            lambda s: invalidate_readback(s, body.reason)))

    @app.post('/v1/address-sessions/{session_id}/confirmation-request')
    def confirmation_request(session_id: UUID, body: VersionRequest, request: Request):
        s = require_repo().get(session_id, token(request))
        if s.current_version != body.expected_version:
            raise ServiceError('VERSION_CONFLICT')
        return view(s) | {'next_action': 'AWAIT_TRUSTED_EVIDENCE', 'confirmation_recorded': False}

    @app.post('/v1/address-sessions/{session_id}/evidence')
    def evidence(session_id: UUID, body: EvidenceRequest):
        def operation(s):
            if body.kind == 'READBACK_COMPLETED':
                return complete_readback(s, body.reference, verifier)
            return confirm_address(s, s.current_version, True, body.reference, verifier)
        return view(require_repo().mutate(session_id, None, body.expected_version, operation, trusted=True))

    @app.post('/v1/address-sessions/{session_id}/save')
    def save(session_id: UUID, body: VersionRequest, request: Request):
        s = require_repo().mutate(session_id, token(request), body.expected_version, lambda s: s, save=True)
        return view(s) | {'backend_outcome': 'ADDRESS_SAVED', 'address_id': str(s.current_saved_address_id)}

    @app.get('/v1/address-sessions/{session_id}/address')
    def address(session_id: UUID, request: Request):
        return require_repo().accepted_address(session_id, token(request))

    @app.post('/v1/webhooks/bolna')
    async def webhook(request: Request):
        try:
            body = await request.json()
            execution = body['execution_id'] if 'execution_id' in body else body['id']
            status = body['status']
            if not isinstance(execution, str) or not 1 <= len(execution) <= 200:
                raise ValueError()
            if status not in {'queued', 'ringing', 'in-progress', 'completed', 'failed', 'busy', 'no-answer', 'canceled'}:
                raise ValueError()
            timestamp = datetime.fromisoformat(body['event_timestamp'].replace('Z', '+00:00')) if body.get('event_timestamp') else datetime.now(timezone.utc)
            if timestamp.utcoffset() is None:
                raise ValueError()
            event_id = body.get('event_id') or hashlib.sha256((execution+':'+status).encode()).hexdigest()
            if not isinstance(event_id, str) or len(event_id) > 200:
                raise ValueError()
        except Exception:
            raise ServiceError('MALFORMED_REQUEST', 400) from None
        return require_repo().webhook(execution, status, timestamp, event_id)

    @app.post('/v1/address-sessions/{session_id}/tool')
    def tool(session_id: UUID, body: ToolRequest, request: Request):
        bound = require_repo().get(session_id, token(request))
        request.state.execution_id = bound.bolna_execution_id
        version = VersionRequest(expected_version=int(body.version))
        if body.action == 'get_address_session':
            return get_session(session_id, request)
        if body.action == 'update_address':
            try:
                changes = AddressChanges.model_validate_json(body.changes_json or '{}')
            except Exception:
                raise ServiceError('INVALID_INPUT', 422) from None
            return patch(session_id, CandidateRequest(expected_version=version.expected_version, changes=changes), request)
        if body.action == 'validate_address':
            return validate(session_id, version, request)
        if body.action == 'prepare_address_readback':
            return readback(session_id, ReadbackRequest(expected_version=version.expected_version, language=body.language), request)
        if body.action == 'interrupt_address_readback':
            return interrupt(session_id, InterruptRequest(expected_version=version.expected_version, reason='INTERRUPTED'), request)
        if body.action == 'request_address_confirmation':
            return confirmation_request(session_id, version, request)
        return save(session_id, version, request)

    return app
