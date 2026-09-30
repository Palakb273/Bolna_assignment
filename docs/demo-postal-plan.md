# Bounded demo postal integration

User request supplies the design and authorization: explicit development/test opt-in, unverified provenance with unknown official metadata, exact CSV mapping, production fail closed, unchanged versioning/consent/save gates, one live call only. User additionally authorized excluding malformed rows for this demo; strict import remains the default.

1. Add failing tests for configuration, mapping, provenance, runtime selection and deterministic validation.
2. Extend metadata only for honest unknown-source fields; implement exact demo CSV importer with explicit rejection reporting and immutable indexed directory.
3. Select runtime from startup settings; separate trusted/demo readiness and allow unknown freshness only through demo directory capability.
4. Import original file unchanged; select a supported demo PIN/state; test API validation/readback and unchanged consent rejection with real PostgreSQL.
5. Run pytest and original unittest suite, start isolated demo settings, and execute exactly one backed-up/restorable Bolna call.
6. Collect redacted evidence, restore hosted configuration, stop tunnel, produce report; no extra features.
