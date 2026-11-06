# Decision register

Use stable IDs and explicit states: confirmed direction, accepted technical decision, proposed, open, superseded. User-confirmed product direction does not imply approval of every stack/provider choice below.

## D-001 — Browser application served by a web server

**State:** confirmed direction. Owner explicitly described a web-server application. GitHub stores source and coordination; runtime hosting is separate. A local sample-data preview server is implemented. Hosting direction now confirmed: Docker at shifts.quigspace.com; see D-015.

## D-002 — Event terminology

**State:** confirmed direction and implemented in delivered prototype/starter. Scheduling occasions are Events. Individual staffing slots are Shifts. External Events are read-only context unless converted by a manager. Keep source labels, documentation and tests consistent.

## D-003 — Two main experiences

**State:** confirmed direction. Manager/admin primarily desktop/laptop; staff primarily phone browser with exceptionally simple UI. Staff Home/Schedule/Me is the current design proposal and prototype, not an irrevocable navigation decision.

## D-004 — Shared durable documentation

**State:** confirmed direction and initial implementation complete. Codex and Claude share AGENTS.md, roadmap, decision register, work log and current handoff. Every material task updates docs with code. Chat history is supplementary context only. No permanent division of agent responsibilities is assumed.

## D-005 — Framework-neutral production planning; modular monolith recommended

**State:** superseded by D-016 for release 1.0. Original proposal: prefer one codebase, relational database and background worker with clear domain boundaries. Suggested evaluation baseline: TypeScript, React, a Node framework and PostgreSQL. Reason: scheduling relies on shared transactional invariants and reliable outbox effects. No production packages or framework have been installed. Resolve under CL-101 before production scaffolding.

## D-006 — Keep prototype as executable design reference

**State:** accepted local preparation decision; reversible. Source fragment is canonical for preview, with generated standalone HTML and a minimal Node server. Purpose: preserve interactive work and enable immediate review from a clean checkout without external services. This is not a decision to implement the production app as one large HTML file.

## D-007 — Explicit publication and server authority

**State:** accepted and implemented by D-017; defaults remain configurable. Original planning: Staff read published snapshots; managers edit drafts. All security and scheduling rules must be enforced server-side. Publication should atomically create revision, audit and outbox entries. The owner has not yet accepted all warning/blocking policies.

## D-008 — Record-preserving termination

**State:** confirmed direction, core implemented; see D-017. Revoke access while retaining records. The server design separates employee records from accounts. Active-session, invite, calendar-token and queued-delivery revocation are release requirements. Retention duration and rehire policy remain open.

## D-009 — Calendar subscriptions first

**State:** accepted implementation, actual-client acceptance remains open. Private read-only iCalendar feed supports several calendar clients with fewer provider dependencies. One-time exports and phone home-screen shortcuts are separate flows. Direct Google OAuth is deferred pending need. Existing downloaded entries cannot be remotely erased. Actual client onboarding must be tested.

## D-010 — GitHub setup and permissions

**State:** owner selected `https://github.com/jrquigley/gig` on November 5, 2026. Verified private, empty, and authenticated account `jrquigley` has admin permission. The supplied repository name is retained; scheduling terminology remains Event. Initial sandbox checks failed, including after a scoped network/config read grant; using the normal Windows account context allowed GitHub CLI keyring and HTTPS access. No token was exposed or persisted. License remains unselected.

## D-011 — Source of truth and simultaneous work

**State:** accepted preparation workflow, subject to owner direction. One roadmap and shared contracts. Use separate task branches/worktrees for simultaneous work. Record owner/task/branch before implementation. Either agent may implement or review; no fabricated second-agent review. Shared progress must be committed/pushed to be visible across computers.

## D-012 — Current dependency policy

**State:** accepted for starter only. Preview build/server/default checks use Node built-ins and require no third-party packages. Optional browser verification uses a separately installed Playwright module. Introduce pinned dependencies and lockfile when the production stack is scaffolded.

## Original foundation questions (current answers follow in D-015–019)

| Question | Why it matters | Default proposal / task |
| --- | --- | --- |
| Where will the server run: Windows, Linux, managed platform, internal network? | Deployment, process supervision, database connectivity, HTTPS | Do not choose silently; CL-101 |
| Single organization or commercial multi-tenant product? | Identity boundaries, tenancy, billing, data isolation | Initial single organization with scoped IDs; CL-101 |
| Expected staff, manager, location and Event counts? | Performance, pagination and test data | Collect representative scale before performance gates |
| Existing auth/SSO or organizational stack? | Account provisioning and support | Choose during CL-101/205 |
| Can staff belong to several departments and locations? | Membership and candidate rules | Data model supports many-to-many; confirm policy |
| Are hour limits warnings or hard blocks; who can override? | Eligibility and publication decisions | Prototype hard-blocks assignment over sample limit; policy unapproved |
| What defines paid hours, breaks, overtime, workweek? | Hour totals and labor constraints | No legal/payroll policy inferred from sample numbers |
| When is incomplete coverage publishable? | Critical staffing exceptions vs ordinary open slots | Separate warnings from blocking validity errors; CL-403/501 |
| What is exact handover and pre/post coverage interpretation? | Interval coverage and duration | Document sample in architecture; confirm for production |
| Are open-shift requests always manager-approved? | Workflow and concurrency | Prototype requires approval; confirm |
| Weekly digest day/time, week boundary, empty weeks? | Reliable delivery and expectations | Example Sunday 5pm Pacific for upcoming week; confirm |
| Which external Event sources are allowed? | Adapter, permissions and network risk | Source-specific allowlists; CL-802 |
| Who may see coworkers across department/location scopes? | Staff privacy and organizational transparency | Published names/times only in allowed locations |
| What retention, export, deletion and rehire policies apply? | History, privacy and lifecycle | Owner policy required; CL-505 |
| Repository visibility, license and release approval owner? | Distribution and governance | Owner decides; CL-010 |

Do not turn all open questions into an immediate questionnaire. Resolve only those needed for the next implementation task while continuing independent work.


## D-013 — Initial empty-repository bootstrap

**State:** accepted implementation choice for CL-010, November 5, 2026. The owner supplied a verified empty private repository and requested the prepared project be posted to GitHub. Import the reviewed starter as the first `main` baseline, without overwriting any existing history, then use task branches and PRs for subsequent work. Keep repository visibility and the owner-supplied repository name unchanged. Use the verified account login with its GitHub no-reply address for this commit because no Git author identity is configured; do not change global Git configuration. Production architecture, hosting and license decisions remain open.


## D-014 — Verified connected source checkpoint

**State:** completed CL-010 checkpoint, November 5, 2026. Canonical source is the private owner-supplied repository `https://github.com/jrquigley/gig`; default branch `main`. Initial source commit `5d97d5ad4acb3bd9c8388a839a6bb2bfe35b1e03` was pushed successfully, and the first Preview checks GitHub workflow passed. Local application build, 9 Node tests and browser smoke passed before upload. The historical standalone delivery remains in `outputs/crewline`; continue development in the connected checkout `outputs/gig` or a clean clone/worktree. No repository visibility, licensing, branch-protection or production-host settings were changed. Production choices remain open and CL-101 is next.


## D-015 — Updated repository and host

**State:** owner-confirmed, November 5, 2026. Current target is public https://github.com/jrquigley/crewline and https://shifts.quigspace.com on Docker. This supersedes D-010/D-014 as the current source location; they remain historical records. Preserve baseline history and existing repository visibility. Upload/merge authorized by the request. No server credentials were supplied and no production reload is claimed. No license/branch-protection settings changed.

## D-016 — Small-team single-container implementation

**State:** accepted implementation under the owner's instruction to build. Django 5.2 LTS, Waitress, server-rendered progressive enhancement, WhiteNoise and SQLite persistent /data. Supersedes D-005's unimplemented TypeScript/React/PostgreSQL proposal. Built-in authentication/forms/CSRF and a single container reduce setup burden while supporting the requested workflows. Short IMMEDIATE transactions serialize writers; actual contention is tested. One local-disk replica only. PostgreSQL/multi-tenancy need their own reviewed migration when scale requires them. Dependencies pinned; not a claim of future indefinite security.

## D-017 — Publication, staffing and employment policy defaults

**State:** implemented defaults, subject to owner pilot feedback. Managers publish explicit revisions; staff never read drafts. Open vacancies can publish, structural interval gaps cannot. Active qualification/availability/overlap/travel/weekly limits hard-block assignment/publication, with no silent override. Required phase headcount is separate from split-shift parts. Default pre/post/handover/travel are 60/30/15/30 minutes; Monday workweek, elapsed planning hours, no paid-break/payroll rules. Availability/leave use workspace timezone; Event local times use location timezone, typed ambiguous/nonexistent DST times are rejected. Offboarding revokes access immediately and reopens future assignments without deleting history; rehire/retention still require policy.

## D-018 — Credentials, email and calendars

**State:** implemented. No public signup/default password. First admin via private environment; staff invitations one-use, fake staff start with unusable passwords. Minimum password 15 characters. Own email change needs current password and new-address verification before sign-in changes. Tokens hashed, sensitive outbox bodies/session invite encrypted with persisted app secret. Keep DB/secret together. SMTP disabled until configured; fake recipients blocked. Durable deduplicated jobs, manual review for ambiguous SMTP outcomes; no exactly-once SMTP guarantee. Weekly Sunday 17:00 next Monday–Sunday, including explicit empty week; full-day outage catch-up pending. Private one-year revocable iCalendar feed first; OAuth deferred, actual clients unverified. Messages/calendar data already accepted/copied cannot be recalled.

## D-019 — Design and remaining operations

**State:** implemented UI with explicit validation limits. Taste palette/type/motion applied to the operational application, preserving the established Crewline product name. Marketing-screen rules are inapplicable to authenticated forms. Actual Playwright/axe/screenshots verified; Taste raw-CDP scripts did not finish, not reported as green. Hallmark inspected but not applied to an existing established design without a named redesign request. No Claude/independent review. Production TLS/provider/device tests, retention/recovery, backup restore, pilot feedback and future external modules remain roadmap gates. No commercial trademark clearance or project license is implied by the working name.
