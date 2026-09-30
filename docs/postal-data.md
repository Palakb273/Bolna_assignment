# Postal data: import and validation

## Explicit unverified development/demo mode

The user-supplied five-column CSV has an exact separate mapping: PostOfficeName→office_name, Pincode→pincode, DistrictsName→district, City→city, State→state. UTF-8/BOM decoding is strict, City is optional, and multiple rows per PIN are preserved. It is always UNVERIFIED_OR_STALE, with null official URL, resource ID and release date. Import time does not assert freshness.

Default import rejects any malformed row. The user authorized explicit exclusion of three malformed rows in this file; the original is never edited. Reproduce with a new output path:

```powershell
$env:APP_ENV='development'
$env:ALLOW_UNVERIFIED_POSTAL_DATA='true'
.venv\Scripts\python.exe scripts/import_demo_postal_data.py --input C:\Users\palak\Downloads\pincodes.csv --output local-data/postal/demo-pincodes.json --reject-malformed-rows
$env:POSTAL_DATA_PATH='C:\Users\palak\OneDrive\Desktop\bolna\local-data\postal\demo-pincodes.json'
.venv\Scripts\python.exe scripts/run_local.py serve
```

Use the immutable artifact path to retain a stable import timestamp. Direct CSV runtime loading also works; exclusion then requires DEMO_REJECT_MALFORMED_ROWS=true. That flag is ignored outside the explicit demo loader and cannot be set through an API request. APP_ENV=production with ALLOW_UNVERIFIED_POSTAL_DATA=true raises a configuration error at startup. Unknown environments and malformed boolean values also fail.

Readiness distinguishes trusted_runtime_ready from demo_runtime_ready. An unverified directory can only satisfy the latter; /health/ready stays HTTP 503 with ready=false. The engine skips missing official freshness only for this explicitly selected demo capability. Validation results and postal-derived fields retain unverified provenance. Versioning, corrections, confirmation verification and save eligibility are unchanged.

The original official-source instructions below continue to apply to production. This demo file does not replace their trust requirements.

The intended source is the Department of Posts [OGD PIN directory](https://www.data.gov.in/resource/all-india-pincode-directory-till-last-month). The [catalog](https://data.gov.in/catalog/all-india-pincode-directory-through-webservice) describes monthly updates; that schedule does not prove a particular file is current. Check the actual resource release date. India Post also has a [circle PIN listing](https://www.indiapost.gov.in/rti/pincodelist), currently exposing PDF lists rather than the required national CSV.

No official CSV has been imported in this workspace. On 2026-09-30 the resource fetch returned a sandbox notice with no download, and the catalog fetch timed out. Unit-test fixtures are synthetic. No source release date, official row count or actual download checksum is claimed.

## Manual import

After installing the project with `pip install -e '.[dev]'`, an operator must download and verify an official release. Supply its real resource identity and release date; do not use a site-footer date. The command does not download data or read .env.

```powershell
.venv\Scripts\python.exe scripts/import_postal_data.py --input local-data/postal/source.csv --output local-data/postal/release.json --resource-url https://www.data.gov.in/resource/all-india-pincode-directory-till-last-month --resource-id ACTUAL_RESOURCE_ID --source-date YYYY-MM-DD --retrieved-at VERIFIED_ISO_UTC_TIMESTAMP --source-kind OFFICIAL_POSTAL_DIRECTORY
```

Replace the resource ID/date placeholders with verified metadata. The output path must not already exist. Output is published only after complete validation via a temporary file and exclusive hard-link creation on the same filesystem; filesystems without hard-link support fail closed. The original CSV should be retained beside the artifact for independent source-hash checks.

Required UTF-8/UTF-8-BOM CSV headers: circlename, regionname, divisionname, officename, pincode, officetype, delivery, district, statename. Extra columns are ignored. PIN, office, district and state must be populated; optional hierarchy/office metadata can be empty. Every row must have the header's column count. Multiple offices and identical duplicate rows are retained. Header/schema compatibility with a current official file remains unverified.

Provenance contains source identity, resource URL, source date, UTC import timestamp, original-byte SHA-256 and normalized-record SHA-256. Normalized records are sorted by their sorted-key JSON representation, then encoded as compact sorted-key UTF-8 JSON without ASCII escaping. Timestamps are excluded from the record digest. A hash identifies content; it does not authenticate its origin. Official-domain URL checking is a guardrail, not proof of provenance. The operator and local artifact storage are trusted.

Load with `load_directory(Path(...), ValidationPolicy(), evaluation_date)`. Check `ready` and `error_code`. The loader rejects synthetic artifacts, bad hashes, absent metadata and stale data. Runtime evaluation rechecks freshness. Default maximum source age is 90 days (day 90 accepted, day 91 rejected); changing it changes the recorded policy identity. Reimporting never resets source age. Lookup uses a private PIN index and returns immutable rows.

## Meaning of validation

The urban-v1 policy requires house_flat, area, city and PIN. house_flat accepts an explicit customer-supplied premise name/description within its 100-character bound. Building/landmark alone do not qualify. Completeness is not proof of deliverability.

PIN conversion accepts Unicode decimal digits and ASCII spaces only. Letters, superscripts and punctuation require clarification. Geographic comparisons use NFC, collapsed whitespace and casefold, with explicit UP/U.P./TN aliases. No fuzzy replacement occurs. City and area are preserved and carry warnings that they have not been verified geographically. A district matching any official row passes; state disagreement across postal rows is an evidence error.

Missing state may be derived from unanimous postal evidence. Normalization returns a bound proposal; `apply_normalization` creates a new version while preserving raw input and revoking old eligibility. Customer PIN corrections clear postal-derived state. Validation results retain origins and source metadata in immutable history.

Outcomes: customer missing/format/conflict issues → NEEDS_CLARIFICATION; missing/corrupt/stale/ambiguous evidence → VALIDATION_ERROR; normalization/derivation → NormalizationProposal; otherwise → VALID. Actions are machine codes, not spoken prompts. Default confirmation verification still rejects all evidence. The backend integrates this engine with PostgreSQL and authenticated voice tools. Omitting source-kind or verified retrieval metadata keeps an imported artifact excluded from production validation; declaring a source official does not independently authenticate it.
