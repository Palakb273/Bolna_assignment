from datetime import date
from uuid import uuid4
import pytest
from app.domain.address import Address, AddressVersion, AddressChanges, NormalizationProposal
from app.domain.session import create_session, update_candidate, apply_normalization, record_validation
from app.domain.errors import DomainError
from app.validation.engine import validate_address
from app.validation.models import PostalRecord, PostalLookupResult, ValidationPolicy
from app.validation.postal_directory import PostalDataError
from test_normalization_transition import provenance


class SyntheticDirectory:
    def __init__(self, rows=None, source=None, error=None):
        self.rows = rows if rows is not None else (PostalRecord(pincode='500032', office_name='Office',
            district='Example District', state='Telangana'),)
        self.source = source or provenance()
        self.error = error
        self.calls = 0

    def lookup_pincode(self, pin):
        self.calls += 1
        if self.error:
            raise self.error
        return PostalLookupResult(pincode=pin, records=self.rows, provenance=self.source)


def snapshot(**patch):
    address = Address(**(dict(house_flat='302', area='Unlisted locality', city='Unlisted city',
                             state='Telangana', pincode='500032') | patch))
    return AddressVersion(version=3, raw=address, canonical=address)


def run(s=None, directory=None):
    return validate_address(s or snapshot(), directory or SyntheticDirectory(), ValidationPolicy(),
                            date(2026, 9, 30), uuid4())


def test_valid_preserves_city_area_and_provenance():
    result = run()
    assert result.status == 'VALID'
    assert result.canonical.city == 'Unlisted city'
    assert result.warnings == ('CITY_NOT_POSTALLY_VERIFIED', 'AREA_NOT_POSTALLY_VERIFIED')
    assert result.source == provenance() and result.policy_version == 'urban-v1:max-age=90'


@pytest.mark.parametrize('patch,code', [({'city': None}, 'CITY_REQUIRED'),
    ({'house_flat': None}, 'HOUSE_IDENTIFIER_REQUIRED'), ({'area': None}, 'AREA_REQUIRED'),
    ({'pincode': None}, 'PINCODE_REQUIRED'), ({'pincode': '500O32'}, 'PINCODE_INVALID_FORMAT')])
def test_local_errors_skip_directory(patch, code):
    d = SyntheticDirectory()
    result = run(snapshot(**patch), d)
    assert result.status == 'NEEDS_CLARIFICATION' and code in result.reason_codes
    assert d.calls == 0


@pytest.mark.parametrize('patch,code', [({'state': 'Haryana'}, 'STATE_PINCODE_CONFLICT'),
    ({'district': 'Other'}, 'DISTRICT_PINCODE_CONFLICT')])
def test_conflicts_do_not_rewrite(patch, code):
    s = snapshot(**patch)
    result = run(s)
    assert result.status == 'NEEDS_CLARIFICATION' and code in result.conflicts
    assert result.canonical == s.canonical


def test_multiple_districts_alias_and_state_ambiguity():
    rows = tuple(PostalRecord(pincode='500032', office_name='Office', district=d, state='Uttar Pradesh')
                 for d in ('A', 'B'))
    assert run(snapshot(state='U.P.', district='b'), SyntheticDirectory(rows)).status == 'VALID'
    bad = rows + (PostalRecord(pincode='500032', office_name='Office', district='C', state='Delhi'),)
    result = run(snapshot(state='UP'), SyntheticDirectory(bad))
    assert result.status == 'VALIDATION_ERROR' and result.reason_codes == ('POSTAL_DATA_AMBIGUOUS',)


@pytest.mark.parametrize('directory,code', [
    (SyntheticDirectory(()), 'PINCODE_NOT_FOUND'),
    (SyntheticDirectory(error=RuntimeError('secret address')), 'POSTAL_DATA_UNAVAILABLE'),
    (SyntheticDirectory(error=PostalDataError('POSTAL_CHECKSUM_MISMATCH')), 'POSTAL_CHECKSUM_MISMATCH'),
    (SyntheticDirectory(source=provenance().model_copy(update={'source_date': date(2025, 1, 1)})), 'POSTAL_DATA_STALE'),
])
def test_failures(directory, code):
    result = run(directory=directory)
    assert result.status != 'VALID' and result.reason_codes == (code,)
    assert 'secret' not in result.model_dump_json()


def test_combined_proposal_converges_and_stale_result_fails():
    s = update_candidate(create_session(uuid4(), 'c', 'e'), 0,
        AddressChanges(house_flat='1', area='Area', city='City', pincode='५०००३२'))
    s = update_candidate(s, 1, AddressChanges(street='Street'))
    s = update_candidate(s, 2, AddressChanges(landmark='Library'))
    p = run(s.versions[-1])
    assert isinstance(p, NormalizationProposal)
    new = apply_normalization(s, 3, p)
    assert (new.current_version, new.validated_version, new.confirmed_version) == (4, None, None)
    assert new.versions[-1].raw.state is None and new.versions[-1].raw.pincode == '५०००३२'
    result = run(new.versions[-1])
    assert result.status == 'VALID'
    saved = record_validation(new, result)
    assert saved.validation_attempts[-1].source == provenance()
    corrected = update_candidate(saved, 4, AddressChanges(house_flat='2'))
    with pytest.raises(DomainError, match='ADDRESS_VERSION_CHANGED'):
        record_validation(corrected, result)


def test_conflict_precedes_normalization():
    result = run(snapshot(pincode='५०००३२', state='Haryana'))
    assert result.status == 'NEEDS_CLARIFICATION'


def test_missing_reference_district_is_not_conflict():
    row = PostalRecord(pincode='500032', office_name='Office', district=' ', state='Telangana')
    result = run(snapshot(district='Anything'), SyntheticDirectory((row,)))
    assert result.status == 'VALIDATION_ERROR' and not result.conflicts


def test_malformed_reference_state_fails_closed_without_uncaught_error():
    row = PostalRecord(pincode='500032', office_name='Office', district='Example', state='Telan\x00gana')
    result = run(snapshot(state=None), SyntheticDirectory((row,)))
    assert result.status == 'VALIDATION_ERROR'
    assert result.reason_codes == ('POSTAL_DATA_CORRUPT',)
