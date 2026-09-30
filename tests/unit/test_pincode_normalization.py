import pytest
from app.validation.normalization import normalize_pincode


@pytest.mark.parametrize('value,canonical,code,changed', [
    ('500032', '500032', None, False), ('500 032', '500032', None, True),
    ('५०००३२', '500032', None, True), (None, None, 'PINCODE_REQUIRED', False),
    ('50003', None, 'PINCODE_WRONG_LENGTH', False),
    ('5000327', None, 'PINCODE_WRONG_LENGTH', False),
    *[(v, None, 'PINCODE_INVALID_FORMAT', False) for v in
      ('500O32', '⁵00032', '500-032', '500\u200b032', '500\t032')],
])
def test_pin_rules(value, canonical, code, changed):
    result = normalize_pincode(value)
    assert result.canonical == canonical
    assert result.reason_codes == (() if code is None else (code,))
    assert result.changed is changed
    if canonical:
        assert not normalize_pincode(canonical).changed
