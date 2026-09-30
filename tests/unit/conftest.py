"""Synthetic evidence ONLY for deterministic domain tests, never production."""

from uuid import uuid4
import pytest

from app.domain.address import AddressChanges
from app.domain.session import create_session, update_candidate, record_validation, ValidationResult, VerifiedEvidence
from app.domain.errors import DomainError


class SyntheticVerifier:
    def __init__(self):
        self.records = {}

    def verify(self, reference):
        if reference not in self.records:
            raise DomainError('EVIDENCE_UNAVAILABLE')
        return self.records[reference]

    def issue(self, session, evidence_kind, sequence, **overrides):
        attempt = session.readback
        values = dict(evidence_id=uuid4(), kind=evidence_kind, session_id=session.session_id,
                      execution_id=session.bolna_execution_id, version=session.current_version,
                      validation_attempt_id=session.validation_attempt_id, readback_id=attempt.id,
                      text_digest=attempt.text_digest, source_sequence=sequence)
        values.update(overrides)
        reference = str(uuid4())
        self.records[reference] = VerifiedEvidence(**values)
        return reference


@pytest.fixture
def verifier():
    return SyntheticVerifier()


@pytest.fixture
def validated():
    def make():
        s = create_session(uuid4(), 'customer-1', 'execution-1')
        s = update_candidate(s, 0, AddressChanges(house_flat='302', building='Galaxy', area='Gachibowli',
                                                city='Hyderabad', pincode='500032'))
        return record_validation(s, ValidationResult(version=1, attempt_id=uuid4(), status='VALID',
                                                      canonical=s.versions[-1].canonical))
    return make
