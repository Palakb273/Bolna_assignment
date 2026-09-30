Phase 2 — Deterministic Address Validation, Confirmation & Persistence
1. Purpose
Phase 2 adds a backend behind the Bolna voice agent so that addresses are no longer stored only in conversational memory.
The production flow becomes:
Customer
   ↓
Bolna voice agent
   ↓
Structured address candidate
   ↓
Our backend
   ↓
Validation
   ↓
Clarification if required
   ↓
Full read-back
   ↓
Explicit confirmation
   ↓
Confirmed address persistence

The backend becomes the authoritative source of truth.
Bolna remains responsible for:
telephony
STT
LLM conversation
TTS
barge-in
language handling
tool invocation

Our system becomes responsible for:
structured state
validation
confirmation integrity
address versioning
PIN validation
persistence
audit trail
security

2. Phase 2 primary objective
The system must guarantee:
An address cannot become a confirmed stored address unless the exact current address version has passed validation and has subsequently been explicitly confirmed by the customer.

That is the most important Phase 2 rule.
3. Why Phase 2 is required
Phase 1 currently depends on conversational state:
Customer says address
      ↓
LLM remembers it
      ↓
LLM reads it back
      ↓
customer confirms

This works for a prototype but creates several production problems.
The LLM could:
forget a previous field
overwrite the wrong field
misinterpret confirmation
save after a correction
invent information
lose state

Phase 2 removes business-critical decisions from the LLM.
Instead:
LLM = conversation controller

Backend = deterministic business authority

4. Phase 2 architecture
                        CUSTOMER
                            │
                            ▼
                    ┌──────────────┐
                    │    BOLNA     │
                    │              │
                    │ STT          │
                    │ LLM          │
                    │ TTS          │
                    │ Barge-in     │
                    └──────┬───────┘
                           │
                       Tool calls
                           │
                           ▼
                    ┌──────────────┐
                    │   FastAPI    │
                    │   Backend    │
                    └──────┬───────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
       ▼                   ▼                   ▼
Address Session       Validation        PostgreSQL
State                 Service
                           │
                           ▼
                     PIN Dataset/API

Potential later extension:
Validation
   ↓
Geocoder / maps

Geocoding is not required for the first Phase 2 milestone.
5. Technology stack
Recommended:
Python 3.11+
FastAPI
Pydantic
SQLAlchemy
PostgreSQL
Alembic
pytest
httpx
Bolna function calling

Optional:
Docker Compose

Not needed initially:
Redis
Celery
Kafka
Kubernetes
message queues

Do not introduce distributed infrastructure without a demonstrated requirement.
6. Core domain model
The canonical address structure will be:
{
  "house_flat": null,
  "building": null,
  "street": null,
  "area": null,
  "landmark": null,
  "city": null,
  "district": null,
  "state": null,
  "pincode": null
}

All values are candidate data until validated and confirmed.
7. Address session
Every active call should have an address collection session.
Example:
{
  "session_id": "addr_session_123",
  "customer_id": "customer_456",
  "bolna_execution_id": "execution_xyz",
  "status": "COLLECTING",
  "current_version": 3,
  "validated_version": 3,
  "confirmed_version": null
}

This session becomes the deterministic state machine for the call.
8. Address versioning
This is one of the most important Phase 2 concepts.
Suppose the current address is:
{
  "house_flat": "302",
  "building": "Galaxy Apartments",
  "area": "Gachibowli",
  "city": "Hyderabad",
  "pincode": "500032"
}

Call this:
address_version = 1

Customer later says:
“Actually it's flat 320.”

Now create:
address_version = 2

The new state becomes:
{
  "house_flat": "320",
  "building": "Galaxy Apartments",
  "area": "Gachibowli",
  "city": "Hyderabad",
  "pincode": "500032"
}

Never mutate history invisibly.
9. Confirmation integrity
Suppose:
current_version = 1
validated_version = 1
confirmed_version = 1

The address is safe to save.
Then customer says:
“Actually change flat 302 to 320.”

Now:
current_version = 2
validated_version = null
confirmed_version = null

The old confirmation is invalid.
After validation:
current_version = 2
validated_version = 2
confirmed_version = null

Only after another complete read-back and explicit confirmation:
confirmed_version = 2

Now persistence is allowed.
Therefore the save condition is:
current_version
==
validated_version
==
confirmed_version

If that condition is false:
SAVE MUST FAIL

10. Phase 2 state machine
SESSION_CREATED
      │
      ▼
COLLECTING
      │
      ▼
CANDIDATE_UPDATED
      │
      ▼
VALIDATING
      │
      ├──── missing fields ────► NEEDS_CLARIFICATION
      │                              │
      │                              ▼
      │                         CANDIDATE_UPDATED
      │                              │
      │                              └────► VALIDATING
      │
      ├──── conflict ──────────► NEEDS_CLARIFICATION
      │
      └──── valid
             │
             ▼
       READY_FOR_READBACK
             │
             ▼
         READ_BACK
             │
             ▼
     WAITING_CONFIRMATION
           /     \
         NO       YES
         │         │
         ▼         ▼
   CANDIDATE     CONFIRMED
    UPDATED          │
         │           ▼
         └──────►  SAVED

11. Required backend endpoints
11.1 Create session
POST /v1/address-sessions

Input:
{
  "customer_id": "customer_123",
  "bolna_execution_id": "execution_456"
}

Response:
{
  "session_id": "session_789",
  "status": "COLLECTING",
  "current_version": 0
}

12. Update candidate address
PATCH /v1/address-sessions/{session_id}/candidate

Input:
{
  "changes": {
    "house_flat": "B-1204",
    "building": "Prestige High Fields"
  }
}

Response:
{
  "current_version": 1,
  "address": {
    "house_flat": "B-1204",
    "building": "Prestige High Fields"
  },
  "status": "CANDIDATE_UPDATED"
}

Important:
Only supplied fields are updated.
Unaffected fields remain unchanged.
13. Validation endpoint
POST /v1/address-sessions/{session_id}/validate

Backend validates the latest current version.
Possible success:
{
  "status": "VALID",
  "version": 3,
  "normalized_address": {
    "house_flat": "B-1204",
    "building": "Prestige High Fields",
    "area": "Financial District",
    "city": "Hyderabad",
    "state": "Telangana",
    "pincode": "500032"
  },
  "missing_fields": [],
  "conflicts": []
}

Possible incomplete:
{
  "status": "NEEDS_CLARIFICATION",
  "version": 3,
  "missing_fields": [
    "pincode"
  ],
  "conflicts": [],
  "recommended_question": "Please ask for the six-digit PIN code."
}

Possible conflict:
{
  "status": "NEEDS_CLARIFICATION",
  "version": 3,
  "missing_fields": [],
  "conflicts": [
    {
      "type": "CITY_PINCODE_MISMATCH",
      "fields": ["city", "pincode"]
    }
  ]
}

14. Confirmation endpoint
POST /v1/address-sessions/{session_id}/confirm

Input:
{
  "version": 3,
  "explicit_confirmation": true
}

The server verifies:
version == current_version
version == validated_version

If yes:
{
  "status": "CONFIRMED",
  "confirmed_version": 3
}

If not:
409 Conflict

Example:
{
  "error": "ADDRESS_VERSION_CHANGED"
}

15. Save endpoint
POST /v1/address-sessions/{session_id}/save

The backend must enforce:
current_version
==
validated_version
==
confirmed_version

Only then:
{
  "status": "SAVED",
  "address_id": "addr_123"
}

Otherwise:
409 Conflict

The LLM cannot bypass this by simply saying:
{
  "confirmed": true
}

The backend determines confirmation validity.
16. Bolna function/tool design
Bolna should initially receive three or four tools.
Tool 1
update_address

Purpose:
Apply customer-supplied changes.
Example:
{
  "session_id": "session_123",
  "changes": {
    "house_flat": "320"
  }
}

Tool 2
validate_address

Purpose:
Ask backend whether current address is complete and consistent.
Tool 3
confirm_address

Purpose:
Mark exact validated version as explicitly confirmed.
Tool 4
save_address

Purpose:
Persist only if backend rules permit.
This separation gives us strong control.
17. Why not one giant tool?
Do not create:
process_address_and_save_everything()

because then:
- validation,
- confirmation,
- mutation,
- persistence
would become coupled.
Small tools allow us to audit exactly what happened.
18. Validation categories
Validation should be separated into layers.
Layer 1 — Schema validation
Check:
field types
maximum lengths
illegal characters
PIN format

Layer 2 — Required-field validation
For standard urban delivery addresses, likely require:
house identifier OR equivalent identifying description
area/locality
city
pincode

Building may become conditionally required when relevant.
19. PIN format validation
PIN:
exactly 6 digits

Regex:
^\d{6}$

Never convert PIN to integer.
Why?
Because identifiers should remain strings.
Use:
"500032"

not:
500032

20. PIN dataset validation
Use an authoritative or sufficiently reliable Indian postal PIN dataset/API.
For:
500032

we may obtain:
state
district
post office/locality information

The validator can use this to check geographic consistency.
21. Geographic conflict handling
Customer:
city = Gurugram
pincode = 500032

Backend should not silently overwrite the customer's city.
Instead:
{
  "status": "NEEDS_CLARIFICATION",
  "conflicts": [
    {
      "type": "CITY_PINCODE_MISMATCH"
    }
  ]
}

Agent then says:
“I may have heard one detail incorrectly. Could you repeat the PIN code digit by digit?”

22. Normalization
Normalization may safely do things like:
"  Gachibowli " → "Gachibowli"

or:
"B 1204" → "B-1204"

only when semantics are clear.
Normalization must not invent geographic facts.
23. Raw vs normalized values
Store both where useful.
Example:
{
  "raw_value": "B twelve zero four",
  "normalized_value": "B-1204"
}

This allows debugging.
24. Address attempts
Every validation attempt should be logged.
Example:
Attempt 1:
missing pincode

Attempt 2:
city/pincode mismatch

Attempt 3:
valid

This becomes extremely valuable for debugging agent behavior.
25. Database schema
customers
id
external_id
name
phone
created_at
updated_at

address_sessions
id
customer_id
bolna_execution_id
status
current_version
validated_version
confirmed_version
started_at
completed_at
created_at
updated_at

address_versions
id
session_id
version
house_flat
building
street
area
landmark
city
district
state
pincode
created_at

validation_attempts
id
session_id
address_version
status
missing_fields
conflicts
normalized_result
created_at

addresses
id
customer_id
source_session_id
source_version
house_flat
building
street
area
landmark
city
district
state
pincode
confirmed_at
created_at
updated_at

call_events
id
session_id
event_type
bolna_execution_id
metadata
created_at

Avoid placing raw secrets or unnecessary PII inside metadata.
26. Idempotency
Save operations should be idempotent.
Calling:
POST /save

twice should not create two identical confirmed addresses for the same session/version.
Use an idempotency condition such as:
unique(session_id, confirmed_version)

27. Concurrency protection
Suppose two API requests attempt to update the address simultaneously.
Use optimistic versioning.
Request:
{
  "expected_version": 3,
  "changes": {
    "house_flat": "320"
  }
}

If actual version is already 4:
409 Conflict

This prevents stale updates.
28. Security model
Phase 2 introduces real customer data, so security becomes significantly more important.
Minimum requirements:
HTTPS only
authenticated Bolna tool calls
server-side authorization
request validation
secret management
rate limiting
audit logs
database least privilege
encrypted backups
PII-safe logs
dependency scanning

29. Tool-call authentication
Bolna should not be allowed to call public backend endpoints without authentication.
Use something like:
Authorization: Bearer <service-secret>

or a signed request mechanism where supported.
The backend must reject requests without valid service authentication.
30. Never trust agent-provided customer/session ownership
Bad:
{
  "customer_id": "customer_999"
}

followed directly by database update.
The server should derive/verify ownership using the authenticated session.
Otherwise you create IDOR-style vulnerabilities.
31. Input validation
Use Pydantic models.
Example:
class AddressChanges(BaseModel):    house_flat: str | None = None    building: str | None = None    ...


Apply sensible length limits.
Example:
building <= 200 characters
area <= 200
pincode == 6 digits

32. Logging rules
Never log:
Authorization headers
API secrets
database credentials
entire raw customer payloads unnecessarily

Logs should instead include:
session ID
request ID
operation
version number
validation result
error category

33. Data retention
Define separate retention for:
confirmed addresses
unconfirmed address attempts
call transcripts
recordings
audit logs

Do not assume Bolna retention equals our retention.
They are separate systems.
34. Bolna webhook integration
Introduce:
POST /v1/webhooks/bolna

Use it for:
call started
connected
completed
failed

Webhook processing should be idempotent.
Duplicate webhook:
same event ID

must not create duplicate state transitions.
35. Failure behavior
Backend unavailable
Agent should not pretend the address was validated.
Say something equivalent to:
“I'm having trouble confirming the details right now.”

Then mark workflow appropriately.
Validation timeout
Do not automatically assume success.
Result:
VALIDATION_ERROR

Database save failure
Agent must not say:
“Your address has been saved.”

unless the save API succeeds.
36. New conceptual outcomes
Phase 2 may introduce:
ADDRESS_CONFIRMED
ADDRESS_SAVED
VALIDATION_FAILED
BACKEND_UNAVAILABLE
SAVE_FAILED
NEEDS_HUMAN_REVIEW
PARTIAL_ADDRESS

Conversation outcome and backend outcome should remain separate.
37. Testing strategy
Phase 2 requires substantially more automated testing than Phase 1.
Unit tests
Test:
normalization
required fields
PIN regex
version increments
confirmation invalidation
save conditions
idempotency

38. Example confirmation test
Initial:
current = 3
validated = 3
confirmed = 3

Customer correction occurs.
Expected:
current = 4
validated = null
confirmed = null

That behavior must have an automated unit test.
39. Save security test
Attempt:
current_version = 4
validated_version = 4
confirmed_version = 3

Call:
POST /save

Expected:
409

No database address created.
40. Integration tests
Test:
create session
update address
validate
confirm
save

End-to-end through API.
Also test:
correction after confirmation
invalid PIN
missing field
duplicate save
stale version
bad authentication

41. Bolna integration tests
With a hosted development agent:
Bolna
→ update_address
→ validate_address
→ read-back
→ confirm_address
→ save_address

Verify tool calls from real conversations.
42. Product tests
Reuse Phase 1 scenarios, but now verify backend state as well.
Example:
Customer:
“Yes, but the flat is 320.”

Expected:
old confirmation invalid
new address version created
validation reruns
full read-back occurs
new confirmation required
save only after new confirmation

43. Security testing phase
Before production:
API security
Test:
missing auth
invalid auth
expired/rotated secret
malformed payloads
oversized fields
injection strings
IDOR attempts
stale session IDs
session/customer mismatch

Database
Test:
least privilege
unique constraints
foreign keys
backup security
migration rollback

Secrets
Run:
secret scanner
dependency vulnerability scanner

44. Manual security review
Review:
Bolna → backend authentication
PII logging
transcript access
recording access
database privileges
admin access
retention
deletion behavior

45. Product audit trail
For a confirmed address, we should be able to answer:
How did this address get into the database?

Example evidence chain:
Call execution
    ↓
Address version 1
    ↓
Validation attempt
    ↓
Customer correction
    ↓
Address version 2
    ↓
Validation success
    ↓
Full read-back
    ↓
Explicit confirmation
    ↓
confirmed_version = 2
    ↓
Address saved

This is one of Phase 2's most valuable capabilities.
46. Phase 2 implementation phases
Phase 2A — Domain model and state machine
Build:
Pydantic schemas
session model
address versions
confirmation state
unit tests

No Bolna integration yet.
Exit criteria
All deterministic state transitions pass automated tests.
47. Phase 2B — Validation engine
Implement:
required fields
normalization
PIN format
PIN dataset lookup
geographic conflict detection

Exit criteria
Known test fixtures produce deterministic validation results.
48. Phase 2C — Persistence
Add PostgreSQL and migrations.
Implement:
address_sessions
address_versions
validation_attempts
addresses

Exit criteria
State survives service restart and integrity constraints work.
49. Phase 2D — API layer
Expose:
create session
update candidate
validate
confirm
save

Add authentication.
Exit criteria
Complete flow works using API tests without Bolna.
50. Phase 2E — Bolna tools
Connect:
update_address
validate_address
confirm_address
save_address

Update Bolna prompt so the agent uses backend state rather than conversational assumptions for business-critical decisions.
Exit criteria
Real test call invokes backend tools correctly.
51. Phase 2F — Webhooks and call linkage
Connect Bolna execution IDs with backend sessions.
Handle:
started
completed
failed

Exit criteria
Every development call can be traced to its address session.
52. Phase 2G — Product QA
Run:
Phase 1 conversational scenarios
+
backend assertions

Verify both:
what customer heard
AND
what backend stored

53. Phase 2H — Security testing
Perform:
auth tests
IDOR tests
input fuzzing
rate limiting
secret scan
dependency scan
PII log review
database permissions review

Critical/high findings block release.
54. Phase 2I — Reliability testing
Test:
API timeout during call
database unavailable
PIN service unavailable
duplicate requests
duplicate webhooks
agent sends stale version
concurrent update

55. Phase 2J — Production-readiness audit
Review:
data flow
security
monitoring
retention
backups
rollback
migration procedure
incident response
runbooks

Only after this should production deployment be considered.
56. Phase 2 acceptance criteria
Phase 2 is complete when:
1. Every call has a deterministic address session.
2. Address changes produce versions.
3. Corrections invalidate prior validation and confirmation.
4. Validation occurs outside the LLM.
5. PIN format is deterministic.
6. PIN/location conflicts can be detected.
7. Agent can ask targeted clarification from backend result.
8. Full address read-back is required.
9. Explicit confirmation refers to a specific address version.
10. Stale confirmation cannot save a changed address.
11. Save endpoint independently enforces validation + confirmation.
12. Confirmed address persists in PostgreSQL.
13. Duplicate saves do not duplicate records.
14. API calls are authenticated.
15. Customer/session ownership is enforced.
16. Bolna calls can be correlated with backend sessions.
17. Failed backend operations never produce false “saved” claims.
18. Audit history can reconstruct address evolution.
19. Automated tests pass.
20. Product integration tests pass.
21. Security tests have no unresolved critical/high issues.
22. Live Bolna calls demonstrate the entire workflow.
57. Recommended repository structure
address-collector/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── sessions.py
│   │   ├── addresses.py
│   │   └── webhooks.py
│   │
│   ├── schemas/
│   │   ├── address.py
│   │   ├── session.py
│   │   └── validation.py
│   │
│   ├── models/
│   │   ├── address.py
│   │   ├── session.py
│   │   └── validation.py
│   │
│   ├── services/
│   │   ├── address_service.py
│   │   ├── validator.py
│   │   ├── pincode_service.py
│   │   └── confirmation_service.py
│   │
│   ├── repositories/
│   │   ├── address_repository.py
│   │   └── session_repository.py
│   │
│   ├── security/
│   │   └── service_auth.py
│   │
│   └── db/
│       ├── session.py
│       └── base.py
│
├── migrations/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   └── fixtures/
│
├── prompts/
│
├── config/
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── security.md
│   ├── testing.md
│   └── phase2-report.md
│
├── pyproject.toml
├── .env.example
└── README.md

58. The most important Phase 2 rule
If you remember only one technical rule, remember this:
CURRENT ADDRESS VERSION
        ==
VALIDATED VERSION
        ==
CONFIRMED VERSION

Only then:
SAVE

That single rule protects us from a large class of voice-agent errors.
59. Simple explanation of Phase 2
If someone asks:
“What are you adding after the voice prototype?”

Answer:
Phase 2 adds a deterministic backend behind the Bolna agent. Every spoken address becomes a versioned structured record, our backend validates it, the agent asks for clarification when needed, and the customer must confirm the exact validated version before the database allows it to be saved.

60. Implementation order
Do not start with Bolna function calling.
Build in this order:
1. Domain/state model
2. Unit tests
3. Validation engine
4. PostgreSQL persistence
5. API endpoints
6. Authentication
7. Integration tests
8. Bolna tool integration
9. Live voice testing
10. Security testing
11. Reliability testing
12. Release audit

That way the business rules are already proven before the LLM is connected to them.
This should now serve as the Phase 2 specification/acceptance contract.