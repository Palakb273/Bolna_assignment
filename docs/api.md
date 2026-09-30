# API

OpenAPI is served at /docs and /openapi.json. All /v1 routes require a Bearer credential. Responses avoid echoing request validation inputs. Session summary omits address values. Read-back and accepted-address retrieval necessarily expose the bound customer's address to the authorized call principal.

| Method/path | Credential | Input/result |
|---|---|---|
| POST /v1/address-sessions | BOLNA_SERVICE_TOKEN | customer_external_id, bolna_execution_id, optional name/phone; returns session_id and one-time call_token |
| GET /v1/address-sessions/{id} | Call token | Current status, versions, validation reasons |
| POST /v1/address-sessions/{id}/execution | BOLNA_SERVICE_TOKEN | One-time binding of a pending execution before any candidate changes |
| PATCH /v1/address-sessions/{id}/candidate | Call token | expected_version, changes (nine fields, omitted preserved/null clears) |
| POST /v1/address-sessions/{id}/validate | Call token | expected_version; applies bound normalization and validates new version in same transaction |
| POST /v1/address-sessions/{id}/readback | Call token | expected_version, optional language en/hi; exact text/id/digest |
| POST /v1/address-sessions/{id}/interrupt | Call token | expected_version, reason INTERRUPTED/REJECTED/UNCERTAIN |
| POST /v1/address-sessions/{id}/confirmation-request | Call token | expected_version; waits for evidence, does not confirm |
| POST /v1/address-sessions/{id}/evidence | EVIDENCE_ADAPTER_TOKEN | expected_version, kind, opaque reference; default verifier denies |
| POST /v1/address-sessions/{id}/save | Call token | expected_version; guarded transaction; ADDRESS_SAVED only after commit |
| GET /v1/address-sessions/{id}/address | Call token | Current accepted record only; superseded records not presented as current |
| POST /v1/address-sessions/{id}/tool | Call token | Bolna flat envelope: action, decimal-string version, optional changes_json/language |
| POST /v1/webhooks/bolna | BOLNA_WEBHOOK_TOKEN | execution_id (or id), status, optional event_id/event_timestamp |
| GET /health/live | None | Process liveness |
| GET /health/ready | None | Database role/schema, postal integrity/freshness, required configuration |

Version-sensitive API requests use strict integers; the Bolna tool envelope deliberately parses a bounded decimal string because function parameter templates stringify values. Unknown fields are rejected. The tool route has no evidence operation.

Errors: 400 malformed JSON, 401 missing/invalid privileged credential, 403 wrong session token, 404 missing resource, 409 version/domain/unique conflict, 422 invalid field/schema, 429 local limit, 503 database/validator/backend unavailable. Bodies contain error.code only. A validator evidence failure is recorded transactionally before a 503 response; the address remains ineligible.

After a timeout on save, retry the same session/version: the unique source_session_id/source_version returns the same address ID. After update timeout, retrieve current version before retrying. Revalidating or preparing a fresh read-back revokes earlier consent even without a version change; do not blindly retry these operations.
