import json
from datetime import date, datetime, timezone
import pytest
from app.validation.postal_directory import import_csv, load_directory, ImportMetadata, PostalDataError
from app.validation.models import ValidationPolicy

HEADER = 'circlename,regionname,divisionname,officename,pincode,officetype,delivery,district,statename\n'
ROWS = 'Circle,Region,Division,Example A,500032,SO,Delivery,Example District,Telangana\n'


def metadata():
    # Synthetic CSV tests exercise importer mechanics, not official acquisition.
    return ImportMetadata(source_name='Department of Posts', resource_url='https://www.data.gov.in/resource/test',
        resource_id='test', source_date=date(2026, 9, 1),
        imported_at=datetime(2026, 9, 2, tzinfo=timezone.utc),
        retrieved_at=datetime(2026, 9, 2, tzinfo=timezone.utc), source_kind='OFFICIAL_POSTAL_DIRECTORY')


def create(tmp_path, rows=ROWS, header=HEADER):
    src, out = tmp_path/'source.csv', tmp_path/'postal.json'
    src.write_text(header + rows, encoding='utf-8-sig')
    provenance = import_csv(src, out, metadata())
    return src, out, provenance


def test_duplicate_rows_and_index(tmp_path):
    _, out, p = create(tmp_path, ROWS * 2)
    directory = load_directory(out, ValidationPolicy(), date(2026, 9, 30))
    assert directory.ready
    lookup = directory.lookup_pincode('500032')
    assert len(lookup.records) == 2 and lookup.provenance == p
    assert directory.lookup_pincode('110001').records == ()


@pytest.mark.parametrize('bad', ['X,broken\n', ROWS.replace('500032', '50003'),
    ROWS.replace('Telangana', ''), ROWS.replace('Example District', ''),
    ROWS.replace('Telangana', 'Telan\x00gana')])
def test_bad_late_row_publishes_nothing(tmp_path, bad):
    with pytest.raises(PostalDataError):
        create(tmp_path, ROWS + bad)
    assert not (tmp_path/'postal.json').exists()


@pytest.mark.parametrize('header', [HEADER.replace('district,', ''), HEADER.replace('district', 'pincode')])
def test_bad_headers(tmp_path, header):
    with pytest.raises(PostalDataError):
        create(tmp_path, header=header)


def test_encoding_and_existing_output(tmp_path):
    src, out, _ = create(tmp_path)
    before = out.read_bytes()
    with pytest.raises(PostalDataError):
        import_csv(src, out, metadata())
    assert out.read_bytes() == before
    src.write_bytes(b'\xff\xfe')
    with pytest.raises(PostalDataError):
        import_csv(src, tmp_path/'bad.json', metadata())


@pytest.mark.parametrize('change', ['tamper', 'missing', 'synthetic'])
def test_untrusted_artifact_not_ready(tmp_path, change):
    _, out, _ = create(tmp_path)
    obj = json.loads(out.read_text())
    if change == 'tamper':
        obj['records'][0]['state'] = 'Delhi'
    elif change == 'missing':
        del obj['provenance']['source_sha256']
    else:
        obj['provenance']['dataset_kind'] = 'SYNTHETIC'
    out.write_text(json.dumps(obj))
    directory = load_directory(out, ValidationPolicy(), date(2026, 9, 30))
    assert not directory.ready
    with pytest.raises(PostalDataError):
        directory.lookup_pincode('500032')


def test_hash_order_and_freshness(tmp_path):
    row_b = ROWS.replace('Example A', 'Example B')
    _, out, p = create(tmp_path, ROWS + row_b)
    other = tmp_path/'other'
    other.mkdir()
    _, _, q = create(other, row_b + ROWS)
    assert p.records_sha256 == q.records_sha256
    assert p.source_sha256 != q.source_sha256
    assert load_directory(out, ValidationPolicy(), date(2026, 11, 30)).ready
    assert not load_directory(out, ValidationPolicy(), date(2026, 12, 1)).ready
    assert not load_directory(out, ValidationPolicy(), date(2026, 8, 1)).ready
    obj = json.loads(out.read_text())
    obj['provenance']['imported_at'] = '2026-12-01T00:00:00Z'
    out.write_text(json.dumps(obj))
    assert not load_directory(out, ValidationPolicy(), date(2026, 12, 1)).ready
