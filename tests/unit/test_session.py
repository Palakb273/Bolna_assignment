from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.address import Address, AddressChanges
from app.domain.errors import DomainError
from app.domain.session import create_session, update_candidate, record_validation, ValidationResult


def collecting():
    return create_session(uuid4(), 'customer-1', 'execution-1')


def candidate():
    return update_candidate(collecting(), 0, AddressChanges(
        house_flat='302', building='Galaxy', area='Gachibowli', city='Hyderabad', pincode='500032'))


def result(session, **overrides):
    data = dict(version=session.current_version, attempt_id=uuid4(), status='VALID',
                canonical=session.versions[-1].canonical)
    data.update(overrides)
    return ValidationResult(**data)


def test_creation_is_empty_and_ownership_is_immutable():
    s = collecting()
    assert (s.status, s.current_version, s.validated_version, s.confirmed_version) == ('COLLECTING', 0, None, None)
    assert s.versions == ()
    with pytest.raises(ValidationError):
        s.customer_id = 'other'


def test_version_preserves_fields_and_history():
    s = candidate()
    changed = update_candidate(s, 1, AddressChanges(house_flat='320'))
    assert changed.current_version == 2
    assert changed.versions[-1].canonical.house_flat == '320'
    assert changed.versions[-1].canonical.building == 'Galaxy'
    assert changed.versions[0].canonical.house_flat == '302'
    assert s.current_version == 1
    assert isinstance(changed.versions, tuple)
    assert changed.versions[-1].raw.house_flat == '320'


def test_identical_patch_is_noop_and_null_clears():
    s = candidate()
    assert update_candidate(s, 1, AddressChanges(house_flat='302')) == s
    assert update_candidate(s, 1, AddressChanges(building=None)).versions[-1].canonical.building is None


@pytest.mark.parametrize('expected', [0, 2, -1, True, '1'])
def test_stale_or_noninteger_update_cannot_mutate(expected):
    s = candidate()
    before = s.model_dump()
    with pytest.raises(DomainError):
        update_candidate(s, expected, AddressChanges(house_flat='320'))
    assert s.model_dump() == before


def test_validation_binds_current_snapshot_and_duplicate_is_idempotent():
    s = candidate()
    attempt = result(s)
    valid = record_validation(s, attempt)
    assert (valid.status, valid.validated_version, valid.validation_attempt_id) == ('READY_FOR_READBACK', 1, attempt.attempt_id)
    assert record_validation(valid, attempt) == valid
    assert len(valid.validation_attempts) == 1
    assert len(valid.audit_events) == 3


@pytest.mark.parametrize('status', ['NEEDS_CLARIFICATION', 'VALIDATION_ERROR'])
def test_invalid_validation_clears_eligibility(status):
    s = candidate()
    s = record_validation(s, result(s))
    s = record_validation(s, result(s, status=status, missing_fields=('pincode',)))
    assert s.status == status
    assert s.validated_version is None
    assert s.confirmed_version is None


def test_stale_validation_and_silent_normalization_rejected():
    s = candidate()
    stale = result(s)
    changed = update_candidate(s, 1, AddressChanges(house_flat='320'))
    with pytest.raises(DomainError, match='ADDRESS_VERSION_CHANGED'):
        record_validation(changed, stale)
    normalized = s.versions[-1].canonical.model_copy(update={'city': 'Other city'})
    with pytest.raises(DomainError, match='NORMALIZATION_REQUIRES_VERSION'):
        record_validation(s, result(s, canonical=normalized))


def test_reused_validation_id_with_different_result_is_rejected():
    s = candidate()
    attempt = result(s)
    s = record_validation(s, attempt)
    with pytest.raises(DomainError, match='VALIDATION_ATTEMPT_REUSED'):
        record_validation(s, attempt.model_copy(update={'status': 'VALIDATION_ERROR'}))


def test_version_zero_never_validates():
    with pytest.raises((DomainError, ValidationError)):
        record_validation(collecting(), ValidationResult(version=0, attempt_id=uuid4(), status='VALID', canonical=Address()))


def test_invalid_pin_cannot_be_marked_valid_by_trusted_result():
    s = update_candidate(collecting(), 0, AddressChanges(house_flat='302', area='A', city='H', pincode='50003'))
    with pytest.raises(DomainError, match='INVALID_CANONICAL_PIN'):
        record_validation(s, result(s))


def test_valid_result_cannot_also_have_missing_or_conflicts():
    s = candidate()
    with pytest.raises((DomainError, ValidationError)):
        record_validation(s, result(s, missing_fields=('area',)))
