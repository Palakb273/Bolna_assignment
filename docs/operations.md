# Operations

Use Python 3.11+ and Docker Desktop's Linux engine. Never overwrite an existing .env. Generate the separate local config once; generation deliberately refuses an existing output.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e '.[dev]'
.venv\Scripts\python.exe scripts/init_local_config.py
docker compose --env-file local-data/development.env up -d postgres
.venv\Scripts\python.exe scripts/run_local.py migrate upgrade head
.venv\Scripts\python.exe scripts/run_local.py serve
```

Start the API after migrations. It listens at http://127.0.0.1:8000. /health/live is independent of readiness. Missing/stale/unverified postal data keeps /health/ready false and validation fails closed. Install a verified artifact at POSTAL_DATA_PATH; see postal-data.md. Environment changes require process restart.

Optional backend container (build/download not implied by local Python verification):

```powershell
docker compose --env-file local-data/development.env up -d --build backend
```

Migration rollback is destructive to affected schema/data. Back up first and use the owner connection, never the runtime role. The isolated migration test creates its own fresh database and tests upgrade/downgrade/upgrade without touching application tables:

```powershell
.venv\Scripts\python.exe scripts/check_migrations.py
```

The named Docker volume preserves data across container restart. Do not run `down -v` to stop the service. Use `docker compose --env-file local-data/development.env stop` to retain data. Runtime and owner passwords are generated independently; changing the environment file does not rotate an existing database role password automatically.

For production use a managed PostgreSQL service and a TLS reverse proxy. Disable access/body logging, apply gateway rate limits and restrict webhook source addresses. Keep generated private artifacts out of backups shared with reviewers. Configure data retention and encrypted recovery procedures before production.
