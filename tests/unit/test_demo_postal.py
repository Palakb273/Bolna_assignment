import hashlib
from datetime import date
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.settings import Settings
from app.api import create_app
from app.validation.models import ValidationPolicy
from app.validation.postal_directory import PostalDataError, load_directory
from test_validation_engine import run, snapshot

HEADER = 'PostOfficeName,Pincode,DistrictsName,City,State\n'
ROW = 'Office,500032,District,City,Example State\n'


def fixture_csv(tmp_path, rows=ROW, header=HEADER):
    path = tmp_path/'pincodes.csv'
    path.write_text(header+rows,encoding='utf-8-sig')
    return path


@pytest.mark.parametrize('env',['development','test'])
def test_demo_setting_allowed_only_explicitly(env):
    assert Settings(app_env=env,allow_unverified_postal_data=True).allow_unverified_postal_data


def test_config_default_and_production_guard(monkeypatch):
    assert not Settings().allow_unverified_postal_data
    with pytest.raises(ValueError):
        Settings(app_env='production',allow_unverified_postal_data=True)
    monkeypatch.setenv('APP_ENV','production')
    monkeypatch.setenv('ALLOW_UNVERIFIED_POSTAL_DATA','true')
    with pytest.raises(ValueError):
        Settings.from_env()


def test_mapping_provenance_and_runtime(tmp_path):
    from app.validation.demo_postal import import_demo_csv, select_directory
    path = fixture_csv(tmp_path,ROW*2)
    artifact, report = import_demo_csv(path)
    p = artifact.provenance
    assert p.source_kind=='UNVERIFIED_OR_STALE' and p.original_filename=='pincodes.csv'
    assert p.resource_url is None and p.resource_id is None and p.source_date is None
    assert p.source_sha256==hashlib.sha256(path.read_bytes()).hexdigest()
    assert p.records_sha256==import_demo_csv(path)[0].provenance.records_sha256
    assert report['rows_read']==report['rows_accepted']==2 and report['unique_pins']==1
    assert len(artifact.records)==2 and artifact.records[0].city=='City'
    cfg=Settings(app_env='test',allow_unverified_postal_data=True,postal_data_path=str(path))
    directory=select_directory(cfg,ValidationPolicy(),date.today())
    assert directory.demo_runtime_ready and not directory.trusted_runtime_ready
    result=run(snapshot(state='Example State'),directory)
    assert result.status=='VALID' and result.source.source_kind=='UNVERIFIED_OR_STALE'
    assert run(snapshot(pincode='999999'),directory).status=='NEEDS_CLARIFICATION'
    assert run(snapshot(state='Wrong'),directory).reason_codes==('STATE_PINCODE_CONFLICT',)
    assert not select_directory(Settings(postal_data_path=str(path)),ValidationPolicy(),date.today()).ready
    output=tmp_path/'artifact.json'
    output.write_text(artifact.model_dump_json())
    assert not load_directory(output,ValidationPolicy(),date.today()).ready


@pytest.mark.parametrize('header',[HEADER.lower(),HEADER.replace('DistrictsName','District'),HEADER.replace('City,','Town,')])
def test_no_fuzzy_mapping(tmp_path,header):
    from app.validation.demo_postal import import_demo_csv
    with pytest.raises(PostalDataError,match='POSTAL_SCHEMA_MISMATCH'):
        import_demo_csv(fixture_csv(tmp_path,header=header))


def test_strict_default_and_explicit_exclusion(tmp_path):
    from app.validation.demo_postal import import_demo_csv
    path=fixture_csv(tmp_path,ROW+'Office,bad,District,,State\n'+',,,,\n')
    with pytest.raises(PostalDataError):
        import_demo_csv(path)
    artifact,report=import_demo_csv(path,reject_malformed_rows=True)
    assert (report['rows_read'],report['rows_accepted'],report['rows_rejected'])==(3,1,2)
    assert report['malformed_reason_counts']['MALFORMED_PINCODE']==1
    for field in ('PINCODE','STATE','DISTRICT','OFFICE_NAME'):
        assert report['malformed_reason_counts']['MISSING_'+field]==1
    assert len(artifact.records)==1


def test_optional_city_and_multiple_districts(tmp_path):
    from app.validation.demo_postal import select_directory
    path=fixture_csv(tmp_path,ROW+'Other office,500032,Other district,,Example State\n')
    d=select_directory(Settings(app_env='test',allow_unverified_postal_data=True,postal_data_path=str(path)),ValidationPolicy(),date.today())
    assert d.ready and run(snapshot(state='Example State',district='Other district'),d).status=='VALID'
    path.write_text(HEADER+ROW+'Other,500032,District,City,Contradictory State\n')
    d=select_directory(Settings(app_env='test',allow_unverified_postal_data=True,postal_data_path=str(path)),ValidationPolicy(),date.today())
    assert run(snapshot(state='Example State'),d).reason_codes==('POSTAL_DATA_AMBIGUOUS',)


def test_demo_cannot_make_production_health_ready(tmp_path):
    path=fixture_csv(tmp_path)
    class ReadyRepo:
        def ready(self): return True
    c=TestClient(create_app(Settings(app_env='development',allow_unverified_postal_data=True,
        postal_data_path=str(path),admin_token='a'*40),repository=ReadyRepo()))
    response=c.get('/health/ready')
    assert response.status_code==503
    assert response.json()['demo_runtime_ready'] is True
    assert response.json()['trusted_runtime_ready'] is False
