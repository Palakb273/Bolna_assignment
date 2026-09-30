from datetime import date, datetime, timezone
from uuid import uuid4
import pytest
from app.domain.address import Address, AddressChanges, NormalizationProposal
from app.domain.validation_metadata import FieldOrigin, PostalDataProvenance
from app.domain.session import create_session, update_candidate, apply_normalization
from app.domain.errors import DomainError


def provenance():
    return PostalDataProvenance(source_name='Test fixture', resource_url='https://data.gov.in/test',
        resource_id='test', source_date=date(2026, 9, 1), imported_at=datetime(2026, 9, 2, tzinfo=timezone.utc),
        source_sha256='a'*64, records_sha256='b'*64, dataset_kind='SYNTHETIC')


def candidate():
    return update_candidate(create_session(uuid4(), 'c', 'e'), 0,
        AddressChanges(house_flat='1', area='Market', city='Town', pincode='५०००३२'))


def proposal(s):
    base = s.versions[-1]
    canonical = Address(**(base.canonical.model_dump() | {'pincode': '500032', 'state': 'Telangana'}))
    origins = tuple(o for o in base.origins if o.field not in ('pincode', 'state')) + (
        FieldOrigin(field='pincode', origin='CUSTOMER_NORMALIZED'),
        FieldOrigin(field='state', origin='POSTAL_DATA', source=provenance()))
    return NormalizationProposal(proposal_id=uuid4(), base_version=base.version, base_snapshot=base,
        canonical=canonical, origins=origins, policy_version='urban-v1', source=provenance())


def test_normalization_preserves_raw_and_rejects_replay():
    s = candidate()
    p = proposal(s)
    new = apply_normalization(s, 1, p)
    assert new.current_version == 2
    assert new.versions[-1].raw.pincode == '५०००३२'
    assert new.versions[-1].canonical.pincode == '500032'
    assert new.validated_version is new.confirmed_version is new.readback is None
    assert s.versions[-1].canonical.pincode == '५०००३२'
    with pytest.raises(DomainError):
        apply_normalization(new, 2, p)
    with pytest.raises(Exception):
        new.versions[-1].origins[0].origin = 'POSTAL_DATA'


def test_wrong_snapshot_and_no_change_rejected():
    s = candidate()
    other = update_candidate(create_session(uuid4(), 'c', 'e'), 0, AddressChanges(pincode='110001'))
    with pytest.raises(DomainError):
        apply_normalization(other, 1, proposal(s))
    p = NormalizationProposal(proposal_id=uuid4(), base_version=1, base_snapshot=s.versions[-1],
        canonical=s.versions[-1].canonical, origins=s.versions[-1].origins, policy_version='urban-v1')
    with pytest.raises(DomainError):
        apply_normalization(s, 1, p)


@pytest.mark.parametrize('explicit', [False, True])
def test_pin_correction_invalidates_only_derived_state(explicit):
    s = candidate()
    s = apply_normalization(s, 1, proposal(s))
    patch = {'pincode': '110001'}
    if explicit:
        patch['state'] = 'Delhi'
    new = update_candidate(s, 2, AddressChanges(**patch))
    assert new.versions[-1].canonical.state == ('Delhi' if explicit else None)
    assert new.versions[-1].raw.state == ('Delhi' if explicit else None)
    assert new.versions[-1].canonical.city == 'Town'


def test_equal_customer_claim_changes_origin_and_survives_pin_change():
    s = candidate()
    s = apply_normalization(s, 1, proposal(s))
    s = update_candidate(s, 2, AddressChanges(state='Telangana'))
    assert s.current_version == 3
    assert next(o for o in s.versions[-1].origins if o.field == 'state').origin == 'CUSTOMER'
    s = update_candidate(s, 3, AddressChanges(pincode='110001'))
    assert s.versions[-1].canonical.state == 'Telangana'
