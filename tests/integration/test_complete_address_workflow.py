import os
from pathlib import Path
import pytest
from app.api import create_app
from app.settings import Settings
from app.domain.confirmation import RejectAllEvidenceVerifier
from app.domain.errors import DomainError
from app.demo_evidence import SyntheticDemoEvidenceVerifier
from scripts.demo_end_to_end import run_demo


def test_production_rejects_demo_adapter():
    adapter = SyntheticDemoEvidenceVerifier('test')
    with pytest.raises(ValueError, match='production'):
        create_app(Settings(app_env='production'), evidence_verifier=adapter)
    with pytest.raises(ValueError, match='production'):
        SyntheticDemoEvidenceVerifier('production')


def test_production_rejects_demo_postal():
    with pytest.raises(ValueError):
        Settings(app_env='production', allow_unverified_postal_data=True)


def test_default_verifier_rejects_synthetic_reference():
    with pytest.raises(DomainError, match='EVIDENCE_UNAVAILABLE'):
        RejectAllEvidenceVerifier().verify('SYNTHETIC-demo-reference')


@pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL'), reason='Real PostgreSQL required')
@pytest.mark.parametrize('pin_input,normalized', [('110001',False), ('1 1 0 0 0 1',True)])
def test_complete_workflow(tmp_path,pin_input,normalized):
    csv=tmp_path/'pincodes.csv'
    csv.write_text('PostOfficeName,Pincode,DistrictsName,City,State\nConnaught Place,110001,New Delhi,New Delhi,Delhi\n')
    result=run_demo(os.environ['TEST_DATABASE_URL'],csv,emit=lambda text: None,pin_input=pin_input)
    assert result['test_result']=='PASS'
    assert result['counts']['addresses']==1
    assert result['counts']['confirmation_events']==2
    assert result['current_version']==result['validated_version']==result['confirmed_version']
    assert result['normalization_observed']==normalized
    assert result['stale_reason']=='EVIDENCE_BINDING_MISMATCH'
    assert result['premature_save_reason']=='ADDRESS_NOT_CONFIRMED'
    assert result['duplicate_address_id']==result['address_id']

