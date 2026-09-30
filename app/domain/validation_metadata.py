"""Immutable reference metadata; no engine dependency and no customer payloads."""
from datetime import date, datetime
from typing import Literal
from pydantic import Field, model_validator
from .base import FrozenModel

AddressField = Literal['house_flat', 'building', 'street', 'area', 'landmark', 'city', 'district', 'state', 'pincode']


class PostalDataProvenance(FrozenModel):
    source_name: str = Field(min_length=1, max_length=200)
    resource_url: str | None = Field(default=None, min_length=1, max_length=1000)
    resource_id: str | None = Field(default=None, min_length=1, max_length=200)
    source_date: date | None = None
    original_filename: str | None = Field(default=None, max_length=255)
    imported_at: datetime
    source_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    records_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    format_version: Literal[1] = 1
    dataset_kind: Literal['OFFICIAL', 'SYNTHETIC', 'UNVERIFIED']
    source_kind: Literal['OFFICIAL_POSTAL_DIRECTORY', 'SYNTHETIC', 'UNVERIFIED_OR_STALE'] = 'UNVERIFIED_OR_STALE'
    retrieved_at: datetime | None = None

    @model_validator(mode='after')
    def chronology(self):
        if (self.dataset_kind != 'UNVERIFIED' or self.source_kind == 'OFFICIAL_POSTAL_DIRECTORY') and (
                self.resource_url is None or self.resource_id is None or self.source_date is None):
            raise ValueError('Known provenance required for official/synthetic artifacts.')
        if self.dataset_kind == 'UNVERIFIED' and self.source_kind != 'UNVERIFIED_OR_STALE':
            raise ValueError('Unverified artifact must retain unverified source kind.')
        if self.imported_at.utcoffset() is None or self.imported_at.utcoffset().total_seconds() != 0:
            raise ValueError('Import timestamp must be UTC.')
        if self.source_date is not None and self.imported_at.date() < self.source_date:
            raise ValueError('Invalid source chronology.')
        if self.retrieved_at is not None and (self.retrieved_at.utcoffset() is None
                or self.retrieved_at > self.imported_at or (self.source_date is not None and self.retrieved_at.date() < self.source_date)):
            raise ValueError('Invalid retrieval chronology.')
        return self


class FieldOrigin(FrozenModel):
    field: AddressField
    origin: Literal['CUSTOMER', 'CUSTOMER_NORMALIZED', 'POSTAL_DATA']
    source: PostalDataProvenance | None = None

    @model_validator(mode='after')
    def derived_source(self):
        if (self.origin == 'POSTAL_DATA') != (self.source is not None):
            raise ValueError('Postal origin requires postal provenance exclusively.')
        return self


class ConflictDetail(FrozenModel):
    code: str = Field(pattern=r'^[A-Z][A-Z0-9_]{0,63}$')
    fields: tuple[AddressField, ...]
