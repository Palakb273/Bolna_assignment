from uuid import uuid4

import pytest

from app.domain.address import AddressChanges
from app.domain.errors import DomainError
from app.domain.session import create_session, update_candidate, record_validation, ValidationResult
from app.domain.confirmation import (prepare_readback, complete_readback, confirm_address,
    invalidate_readback, require_save_eligible, record_saved)


def accept(s, verifier, sequence=10):
    s = prepare_readback(s, uuid4())
    s = complete_readback(s, verifier.issue(s, 'READBACK_COMPLETED', sequence), verifier)
    return confirm_address(s, s.current_version, True,
                           verifier.issue(s, 'CUSTOMER_CONFIRMED', sequence + 1), verifier)


def validate(s):
    return record_validation(s, ValidationResult(version=s.current_version, attempt_id=uuid4(),
                                                 status='VALID', canonical=s.versions[-1].canonical))


def test_version_zero_and_unconfirmed_cannot_save(validated):
    for s in [create_session(uuid4(), 'c', 'e'), validated(), prepare_readback(validated(), uuid4())]:
        with pytest.raises(DomainError):
            require_save_eligible(s)


def test_required_three_to_four_correction_regression(validated, verifier):
    s = update_candidate(validated(), 1, AddressChanges(street='Example Road'))
    s = update_candidate(s, 2, AddressChanges(landmark='Example Library'))
    s = accept(validate(s), verifier)
    assert (s.current_version, s.validated_version, s.confirmed_version) == (3, 3, 3)
    assert require_save_eligible(s).version == 3
    changed = update_candidate(s, 3, AddressChanges(house_flat='320'))
    assert (changed.current_version, changed.validated_version, changed.confirmed_version) == (4, None, None)
    assert changed.readback is None
    with pytest.raises(DomainError):
        require_save_eligible(changed)
    revalidated = validate(changed)
    inconsistent = revalidated.model_copy(update={'confirmed_version': 3})
    with pytest.raises(DomainError):
        require_save_eligible(inconsistent)
    final = accept(revalidated, verifier, sequence=20)
    assert require_save_eligible(final).canonical.house_flat == '320'


@pytest.mark.parametrize('field,value', [('current_version', 0), ('current_version', 2),
    ('validated_version', None), ('confirmed_version', None), ('confirmed_version', 2),
    ('validation_attempt_id', uuid4()), ('readback', None), ('status', 'COLLECTING'),
    ('versions', ()), ('evidence_history', ())])
def test_save_rechecks_each_guard_independently(validated, verifier, field, value):
    s = accept(validated(), verifier)
    bad = s.model_copy(update={field: value})
    with pytest.raises(DomainError):
        require_save_eligible(bad)


def test_save_rejects_forged_playback_and_unordered_evidence(validated, verifier):
    s = accept(validated(), verifier)
    for field, value in [('completion', None), ('confirmation', None),
                         ('text_digest', '0' * 64), ('rendered_text', 'Omitted everything')]:
        bad = s.model_copy(update={'readback': s.readback.model_copy(update={field: value})})
        with pytest.raises(DomainError):
            require_save_eligible(bad)
    early = s.readback.confirmation.model_copy(update={'source_sequence': 9})
    bad = s.model_copy(update={'readback': s.readback.model_copy(update={'confirmation': early}),
                              'evidence_history': (s.readback.completion, early)})
    with pytest.raises(DomainError):
        require_save_eligible(bad)


def test_save_receipt_is_idempotent_and_does_not_claim_real_persistence(validated, verifier):
    s = accept(validated(), verifier)
    address_id = uuid4()
    saved = record_saved(s, address_id, 1)
    assert saved.status == 'SAVED'
    assert saved.current_saved_address_id == address_id
    assert len(saved.saved_references) == 1
    assert record_saved(saved, address_id, 1) == saved
    assert s.status == 'CONFIRMED'
    with pytest.raises(DomainError, match='SAVE_RECEIPT_CONFLICT'):
        record_saved(saved, uuid4(), 1)


def test_correction_after_saved_retains_history_but_revokes_current_acceptance(validated, verifier):
    s = record_saved(accept(validated(), verifier), uuid4(), 1)
    changed = update_candidate(s, 1, AddressChanges(house_flat='320'))
    assert changed.current_saved_address_id is None
    assert changed.saved_references == s.saved_references
    with pytest.raises(DomainError):
        require_save_eligible(changed)
    final = record_saved(accept(validate(changed), verifier, 20), uuid4(), 2)
    assert len(final.saved_references) == 2
    assert final.saved_references[0] == s.saved_references[0]


@pytest.mark.parametrize('reason', ['INTERRUPTED', 'REJECTED', 'UNCERTAIN'])
def test_post_save_invalidation_retains_receipt_and_requires_new_evidence(validated, verifier, reason):
    address_id = uuid4()
    saved = record_saved(accept(validated(), verifier), address_id, 1)
    changed = invalidate_readback(saved, reason)
    assert changed.current_saved_address_id is None
    assert changed.saved_references == saved.saved_references
    with pytest.raises(DomainError):
        record_saved(changed, address_id, 1)
    final = record_saved(accept(changed, verifier, 20), address_id, 1)
    assert len(final.saved_references) == 1
    assert final.current_saved_address_id == address_id


def test_no_address_values_in_audit_events(validated, verifier):
    s = record_saved(accept(validated(), verifier), uuid4(), 1)
    serialized = str([event.model_dump() for event in s.audit_events])
    assert 'Galaxy' not in serialized
    assert 'Hyderabad' not in serialized
    assert '500032' not in serialized
