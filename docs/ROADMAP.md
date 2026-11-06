# Full implementation roadmap

This is the shared execution plan for Codex and Claude. Update it with each meaningful change. Tasks below describe production outcomes unless explicitly labeled preview. A UI simulation does not complete a server task.

## Status and ownership

`done`, `ready`, `planned`, `in-progress`, `review`, `blocked`, `deferred`.

Release 1.0 implementation owner: **Codex**, branch `codex/CL-101-authenticated-app`. Statuses below reflect implemented code versus remaining operational/client acceptance; a partial task is not fully complete. Suggested branches and division of labor are in [Contributing](../CONTRIBUTING.md). Claim an owner and branch before starting. No work is currently assigned to Claude and no Claude review has been performed. Dates and effort estimates will be set after deployment constraints, staff scale and team availability are known; milestone order below is not a calendar promise.

## Delivery sequence

```text
M0 Preview + shared project records
  → M1 Repository + production foundation
  → M2 Identity, permissions, people, locations and skills
  → M3 Staff self-service + M4 Event scheduling
  → M5 Publishing, offboarding and audit
  → M6 Email + M7 Personal calendars
  → M9 Pilot, release and operations

M8 External Event module follows stable core contracts; it need not block the core pilot.
M10 Optional enhancements follow evidence from real use.
```

Tasks in one milestone may depend on a later-numbered task where a shared contract must be designed first. Follow task dependencies rather than implementing entire milestones blindly.

## M0 — Preview and project continuity

| ID | State | Deliverable / acceptance |
| --- | --- | --- |
| CL-001 | done | Interactive manager/staff prototype with sample Events, people and coverage; prior browser workflows exercised |
| CL-002 | done | Event terminology applied to the prototype, source identifiers and delivered starter; regression check added |
| CL-003 | done | Portable standalone preview build, Node HTTP preview server, local health endpoint and automated starter checks |
| CL-004 | done | Shared requirements, full roadmap, architecture proposal, decisions, work log, handoff, AGENTS.md and CLAUDE.md |
| CL-005 | done | Optional portable browser-smoke harness and reproducible preview build; actual results in TESTING.md and WORKLOG.md |

**Exit:** Another contributor can run the sample and identify exactly what is real vs simulated. No production-ready claim.

## M1 — GitHub and production foundation

| ID | State | Depends on | Deliverable / acceptance |
| --- | --- | --- | --- |
| CL-010 | done; Codex | Owner GitHub account | Earlier private repository baseline complete; owner then selected public jrquigley/crewline, baseline history preserved and authenticated release delivered through PR; checkpoint in HANDOFF/WORKLOG; no license grant selected |
| CL-011 | planned | CL-010 | Branch protection, required checks, PR/issue workflow and paired-agent ownership; verify permissions; first clean-checkout handoff succeeds |
| CL-101 | done; Codex | CL-004 | Resolve minimum architecture decisions: hosting environment, first deployment scale, auth approach and application framework; record accepted ADR and implementation layout |
| CL-102 | done; Codex | CL-101 | Django application, pinned dependencies, validated configuration, server forms, styled error boundaries and tests; Python compile/check tooling replaces a TypeScript typecheck; keep prototype runnable as reference |
| CL-103 | done; Codex | CL-102 | SQLite schema migrations and synthetic fixtures (D-016; PostgreSQL deferred); clean database bootstrap and upgrade test; rollback or forward-recovery plan |
| CL-104 | done; Codex | CL-102–103 | Development/staging configuration, example variable names, local database/worker startup and health/readiness checks; clean checkout works without undocumented local paths |
| CL-105 | done; Codex | CL-010, CL-102–104 | Production CI: static/type checks, tests, migration validation, dependency/security checks and artifact build; no privileged secrets for untrusted PRs |

**Exit:** Reproducible production skeleton, accepted decisions, working migrations, documented local/staging setup. No real staff data until authorization baseline is verified.

## M2 — Identity, permissions and organization data

| ID | State | Depends on | Deliverable / acceptance |
| --- | --- | --- | --- |
| CL-201 | partial; Codex | CL-103 | Organization, departments, locations and IANA timezones with create/update/archive rules; references remain historically valid |
| CL-202 | done; Codex | CL-201, CL-205 | Admin, manager and staff roles; explicit manager department/location scopes; API, export, notification and calendar authorization tests |
| CL-203 | done; Codex | CL-201–202 | Staff profiles, department/location memberships, lifecycle states and directory; invite/new staff cannot sign in before validation; no hard-delete default |
| CL-204 | partial; Codex | CL-203 | Skills catalog, employee qualifications and assignment requirements; expiry data model reserved; missing/expired skills denied according to accepted policy |
| CL-205 | partial; Codex | CL-102–103 | Authentication, verified contact/login addresses, secure sessions, invitation acceptance, recovery, rate limiting and auth-provider configuration; active-session denial and session rotation tests |
| CL-206 | planned | CL-203 | Synthetic staff import/export with validation, duplicate detection, dry run, audit and scope checks; document required CSV columns if selected |

**Exit:** Staff and managers can authenticate with correct scopes. Cross-user and cross-location access tests pass. No browser-only permission enforcement.

## M3 — Simple staff experience

| ID | State | Depends on | Deliverable / acceptance |
| --- | --- | --- | --- |
| CL-301 | done; Codex | CL-202–205 | Phone-first Home/Schedule/Me, next shift and self-service profile; only own profile editable; pending email change does not replace verified sign-in until verified |
| CL-302 | partial; Codex | CL-301, CL-402, CL-501 | Time-off request/approve/decline/cancel workflows with private reasons, manager impact preview and transactional handling of assigned shifts; approval history retained |
| CL-303 | partial; Codex | CL-301, CL-404 | Recurring availability limits, one-time blocks and exceptions with timezone-safe intervals; changes to assigned availability flag manager conflicts rather than silently canceling work |
| CL-304 | done; Codex | CL-301, CL-501, CL-503 | Staff schedule and coworker view use published data and scope-safe fields; availability notes/contact details never leaked |
| CL-305 | partial; Codex | CL-301–304 | Usability pass: large targets, plain-language errors, empty/loading/error states, keyboard/screen reader behavior, slow network and mobile-browser testing |

**Exit:** Staff can use Home/Schedule/Me without training for ordinary tasks, and cannot see drafts or private coworker information.

## M4 — Event and shift planning

| ID | State | Depends on | Deliverable / acceptance |
| --- | --- | --- | --- |
| CL-401 | done; Codex | CL-201–204 | Arbitrary-date Event creation/edit/cancel; coverage phases, multiple departments/skills and headcounts; Events can span midnight; no assumed repeating schedule |
| CL-402 | done; Codex | CL-204, CL-404 | Shared server scheduling validator for active employment, memberships, skills, availability, approved leave, overlap, travel and hour limits; human-readable reason codes and tests |
| CL-403 | done; Codex | CL-401–402 | Interval-based pre/during/post headcount and qualified coverage plus handover checks; counts alone cannot falsely mark a partially covered interval staffed |
| CL-404 | partial; Codex | CL-103 | Time model: UTC instants plus location timezone, overnight and DST handling, half-open intervals, cross-week hours and break policy; ambiguous/nonexistent local times handled explicitly |
| CL-405 | done; Codex | CL-301, CL-402, CL-501 | Open-shift request and manager approval; revalidate at approval and atomically prevent double claims; losing requester sees clear result |
| CL-406 | done; Codex | CL-401–404 | Desktop Event board and detailed assignment UI with scope filters, candidate reasons, coverage problems and explicit draft state; no stale overwrite on concurrent edits |
| CL-407 | done; Codex | CL-402, CL-404, CL-406 | Employee scheduled-hours view with scope vs all-location totals, week boundaries and policy limits; draft/published totals clearly labeled |
| CL-408 | partial; Codex | CL-401, CL-501 | Event/shift cancellation, time changes and reopen behavior; publication diff includes moved/removed assignments; restore operations audited |

**Exit:** An irregular, multi-department week can be planned accurately. Concurrency tests prove two valid-looking browser edits cannot commit an invalid combined schedule.

## M5 — Publication, termination and audit

| ID | State | Depends on | Deliverable / acceptance |
| --- | --- | --- | --- |
| CL-501 | done; Codex | CL-202, CL-402–404 | Versioned drafts and publication snapshots; optimistic concurrency; validate and publish in transaction; transactional outbox captures affected-person changes; draft isolation tests |
| CL-502 | done; Codex | CL-203, CL-205, CL-501 | Immediate record-preserving termination: access denial, session/invite revocation, calendar-token revocation, pending-request closure, future-shift reopening and delivery suppression; history intact after rollback/retry |
| CL-503 | done; Codex | CL-202, CL-501 | Public-to-staff schedule projections with visibility policy and field allowlist; contact info and absence reasons excluded from responses and exports |
| CL-504 | partial; Codex | CL-103, CL-202 | Durable audit records for mutation/publication/access lifecycle with actor, reason, before/after references and correlation ID; restricted readers and retention policy |
| CL-505 | planned | CL-502, CL-504 | Archive/rehire/correct-lifecycle procedure; no automatic restoration of old sessions/feed tokens/invites; retention and lawful deletion policy specified by owner |

**Exit:** Publishing, cancellation and termination remain coherent under concurrent changes, retries and worker delay. Old active sessions and tokens cannot bypass termination.

## M6 — Staff email and weekly schedule delivery

| ID | State | Depends on | Deliverable / acceptance |
| --- | --- | --- | --- |
| CL-601 | partial; Codex | CL-501 | Provider adapter and transactional outbox worker with idempotency, bounded retries, backoff, dead-letter handling, error reporting and recipient status recheck |
| CL-602 | done; Codex | CL-601, CL-408 | Shift update/cancellation emails generated from publication diff; only affected active staff receive correct old/new times, dates, locations and timezone |
| CL-603 | partial; Codex | CL-601, CL-404 | Weekly digest job with agreed next-week boundary and local send time; exactly-once effect per recipient/week, duplicate scheduler-run and DST tests; defined empty-schedule policy |
| CL-604 | planned | CL-601–603 | Verified sender domain/provider configuration, text/HTML templates, bounce/complaint handling and delivery-event signature verification; no real sends in tests |
| CL-605 | partial; Codex | CL-604 | Admin delivery status, safe retry, contact verification and mandatory operational-vs-optional communication policy; no provider secrets in UI/logs |

**Exit:** Provider sandbox tests and failure-injection tests pass. Owner explicitly authorizes first real staff delivery after staging review.

## M7 — Personal calendars and phone access

| ID | State | Depends on | Deliverable / acceptance |
| --- | --- | --- | --- |
| CL-701 | done; Codex | CL-501–503 | Private per-staff iCalendar subscription with high-entropy token hashed at rest, revocation/rotation and current employment checks; only published own shifts returned |
| CL-702 | partial; Codex | CL-701, CL-408 | Stable calendar UID, sequence/revision, timezone and update/cancellation semantics; clients tested for moved/canceled shifts; no draft data in feeds |
| CL-703 | partial; Codex | CL-701–702 | Google Calendar, Android calendar, Apple Calendar/iPhone and Outlook onboarding; distinguish subscription from one-time `.ics` download and from add-to-home-screen; actual client test matrix |
| CL-704 | partial; Codex | CL-301, CL-703 | Mobile manifest/icons and installation guidance; app remains useful in ordinary browser; private screens/calendars excluded from offline cache and notification content |
| CL-705 | deferred | CL-703, owner decision | Optional direct Google OAuth integration if subscription UX is insufficient; minimal scopes, encrypted tokens, consent/revocation and maintenance plan |

**Exit:** Current own published shifts update on tested calendar clients after client refresh; terminated tokens fail. Document that already downloaded/copied calendar entries cannot be remotely erased.

## M8 — External Events and modular expansion

| ID | State | Depends on | Deliverable / acceptance |
| --- | --- | --- | --- |
| CL-801 | planned | CL-101, CL-201, CL-504 | Module registry and per-organization enablement with permissions, configuration, health and migration boundaries; disabled module leaves core staff UI unchanged |
| CL-802 | planned | CL-801 | Read-only external Event adapter, explicit source allowlist, safe parser, import limits, timezone normalization, deduplication and stale-source indicators; malformed feeds and SSRF defenses tested |
| CL-803 | planned | CL-802, CL-401 | External context displayed distinctly; manager explicitly converts a source item into a staffed Event and reviews generated coverage; subsequent source edits never silently rewrite staffing |
| CL-804 | deferred | CL-803 | Additional approved providers/webhooks and optional demand suggestions, with provenance and manual control |

**Exit:** External context informs coverage without silently creating assignments or expanding staff complexity. Failure does not take scheduling offline.

## M9 — Pilot, production deployment and operations

| ID | State | Depends on | Deliverable / acceptance |
| --- | --- | --- | --- |
| CL-901 | partial; Codex | CL-104–105 | Production/staging deployment artifacts for chosen host, TLS, secrets, database, worker and scheduler; migrations and roll-forward/rollback rehearsed |
| CL-902 | partial; Codex | M3–M7 core | End-to-end authorization, conflict, concurrency, DST, accessibility and phone-browser acceptance suite; no known critical/high-impact access failures |
| CL-903 | partial; Codex | CL-901 | Structured safe logs, metrics, health/readiness, worker/digest lag alerts, email failures and access anomaly monitoring; no sensitive data logged |
| CL-904 | planned | CL-901 | Encrypted backups and tested restore, agreed recovery objectives, database retention, operator/runbook and incident procedure |
| CL-905 | planned | CL-902–904 | Owner pilot with synthetic data, then approved limited real staff; verify invitations, permissions, hours, termination, delivery and calendar updates |
| CL-906 | planned | CL-905 | Release checklist signed off, source/release tag recorded, deployment version visible, support/rollback responsibilities documented and training material delivered |

**Exit:** Owner accepts real workflow results and operating responsibilities. Release record includes tested version, environment and remaining limitations.

## M10 — Optional expansion after pilot

| ID | State | Depends on | Deliverable / acceptance |
| --- | --- | --- | --- |
| CL-1001 | deferred | Pilot feedback | Shift swaps, offers and emergency fill; revalidate both participants and preserve audit |
| CL-1002 | deferred | Skills policy | Certification expiry reminders and credential evidence with privacy controls |
| CL-1003 | deferred | Time policy | Time clock, attendance, timesheets and payroll export; keep scheduled vs worked hours distinct |
| CL-1004 | deferred | Sufficient usage evidence | Assisted scheduling/forecasting with explainable constraints and human approval |
| CL-1005 | deferred | Commercial direction | Multi-tenant onboarding, organization isolation review, billing, quotas and support tooling |
| CL-1006 | deferred | Owner priorities | Broader localization, SMS/push, advanced reporting and integrations |

## Release-wide definition of done

All relevant requirements traced to tests; no real data in fixtures; code and docs committed together; deployment and rollback verified; monitoring and backups operating; manager and staff acceptance complete; active-session/calendar termination tested; email duplicate/retry behavior verified; independent review recorded if performed. Never infer a review from an agent's name in a branch.

## Release 1.0 implementation notes and remaining acceptance

The original acceptance descriptions above remain the full roadmap, including deliberately broader goals. `partial` means working core code exists but some listed acceptance is still open:

| Task | Implemented now | Remaining work |
| --- | --- | --- |
| CL-105 | Django/dependency/migration/security checks and real Docker/browser/persistence CI | Passing remote run recorded in WORKLOG; keep subsequent release checks green |
| CL-201 / 204 | Multiple catalogs/memberships and required skill checks | Catalog edit/archive, effective dates and skill expiry/evidence |
| CL-205 | Password auth, sessions, one-use invite/recovery, throttles, verified email changes | Real transport acceptance, optional MFA/SSO and independent review |
| CL-302 / 303 | Requests/approve/decline, impact preview/reopening; weekly/date unavailable blocks | Staff cancellation of time-off request and richer exception/effective-date policy |
| CL-305 / 902 | Real browser workflows, 72 widths/routes, axe and visual review | Actual Safari/Android, screen-reader/zoom, slow network, nontechnical user pilot and load |
| CL-404 / 408 | UTC/location timezones, overnight/DST, published updates/cancellation | Break/payroll policy and actual calendar/provider update acceptance |
| CL-504 | Retained publications and authorized audit list | External tamper resistance/correlation policy and owner retention |
| CL-601 / 603 / 605 | Encrypted durable outbox, lease/review/manual retry, unique weekly jobs and status | Provider bounce/receipt handling, complete-day outage digest catch-up, communications policy; SMTP cannot promise exactly-once effects |
| CL-702 / 703 / 704 | Revocable feed, stable UID/sequence/cancellations, phone/client guidance | Actual Google/Apple/Android/Outlook client matrix; install manifest/icons beyond browser shortcut |
| CL-901 / 903 | Non-root Compose image, persistent data, TLS/proxy runbook, health and safe app logs | Owner production deploy, real proxy verification, metrics/alerts and restore rehearsal |

CL-801–803 are planned: only a manual manager coverage-context note exists. Do not mark a live external Event module implemented. CL-206 CSV import, CL-505 rehire/retention, CL-604 provider operations, CL-904 backups/restore policy, CL-905 pilot and CL-906 owner release acceptance remain open. Optional expansions stay deferred.

## Next work queue

1. Verify release PR/main Actions and owner Docker/HTTPS first start using DEPLOYMENT.md. Do not claim the public server was reloaded by a source upload.
2. CL-905: synthetic-data manager/staff pilot; authorize and verify real SMTP/calendar clients; record usability/accessibility findings.
3. CL-904 / 505: agree retention, backup ownership and RPO/RTO; rehearse isolated restore; design safe rehire.
4. CL-011: choose protections/collaboration policy. Ask Claude for an independent scoped review when available; none is claimed yet.
5. Address partial acceptance above from pilot evidence, then CL-801–803 external modules. PostgreSQL, multi-tenancy and optional enhancements follow demonstrated need.

No deployment date or commercial compliance claim is inferred. Claim the next task/branch before changing code; either agent can resume it.
