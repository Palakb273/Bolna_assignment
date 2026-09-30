from uuid import uuid4
from hashlib import sha256

import pytest

from app.domain.address import AddressChanges, render_readback
from app.domain.errors import DomainError
from app.domain.session import create_session, update_candidate, record_validation, ValidationResult
from app.domain.confirmation import prepare_readback, complete_readback, confirm_address, invalidate_readback


def completed(s, verifier, sequence=10):
    reference = verifier.issue(s, 'READBACK_COMPLETED', sequence)
    return complete_readback(s, reference, verifier)


def confirmed(s, verifier):
    s = completed(s, verifier)
    reference = verifier.issue(s, 'CUSTOMER_CONFIRMED', 11)
    return confirm_address(s, s.current_version, True, reference, verifier)


def test_prepare_only_renders_exact_full_address(validated):
    s = prepare_readback(validated(), uuid4())
    text = render_readback(s.versions[-1].canonical)
    assert s.readback.rendered_text == text
    assert s.readback.text_digest == sha256(text.encode()).hexdigest()
    assert s.readback.completion is None
    assert s.confirmed_version is None
    assert s.status == 'READ_BACK'


def test_unvalidated_address_and_zero_cannot_prepare(validated):
    for s in [create_session(uuid4(), 'c', 'e'), update_candidate(validated(), 1, AddressChanges(house_flat='320'))]:
        with pytest.raises(DomainError):
            prepare_readback(s, uuid4())


def test_default_verifier_fails_closed_even_with_true_and_matching_token(validated):
    s = prepare_readback(validated(), uuid4())
    for token in ['trusted=true', s.readback.text_digest, str(s.readback.id)]:
        with pytest.raises(DomainError):
            complete_readback(s, token)
        with pytest.raises(DomainError):
            confirm_address(s, 1, True, token)


def test_confirm_requires_completed_readback(validated, verifier):
    s = prepare_readback(validated(), uuid4())
    token = verifier.issue(s, 'CUSTOMER_CONFIRMED', 11)
    with pytest.raises(DomainError, match='READBACK_NOT_COMPLETED'):
        confirm_address(s, 1, True, token, verifier)


def test_success_and_exact_confirmation_replay_are_idempotent(validated, verifier):
    s = completed(prepare_readback(validated(), uuid4()), verifier)
    assert s.status == 'WAITING_CONFIRMATION'
    token = verifier.issue(s, 'CUSTOMER_CONFIRMED', 11)
    final = confirm_address(s, 1, True, token, verifier)
    assert final.confirmed_version == 1
    assert final.status == 'CONFIRMED'
    assert confirm_address(final, 1, True, token, verifier) == final
    assert len(final.evidence_history) == 2


@pytest.mark.parametrize('value', [False, None, 1, 'true', 'yes', 'maybe'])
def test_confirmation_flag_must_be_literal_true(validated, verifier, value):
    s = completed(prepare_readback(validated(), uuid4()), verifier)
    token = verifier.issue(s, 'CUSTOMER_CONFIRMED', 11)
    with pytest.raises(DomainError):
        confirm_address(s, 1, value, token, verifier)


@pytest.mark.parametrize('field,value', [('session_id', uuid4()), ('execution_id', 'other'),
    ('version', 2), ('validation_attempt_id', uuid4()), ('readback_id', uuid4()),
    ('text_digest', '0' * 64), ('kind', 'READBACK_COMPLETED')])
def test_wrong_evidence_binding_rejected_without_mutation(validated, verifier, field, value):
    s = completed(prepare_readback(validated(), uuid4()), verifier)
    before = s.model_dump()
    token = verifier.issue(s, 'CUSTOMER_CONFIRMED', 11, **{field: value})
    with pytest.raises(DomainError):
        confirm_address(s, 1, True, token, verifier)
    assert s.model_dump() == before


@pytest.mark.parametrize('sequence', [9, 10])
def test_confirmation_must_follow_playback_completion(validated, verifier, sequence):
    s = completed(prepare_readback(validated(), uuid4()), verifier)
    token = verifier.issue(s, 'CUSTOMER_CONFIRMED', sequence)
    with pytest.raises(DomainError):
        confirm_address(s, 1, True, token, verifier)


@pytest.mark.parametrize('reason', ['INTERRUPTED', 'REJECTED', 'UNCERTAIN'])
@pytest.mark.parametrize('stage', ['prepared', 'completed', 'confirmed'])
def test_invalidation_without_field_changes_requires_new_attempt(validated, verifier, reason, stage):
    s = prepare_readback(validated(), uuid4())
    old_id = s.readback.id
    if stage == 'completed':
        s = completed(s, verifier)
    if stage == 'confirmed':
        s = confirmed(s, verifier)
    old = s
    changed = invalidate_readback(s, reason)
    assert changed.current_version == changed.validated_version == 1
    assert changed.readback is None and changed.confirmed_version is None
    assert changed.status == 'READY_FOR_READBACK'
    with pytest.raises(DomainError):
        prepare_readback(changed, old_id)
    stale = verifier.issue(old, 'CUSTOMER_CONFIRMED', 12)
    new = prepare_readback(changed, uuid4())
    new = completed(new, verifier, sequence=20)
    with pytest.raises(DomainError):
        confirm_address(new, 1, True, stale, verifier)


def test_revalidation_same_version_revokes_consent(validated, verifier):
    s = confirmed(prepare_readback(validated(), uuid4()), verifier)
    old_validation = s.validation_attempts[-1]
    revalidated = record_validation(s, ValidationResult(version=1, attempt_id=uuid4(), status='VALID',
                                                        canonical=s.versions[-1].canonical))
    assert revalidated.confirmed_version is None and revalidated.readback is None
    assert record_validation(revalidated, old_validation) == revalidated


def test_reused_evidence_id_with_new_binding_rejected(validated, verifier):
    s = completed(prepare_readback(validated(), uuid4()), verifier)
    token = verifier.issue(s, 'CUSTOMER_CONFIRMED', 11, evidence_id=s.readback.completion.evidence_id)
    with pytest.raises(DomainError, match='EVIDENCE_REUSED'):
        confirm_address(s, 1, True, token, verifier)


def test_verifier_failure_is_sanitized(validated):
    class BrokenVerifier:
        def verify(self, reference):
            raise OSError('secret-provider-token')
    with pytest.raises(DomainError) as error:
        complete_readback(prepare_readback(validated(), uuid4()), 'secret-reference', BrokenVerifier())
    assert str(error.value) == 'EVIDENCE_UNAVAILABLE'


def test_completion_duplicate_is_noop(validated, verifier):
    s = prepare_readback(validated(), uuid4())
    token = verifier.issue(s, 'READBACK_COMPLETED', 10)
    s = complete_readback(s, token, verifier)
    assert complete_readback(s, token, verifier) == s
