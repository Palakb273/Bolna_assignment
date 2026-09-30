"""PostgreSQL schema. Immutable domain histories are projected transactionally."""
from sqlalchemy import (MetaData, Table, Column, String, Integer, DateTime, ForeignKey,
                        UniqueConstraint, CheckConstraint, Index, text, create_engine, ForeignKeyConstraint)
from sqlalchemy.dialects.postgresql import JSONB, UUID

metadata = MetaData()


def identifier(name='id', **kwargs):
    return Column(name, UUID(as_uuid=True), **kwargs)


def timestamp(name):
    return Column(name, DateTime(timezone=True), nullable=False, server_default=text('now()'))


customers = Table('customers', metadata, identifier(primary_key=True),
    Column('external_id', String(200), unique=True, nullable=False), Column('name', String(200)),
    Column('phone', String(30)), timestamp('created_at'), timestamp('updated_at'))
sessions = Table('address_sessions', metadata, identifier(primary_key=True),
    identifier('customer_id', nullable=False), Column('bolna_execution_id', String(200), nullable=False, unique=True),
    Column('status', String(40), nullable=False), Column('current_version', Integer, nullable=False),
    Column('validated_version', Integer), Column('confirmed_version', Integer),
    Column('state', JSONB, nullable=False), Column('token_hash', String(64), nullable=False),
    Column('token_expires_at', DateTime(timezone=True), nullable=False),
    Column('call_status', String(30), nullable=False, server_default='created'),
    timestamp('created_at'), timestamp('updated_at'), Column('completed_at', DateTime(timezone=True)),
    ForeignKeyConstraint(['customer_id'], ['customers.id']),
    CheckConstraint('current_version >= 0'),
    CheckConstraint('validated_version IS NULL OR validated_version = current_version'),
    CheckConstraint('confirmed_version IS NULL OR confirmed_version = validated_version'))


def history(name, *columns, constraints=()):
    return Table(name, metadata, identifier(primary_key=True),
        Column('session_id', UUID(as_uuid=True), ForeignKey('address_sessions.id'), nullable=False),
        *columns, timestamp('created_at'), *constraints)


versions = history('address_versions', Column('version', Integer, nullable=False),
    Column('raw_address', JSONB, nullable=False), Column('canonical_address', JSONB, nullable=False),
    Column('field_origins', JSONB, nullable=False), Column('metadata', JSONB, nullable=False),
    constraints=(UniqueConstraint('session_id', 'version'), CheckConstraint('version > 0')))
validations = history('validation_attempts', identifier('attempt_id', nullable=False, unique=True),
    Column('address_version', Integer, nullable=False), Column('status', String(30), nullable=False),
    Column('reason_codes', JSONB, nullable=False), Column('missing_fields', JSONB, nullable=False),
    Column('conflicts', JSONB, nullable=False), Column('warnings', JSONB, nullable=False),
    Column('policy_version', String(100)), Column('field_origins', JSONB, nullable=False),
    Column('postal_provenance', JSONB), Column('data', JSONB, nullable=False))
readbacks = history('readback_attempts', identifier('attempt_id', nullable=False, unique=True),
    Column('execution_id', String(200), nullable=False), Column('address_version', Integer, nullable=False),
    identifier('validation_attempt_id', nullable=False), Column('rendered_text', String, nullable=False),
    Column('text_digest', String(64), nullable=False), Column('status', String(30), nullable=False),
    timestamp('prepared_at'), Column('completed_at', DateTime(timezone=True)),
    Column('interrupted_at', DateTime(timezone=True)))
confirmations = history('confirmation_events', identifier('evidence_id', nullable=False, unique=True),
    Column('execution_id', String(200), nullable=False), Column('address_version', Integer, nullable=False),
    identifier('validation_attempt_id', nullable=False), identifier('readback_attempt_id', nullable=False),
    Column('outcome', String(40), nullable=False), Column('source', String(40), nullable=False),
    Column('source_sequence', Integer, nullable=False), timestamp('observed_at'), Column('data', JSONB, nullable=False),
    constraints=(UniqueConstraint('execution_id', 'source_sequence'),))
addresses = Table('addresses', metadata, identifier(primary_key=True),
    Column('customer_id', UUID(as_uuid=True), ForeignKey('customers.id'), nullable=False),
    Column('source_session_id', UUID(as_uuid=True), ForeignKey('address_sessions.id'), nullable=False),
    Column('source_version', Integer, nullable=False), Column('canonical_address', JSONB, nullable=False),
    timestamp('confirmed_at'), Column('superseded_at', DateTime(timezone=True)), timestamp('created_at'), timestamp('updated_at'),
    UniqueConstraint('source_session_id', 'source_version'))
Index('one_current_address_per_customer', addresses.c.customer_id, unique=True,
      postgresql_where=addresses.c.superseded_at.is_(None))
call_events = history('call_events', Column('event_id', String(64), nullable=False, unique=True),
    Column('execution_id', String(200), nullable=False), Column('event_type', String(40), nullable=False),
    Column('event_timestamp', DateTime(timezone=True), nullable=False), Column('metadata', JSONB, nullable=False))
audit = history('audit_events', Column('sequence', Integer, nullable=False), Column('operation', String(40), nullable=False),
    Column('version', Integer, nullable=False), Column('actor', String(40), nullable=False),
    Column('metadata', JSONB, nullable=False), constraints=(UniqueConstraint('session_id', 'sequence'),))


def make_engine(url):
    if not url.startswith('postgresql+psycopg://'):
        raise ValueError('PostgreSQL psycopg URL required.')
    return create_engine(url, pool_pre_ping=True, hide_parameters=True,
                         connect_args={'connect_timeout': 5}, echo=False)
