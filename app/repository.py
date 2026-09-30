import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from sqlalchemy import select, update, text
from sqlalchemy.dialects.postgresql import insert
from . import database as db
from .domain.session import Session, create_session, evolve
from .domain.confirmation import require_save_eligible, record_saved
from .observability import log_transition


class ServiceError(Exception):
    def __init__(self, code, status=409):
        self.code, self.status = code, status
        super().__init__(code)


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def now():
    return datetime.now(timezone.utc)


class Repository:
    def __init__(self, engine):
        self.engine = engine

    def ready(self):
        with self.engine.connect() as conn:
            conn.execute(select(db.sessions.c.id).limit(1))
            if conn.execute(text('SELECT rolsuper FROM pg_roles WHERE rolname = current_user')).scalar():
                return False
        return True

    def create(self, external_id, execution_id, name=None, phone=None):
        token = secrets.token_urlsafe(32)
        with self.engine.begin() as conn:
            customer = conn.execute(insert(db.customers).values(id=uuid4(), external_id=external_id,
                name=name, phone=phone).on_conflict_do_nothing(index_elements=['external_id']).returning(db.customers.c.id)).scalar()
            if customer is None:
                customer = conn.execute(select(db.customers.c.id).where(db.customers.c.external_id == external_id)).scalar_one()
            state = create_session(uuid4(), str(customer), execution_id)
            conn.execute(insert(db.sessions).values(id=state.session_id, customer_id=customer,
                bolna_execution_id=execution_id, status=state.status, current_version=0,
                state=state.model_dump(mode='json'), token_hash=digest(token), token_expires_at=now()+timedelta(hours=4)))
            self._project(conn, state, None, 'admin')
        log_transition(state, 'SESSION_CREATED')
        return state, token

    def _load(self, conn, session_id, token, lock=False, trusted=False):
        row = conn.execute(select(db.sessions).where(db.sessions.c.id == session_id)).mappings().first()
        if row is None:
            raise ServiceError('SESSION_NOT_FOUND', 404)
        if not trusted and (not token or not hmac.compare_digest(row['token_hash'], digest(token))
                            or row['token_expires_at'] < now()):
            raise ServiceError('FORBIDDEN', 403)
        if lock:
            # Same lock order for every mutation, including cross-session customer saves.
            conn.execute(select(db.customers.c.id).where(db.customers.c.id == row['customer_id']).with_for_update()).one()
            row = conn.execute(select(db.sessions).where(db.sessions.c.id == session_id).with_for_update()).mappings().one()
        return Session.model_validate_json(json.dumps(row['state']))

    def get(self, session_id, token):
        with self.engine.connect() as conn:
            return self._load(conn, session_id, token)

    def link_execution(self, session_id, execution_id):
        with self.engine.begin() as conn:
            s = self._load(conn, session_id, None, lock=True, trusted=True)
            if s.current_version != 0 or not s.bolna_execution_id.startswith('pending-'):
                raise ServiceError('EXECUTION_ALREADY_BOUND')
            values = s.model_dump(mode='json') | {'bolna_execution_id': execution_id}
            bound = Session.model_validate_json(json.dumps(values))
            bound = evolve(bound, 'EXECUTION_BOUND')
            self._project(conn,bound,s,'admin')
            conn.execute(update(db.sessions).where(db.sessions.c.id==session_id).values(
                bolna_execution_id=execution_id,state=bound.model_dump(mode='json'),updated_at=now()))
        log_transition(bound,'EXECUTION_BOUND')
        return bound

    def mutate(self, session_id, token, expected_version, operation, *, trusted=False, save=False):
        with self.engine.begin() as conn:
            old = self._load(conn, session_id, token, lock=True, trusted=trusted)
            if old.bolna_execution_id.startswith('pending-'):
                raise ServiceError('EXECUTION_NOT_BOUND')
            if expected_version != old.current_version:
                raise ServiceError('VERSION_CONFLICT')
            state = operation(old)
            if save:
                snapshot = require_save_eligible(state)
                existing = conn.execute(select(db.addresses.c.id).where(
                    db.addresses.c.source_session_id == session_id,
                    db.addresses.c.source_version == snapshot.version)).scalar()
                address_id = existing or uuid4()
                conn.execute(update(db.addresses).where(db.addresses.c.customer_id == old.customer_id,
                    db.addresses.c.id != address_id, db.addresses.c.superseded_at.is_(None)).values(superseded_at=now(), updated_at=now()))
                if existing is None:
                    conn.execute(insert(db.addresses).values(id=address_id, customer_id=old.customer_id,
                        source_session_id=session_id, source_version=snapshot.version,
                        canonical_address=snapshot.canonical.model_dump()))
                else:
                    conn.execute(update(db.addresses).where(db.addresses.c.id == address_id).values(superseded_at=None, updated_at=now()))
                state = record_saved(state, address_id, snapshot.version)
            if old.current_saved_address_id and state.current_saved_address_id is None:
                conn.execute(update(db.addresses).where(db.addresses.c.id == old.current_saved_address_id,
                    db.addresses.c.superseded_at.is_(None)).values(superseded_at=now(), updated_at=now()))
            self._project(conn, state, old, 'adapter' if trusted else 'call')
            conn.execute(update(db.sessions).where(db.sessions.c.id == session_id).values(
                state=state.model_dump(mode='json'), status=state.status, current_version=state.current_version,
                validated_version=state.validated_version, confirmed_version=state.confirmed_version, updated_at=now()))
        # Never report state until the transaction context has committed successfully.
        log_transition(state, state.audit_events[-1].operation)
        return state

    def _project(self, conn, state, old, actor):
        for version in state.versions[len(old.versions) if old else 0:]:
            conn.execute(insert(db.versions).values(id=uuid4(), session_id=state.session_id,
                version=version.version, raw_address=version.raw.model_dump(), canonical_address=version.canonical.model_dump(),
                field_origins=[o.model_dump(mode='json') for o in version.origins],
                metadata={'normalization_id': str(version.normalization_id) if version.normalization_id else None,
                          'policy_version': version.policy_version}))
        for v in state.validation_attempts[len(old.validation_attempts) if old else 0:]:
            conn.execute(insert(db.validations).values(id=uuid4(), session_id=state.session_id,
                attempt_id=v.attempt_id, address_version=v.version, status=v.status, reason_codes=list(v.reason_codes),
                missing_fields=list(v.missing_fields), conflicts=list(v.conflicts), warnings=list(v.warnings),
                policy_version=v.policy_version, field_origins=[o.model_dump(mode='json') for o in v.origins],
                postal_provenance=v.source.model_dump(mode='json') if v.source else None, data=v.model_dump(mode='json')))
        if old and old.readback and (state.readback is None or old.readback.id != state.readback.id):
            conn.execute(update(db.readbacks).where(db.readbacks.c.attempt_id == old.readback.id).values(status='INVALIDATED', interrupted_at=now()))
        if state.readback:
            r = state.readback
            conn.execute(insert(db.readbacks).values(id=uuid4(), session_id=state.session_id, attempt_id=r.id,
                execution_id=r.execution_id, address_version=r.version, validation_attempt_id=r.validation_attempt_id,
                rendered_text=r.rendered_text, text_digest=r.text_digest, status=state.status,
                completed_at=now() if r.completion else None).on_conflict_do_update(index_elements=['attempt_id'],
                    set_={'status': state.status, 'completed_at': now() if r.completion else None}))
        for e in state.evidence_history[len(old.evidence_history) if old else 0:]:
            conn.execute(insert(db.confirmations).values(id=uuid4(), session_id=state.session_id,
                evidence_id=e.evidence_id, execution_id=e.execution_id, address_version=e.version,
                validation_attempt_id=e.validation_attempt_id, readback_attempt_id=e.readback_id,
                outcome=e.kind, source='INDEPENDENT_ADAPTER', source_sequence=e.source_sequence, data=e.model_dump(mode='json')))
        for event in state.audit_events[len(old.audit_events) if old else 0:]:
            conn.execute(insert(db.audit).values(id=uuid4(), session_id=state.session_id, sequence=event.sequence,
                operation=event.operation, version=event.version, actor=actor,
                metadata={'reference_id': str(event.reference_id) if event.reference_id else None, 'reason': event.reason}))

    def accepted_address(self, session_id, token):
        with self.engine.connect() as conn:
            state = self._load(conn, session_id, token)
            row = conn.execute(select(db.addresses).where(db.addresses.c.id == state.current_saved_address_id,
                db.addresses.c.superseded_at.is_(None))).mappings().first()
            if row is None:
                raise ServiceError('ADDRESS_NOT_SAVED', 404)
            return {'address_id': str(row['id']), 'source_version': row['source_version'], 'canonical_address': row['canonical_address']}

    def webhook(self, execution_id, status, event_timestamp, event_id):
        with self.engine.begin() as conn:
            row = conn.execute(select(db.sessions).where(db.sessions.c.bolna_execution_id == execution_id).with_for_update()).mappings().first()
            if row is None:
                raise ServiceError('SESSION_NOT_FOUND', 404)
            key = digest(execution_id + ':' + event_id)
            added = conn.execute(insert(db.call_events).values(id=uuid4(), session_id=row['id'], event_id=key,
                execution_id=execution_id, event_type=status, event_timestamp=event_timestamp, metadata={})
                .on_conflict_do_nothing(index_elements=['event_id']).returning(db.call_events.c.id)).scalar()
            rank = {'created': 0, 'queued': 1, 'ringing': 2, 'in-progress': 3, 'completed': 4, 'failed': 4,
                    'busy': 4, 'no-answer': 4, 'canceled': 4}
            if added and rank[status] > rank[row['call_status']]:
                conn.execute(update(db.sessions).where(db.sessions.c.id == row['id']).values(call_status=status,
                    completed_at=now() if rank[status] == 4 else None, updated_at=now()))
        return {'received': True, 'duplicate': added is None}
