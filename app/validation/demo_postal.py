"""Explicit development-only CSV adapter; never establishes official trust."""
import csv
import hashlib
import io
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from pydantic import ValidationError
from app.domain.validation_metadata import PostalDataProvenance
from .models import PostalRecord
from .postal_directory import (PostalArtifact, PostalDataError, LocalPostalDirectory,
    records_bytes, check_record_text, load_directory)

MAPPING = {'PostOfficeName':'office_name','Pincode':'pincode','DistrictsName':'district','City':'city','State':'state'}


def import_demo_csv(path: Path, *, reject_malformed_rows=False):
    try:
        raw=path.read_bytes()
        reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),strict=True)
        if len(reader.fieldnames or [])!=len(MAPPING) or set(reader.fieldnames or [])!=set(MAPPING):
            raise PostalDataError('POSTAL_SCHEMA_MISMATCH')
        records=[]
        counts=Counter()
        read=rejected=0
        for row in reader:
            read+=1
            reasons=[]
            if None in row or any(v is None for v in row.values()):
                reasons.append('ROW_SHAPE_MISMATCH')
            else:
                values={target:row[col].strip() for col,target in MAPPING.items()}
                for name in ('pincode','state','district','office_name'):
                    if not values[name]: reasons.append('MISSING_'+name.upper())
                if values['pincode'] and not re.fullmatch(r'[1-9][0-9]{5}',values['pincode']):
                    reasons.append('MALFORMED_PINCODE')
                values['city']=values['city'] or None
                if not reasons:
                    try:
                        record=PostalRecord(**values)
                        check_record_text((record,))
                    except (ValidationError,PostalDataError):
                        reasons.append('INVALID_SOURCE_TEXT')
            if reasons:
                rejected+=1
                counts.update(reasons)
            else:
                records.append(record)
        report={'rows_read':read,'rows_accepted':len(records),'rows_rejected':rejected,
            'unique_pins':len({r.pincode for r in records}),'malformed_reason_counts':dict(counts)}
        if rejected and not reject_malformed_rows:
            raise PostalDataError('POSTAL_MALFORMED_ROWS')
        if not records: raise PostalDataError('POSTAL_DATA_EMPTY')
        source=PostalDataProvenance(source_name='User-supplied development CSV',original_filename=path.name,
            imported_at=datetime.now(timezone.utc),source_sha256=hashlib.sha256(raw).hexdigest(),
            records_sha256=hashlib.sha256(records_bytes(tuple(records))).hexdigest(),
            dataset_kind='UNVERIFIED',source_kind='UNVERIFIED_OR_STALE')
        report.update(source.model_dump(mode='json'),trusted_runtime_ready=False,demo_runtime_ready=True)
        return PostalArtifact(provenance=source,records=tuple(records)),report
    except PostalDataError:
        raise
    except (OSError,UnicodeError,csv.Error,ValueError):
        raise PostalDataError('POSTAL_IMPORT_FAILED') from None


def select_directory(settings,policy,as_of):
    path=Path(settings.postal_data_path or '__missing_postal__')
    if not settings.allow_unverified_postal_data:
        return load_directory(path,policy,as_of)
    if settings.app_env not in {'development','test'}:
        raise ValueError('Unverified data is forbidden in production')
    try:
        if path.suffix.lower()=='.csv':
            artifact,_=import_demo_csv(path,reject_malformed_rows=settings.demo_reject_malformed_rows)
        else:
            artifact=PostalArtifact.model_validate_json(path.read_bytes())
            check_record_text(artifact.records)
            if not artifact.records or hashlib.sha256(records_bytes(artifact.records)).hexdigest()!=artifact.provenance.records_sha256:
                raise PostalDataError('POSTAL_CHECKSUM_MISMATCH')
        if artifact.provenance.source_kind!='UNVERIFIED_OR_STALE' or artifact.provenance.dataset_kind!='UNVERIFIED':
            return load_directory(path,policy,as_of)
        return LocalPostalDirectory(artifact,demo=True)
    except PostalDataError as exc:
        return LocalPostalDirectory(error_code=exc.code)
    except (OSError,ValueError):
        return LocalPostalDirectory(error_code='POSTAL_DATA_UNAVAILABLE')
