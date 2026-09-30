# Phase 2B validation design

The user approved docs/phase2b-design-review.md. This specification resolves its implementation details and supplements docs/phase2b-proposed-design.txt. Scope is Phase 2B only; preserve the strict Phase 2A evidence gate.

## Outcomes and boundaries

The pure engine consumes an immutable AddressVersion, an injected PostalDirectory, ValidationPolicy and evaluation date. It returns either NormalizationProposal or the existing domain ValidationResult, extended with immutable explanatory metadata. The domain retains VALID, NEEDS_CLARIFICATION and VALIDATION_ERROR. NORMALIZATION_REQUIRED belongs only to the proposal union. Neither outcome confirms or saves an address.

Place shared provenance/origin/proposal types in app/domain/validation_metadata.py so domain code never imports the validation engine. Keep existing conflict-code tuples compatible; add structured conflict details, reason codes, warning codes, next_action, policy_version and optional postal provenance. VALID engine results always carry postal provenance. Existing 2A synthetic tests remain explicitly synthetic; their compatibility defaults do not constitute a production validator.

## Completeness and comparison policy

Policy urban-v1 requires house_flat, area, city and PIN. An alternative premise description uses the existing house_flat text field: it accepts a customer-supplied name or identifying description as well as a number (within its existing 100-character limit). The upstream collection layer must place an explicitly supplied premise description there; 2B does not infer it from building or landmark. Longer input is clarified upstream, never truncated. This tests completeness only, not deliverability.

City and area are preserved and checked for presence only; emit CITY_NOT_POSTALLY_VERIFIED and AREA_NOT_POSTALLY_VERIFIED warnings on otherwise valid results. State/district comparisons use NFC, whitespace collapse and casefold, plus a versioned explicit state alias map (UP and U.P. to Uttar Pradesh; TN to Tamil Nadu). No fuzzy matching. A supplied district matching any record passes; multiple districts are not corruption. A unanimous state may be derived only when absent. Do not derive district in 2B. Missing reference district when needed is an evidence error, not customer contradiction.

## Normalization and provenance

PIN normalization permits only Unicode decimal characters and ASCII space U+0020; remove those spaces and convert decimal characters with unicodedata.decimal. Reject all other characters, including letter O, superscripts, punctuation, tabs and zero-width characters. Require exactly six ASCII digits after conversion. Empty/malformed candidates need clarification. Other customer fields are compared without rewriting spelling.

A proposal binds base version, exact base raw/canonical snapshot and origins, proposal UUID, policy version, changed canonical fields and their origins, and postal provenance when used. Apply through a dedicated expected-version domain transition, preserving raw and immutable history. Increment once, clear validation/read-back/confirmation/current saved pointer, then validate the new version. Never apply proposals via update_candidate, which records customer input. Reapplication fails as stale. Normalization must converge without a loop.

Record origins CUSTOMER, CUSTOMER_NORMALIZED or POSTAL_DATA for each populated canonical field, with dataset provenance for derived values. Customer patches update origins explicitly. On a changed PIN, remove old postal-derived state unless the same patch explicitly supplies state; preserve customer-supplied state for conflict checking. An explicit customer claim equal to a derived value changes its origin and is therefore a meaningful version change. Historical versions remain unchanged.

## Postal directory and errors

Use a manually imported, immutable official Department of Posts snapshot. Runtime lookups are local and indexed by PIN, returning all rows plus provenance. A directory has internal readiness/error information and never falls back to synthetic records. The trusted operator supplies official resource URL/ID and release date; hashes verify integrity, not authenticity.

Provenance contains source name, resource URL/ID, source release date, UTC import timestamp, source-byte SHA-256, normalized-records SHA-256, format version and dataset kind OFFICIAL or SYNTHETIC. Hash normalized records with documented stable UTF-8 JSON serialization, sorted keys/rows, and no timestamps in the record digest. Preserve multiple offices and duplicate rows. Never overwrite an existing different artifact at the same output path.

Initial importer accepts UTF-8/UTF-8-BOM CSV with circlename, regionname, divisionname, officename, pincode, officetype, delivery, district, statename; validate against the acquired official file before claiming real ingestion. Strip header BOM, reject duplicate/missing headers, invalid encoding, malformed rows, empty mandatory office/state/district and non-six-ASCII PIN. Optional metadata may be empty. Extra columns may be ignored and documented. Reject the entire import on any bad row and publish output only after validation succeeds.

Policy defaults to maximum source age 90 days, configurable and recorded with policy identity. Use an injected date: age >90 is stale; future release/import chronology is invalid; reimporting cannot renew source age. Missing provenance, stale/corrupt/unavailable data, reference ambiguity across states and lookup exceptions return VALIDATION_ERROR with safe codes. Customer omissions/format problems/unknown PIN/strong geographic conflicts return NEEDS_CLARIFICATION. Perform local completeness/format checks first; only then consult the directory. Infrastructure failures take precedence over geographic decisions. Known conflicts take precedence over applying normalization/derivation proposals. Deterministic question priority is premise, area, city, PIN, state conflict, district conflict. Errors return RETRY_VALIDATION; proposals return APPLY_NORMALIZATION; valid results return READY_FOR_READBACK.

## Verification and completion

Unit tests use explicitly synthetic injected directories only. Verify real official-file import separately with source date, retrieval/import date and hashes. If acquisition is unavailable, report real ingestion NOT_RUN and do not claim fully proven 2B completion. Preserve all existing tests, strict evidence default denial and version/save guards. No new service, database, network-per-validation, scheduler, voice integration or deployment. Never read or modify .env. Keep test_result separate from conversation_outcome and backend_outcome.
