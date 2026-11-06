# Implemented schema and invariants

Source of truth: `app/scheduling/models.py` and committed migrations. Database: SQLite in `/data/crewline.sqlite3`. All times are UTC-aware instants in storage; workspace/location IANA zones determine local meaning. IDs are ordinary stable integers, never permission grants.

| Entity | Main relations / state | Contract |
| --- | --- | --- |
| Workspace | singleton ID 1, rules, timezone, email settings, serialization epoch | One organization; no tenant isolation claim |
| Department / Location / Skill | unique catalog name; Location timezone | Referenced catalogs protected from destructive deletion; UI currently adds catalogs |
| User (Django) | normalized email username, PBKDF2 password, active/staff/superuser | Account lifecycle separate from staff history |
| Employee | one protected User, name, phone, pending email, weekly limit, ended_at, fictional flag | Multiple departments/locations/skills through membership tables; no default hard delete |
| Event | location, starts/ends, manager notes/context, version/published_version/current snapshot, canceled | Positive interval database constraint; draft versions separate from staff data |
| CoverageRequirement | Event, phase, department, skill, minimum | Unique group; required headcount survives shift splitting |
| Shift | Event, phase, department, one primary skill, starts/ends, optional Employee | Positive interval constraint; null employee is an open slot |
| Publication | protected Event/User, version, immutable-by-service snapshot, created_at | Historical names/times retained; no UI mutation or deletion |
| Availability | Employee, weekday OR date, local start/end | Weekly or one-date unavailable block; finish before start means overnight |
| TimeOff | Employee, local first/last day, private note, status, created_at | All-day workspace-zone interval; decisions audit and reopen conflicts |
| ShiftRequest | Employee, Shift, status, created_at | Unique pending claim per employee/shift; approval revalidates atomically |
| AccessToken | User, digest, purpose, payload, expiry/revocation | SHA-256 bearer secret digest only; payload may hold pending email |
| Session (Django) | signed server-side session data, expiry | Private invite link additionally encrypted; employment end deletes sessions |
| LoginAttempt | hashed account/network key, count, blocked_until | 15-minute throttle window; old entries pruned by worker |
| Outbox | User, unique key, subject/recipient, encrypted body, delivery/lease status | Unique enqueue effect; review ambiguous SMTP result before retry |
| Audit | protected actor, action, target, small JSON details, created_at | Restricted history, not a tamper-proof external audit ledger |

Manager scope is the employee's department/location memberships plus `User.is_staff`; only a superuser grants management capability. Ordinary staff contact edits cannot grant a role. Existing sign-in email remains until a new-address verification token is confirmed. Each invitation/recovery token is one-use.

Current migrations: 0001 initial schema; 0002 coverage setting validation; 0003 explicit coverage requirements. For legacy records without an explicit requirement, validation derives the original group count until the next coverage/split operation records it. There is no production migration from the old browser preview; its sample state was intentionally memory-only.

Database constraints enforce positive Event/Shift intervals, unique catalog names, unique access/outbox keys and unique pending claims. Cross-record scheduling, role/scope and coverage invariants are service validations inside serialized transactions. Direct database writes can bypass application rules; production administration should use supported workflows.

Not yet modeled: skill expiry/evidence, effective-dated memberships, rehire episodes, breaks/payroll, multi-tenancy, live external-source provenance, retention/deletion policy, email provider receipts. Retention currently means indefinite preservation until the owner specifies policy. Backups must include the database AND its matching secret; rotating the secret makes encrypted pending bodies unreadable and invalidates signed sessions.
