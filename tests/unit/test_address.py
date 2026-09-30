import pytest
from pydantic import ValidationError

from app.domain.address import Address, AddressChanges, AddressVersion, apply_changes, render_readback


def test_unicode_and_identifiers_are_preserved():
    address = Address(house_flat='B-0302', building='अपर्णा', pincode='050032')
    assert address.house_flat == 'B-0302'
    assert address.building == 'अपर्णा'
    assert address.pincode == '050032'
    assert Address(pincode='५०००३२').pincode == '५०००३२'


@pytest.mark.parametrize('value', [302, True, 3.02, [], {}])
def test_no_string_coercion(value):
    with pytest.raises(ValidationError):
        Address(house_flat=value)


@pytest.mark.parametrize('field,limit', [('house_flat', 100), ('building', 200), ('area', 200), ('pincode', 32)])
def test_field_length_boundaries(field, limit):
    assert getattr(Address(**{field: 'a' * limit}), field) == 'a' * limit
    with pytest.raises(ValidationError):
        Address(**{field: 'a' * (limit + 1)})


@pytest.mark.parametrize('value', ['', '  ', '\t', 'abc\nxyz', 'a\x00b', '\ud800'])
def test_blank_control_and_surrogate_rejected(value):
    with pytest.raises(ValidationError):
        Address(building=value)


def test_unknown_fields_and_empty_patch_rejected():
    with pytest.raises(ValidationError):
        Address(confirmed=True)
    with pytest.raises(ValidationError):
        AddressChanges()


def test_null_clears_and_omission_preserves_without_mutation():
    base = Address(house_flat='302', building='Galaxy Apartments')
    changed = apply_changes(base, AddressChanges(house_flat=None))
    assert changed.house_flat is None
    assert changed.building == 'Galaxy Apartments'
    assert base.house_flat == '302'


def test_candidate_pin_does_not_claim_validity():
    assert Address(pincode='50003').pincode == '50003'


def test_snapshot_and_nested_address_are_frozen():
    original = Address(house_flat='302')
    snapshot = AddressVersion(version=1, raw=original, canonical=original)
    with pytest.raises(ValidationError):
        snapshot.canonical.house_flat = '320'
    with pytest.raises(ValidationError):
        snapshot.version = 2
    with pytest.raises(ValidationError):
        AddressVersion(version=0, raw=original, canonical=original)


def test_readback_includes_every_supplied_field_and_separate_pin_digits():
    address = Address(house_flat='B-302', building='Galaxy', street='Example Road',
                      area='Example Colony', landmark='Example Library', city='Hyderabad',
                      district='Example District', state='Telangana', pincode='500032')
    assert render_readback(address) == (
        'House or flat B-302; building Galaxy; street Example Road; area Example Colony; '
        'landmark Example Library; city Hyderabad; district Example District; state Telangana; '
        'PIN 5, 0, 0, 0, 3, 2. Is this full address correct?')
    assert render_readback(Address(city='Hyderabad')) == 'City Hyderabad. Is this full address correct?'


def test_rendered_validation_error_does_not_echo_private_input():
    with pytest.raises(ValidationError) as error:
        Address(building='sentinel-private-address\n')
    assert 'sentinel-private-address' not in str(error.value)
