"""Trusted-operator import and fail-closed immutable runtime directory."""
import csv
import hashlib
import io
import json
import os
import tempfile
import unicodedata
from datetime import date, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Protocol, Literal
from urllib.parse import urlparse
from pydantic import Field
from app.domain.base import FrozenModel
from app.domain.validation_metadata import PostalDataProvenance
from .models import PostalRecord, PostalLookupResult, ValidationPolicy


class PostalDataError(ValueError):
    def __init__(self, code='POSTAL_DATA_CORRUPT'):
        self.code = code
        super().__init__(code)


class ImportMetadata(FrozenModel):
    source_name: str = Field(min_length=1, max_length=200)
    resource_url: str = Field(min_length=1, max_length=1000)
    resource_id: str = Field(min_length=1, max_length=200)
    source_date: date
    imported_at: datetime
    retrieved_at: datetime | None = None
    source_kind: Literal['OFFICIAL_POSTAL_DIRECTORY', 'UNVERIFIED_OR_STALE'] = 'UNVERIFIED_OR_STALE'


class PostalDirectory(Protocol):
    def lookup_pincode(self, pincode: str) -> PostalLookupResult: ...


class PostalArtifact(FrozenModel):
    provenance: PostalDataProvenance
    records: tuple[PostalRecord, ...]


def records_bytes(records: tuple[PostalRecord, ...]) -> bytes:
    # Preserve the previous official artifact digest when no city was supplied.
    rows = [{k:v for k,v in r.model_dump().items() if k != 'city' or v is not None} for r in records]
    rows.sort(key=lambda r: json.dumps(r, sort_keys=True, ensure_ascii=False))
    return json.dumps(rows, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def check_record_text(records: tuple[PostalRecord, ...]) -> None:
    for record in records:
        if any(value is not None and (not value.strip() or any(
                unicodedata.category(c) in {'Cc', 'Cs'} for c in value))
                for value in record.model_dump().values()):
            raise PostalDataError('POSTAL_DATA_CORRUPT')


def check_source(source: PostalDataProvenance, policy: ValidationPolicy, as_of: date, *, allow_unverified=False) -> None:
    if allow_unverified and source.source_kind=='UNVERIFIED_OR_STALE' and source.dataset_kind=='UNVERIFIED':
        return  # Explicit demo capability only; no fabricated official freshness.
    if source.source_date is None:
        raise PostalDataError('POSTAL_SOURCE_UNTRUSTED')
    if source.source_date > as_of or source.imported_at.date() > as_of:
        raise PostalDataError('POSTAL_DATA_INVALID_DATE')
    if (as_of - source.source_date).days > policy.max_source_age_days:
        raise PostalDataError('POSTAL_DATA_STALE')


def official_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or ''
    return parsed.scheme == 'https' and any(host == domain or host.endswith('.' + domain)
        for domain in ('data.gov.in', 'indiapost.gov.in'))


def import_csv(source: Path, output: Path, provenance_inputs: ImportMetadata) -> PostalDataProvenance:
    """Operator establishes authenticity; this operation establishes schema/integrity."""
    mapping = dict(circlename='circle', regionname='region', divisionname='division',
        officename='office_name', pincode='pincode', officetype='office_type', delivery='delivery',
        district='district', statename='state')
    try:
        if not official_url(provenance_inputs.resource_url):
            raise PostalDataError('POSTAL_SOURCE_UNTRUSTED')
        raw = source.read_bytes()
        reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')), strict=True)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)) or not set(mapping) <= set(headers):
            raise PostalDataError('POSTAL_SCHEMA_MISMATCH')
        records = []
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise PostalDataError()
            values = {target: row[col].strip() for col, target in mapping.items()}
            for key in ('circle', 'region', 'division', 'office_type', 'delivery'):
                values[key] = values[key] or None
            records.append(PostalRecord(**values))
        if not records:
            raise PostalDataError('POSTAL_DATA_EMPTY')
        check_record_text(tuple(records))
        payload = records_bytes(tuple(records))
        provenance = PostalDataProvenance(**provenance_inputs.model_dump(),
            source_sha256=hashlib.sha256(raw).hexdigest(), records_sha256=hashlib.sha256(payload).hexdigest(),
            dataset_kind='OFFICIAL')
        artifact = b'{"provenance":' + provenance.model_dump_json().encode() + b',"records":' + payload + b'}'
        # Same-directory temporary file plus exclusive hard-link publication avoids partial output or overwrite.
        output.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(dir=output.parent, suffix='.tmp', delete=False) as temp:
                temp_path = Path(temp.name)
                temp.write(artifact)
                temp.flush()
                os.fsync(temp.fileno())
            os.link(temp_path, output)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
        return provenance
    except PostalDataError:
        raise
    except Exception:
        raise PostalDataError('POSTAL_IMPORT_FAILED') from None


class LocalPostalDirectory:
    def __init__(self, artifact: PostalArtifact | None = None, error_code: str | None = None, *, demo=False):
        index = {}
        if artifact:
            for row in artifact.records:
                index.setdefault(row.pincode, []).append(row)
        self._index = MappingProxyType({pin: tuple(rows) for pin, rows in index.items()})
        self._source = artifact.provenance if artifact else None
        self.error_code = error_code
        self.ready = artifact is not None and error_code is None
        self.demo_runtime_ready = self.ready and demo and self._source.source_kind=='UNVERIFIED_OR_STALE'
        self.trusted_runtime_ready = self.ready and not demo and self._source.source_kind=='OFFICIAL_POSTAL_DIRECTORY'

    def lookup_pincode(self, pincode: str) -> PostalLookupResult:
        if not self.ready:
            raise PostalDataError(self.error_code or 'POSTAL_DATA_UNAVAILABLE')
        return PostalLookupResult(pincode=pincode, records=self._index.get(pincode, ()), provenance=self._source)


def load_directory(path: Path, policy: ValidationPolicy, as_of: date) -> LocalPostalDirectory:
    try:
        artifact = PostalArtifact.model_validate_json(path.read_bytes())
        check_record_text(artifact.records)
        if (artifact.provenance.dataset_kind != 'OFFICIAL'
                or artifact.provenance.source_kind != 'OFFICIAL_POSTAL_DIRECTORY'
                or artifact.provenance.retrieved_at is None
                or not official_url(artifact.provenance.resource_url)):
            raise PostalDataError('POSTAL_SOURCE_UNTRUSTED')
        if not artifact.records or hashlib.sha256(records_bytes(artifact.records)).hexdigest() != artifact.provenance.records_sha256:
            raise PostalDataError('POSTAL_CHECKSUM_MISMATCH')
        check_source(artifact.provenance, policy, as_of)
        return LocalPostalDirectory(artifact)
    except PostalDataError as exc:
        return LocalPostalDirectory(error_code=exc.code)
    except Exception:
        return LocalPostalDirectory(error_code='POSTAL_DATA_UNAVAILABLE')
