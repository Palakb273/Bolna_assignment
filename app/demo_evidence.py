"""SYNTHETIC evidence for an in-process offline demonstration only.

No HTTP route or environment switch selects this adapter. Production startup
rejects it even if constructed with a development setting elsewhere.
"""
from uuid import uuid4
from .domain.session import VerifiedEvidence
from .domain.errors import DomainError


class SyntheticDemoEvidenceVerifier:
    nonproduction_only = True

    def __init__(self, app_env):
        if app_env not in {'development', 'test'}:
            raise ValueError('Synthetic demo evidence is forbidden in production')
        self._records = {}

    def issue(self, readback, kind, sequence):
        reference = 'SYNTHETIC-' + str(uuid4())
        self._records[reference] = VerifiedEvidence(
            evidence_id=uuid4(), kind=kind, session_id=readback.session_id,
            execution_id=readback.execution_id, version=readback.version,
            validation_attempt_id=readback.validation_attempt_id,
            readback_id=readback.id, text_digest=readback.text_digest,
            source_sequence=sequence)
        return reference

    def verify(self, reference):
        if reference not in self._records:
            raise DomainError('EVIDENCE_UNAVAILABLE')
        return self._records[reference]
