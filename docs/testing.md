# Testing

```powershell
.venv\Scripts\python.exe -m pytest -q
python -m unittest discover -s tests -q
.venv\Scripts\python.exe scripts/run_local.py test -q
.venv\Scripts\python.exe scripts/check_migrations.py
.venv\Scripts\python.exe scripts/check_durability.py write
docker compose --env-file local-data/development.env restart postgres
.venv\Scripts\python.exe scripts/check_durability.py check
```

The ordinary pytest command skips PostgreSQL tests unless TEST_DATABASE_URL is set. run_local.py test uses only the generated local config and activates real PostgreSQL tests. SQLite is never used as PostgreSQL evidence. Tests add uniquely named synthetic customers/sessions to the local development database; no real customer address is needed.

Coverage includes original helpers, strict schemas, Unicode PINs, immutable version/origin history, confirmation binding/replay, postal errors/provenance/freshness, API authentication/ownership, malformed JSON, oversized/unknown fields, SQL-like text parameterization, webhook duplicate/out-of-order handling, concurrent update winner, concurrent idempotent saves, commit-failure rollback, real foreign keys/unique constraints and immutable-table privileges.

API success-path tests inject a synthetic directory/verifier only into the test application's constructor. Production startup has no synthetic evidence switch. These tests do not prove official PIN facts, playback, customer consent or actual Bolna tool substitution.

One framework warning currently notes Starlette's future move from httpx to httpx2; the requested httpx test client works in the pinned versions. Record exact latest counts in final-report.md, not inferred counts.

Real voice scenarios: happy path, progressive/full first-turn address, PIN zeros, Hindi, Hinglish, correction, barge-in, correction during confirmation, yes-but, difficult building name, silence, refusal, busy, human request and backend failure. For each record conversation_outcome, backend_outcome and test_result independently. Initial voice test_result is NOT_RUN; never infer confirmation from call completion.
