# Phase 2B implementation report

Status: implementation and synthetic checks complete; official-file ingestion and independent review remain pending. Phase 2B is not yet fully accepted. Phase 2 overall remains incomplete.

Implemented deterministic PIN normalization, urban completeness checks, conservative state/district matching, city/area warnings, versioned normalization preserving raw input, field origins and derivation invalidation, immutable validation metadata, manual CSV ingestion, checksum verification, local lookup and fail-closed freshness/readiness.

## Verification

- Full suite: 159 passed, 26 subtests passed.
- Original Phase 1 unittest command: 18 passed.
- Import CLI help: passed.
- Independent review: attempted but reviewer stopped on a usage-limit error; no independent verdict was produced. Author self-review completed instead and found/fixed malformed postal-text handling with failing-then-passing regressions. This does not satisfy the independent-review gate.
- Official CSV acquisition/import/lookup: NOT_RUN. The resource fetch returned a sandbox notice, catalog fetch timed out, and India Post circle listing exposed PDFs. No official release or geographic fixture facts have been invented.
- Live conversation_outcome: null. Live backend_outcome: null. Live test_result: NOT_RUN.

Tests cover raw preservation, stale versions/proposals, v3 confirmed → v4 normalized with revoked evidence, origin-aware customer patches, metadata attempt reuse, malformed Unicode, directory corruption/expiry, conflicts, multiple district matches and continued default-deny confirmation. Synthetic tests establish code behavior only.

## Usage and limits

See [postal-data.md](postal-data.md) for source checks, import command, freshness policy and trust boundaries; [execution ledger](phase2b-progress.md) for implementation evidence; [plan](superpowers/plans/2026-09-30-phase2b-validation.md) for remaining acceptance work.

The supplied directory and normalization proposals are trusted internal inputs, not agent/API request schemas. Frozen Python objects are not a sandbox. Importer mechanics tests use synthetic CSVs under temporary paths while simulating an operator; none are runtime reference files. A valid result checks completeness and postal consistency, not the physical existence/deliverability of a premise, city or locality. Official source authenticity remains an operator obligation.

Remaining gates: finish independent review and acquire a verifiable current official CSV, confirm/map its headers, import it, retain provenance/checksums and verify actual lookups. If its headers differ, add an explicit tested mapping instead of silently guessing. After those gates, Phase 2C introduces persistence. No API, database, actual voice evidence, deployment or live address save was implemented.
