"""Pure validation. Directory injection is a trusted internal boundary."""
import unicodedata
from datetime import date
from uuid import UUID
from app.domain.address import Address, AddressVersion, NormalizationProposal
from app.domain.session import ValidationResult
from app.domain.validation_metadata import FieldOrigin, ConflictDetail
from .models import PostalLookupResult, ValidationPolicy
from .normalization import normalize_pincode
from .required_fields import missing_required_fields
from .postal_directory import PostalDirectory, PostalDataError, check_source, check_record_text


def comparison(value: str) -> str:
    return ' '.join(unicodedata.normalize('NFC', value).split()).casefold()


def state_key(value: str) -> str:
    key = comparison(value)
    return {'up': 'uttar pradesh', 'u.p.': 'uttar pradesh', 'tn': 'tamil nadu'}.get(key, key)


def validate_address(snapshot: AddressVersion, directory: PostalDirectory, policy: ValidationPolicy,
                     as_of: date, attempt_id: UUID) -> ValidationResult | NormalizationProposal:
    snapshot = AddressVersion.model_validate(snapshot)
    address = snapshot.canonical

    def result(status, *, codes=(), missing=(), conflicts=(), source=None, action='RETRY_VALIDATION', warnings=()):
        return ValidationResult(version=snapshot.version, attempt_id=attempt_id, status=status,
            canonical=address, origins=snapshot.origins, missing_fields=missing, conflicts=conflicts,
            reason_codes=codes, warnings=warnings, source=source, policy_version=policy.identity,
            next_action=action, conflict_details=tuple(ConflictDetail(code=c, fields=(
                'state' if c == 'STATE_PINCODE_CONFLICT' else 'district', 'pincode')) for c in conflicts))

    missing = missing_required_fields(address)
    pin = normalize_pincode(address.pincode)
    required_codes = {'house_flat': 'HOUSE_IDENTIFIER_REQUIRED', 'area': 'AREA_REQUIRED',
                      'city': 'CITY_REQUIRED', 'pincode': 'PINCODE_REQUIRED'}
    codes = tuple(required_codes[f] for f in missing)
    codes += tuple(c for c in pin.reason_codes if c not in codes)
    if codes:
        action = {'house_flat': 'ASK_PREMISE', 'area': 'ASK_AREA', 'city': 'ASK_CITY',
                  'pincode': 'ASK_PINCODE'}.get(missing[0] if missing else '', 'REPEAT_PINCODE')
        return result('NEEDS_CLARIFICATION', codes=codes, missing=missing, action=action)
    try:
        lookup = PostalLookupResult.model_validate(directory.lookup_pincode(pin.canonical))
        check_source(lookup.provenance, policy, as_of,
                     allow_unverified=getattr(directory,'demo_runtime_ready',False))
        if lookup.pincode != pin.canonical or any(r.pincode != pin.canonical for r in lookup.records):
            raise PostalDataError('POSTAL_DATA_CORRUPT')
        check_record_text(lookup.records)
        states = {state_key(r.state) for r in lookup.records}
        if lookup.records and ('' in states or len(states) != 1):
            raise PostalDataError('POSTAL_DATA_AMBIGUOUS')
        if address.district and any(not comparison(r.district) for r in lookup.records):
            raise PostalDataError('POSTAL_DATA_INCOMPLETE')
    except PostalDataError as exc:
        # Only known internal codes cross the boundary, never arbitrary exception text.
        allowed = {'POSTAL_DATA_STALE', 'POSTAL_DATA_INVALID_DATE', 'POSTAL_DATA_CORRUPT',
            'POSTAL_DATA_AMBIGUOUS', 'POSTAL_DATA_INCOMPLETE', 'POSTAL_CHECKSUM_MISMATCH',
            'POSTAL_SOURCE_UNTRUSTED', 'POSTAL_DATA_UNAVAILABLE'}
        return result('VALIDATION_ERROR', codes=(exc.code if exc.code in allowed else 'POSTAL_DATA_UNAVAILABLE',))
    except Exception:
        return result('VALIDATION_ERROR', codes=('POSTAL_DATA_UNAVAILABLE',))
    source = lookup.provenance
    if not lookup.records:
        return result('NEEDS_CLARIFICATION', codes=('PINCODE_NOT_FOUND',), source=source, action='REPEAT_PINCODE')
    conflicts = []
    if address.state and state_key(address.state) not in states:
        conflicts.append('STATE_PINCODE_CONFLICT')
    if address.district and comparison(address.district) not in {comparison(r.district) for r in lookup.records}:
        conflicts.append('DISTRICT_PINCODE_CONFLICT')
    if conflicts:
        return result('NEEDS_CLARIFICATION', codes=tuple(conflicts), conflicts=tuple(conflicts), source=source,
            action='CLARIFY_STATE_OR_PINCODE' if conflicts[0] == 'STATE_PINCODE_CONFLICT' else 'CLARIFY_DISTRICT_OR_PINCODE')
    values = address.model_dump()
    origins = {o.field: o for o in snapshot.origins}
    reasons = []
    if pin.changed:
        values['pincode'] = pin.canonical
        origins['pincode'] = FieldOrigin(field='pincode', origin='CUSTOMER_NORMALIZED')
        reasons.append('PINCODE_CANONICALIZED')
    if address.state is None:
        values['state'] = sorted(r.state for r in lookup.records)[0]
        origins['state'] = FieldOrigin(field='state', origin='POSTAL_DATA', source=source)
        reasons.append('STATE_DERIVED_FROM_PINCODE')
    if reasons:
        return NormalizationProposal(proposal_id=attempt_id, base_version=snapshot.version,
            base_snapshot=snapshot, canonical=Address(**values),
            origins=tuple(origins[k] for k in Address.model_fields if k in origins),
            policy_version=policy.identity, source=source, reason_codes=tuple(reasons))
    return result('VALID', source=source, action='READY_FOR_READBACK',
                  warnings=('CITY_NOT_POSTALLY_VERIFIED', 'AREA_NOT_POSTALLY_VERIFIED'))
