import json
import logging
from contextvars import ContextVar

request_id = ContextVar('request_id', default=None)
logger = logging.getLogger('address_backend')


def log_transition(state, operation):
    logger.info(json.dumps({'request_id': request_id.get(), 'session_id': str(state.session_id),
        'execution_id': state.bolna_execution_id, 'operation': operation, 'version': state.current_version,
        'status': state.status, 'reason_codes': list(state.validation_attempts[-1].reason_codes) if state.validation_attempts else []}))
