# Ledger — docs/superpowers/plans/2026-09-30-phase2a-domain.md

Execution approved. Scope: Phase 2A only, direct execution, strict evidence gate.
Baseline: original unittest suite 18/18 PASS. Project-local Python environment available; Pydantic 2.13.5 and pytest 9.1.1 installed. No secrets read.
Preflight: Task 1 Address feeds Task 2 snapshots; Task 2 Session/ValidationResult feeds Task 3 evidence binding; Task 4 rechecks all guards. Confirmation models will live in session.py to avoid circular dependencies; operations and verifier live in confirmation.py.
Ruling: No Git repository/worktree was available in the supplied project; retain a ledger rather than inventing commit history. Cost: changes lack Git snapshots.
Ruling: Distinguish verification trust from Python object construction. Domain operations accept evidence only through a process-injected verifier; no public routes exist. A future trusted adapter must establish provenance. In-process Python types are not a security sandbox.

Task 1: complete. New test file initially failed for missing app package; after implementation full suite 40 PASS.
Task 2: complete. New session tests initially failed for missing session module; after implementation full suite 56 PASS.
Task 3: complete. Evidence tests initially failed for missing confirmation module; after implementation full suite 89 PASS. Synthetic verifier is only under tests.
Task 4: complete. Save tests initially failed for missing require_save_eligible; after implementation full suite 108 PASS, 26 subtests; original unittest suite 18 PASS. Independent read-only review found no critical, important or minor issues and reproduced both passing suites.
Ruling: Keep immutable evidence/read-back types with Session to avoid a circular import, and split save tests into their own file. Cost: session.py carries the aggregate's related value objects.
Ruling: Guard VALID canonical PIN against non-ASCII/non-six-digit values even when an internal validator claims success. This is a minimal invariant; required fields/geography remain 2B. Cost: Unicode PIN candidates need explicit normalization before becoming valid.
Ruling: Restored missing .env.example with placeholders only so the existing README link works; did not read or modify the user's .env.
Packaging verification: an offline no-build-isolation probe failed because the existing environment lacked bdist_wheel. The documented isolated install initially encountered sandbox network restrictions; rerunning with approved network access successfully built and installed bolna-address-collector 0.2.0. No application change was needed. Generated packaging/test output is ignored.
