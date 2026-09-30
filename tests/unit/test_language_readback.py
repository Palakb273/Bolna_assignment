from uuid import uuid4
from app.domain.confirmation import prepare_readback, complete_readback


def test_hindi_text_is_exact_and_evidence_bound(validated, verifier):
    s = prepare_readback(validated(), uuid4(), language='hi')
    assert 'पिन' in s.readback.rendered_text
    assert '5, 0, 0, 0, 3, 2' in s.readback.rendered_text
    s = complete_readback(s, verifier.issue(s, 'READBACK_COMPLETED', 1), verifier)
    assert s.status == 'WAITING_CONFIRMATION'
