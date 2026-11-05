# Proposed production architecture

**Status: proposal.** The owner confirmed a web-server application, GitHub source and shared-agent documentation. Framework, database service, authentication provider and hosting target are not yet approved or implemented. The Node preview server is an interface-review tool, not the production backend.

## Recommended starting shape

A modular monolith: one application codebase with a browser UI, authenticated server/API, relational database, worker and scheduler. Keep domain rules in a shared server-side module rather than duplicating decisions in UI components. The worker may be a separate process from the same release. A single organization with multiple departments/locations is the initial planning baseline; confirm future multi-tenant intent before schema finalization.

Proposed stack to evaluate in CL-101: TypeScript browser and server code, React UI, a supported Node server framework, PostgreSQL, and a transactional database outbox. These are proposals, not installed dependencies. An existing organizational stack could be a better choice; record the decision and reasons rather than silently introducing a parallel architecture.

```text
Phone / desktop browser
    ↓ HTTPS
Web app + authenticated API
    ├── identity / access
    ├── people / skills / organization
    ├── availability / leave
    ├── Events / shifts / rule validation
    ├── draft / publication / audit
    ├── personal calendar feed
    └── optional external Event module
          ↓ transactions
PostgreSQL: records + revisions + outbox + delivery state
          ↓
Worker ← scheduler
    ├── operational email provider adapter
    └── external Event import adapters
```

No browser communicates directly with privileged database credentials or mail-provider keys. An optional calendar subscription is a read-only token-authenticated endpoint, not an unauthenticated general staff API.

## Module boundaries

| Module | Owns | Public contracts |
| --- | --- | --- |
| Identity/access | Accounts, sessions, invitations, roles, scopes, access version | Current principal, permission predicates, revocation |
| Organization/people | Departments, locations, staff, memberships, skills, lifecycle | Staff summaries and qualification checks |
| Availability/leave | Recurring limits, exceptions, time-off lifecycle | Effective unavailable intervals and leave approval impact |
| Scheduling | Event, coverage requirement, shift slot, assignment, validation | Candidate evaluation, rule issues, hour totals |
| Publishing | Draft revision, staff-visible snapshot, publication diff | Immutable published revision and change events |
| Communications | Outbox, email templates, delivery attempts, digest schedule | Idempotent deliverable creation and status |
| Calendars | Feed tokens, calendar item UID/revision, client serialization | Own published shifts only |
| Integrations | Module enablement, external source/item/import | Read-only external Event context and explicit conversion |
| Audit/operations | Actor/action records, correlation, retention, health | Authorized history and operational diagnostics |

Modules call stable application services; they do not directly rewrite another module's tables without a documented transaction boundary. Disable optional integrations without breaking core planning.

## Time and scheduling invariants

1. Store exact start/end instants and the location's IANA timezone. Keep the original local-time intent where necessary for recurring availability. Never use the server's local timezone implicitly.
2. Use half-open intervals `[start, end)`: adjacent shifts with no overlap do not double-book a person. A positive handover requires concurrent qualified people, not the same person's conflicting assignments.
3. Validate active employment, location and department scope, required skills, qualification expiry policy, availability, approved leave, overlapping assignments, interlocation travel buffer and hour policy. Recheck inside the assignment/publication transaction.
4. Staff can have multiple department/location memberships in the planned production schema. The prototype uses a simpler primary department field.
5. Availability changes must expose existing assignment conflicts; they do not silently delete assignments. Time-off approvals need an explicit disposition of affected shifts, with manager impact preview.
6. Validate coverage as a time-varying count of distinct qualified people, not merely filled slot counts. Split at every relevant interval boundary and compare against headcount/skill requirements for that segment.
7. Sample rule interpretation: before-Event requirement begins `Event.start - preMinutes`; handover extends the outgoing coverage into the next phase; after-Event coverage lasts through `Event.end + postMinutes`. The prototype creates pre `[start-pre, start+handover)`, during `[start,end+handover)`, post `[end,end+post)`. Production rules need an accepted policy for Events with custom phase times and whether post duration includes handover. Record it before CL-403 completion.
8. Calculate weekly hours from actual intersecting intervals in the configured workweek. Include cross-location commitments for limits; show filtered totals separately. Scheduled hours are not worked/payroll hours. Paid/unpaid break and overtime policy remains open.
9. Overnight Events need real dates on both ends. Handle ambiguous and nonexistent local times at DST changes explicitly. Calendar serialization and emails use the same canonical instants.
10. Database concurrency controls plus transaction-time validation prevent two separately valid edits from producing an invalid combined assignment. Application-only checks before a write are insufficient.

## Drafts and publication

Managers edit a draft revision. Staff read a stable published projection. A publish command includes the expected draft/revision version to detect stale edits. Inside one database transaction:

1. Authenticate current actor and scope.
2. Lock or otherwise serialize affected assignments and validate expected versions.
3. Re-run eligibility, conflict, hours and coverage rules.
4. Compute changes from the previous published revision, including additions, removals, time/location/role changes and cancellations.
5. Write an immutable publication/snapshot and an audit entry.
6. Insert affected-recipient outbox records with stable idempotency keys.
7. Commit. Delivery happens after commit; provider failure never rolls back a published schedule.

Open-shift publication policy needs owner confirmation: the prototype permits publishing open slots but blocks rule errors. Coverage warnings vs blocking failures must be separately modeled rather than treating every issue identically. Do not let raw UI toggles override safety constraints without a permissioned reason and audit record.

## Authentication, authorization and termination

Separate `user_account` from `employee_record`. A person can retain scheduling history after account access ends. Use secure HttpOnly session cookies, appropriate SameSite/CSRF protections, HTTPS, login throttling and recovery protections under the selected authentication design. Store session secrets securely; do not treat client storage as authoritative identity.

For every protected API request, export, websocket subscription if introduced, and calendar-feed request, check current employment/account state, organization, role and scopes. A cached role or long-lived signed token alone must not keep a terminated employee active; use an authoritative access-version/status lookup or equivalent revocation design.

Immediate termination transaction:

- Record effective end, actor/reason and prior state; update the authoritative account/employment access state so new requests fail immediately.
- Revoke sessions, outstanding invitations, recovery/magic-link grants and calendar subscriptions. If an external identity provider requires asynchronous revocation, local access denial still takes effect in the transaction.
- Close pending staff requests and prevent new assignments.
- Preserve past worked/scheduled history and published revision references. Future assignments become reopened slots using append-only assignment/publication transitions, not destructive erasure of prior records.
- For already published future assignments, record an explicit cancellation/reopen revision in the same service operation; notify authorized managers/replacements according to policy. Unpublished work remains draft.
- Cancel/suppress pending communications to the inactive account. Workers recheck status immediately before delivery; record any already in-flight send that cannot be recalled.
- Emit audit and outbox records. Make retries idempotent.

Rehire is a new access authorization, not restoration of old sessions or feed tokens. Retention and deletion rules need owner/legal policy; no retention duration is invented here. Previously downloaded calendar/email copies cannot be erased by revoking website access.

## Proposed API surface

Routes are draft contracts for CL-101/102, not implemented endpoints. Only the preview server endpoints documented in README currently exist.

| Method and route | Purpose / key guard |
| --- | --- |
| `GET /api/me` | Principal, own profile and permitted scopes; active account only |
| `PATCH /api/me/profile` | Own contact changes; verified-address workflow |
| `GET/POST /api/departments`, `/api/locations` | Admin or explicitly scoped management |
| `GET/POST /api/staff` | Scope-safe directory and onboarding |
| `PATCH /api/staff/:id` | Authorized profile/membership/skill changes; expected version |
| `POST /api/staff/:id/terminate` | Explicit impact preview/version, immediate lifecycle transition |
| `GET/POST /api/events` | Scoped Event list/create with timezone-aware date interval |
| `PATCH /api/events/:id` | Versioned edit/cancel; separate draft vs publication |
| `POST /api/events/:id/coverage` | Phase, headcount, department, required skill set |
| `PATCH /api/shifts/:id` | Validated times/assignment; expected version |
| `GET /api/shifts/:id/candidates` | Authorized candidate reasons and schedule conflicts |
| `POST /api/shifts/:id/requests` | Active own request for eligible published open slot |
| `POST /api/shift-requests/:id/approve` | Manager revalidation and atomic assignment |
| `GET/POST /api/me/availability` | Own availability plus recurrence/exception schema |
| `GET/POST /api/me/time-off` | Own request lifecycle; reasons private |
| `POST /api/time-off/:id/decision` | Manager impact preview and affected-shift disposition |
| `POST /api/schedules/:id/validate` | Rule issues for draft/expected version |
| `POST /api/schedules/:id/publish` | Transactional publication and outbox |
| `GET /api/me/schedule` | Own published shifts only |
| `GET /api/team-schedule` | Published field allowlist and scope filtering |
| `GET /api/scheduled-hours` | Draft/published choice, workweek, filtered and global totals |
| `POST/DELETE /api/me/calendar-subscription` | Token create/rotate/revoke, secret shown only as needed |
| `GET /calendar/:token.ics` | Read-only own published feed; no contact/absence details |
| `GET/POST /api/modules/...` | Permissioned module settings and external source actions |
| `GET /healthz`, `/readyz` | Non-sensitive liveness and dependency readiness |

Use bounded pagination, input schema validation, field allowlists and idempotency keys for retriable commands. Error body should include a stable code, useful message, field errors and correlation ID, with no private unrelated person's data. Example codes: `STALE_REVISION`, `SHIFT_CONFLICT`, `SKILL_REQUIRED`, `OUTSIDE_AVAILABILITY`, `ACCOUNT_INACTIVE`, `COVERAGE_GAP`. Exact HTTP status and nondisclosure behavior must be made consistent in the API contract and tested.

## Email and scheduler behavior

Mail templates consume immutable publication differences. Both old and new assignees may need updates when an assignment moves. Staff never receive manager drafts. Queue entries have recipient, revision, kind, idempotency key, status and safe retry metadata. At delivery, confirm account/contact state and suppress obsolete/canceled work according to a documented policy. Provider event callbacks must be authenticated and idempotent.

For weekly digest, define workweek and organization timezone; the sample UI uses Sunday 5pm Pacific, but this is an example. Digest idempotency key includes organization, recipient, upcoming week and message kind. Duplicate scheduler processes and DST transitions must not duplicate sends. Define empty schedules and holidays, late publication, digest regeneration and dead-letter/manual retry policies. A cron expression alone is insufficient evidence of reliable delivery.

## Calendar and external Event integrations

Start with standards-based read-only iCalendar subscriptions, not mandatory Google/Apple accounts. Use stable per-shift UID, sequence/revision and UTC or well-defined timezone serialization. New publication drives calendar revision; clients may poll slowly. Tokens are high entropy, hashed at rest, revocable and excluded from logs. Add-to-home-screen is separate from calendar subscription. Direct Google OAuth is optional later.

External Events enter an isolated adapter and provenance store. Use source allowlists, safe outbound network policy, parser limits, rate limits, deduplication, timezone normalization and stale/error indicators. Prevent server-side requests to internal/private network addresses if remote feed URLs are accepted. Conversion into a staffed Event is explicit and auditable; subsequent source updates show differences rather than silently rescheduling staff.

## Operations and release

Production needs separate staging, TLS, migrations, safe secret injection, backups/restore, health/readiness, worker/scheduler monitoring and a deployment/rollback runbook. Database jobs and application version must be compatible across deploys. Introduce dependency locks when dependencies are added. Do not put real data on the unauthenticated preview server. See [Deployment](DEPLOYMENT.md) and M9 of the roadmap.
