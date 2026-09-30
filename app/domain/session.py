"""Immutable session transitions; callers are trusted internal application code."""

import re
import unicodedata
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, StrictInt, field_validator, model_validator

from .address import Address, AddressChanges, AddressVersion, FrozenModel, NormalizationProposal, apply_changes
from .validation_metadata import FieldOrigin, PostalDataProvenance, ConflictDetail
from .errors import DomainError

PositiveVersion = Annotated[StrictInt, Field(gt=0)]
AddressField = Literal['house_flat', 'building', 'street', 'area', 'landmark', 'city', 'district', 'state', 'pincode']
Status = Literal['COLLECTING', 'CANDIDATE_UPDATED', 'NEEDS_CLARIFICATION', 'VALIDATION_ERROR',
                 'READY_FOR_READBACK', 'READ_BACK', 'WAITING_CONFIRMATION', 'CONFIRMED', 'SAVED']


class ValidationResult(FrozenModel):
    version: PositiveVersion
    attempt_id: UUID
    status: Literal['VALID', 'NEEDS_CLARIFICATION', 'VALIDATION_ERROR']
    canonical: Address
    missing_fields: tuple[AddressField, ...] = ()
    conflicts: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    conflict_details: tuple[ConflictDetail, ...] = ()
    next_action: str | None = None
    policy_version: str | None = None
    source: PostalDataProvenance | None = None
    origins: tuple[FieldOrigin, ...] = ()

    @field_validator('conflicts', 'reason_codes', 'warnings')
    @classmethod
    def safe_codes(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not re.fullmatch(r'[A-Z][A-Z0-9_]{0,63}', value) for value in values):
            raise ValueError('Use bounded conflict codes only.')
        return values

    @model_validator(mode='after')
    def consistent_result(self) -> Self:
        if self.status == 'VALID' and (self.missing_fields or self.conflicts):
            raise ValueError('A valid result cannot contain missing fields or conflicts.')
        return self


class VerifiedEvidence(FrozenModel):
    """A verifier's trusted result, never an agent-facing request schema."""

    evidence_id: UUID
    kind: Literal['READBACK_COMPLETED', 'CUSTOMER_CONFIRMED']
    session_id: UUID
    execution_id: str = Field(min_length=1, max_length=200)
    version: PositiveVersion
    validation_attempt_id: UUID
    readback_id: UUID
    text_digest: str = Field(pattern=r'^[0-9a-f]{64}$')
    source_sequence: PositiveVersion


class ReadbackAttempt(FrozenModel):
    language: Literal['en', 'hi'] = 'en'
    id: UUID
    session_id: UUID
    execution_id: str
    version: PositiveVersion
    validation_attempt_id: UUID
    rendered_text: str
    text_digest: str
    completion: VerifiedEvidence | None = None
    confirmation: VerifiedEvidence | None = None


class SavedReference(FrozenModel):
    address_id: UUID
    source_version: PositiveVersion
    validation_attempt_id: UUID
    readback_id: UUID
    completion_evidence_id: UUID
    confirmation_evidence_id: UUID


class AuditEvent(FrozenModel):
    sequence: PositiveVersion
    operation: Literal['SESSION_CREATED', 'EXECUTION_BOUND', 'CANDIDATE_UPDATED', 'CANONICAL_NORMALIZED', 'VALIDATION_RECORDED', 'READBACK_PREPARED',
                       'READBACK_COMPLETED', 'CONFIRMED', 'READBACK_INVALIDATED', 'SAVE_RECORDED']
    version: Annotated[StrictInt, Field(ge=0)]
    reference_id: UUID | None = None
    reason: Literal['INTERRUPTED', 'REJECTED', 'UNCERTAIN'] | None = None


class Session(FrozenModel):
    session_id: UUID
    customer_id: str = Field(min_length=1, max_length=200)
    bolna_execution_id: str = Field(min_length=1, max_length=200)
    status: Status = 'COLLECTING'
    versions: tuple[AddressVersion, ...] = ()
    current_version: Annotated[StrictInt, Field(ge=0)] = 0
    validated_version: PositiveVersion | None = None
    validation_attempt_id: UUID | None = None
    validation_attempts: tuple[ValidationResult, ...] = ()
    confirmed_version: PositiveVersion | None = None
    readback: ReadbackAttempt | None = None
    used_readback_ids: tuple[UUID, ...] = ()
    evidence_history: tuple[VerifiedEvidence, ...] = ()
    saved_references: tuple[SavedReference, ...] = ()
    current_saved_address_id: UUID | None = None
    audit_events: tuple[AuditEvent, ...] = ()

    @field_validator('customer_id', 'bolna_execution_id')
    @classmethod
    def safe_identity(cls, value: str) -> str:
        if not value.strip() or any(unicodedata.category(char) in {'Cc', 'Cs'} for char in value):
            raise ValueError('Identity must be bounded nonblank text without control characters.')
        return value


def evolve(session: Session, operation: str, *, reference_id: UUID | None = None,
           reason: str | None = None, **changes) -> Session:
    """Validate replacement state rather than using unvalidated model_copy updates."""
    values = {name: getattr(session, name) for name in Session.model_fields}
    values.update(changes)
    event = AuditEvent(sequence=len(session.audit_events) + 1, operation=operation,
                       version=values['current_version'], reference_id=reference_id, reason=reason)
    values['audit_events'] = session.audit_events + (event,)
    return Session(**values)


def create_session(session_id: UUID, customer_id: str, execution_id: str) -> Session:
    session = Session(session_id=session_id, customer_id=customer_id, bolna_execution_id=execution_id)
    return evolve(session, 'SESSION_CREATED')


def check_version(session: Session, version: int, *, allow_zero: bool = False) -> None:
    if type(version) is not int or version != session.current_version or version < (0 if allow_zero else 1):
        raise DomainError('ADDRESS_VERSION_CHANGED')


def current_address(session: Session) -> AddressVersion:
    if (session.current_version <= 0 or len(session.versions) != session.current_version
            or any(item.version != index for index, item in enumerate(session.versions, 1))):
        raise DomainError('INVALID_VERSION_HISTORY')
    return session.versions[-1]


def update_candidate(session: Session, expected_version: int, changes: AddressChanges) -> Session:
    check_version(session, expected_version, allow_zero=True)
    base = current_address(session) if session.current_version else None
    canonical = apply_changes(base.canonical if base else Address(), changes)
    raw = apply_changes(base.raw if base else Address(), changes)
    origins = {o.field: o for o in base.origins} if base else {}
    if base and canonical.pincode != base.canonical.pincode:
        for field in ('state', 'district'):
            if field not in changes.model_fields_set and origins.get(field) and origins[field].origin == 'POSTAL_DATA':
                canonical = apply_changes(canonical, AddressChanges(**{field: None}))
                origins.pop(field)
    for field in changes.model_fields_set:
        if getattr(canonical, field) is None:
            origins.pop(field, None)
        else:
            origins[field] = FieldOrigin(field=field, origin='CUSTOMER')
    origin_tuple = tuple(origins[k] for k in Address.model_fields if k in origins)
    if base and canonical == base.canonical and raw == base.raw and origin_tuple == base.origins:
        return session
    if not base and canonical == Address():
        return session
    version = AddressVersion(version=session.current_version + 1, raw=raw, canonical=canonical, origins=origin_tuple)
    return evolve(session, 'CANDIDATE_UPDATED', versions=session.versions + (version,),
                  current_version=version.version, status='CANDIDATE_UPDATED', validated_version=None,
                  validation_attempt_id=None, confirmed_version=None, readback=None,
                  current_saved_address_id=None)


def apply_normalization(session: Session, expected_version: int, proposal: NormalizationProposal) -> Session:
    check_version(session, expected_version)
    proposal = NormalizationProposal.model_validate(proposal)
    if proposal.session_id is not None and proposal.session_id != session.session_id:
        raise DomainError('NORMALIZATION_SESSION_MISMATCH')
    base = current_address(session)
    if proposal.base_version != expected_version or proposal.base_snapshot != base:
        raise DomainError('NORMALIZATION_BASE_CHANGED')
    if proposal.canonical == base.canonical:
        raise DomainError('EMPTY_NORMALIZATION')
    version = AddressVersion(version=base.version + 1, raw=base.raw, canonical=proposal.canonical,
        origins=proposal.origins, normalization_id=proposal.proposal_id, policy_version=proposal.policy_version)
    return evolve(session, 'CANONICAL_NORMALIZED', reference_id=proposal.proposal_id,
        versions=session.versions + (version,), current_version=version.version,
        status='CANDIDATE_UPDATED', validated_version=None, validation_attempt_id=None,
        confirmed_version=None, readback=None, current_saved_address_id=None)


def record_validation(session: Session, result: ValidationResult) -> Session:
    check_version(session, result.version)
    # Revalidate even an internally copied result before using its eligibility claim.
    result = ValidationResult.model_validate(result)
    for previous in session.validation_attempts:
        if previous.attempt_id == result.attempt_id:
            if previous != result:
                raise DomainError('VALIDATION_ATTEMPT_REUSED')
            return session  # Never restore eligibility revoked by a newer attempt.
    address = current_address(session).canonical
    if result.canonical != address:
        raise DomainError('NORMALIZATION_REQUIRES_VERSION')
    if result.origins and result.origins != current_address(session).origins:
        raise DomainError('VALIDATION_ORIGINS_MISMATCH')
    if result.status == 'VALID' and not re.fullmatch(r'[0-9]{6}', address.pincode or ''):
        raise DomainError('INVALID_CANONICAL_PIN')
    valid = result.status == 'VALID'
    return evolve(session, 'VALIDATION_RECORDED', reference_id=result.attempt_id,
                  validation_attempts=session.validation_attempts + (result,),
                  validated_version=result.version if valid else None,
                  validation_attempt_id=result.attempt_id,
                  status='READY_FOR_READBACK' if valid else result.status,
                  readback=None, confirmed_version=None, current_saved_address_id=None)
