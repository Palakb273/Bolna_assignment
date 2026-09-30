import unicodedata
from app.domain.address import FrozenModel


class PinNormalization(FrozenModel):
    canonical: str | None = None
    reason_codes: tuple[str, ...] = ()
    changed: bool = False


def normalize_pincode(value: str | None) -> PinNormalization:
    if value is None or not value.replace(' ', ''):
        return PinNormalization(reason_codes=('PINCODE_REQUIRED',))
    try:
        canonical = ''.join(str(unicodedata.decimal(c)) for c in value if c != ' ')
    except (ValueError, TypeError):
        return PinNormalization(reason_codes=('PINCODE_INVALID_FORMAT',))
    if len(canonical) != 6:
        return PinNormalization(reason_codes=('PINCODE_WRONG_LENGTH',))
    return PinNormalization(canonical=canonical, changed=canonical != value)
