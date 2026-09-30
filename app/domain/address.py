"""Strict candidate schemas. Postal validation is a later milestone."""

import unicodedata
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

from .errors import DomainError
from .base import FrozenModel
from .validation_metadata import FieldOrigin, PostalDataProvenance


class Address(FrozenModel):
    house_flat: str | None = Field(default=None, max_length=100)
    building: str | None = Field(default=None, max_length=200)
    street: str | None = Field(default=None, max_length=200)
    area: str | None = Field(default=None, max_length=200)
    landmark: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=200)
    district: str | None = Field(default=None, max_length=200)
    state: str | None = Field(default=None, max_length=200)
    pincode: str | None = Field(default=None, max_length=32)

    @field_validator('*')
    @classmethod
    def check_text(cls, value: str | None) -> str | None:
        if value is not None and (not value.strip() or any(
                unicodedata.category(char) in {'Cc', 'Cs'} for char in value)):
            raise ValueError('Use nonblank text without control characters, or null.')
        return value


class AddressChanges(Address):
    @model_validator(mode='after')
    def require_changes(self) -> Self:
        if not self.model_fields_set:
            raise ValueError('Supply at least one field.')
        return self


class AddressVersion(FrozenModel):
    version: Annotated[StrictInt, Field(gt=0)]
    raw: Address
    canonical: Address
    origins: tuple[FieldOrigin, ...] = ()
    normalization_id: UUID | None = None
    policy_version: str | None = None

    @model_validator(mode='after')
    def complete_origins(self):
        fields = {k for k, v in self.canonical.model_dump().items() if v is not None}
        if not self.origins:
            object.__setattr__(self, 'origins', tuple(FieldOrigin(field=k, origin='CUSTOMER')
                                                   for k in Address.model_fields if k in fields))
        elif len(self.origins) != len(fields) or {o.field for o in self.origins} != fields:
            raise ValueError('Origins must uniquely cover populated canonical fields.')
        return self


class NormalizationProposal(FrozenModel):
    session_id: UUID | None = None
    proposal_id: UUID
    base_version: Annotated[StrictInt, Field(gt=0)]
    base_snapshot: AddressVersion
    canonical: Address
    origins: tuple[FieldOrigin, ...]
    policy_version: str = Field(min_length=1, max_length=100)
    source: PostalDataProvenance | None = None
    reason_codes: tuple[str, ...] = ()
    next_action: str = 'APPLY_NORMALIZATION'


def apply_changes(address: Address, changes: AddressChanges) -> Address:
    values = address.model_dump()
    values.update(changes.model_dump(exclude_unset=True))
    return Address.model_validate(values)


def render_readback(address: Address, language: str = 'en') -> str:
    labels = {'house_flat': 'house or flat', 'pincode': 'PIN'}
    if language not in ('en', 'hi'):
        raise DomainError('UNSUPPORTED_LANGUAGE')
    if language == 'hi':
        labels = dict(house_flat='घर या फ्लैट', building='इमारत', street='सड़क', area='इलाका',
                      landmark='नज़दीकी पहचान', city='शहर', district='ज़िला', state='राज्य', pincode='पिन')
    parts = []
    for field, value in address.model_dump().items():
        if value is not None:
            spoken = ', '.join(value) if field == 'pincode' else value
            parts.append(f'{labels.get(field, field)} {spoken}')
    if not parts:
        raise DomainError('EMPTY_ADDRESS')
    text = '; '.join(parts)
    return text[0].upper() + text[1:] + ('. क्या यह पूरा पता सही है?' if language == 'hi' else '. Is this full address correct?')
