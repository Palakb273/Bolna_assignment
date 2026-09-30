"""Fail-closed evidence gates, independent of LLM-reported booleans."""

from hashlib import sha256
import re
from typing import Literal, Protocol
from uuid import UUID

from .address import AddressVersion, render_readback
from .errors import DomainError
from .session import (Session, ReadbackAttempt, SavedReference, VerifiedEvidence, current_address,
                      check_version, evolve)


class EvidenceVerifier(Protocol):
    def verify(self, reference: str) -> VerifiedEvidence:
        """Resolve independently authenticated evidence; never trust a model assertion."""
        ...


class RejectAllEvidenceVerifier:
    def verify(self, reference: str) -> VerifiedEvidence:
        raise DomainError('EVIDENCE_UNAVAILABLE')


_DENY = RejectAllEvidenceVerifier()


def _validated_address(session: Session) -> AddressVersion:
    address = current_address(session)
    if session.validated_version != session.current_version or not session.validation_attempts:
        raise DomainError('ADDRESS_NOT_VALIDATED')
    latest = session.validation_attempts[-1]
    if (latest.attempt_id != session.validation_attempt_id or latest.version != session.current_version
            or latest.status != 'VALID' or latest.canonical != address.canonical
            or latest.missing_fields or latest.conflicts):
        raise DomainError('ADDRESS_NOT_VALIDATED')
    if not re.fullmatch(r'[0-9]{6}', address.canonical.pincode or ''):
        raise DomainError('INVALID_CANONICAL_PIN')
    return address


def _current_readback(session: Session) -> ReadbackAttempt:
    address = _validated_address(session)
    attempt = session.readback
    if attempt is None:
        raise DomainError('READBACK_REQUIRED')
    text = render_readback(address.canonical, attempt.language)
    if (attempt.session_id != session.session_id or attempt.execution_id != session.bolna_execution_id
            or attempt.version != session.current_version or attempt.validation_attempt_id != session.validation_attempt_id
            or attempt.rendered_text != text or attempt.text_digest != sha256(text.encode('utf-8')).hexdigest()
            or not session.used_readback_ids or session.used_readback_ids[-1] != attempt.id):
        raise DomainError('READBACK_CHANGED')
    return attempt


def _resolve(reference: str, verifier: EvidenceVerifier) -> VerifiedEvidence:
    if not isinstance(reference, str) or not reference.strip() or len(reference) > 200:
        raise DomainError('EVIDENCE_UNAVAILABLE')
    try:
        return VerifiedEvidence.model_validate(verifier.verify(reference))
    except Exception:
        # Provider errors can contain credentials or transcripts.
        raise DomainError('EVIDENCE_UNAVAILABLE') from None


def _check_binding(session: Session, attempt: ReadbackAttempt, evidence: VerifiedEvidence,
                   kind: str) -> None:
    if (evidence.kind != kind or evidence.session_id != session.session_id
            or evidence.execution_id != session.bolna_execution_id or evidence.version != session.current_version
            or evidence.validation_attempt_id != session.validation_attempt_id or evidence.readback_id != attempt.id
            or evidence.text_digest != attempt.text_digest):
        raise DomainError('EVIDENCE_BINDING_MISMATCH')


def _check_new_evidence(session: Session, evidence: VerifiedEvidence) -> None:
    if any(previous.evidence_id == evidence.evidence_id for previous in session.evidence_history):
        raise DomainError('EVIDENCE_REUSED')
    if session.evidence_history and evidence.source_sequence <= max(e.source_sequence for e in session.evidence_history):
        raise DomainError('EVIDENCE_OUT_OF_ORDER')


def prepare_readback(session: Session, attempt_id: UUID, language: str = 'en') -> Session:
    address = _validated_address(session)
    if attempt_id in session.used_readback_ids:
        raise DomainError('READBACK_ATTEMPT_REUSED')
    text = render_readback(address.canonical, language)
    attempt = ReadbackAttempt(id=attempt_id, session_id=session.session_id, language=language,
                              execution_id=session.bolna_execution_id, version=session.current_version,
                              validation_attempt_id=session.validation_attempt_id, rendered_text=text,
                              text_digest=sha256(text.encode('utf-8')).hexdigest())
    return evolve(session, 'READBACK_PREPARED', reference_id=attempt_id, readback=attempt,
                  used_readback_ids=session.used_readback_ids + (attempt_id,),
                  confirmed_version=None, current_saved_address_id=None, status='READ_BACK')


def complete_readback(session: Session, evidence_reference: str,
                      verifier: EvidenceVerifier = _DENY) -> Session:
    attempt = _current_readback(session)
    evidence = _resolve(evidence_reference, verifier)
    _check_binding(session, attempt, evidence, 'READBACK_COMPLETED')
    if attempt.completion == evidence and evidence in session.evidence_history:
        return session
    _check_new_evidence(session, evidence)
    if attempt.completion is not None:
        raise DomainError('READBACK_ALREADY_COMPLETED')
    return evolve(session, 'READBACK_COMPLETED', reference_id=evidence.evidence_id,
                  readback=attempt.model_copy(update={'completion': evidence}),
                  evidence_history=session.evidence_history + (evidence,), status='WAITING_CONFIRMATION')


def confirm_address(session: Session, version: int, explicit_confirmation: bool, evidence_reference: str,
                    verifier: EvidenceVerifier = _DENY) -> Session:
    check_version(session, version)
    attempt = _current_readback(session)
    if attempt.completion is None:
        raise DomainError('READBACK_NOT_COMPLETED')
    if explicit_confirmation is not True:
        raise DomainError('EXPLICIT_CONFIRMATION_REQUIRED')
    evidence = _resolve(evidence_reference, verifier)
    _check_binding(session, attempt, evidence, 'CUSTOMER_CONFIRMED')
    if evidence.source_sequence <= attempt.completion.source_sequence:
        raise DomainError('EVIDENCE_OUT_OF_ORDER')
    if (attempt.confirmation == evidence and evidence in session.evidence_history
            and session.confirmed_version == version):
        return session
    _check_new_evidence(session, evidence)
    if attempt.confirmation is not None:
        raise DomainError('ADDRESS_ALREADY_CONFIRMED')
    return evolve(session, 'CONFIRMED', reference_id=evidence.evidence_id,
                  readback=attempt.model_copy(update={'confirmation': evidence}),
                  evidence_history=session.evidence_history + (evidence,), confirmed_version=version,
                  status='CONFIRMED')


def invalidate_readback(session: Session, reason: Literal['INTERRUPTED', 'REJECTED', 'UNCERTAIN']) -> Session:
    if reason not in {'INTERRUPTED', 'REJECTED', 'UNCERTAIN'}:
        raise DomainError('INVALID_INVALIDATION_REASON')
    return evolve(session, 'READBACK_INVALIDATED', reason=reason, readback=None, confirmed_version=None,
                  current_saved_address_id=None,
                  status='READY_FOR_READBACK' if session.validated_version is not None else session.status)


def require_save_eligible(session: Session) -> AddressVersion:
    """Independently recheck the aggregate; this function never writes a database."""
    try:
        session = Session.model_validate(session)
    except ValueError:
        raise DomainError('INVALID_SESSION') from None
    address = _validated_address(session)
    if (session.status not in {'CONFIRMED', 'SAVED'}
            or session.current_version != session.confirmed_version):
        raise DomainError('ADDRESS_NOT_CONFIRMED')
    attempt = _current_readback(session)
    completion, confirmation = attempt.completion, attempt.confirmation
    if completion is None or confirmation is None:
        raise DomainError('CONFIRMATION_EVIDENCE_REQUIRED')
    _check_binding(session, attempt, completion, 'READBACK_COMPLETED')
    _check_binding(session, attempt, confirmation, 'CUSTOMER_CONFIRMED')
    if (completion not in session.evidence_history or confirmation not in session.evidence_history
            or completion.evidence_id == confirmation.evidence_id
            or confirmation.source_sequence <= completion.source_sequence):
        raise DomainError('INVALID_CONFIRMATION_EVIDENCE')
    return address


def record_saved(session: Session, address_id: UUID, version: int) -> Session:
    """Trusted repository hook for a committed receipt; no persistence occurs here."""
    check_version(session, version)
    require_save_eligible(session)
    for receipt in session.saved_references:
        if receipt.source_version == version:
            if receipt.address_id != address_id:
                raise DomainError('SAVE_RECEIPT_CONFLICT')
            if session.status == 'SAVED' and session.current_saved_address_id == address_id:
                return session
            return evolve(session, 'SAVE_RECORDED', reference_id=address_id, status='SAVED',
                          current_saved_address_id=address_id)
        if receipt.address_id == address_id:
            raise DomainError('SAVE_RECEIPT_CONFLICT')
    attempt = session.readback  # Eligibility above guarantees complete evidence.
    receipt = SavedReference(address_id=address_id, source_version=version,
                             validation_attempt_id=session.validation_attempt_id, readback_id=attempt.id,
                             completion_evidence_id=attempt.completion.evidence_id,
                             confirmation_evidence_id=attempt.confirmation.evidence_id)
    return evolve(session, 'SAVE_RECORDED', reference_id=address_id, status='SAVED',
                  current_saved_address_id=address_id, saved_references=session.saved_references + (receipt,))
