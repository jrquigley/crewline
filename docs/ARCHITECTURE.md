# Implemented architecture

Version 1.0.0 is a single-organization Django 5.2 LTS modular monolith. The earlier TypeScript/React/PostgreSQL proposal is superseded by D-016. Production dependencies are pinned in requirements.txt. Python 3.13 runs inside a non-root container; Waitress serves server-rendered HTML and WhiteNoise serves local static assets. Forms work without JavaScript; JavaScript adds clipboard, password visibility, search focus and small form conveniences.

```text
Phone / desktop browser → HTTPS reverse proxy → Waitress / Django
                                                 ├─ sessions, CSRF, scopes
                                                 ├─ people, availability, Events
                                                 ├─ drafts → publication → staff projection
                                                 ├─ private token calendar feed
                                                 └─ background worker → SMTP (optional)
                                                      ↓
                                               /data/crewline.sqlite3
                                               /data/secret.key
```

## Identity and privacy

Django User accounts are separate from retained Employee records. Superusers administer everything. Staff managers (`is_staff`) require an Employee and department/location memberships; mixed-department Events are editable only when every department is in scope. Ordinary staff can read their own published assignments and permitted coworker names/times at their locations. Private contacts, manager notes, availability and time-off reasons stay out of team projections. Authentication, exported hours and mutation authorization are server-side.

Passwords use Django PBKDF2 with its current iteration policy, at least 15 characters, similarity/common-password validation and no shared default. Sessions are HttpOnly/SameSite Lax, HTTPS-secure by default, 12 hours, and rotate through Django login/password flows. Sign-in throttles hashed account and network identifiers. CSRF applies to every mutation; logout is POST. Invitations/recovery/email/calendar secrets are cryptographically random, SHA-256 hashed in AccessToken, expiring and revocable. Calendar tokens last one year and can be rotated sooner. Sensitive outbox bodies and transient invitation links in server sessions are Fernet encrypted using a key derived from the persistent app secret. The rest of the database contains personal data in plaintext and requires protected disks/backups.

CSP limits scripts/fonts/connections to self and denies embedding; cookies, HSTS, no-store for private responses and safe application logging are configured. Proxy access/error logging must also redact bearer-token routes. Django uses same-origin Referrer-Policy so browser form submissions retain valid CSRF origins. `TRUST_PROXY=true` is appropriate only behind a private trusted proxy that overwrites forwarding headers. No SSO/MFA or general REST API is included.

## Event workflow and intervals

An Event has one location/timezone and any number of department/skill coverage groups. Create an Event → choose staff for setup, Event and closing slots → review → publish. Setup defaults to 60 minutes before the Event through 15 minutes after its start; Event coverage runs from start through 15 minutes after finish; closing runs from finish through 30 minutes after finish. These handovers intentionally need different people where intervals overlap. Rules are configurable. Changing workspace coverage rules applies to later validation as well as new slots, so review existing drafts before publishing after a rules change.

CoverageRequirement keeps required headcount distinct from the number of shift parts. An interval sweep checks that enough structural slots cover every required segment. Open positions are allowed at publication and visibly marked; gaps in the underlying coverage intervals block publication. Assigned people must satisfy every eligibility rule. Splitting a shift adds an open second part with a handover without inflating required headcount. Each assignment is at most 24 hours; Events can span up to 48 hours and require splitting long parts before assignment.

Eligibility checks active employment, departments, location, skill, recurring/date unavailable intervals, approved all-day leave, overlapping assignments, inter-location travel buffers and employee weekly-hour limits. It considers drafts and current publications conservatively so an unpublished reassignment does not silently free a person's published commitment. Same-slot draft/published overlapping durations are unioned for limits. Hours are elapsed time, weeks start Monday in the workspace timezone, and DST ambiguous/nonexistent typed times are rejected explicitly. Availability/leave use workspace local time; Event displays use the Event location timezone. There is no breaks/payroll/legally configurable overtime engine.

## Transactions and publication

SQLite `IMMEDIATE` transactions serialize writers before validation; a Workspace epoch update documents the serialization boundary. Assignment, publication, requests and offboarding revalidate inside short atomic transactions. Event versions reject stale forms. This is intentionally one container on a local persistent disk, not multiple replicas. PostgreSQL requires a separate migration, locking review and concurrency suite.

Managers edit Event/Shift drafts. Immutable Publication JSON records and the current snapshot supply staff/calendar views. Publish validates, records revision/audit and queues affected-person diffs atomically. Cancellation publishes a canceled revision. Time-off approval and termination reopen impacted current assignments with targeted snapshot updates while preserving unrelated drafts. Employment termination disables User, revokes tokens, removes sessions, closes pending requests and cancels pending sends. Historical revisions remain. Mail already accepted by a provider and calendar data already copied to a device cannot be recalled.

## Mail and background work

The Waitress process starts one bounded background thread, every 30 seconds. It creates unique recipient/week next-Monday–Sunday digests, then claims up to 20 queued jobs. Default weekly time is Sunday 17:00 workspace time; empty weeks get an explicit no-shifts message. An outage covering the entire configured send day currently misses that week's digest; catch-up scheduling is future work.

SMTP is disabled without SMTP_HOST. Pending jobs persist and may send when enabled; review the queue before turning on a provider after a long disabled period. Fictional `.example`/`@example.com` recipients are always blocked. Outbox keys deduplicate creation. Provider failure or an abandoned sending lease becomes `review`; an administrator checks the provider before manually retrying. SMTP cannot guarantee exactly-once delivery across a crash after provider acceptance. No blind automatic resend hides that ambiguity. Sender verification, bounce processing and live transport acceptance remain operator/provider work.

## Calendar and future modules

The private feed contains only the token owner's published shifts, stable per-shift UID/revision and cancellations derived from retained publications. UTC timestamps and UTF-8 line folding follow iCalendar. Client refresh timing is controlled by Google/Apple/etc. Actual phone clients remain to be verified. No OAuth sync or remote deletion of downloaded entries is claimed.

External Event context is a manual manager-only note today. Future safe read-only adapters need explicit source allowlists, parser/network limits, provenance, stale-state indicators and explicit conversion into staffing; do not add arbitrary URL fetching to the current view. Module and multi-tenant registries are planned, not implemented.
