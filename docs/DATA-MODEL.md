# Proposed data model and invariants

**Design only; no production schema or migrations exist yet.** CL-103 will select exact database types, constraints, indexes and migration tooling after CL-101. Identifiers should be stable non-secret IDs; authorization must not depend on an ID being hard to guess. Distinguish credentials from IDs.

## Organization and people

| Entity | Main fields / relations | Required invariant |
| --- | --- | --- |
| Organization | id, name, scheduling timezone, workweek start, module settings | Scope included in all owned records even if initially single organization |
| Department | id, organization, name, archived_at | Archived departments remain referenced by history |
| Location | id, organization, name, IANA timezone, address, archived_at | Display timezone never inferred from browser/server timezone |
| EmployeeRecord | id, organization, display name, contact fields, lifecycle, effective dates, weekly policy, version | History can exist without an active login; no destructive default deletion |
| EmployeeDepartment | employee, department, effective interval | Multiple memberships possible; validate effective interval |
| EmployeeLocation | employee, location, effective interval | Locations govern scheduling eligibility/visibility under chosen policy |
| Skill | id, organization, name, archived_at | Stable catalog avoids text-string drift |
| EmployeeSkill | employee, skill, effective/expiry dates, evidence reference if enabled | Evaluate qualification at shift time, not only current date |
| UserAccount | id, employee or admin linkage, verified email, status, auth provider subject, access version | Active account and current role/scope required for protected operations |
| RoleGrant / ManagerScope | account, role, department/location scope, effective dates | Admin, manager and staff permissions explicit; no accidental wildcard |
| Session / Invitation | account, hashed secret/provider reference, expiry, revoked_at | Tokens not stored/logged in plaintext; lifecycle revocation is authoritative |

Do not make email the employee primary key. Email changes can be pending verification and old history remains attached to the same stable employee. Rehire/lifecycle corrections retain history and create fresh access grants.

## Availability and leave

| Entity | Main fields | Invariant |
| --- | --- | --- |
| AvailabilityRule | employee, local weekday/recurrence, local time bounds, timezone, effective dates | Recurrence describes local-time intent; overnight boundaries explicit |
| AvailabilityException | employee, date/instant interval, kind, precedence | Deterministic precedence over recurrence, audited |
| TimeOffRequest | employee, interval/all-day local dates+timezone, private reason, status, version | Applicant and authorized manager only can see reason |
| TimeOffDecision | request, actor, decision, timestamp, impact/disposition reference | Assigned-shift effects are reviewed and committed consistently |

All-day leave is not blindly a fixed 24-hour UTC interval. Normalize using the relevant timezone and effective local date boundaries. Changing availability does not silently delete existing shifts.

## Events, coverage and assignments

| Entity | Main fields | Invariant |
| --- | --- | --- |
| Event | id, organization, location, title, starts_at, ends_at, timezone, lifecycle, version, source linkage | Real dates on both ends; end strictly after start; supports overnight |
| CoverageRequirement | Event, phase/custom bounds, department, skill requirements, minimum headcount, rule revision | Headcount is distinct qualified staff in every required interval segment |
| ShiftSlot | Event, coverage linkage, department, starts_at, ends_at, role, status, version | Exists independently of an assignee, so it can be open |
| ShiftSkillRequirement | shift/coverage, skill, requirement policy | Supports several required skills; not just one display string |
| Assignment | slot, employee, effective assignment revision, status, created/released/canceled metadata | At most one current assignee per slot; historical revisions retained |
| OpenShiftRequest | slot, employee, status, request/decision timestamps, expected revision | At most one active request per employee/slot; approval revalidates atomically |
| RuleSet / RuleRevision | organization, optional scoped overrides, timing, conflict/hour policies, effective/version | Publication refers to evaluated rule revision; overrides need explicit policy |

Indexes should support employee time-overlap queries, Event intervals per location, pending requests and weekly-hour ranges. Evaluate database-level overlap protections or scoped serialization in addition to service validation. Cross-location travel and skills cannot be guaranteed by a simple unique key.

## Draft and published state

| Entity | Main fields | Invariant |
| --- | --- | --- |
| ScheduleDraft | organization/scope, period, revision, optimistic version, editor | Staff never read uncommitted drafts |
| Publication | organization/scope, period, revision, previous revision, actor, timestamp, rule revision | Immutable checkpoint linked to audit and outbox |
| PublishedShift | publication, stable slot/assignment refs, employee, time/location/role snapshot, cancellation state | A moved/canceled shift preserves identity and old publication history |
| PublicationDiff | old/new revision, affected employee/shift, change type | Same source for staff change summaries, emails and calendar revisions |

Decide whether published projections are stored rows, immutable revisions or a combination during CL-103. Required behavior is stable snapshots plus auditable deltas; raw JSON copies in a browser do not satisfy it. Contact details should remain in access-controlled people records, not copied into every public schedule revision.

## Communications, calendars and modules

| Entity | Main fields | Invariant |
| --- | --- | --- |
| OutboxMessage | kind, aggregate/revision, recipient, idempotency key, payload reference, status, attempt/next-attempt | Created in domain transaction; no actual send inside publication transaction |
| DeliveryAttempt | outbox, provider id, status, safe error, timestamp | Retry audit without exposing tokens/contact payloads in ordinary logs |
| DigestRun | organization, recipient, upcoming week, timezone, generation/publication refs | Unique effective delivery key prevents duplicate scheduled sends |
| CalendarSubscription | employee/account, token hash, created/revoked/rotated timestamps, access version | Current active account/status and token required; feeds contain only own published shifts |
| CalendarItemRevision | stable shift UID, sequence, published revision/cancellation | Stable identities permit update and cancellation rather than duplicate entries |
| ModuleEnablement | organization, module id, enabled/config ref | Disabled module does not mutate core staff schedules |
| ExternalSource | organization, adapter, allowlisted locator, sync policy, status | Secrets separate from ordinary source metadata |
| ExternalEvent | source UID, provenance, normalized times, source version, imported_at, stale/error state | Read-only context until explicit conversion; deduplicated by source and UID |
| ExternalConversion | external item, staffed Event, actor, timestamp | Source updates never silently overwrite staffed assignments |

## Audit and retention

AuditEntry: stable id, organization, actor account/service identity, action, target, timestamp, before/after revision references, reason, correlation id. Restrict read access. Avoid copying raw sensitive reasons or credentials into unrestricted audit text.

Retention duration, privacy deletion, backup retention and legal holds require an accepted owner policy. Operational offboarding preserves authorized history while preventing the former employee from accessing it through old sessions or calendar URLs. A future deletion workflow must be separate and authorized.

## Transactions that require design and tests

- Assign/reassign slot + conflict checks + expected-version guard + audit.
- Approve open-shift request + assignment + close competing requests + audit.
- Approve leave + affected-shift disposition + publication if needed + outbox.
- Publish revision + immutable snapshots + diff + audit + outbox.
- Terminate employment + authoritative denial + grants/token revocation + future assignment transitions + published cancellations/reopen + communication suppression + audit.
- Rotate calendar token without allowing a window where a revoked token remains usable.

Define lock ordering and isolation/retry strategy before implementing these operations. Test with multiple concurrent transactions, not just sequential browser clicks.
