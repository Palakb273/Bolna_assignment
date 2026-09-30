from typing import Literal
from pydantic import Field
from app.domain.base import FrozenModel
from app.domain.validation_metadata import PostalDataProvenance


class ValidationPolicy(FrozenModel):
    version: Literal['urban-v1'] = 'urban-v1'
    max_source_age_days: int = Field(default=90, ge=0, le=3660)

    @property
    def identity(self) -> str:
        return f'{self.version}:max-age={self.max_source_age_days}'


class PostalRecord(FrozenModel):
    pincode: str = Field(pattern=r'^[0-9]{6}$')
    office_name: str = Field(min_length=1, max_length=500)
    district: str = Field(min_length=1, max_length=500)
    state: str = Field(min_length=1, max_length=200)
    city: str | None = Field(default=None, max_length=500)
    office_type: str | None = None
    delivery: str | None = None
    division: str | None = None
    region: str | None = None
    circle: str | None = None


class PostalLookupResult(FrozenModel):
    pincode: str = Field(pattern=r'^[0-9]{6}$')
    records: tuple[PostalRecord, ...]
    provenance: PostalDataProvenance
