from uuid import uuid4
import pytest
from app.domain.address import AddressChanges
from app.domain.session import create_session, update_candidate, record_validation, apply_normalization, ValidationResult
from app.domain.confirmation import prepare_readback, complete_readback, confirm_address, require_save_eligible
from app.domain.errors import DomainError
from test_validation_engine import run


def test_normalizing_confirmed_v3_revokes_prior_evidence(verifier):
    s = update_candidate(create_session(uuid4(), 'c', 'e'), 0,
        AddressChanges(house_flat='1', area='Area', city='City', pincode='500032'))
    s = update_candidate(s, 1, AddressChanges(street='Street'))
    s = update_candidate(s, 2, AddressChanges(landmark='Library'))
    # Existing 2A synthetic validation permits missing state; 2B will explicitly derive it.
    s = record_validation(s, ValidationResult(version=3, attempt_id=uuid4(), status='VALID',
                                             canonical=s.versions[-1].canonical))
    s = prepare_readback(s, uuid4())
    s = complete_readback(s, verifier.issue(s, 'READBACK_COMPLETED', 1), verifier)
    s = confirm_address(s, 3, True, verifier.issue(s, 'CUSTOMER_CONFIRMED', 2), verifier)
    assert require_save_eligible(s).version == 3
    new = apply_normalization(s, 3, run(s.versions[-1]))
    assert (new.current_version, new.validated_version, new.confirmed_version) == (4, None, None)
    assert new.readback is None and new.evidence_history == s.evidence_history
    new = record_validation(new, run(new.versions[-1]))
    with pytest.raises(DomainError):
        require_save_eligible(new)
    new = prepare_readback(new, uuid4())
    with pytest.raises(DomainError, match='EVIDENCE_UNAVAILABLE'):
        complete_readback(new, 'agent assertion')


def test_late_v3_result_and_metadata_reuse_rejected():
    s = update_candidate(create_session(uuid4(), 'c', 'e'), 0,
        AddressChanges(house_flat='1', area='Area', city='City', state='Telangana', pincode='500032'))
    s = update_candidate(s, 1, AddressChanges(street='Street'))
    s = update_candidate(s, 2, AddressChanges(landmark='Library'))
    result = run(s.versions[-1])
    changed = update_candidate(s, 3, AddressChanges(house_flat='2'))
    with pytest.raises(DomainError, match='ADDRESS_VERSION_CHANGED'):
        record_validation(changed, result)
    accepted = record_validation(s, result)
    with pytest.raises(DomainError, match='VALIDATION_ATTEMPT_REUSED'):
        record_validation(accepted, result.model_copy(update={'warnings': ()}))


def test_mismatched_origin_metadata_rejected():
    s = update_candidate(create_session(uuid4(), 'c', 'e'), 0,
        AddressChanges(house_flat='1', area='Area', city='City', state='Telangana', pincode='500032'))
    result = run(s.versions[-1])
    with pytest.raises(DomainError, match='VALIDATION_ORIGINS_MISMATCH'):
        record_validation(s, result.model_copy(update={'origins': result.origins[:-1]}))
