# Work log

Append completed engineering work, evidence, limitations and planned next steps. Do not rewrite past entries to imply work was completed earlier than it was. This log records actions and decisions, not private reasoning transcripts.

## 2026-11-04 — Initial design and prototype (retrospective record)

**Agent:** Codex. **Tasks:** CL-001. **Basis:** owner requested multi-department/location irregular Event scheduling, skills, availability, open shifts, notifications, termination/history, calendars, simple phone staff UI and desktop management.

Created the Crewline working-name interface: Event board with pre/during/post coverage, weekly employee hours, location/department filters, staff directory/profile editing, skills and location eligibility, open-shift request/approval, time-off workflows, recurring/one-time unavailable periods, sample rules, explicit publishing and staff-visible snapshots. Added multi-department coverage slots, sample historical records and simulated access denial for terminated staff. Added contact email verification-pending state, sample notification settings/templates, calendar onboarding screens and optional external Event context.

Validated original prototype using bundled Playwright with installed Microsoft Edge. Exercised draft isolation/publication, missing-skill rejection, open-shift approval, mixed-department coverage, Event creation, pending email verification, conditional availability fields and simulated termination. Checked 24 page/viewport combinations at 1024px/360px/320px without horizontal overflow or runtime exceptions. Inspected light/dark screenshots. These were interface checks, not real backend or calendar-provider tests.

Found and fixed a CSS issue where styled fields overrode the HTML hidden state. Fixed staff reading draft assignments by introducing published sample snapshots. Added historical rows separate from future assignments so simulated offboarding did not erase sample history.

Limitations explicitly communicated: no authentication backend, database, actual mail, weekly job, live calendar feed, external source service or production deployment. The original browser prototype was saved in the chat visualization directory; its portable source is now copied into this project under `prototype/`.

## 2026-11-04–05 — Repository-ready web-server starter and full roadmap

**Agent:** Codex. **Tasks:** CL-002–005. **Owner direction:** use Event terminology, serve as a web application, store on GitHub, document all work/plans, and enable Codex/Claude handoffs. Owner confirmed GitHub account exists, no new project repository yet.

### Changes

- Replaced prior scheduling-unit terminology with Event/Events throughout the delivered prototype and source identifiers; invalidated older saved host state with schema version 3.
- Preserved the canonical fragment at `prototype/crewline.fragment.html` and synchronized the in-chat reference.
- Created a portable standalone build in `scripts/build-preview.mjs`, generated `public/index.html`, removed dependence on optional host design controls and supplied memory-only preview state/decorative symbol fallback.
- Added a dependency-free Node HTTP server with preview-only route allowlist, loopback default, health identity, no-cache and restrictive preview headers.
- Added default Node checks and an optional portable Playwright smoke harness; prepared a GitHub Actions workflow and PR template.
- Wrote README, shared agent instructions, Claude entry point, contribution process, requirements traceability, full task roadmap with milestone gates, proposed architecture/API/data model, accepted/proposed/open decisions, GitHub access, deployment, testing, work log and current handoff.
- Added Git ignore/line-ending policies. No real staff data, secrets, provider accounts or third-party runtime dependencies were added.

### Environment and access checks

Node reported `v24.22.1` on the original workstation. Git and GitHub CLI were available. The current workspace was not a Git repository. `gh auth status` could not read its configuration due to sandbox file-access denial, so authentication remains unverified. No remote repository, Git initialization, commit, push, account invite, email or deployment was performed.

Verified GitHub CLI browser-authentication/setup/repository-create instructions and official OpenAI local Git workflow documentation; links are recorded in GITHUB-ACCESS.md. Also verified that GitHub Pages is static hosting, so production server hosting remains a separate decision.

### Validation

- `node scripts/build-preview.mjs`: passed; generated the standalone preview.
- `node scripts/build-preview.mjs --check`: passed; generated document matches canonical source.
- `node --test tests/preview.test.mjs`: **9 passed, 0 failed**. Includes live loopback HTTP checks, script parsing, terminology and all local documentation links.
- `node scripts/browser-smoke.cjs` with local Playwright module and `BROWSER_CHANNEL=msedge`: **passed**. Exercises assignment rejection, draft isolation/publication, request approval, mixed-department coverage, Event creation, pending contact verification, availability controls, offboarding/history, 24 responsive combinations and no JavaScript exceptions.
- Repository-wide terminology scan: no superseded scheduling-unit term found in the delivered project.
- Packaged `crewline-starter.zip` with all 27 project files, including `.github` and `.gitignore`; archive contents/integrity verified. The archive contains no Git metadata, credentials, installed dependencies or external service configuration.
- `npm test` was attempted but npm was not on PATH in the current Codex shell. No npm test result is claimed; the direct Node build/check/test equivalents above passed. README and TESTING include direct commands.
- GitHub CI, actual iOS/Android devices, calendar providers, email delivery, production sessions/database/concurrency and a second-agent review were **not run** because those services/workflows are not implemented or connected.

See TESTING.md for repeatable commands and limits. The packaged project has no application dependencies. No approval was requested for GitHub credential access because the remote repository does not yet exist and the owner requested setup instructions, not an immediate remote write.

### Next work

CL-010: owner creates/selects repository, completes authentication and shares URL/local project location; agent verifies permitted access before pushing. CL-101: choose production hosting/stack/auth baseline and resolve minimum scheduling policy decisions; then CL-102–105 production foundation. All production tasks remain unassigned. The architecture and data model are proposals, not deployed functionality.

## Work-log entry template

```text
Date/timezone:
Agent/person:
Roadmap task ID(s), branch and checkpoint:
Problem and intended behavior:
Files/contracts changed:
Actions actually completed:
Decisions made (and decision IDs):
Validation commands, environment and results:
Checks not run and why:
Known limitations / unfinished work:
Next action, dependencies and proposed owner:
Handoff/roadmap/contracts updated:
```


## 2026-11-05 — Connect the owner-supplied GitHub repository

**Agent:** Codex. **Task:** CL-010. **Owner:** Codex. **Branch:** initial `main` bootstrap. **Repository:** https://github.com/jrquigley/gig.

The owner provided the repository URL after creating it. Initial sandbox GitHub checks failed due to network/config access. A scoped permission grant was obtained, but Windows credential/config access still failed in the sandbox. Read-only verification in the normal Windows account context succeeded: authenticated account `jrquigley`, admin permission, private repository and no existing commits. No password or raw token was printed or saved.

Cloned the empty repository into `outputs/gig` and copied the 27-file prepared starter. This checkout is the canonical connected project; the earlier `outputs/crewline` and ZIP are delivery snapshots. Updated current repository state, access instructions, decisions, roadmap and this handoff. Recorded the first-baseline-on-main exception for an empty repository; later work uses PRs.

No Git author identity was configured, so the initial commit will use the verified account login and standard GitHub no-reply address via per-command settings, without changing global Git configuration. Sandbox ownership differs from the user checkout; run Git in the authorized normal account context instead of adding a global safe-directory exception.

Pre-import validation in the connected checkout passed: `node scripts/build-preview.mjs --check`, all 9 Node tests, and the Microsoft Edge browser smoke suite including 24 responsive combinations with no runtime exceptions. First push, commit checkpoint and remote CI results will be recorded after completion. Production implementation remains unstarted; CL-101 is the next design/foundation task.


### CL-010 verified import checkpoint

Initial project commit: `5d97d5ad4acb3bd9c8388a839a6bb2bfe35b1e03` (`Add Event scheduling preview and shared implementation roadmap`), pushed to private `origin/main`. GitHub default branch confirmed `main`. Initial remote [Preview checks run](https://github.com/jrquigley/gig/actions/runs/42096161232) completed with conclusion **success**. Root content was verified through GitHub's repository API.

The local pre-push build freshness, all 9 Node tests and browser smoke/24 responsive combinations passed. No application behavior changed during connection. Author/committer identity used the verified account `jrquigley` and GitHub no-reply address via per-command Git settings; no global author or safe-directory settings were changed.

Post-import handoff updates are on `codex/CL-010-repository-handoff` for a documentation PR, following the shared process. They replace stale no-repository/unverified-CI statements in the current-state documents, mark CL-010 complete, and identify CL-101 as the next ready task. The original preparatory entries above remain an accurate historical record. Review and CI results for the documentation PR are visible in GitHub; no human or Claude review is claimed. No production deployment, actual staff communication, permission-setting change or license grant occurred.


## 2026-11-05 — CL-101 release implementation, new Crewline repository

**Agent/owner:** Codex. **Branch:** codex/CL-101-authenticated-app. **Scope:** functioning authenticated website requested by owner, five synthetic staff, intuitive manager/phone staff UI, Docker readiness, tests/design and durable shared documentation. The owner selected public jrquigley/crewline and shifts.quigspace.com. Verified the new repository empty/public and preserved its visibility. Cloned previous baseline history into outputs/crewline-app, changed its origin, left the earlier repository unchanged. No agents/Claude review or production deployment occurred.

Implemented Django 5.2.19/Waitress/SQLite production app; complete source is under app/. Built server-side auth, CSRF, throttles, invitations/recovery, current-password new-address verification, scoped manager roles, staff/department/location/skill administration, Event drafts/coverage/assignment and split handovers, hours/CSV, publish/cancel revisions, availability/time off/open-shift requests, history and transactional termination/session/token revocation. Added encrypted database outbox, bounded background delivery/digests and private iCalendar feeds. Non-root Dockerfile/Compose, validated environment bootstrap, persistent generated secret and five seed employees have no shared passwords. Added migrations and service tests, real browser harness and Docker/browser/persistence CI. Taste palette/type/motion applied; local licensed variable font, original mark, no external runtime assets.

Meaningful failures corrected during development: missing static manifest before tests; browser Origin:null caused by no-referrer policy (changed same-origin); pending email verification was initially addressed to the old recipient (explicit new recipient); sensitive outbox and transient invite values now encrypted; targeted offboarding/leave snapshots deep-copy before diff; separate minimum coverage from shift rotations; current-password challenge for email changes; early throttle response avoids repeated password work; private token application log paths redacted. None of these failures is presented as a passing initial check.

Validation: 52 Django tests passed including real two-thread overlapping assignment contention, scopes, publication/draft isolation, offboarding active session/calendar/history, interval/DST/hours/availability, one-use tokens and email/digest idempotency. Complete Edge browser suite passed after CSRF fix; final Playwright 1.62.1/Chromium 151 suite passed with 72 responsive route/width checks and 16 axe-core 4.14.0 screen audits (zero automated WCAG-tag violations; manual/incomplete rules remain). No runtime errors, failed static assets or horizontal overflow. Final screenshots inspected. pip-audit found no known advisories in nine runtime pins. Django checks/migration drift and archived preview tests are rerun at final delivery; remote CI outcome will be appended separately.

Taste consistency/layout/perf scripts attempted with Edge and downloaded Chromium; raw Chrome/CDP failed or stalled. Incomplete reports are not passing. Playwright/axe/screenshots provided actual working product checks. Local Docker unavailable; GitHub CI must supply actual build/start/UID/browser/volume replacement evidence. No real SMTP sends, actual phone calendars, production TLS/proxy, restore or user pilot verified. Source contains synthetic data/test-only passwords only. Full README, architecture/schema, requirements, roadmap statuses, decisions D-015–019, deployment/test/design/user guides and current handoff updated; previous worklog preserved. Next: remote PR/CI/merge and owner Docker pilot, then remaining operational/client/module acceptance in ROADMAP.


### Remote validation correction before merge

First remote Docker build/start passed; application/dependency/preview jobs passed. Browser assignment failed because the harness computed tomorrow in runner UTC while seeded Events use workspace Pacific time. Changed the harness to read the server form date, retaining real conflict enforcement. Added a shared-employee scope regression: non-admin managers cannot edit records with departments/locations outside their full scope, preventing a restricted form from dropping uneditable memberships. Added bearer-log redaction regression; current suite is 54 tests. Final remote rerun and evidence follow.


### Docker validation and targeted-publication hardening

Remote run https://github.com/jrquigley/crewline/actions/runs/42156197473 passed on a6a4ed6, including the actual Linux production image, live authenticated browser/axe flow, non-root UID 10001 and retained records/password after replacement using the original named volume without bootstrap credentials. The matching preview run passed. Additional review then found a targeted leave/termination revision could mark unrelated drafts clean and derive email labels from draft metadata. Fixed targeted publication to preserve a dirty draft version and render notifications exclusively from published snapshots; notifications now show prior and current times with both dates/timezone. Added two regression tests: current 56 Django tests pass. These follow-up changes trigger another full remote run before merge. Shared staff edit UI now explains when an administrator is needed.

### Verified release application checkpoint

Application commit **95773324a99047d3ac086f639d325ae32872f9e2** passed the full [Application and Docker PR run](https://github.com/jrquigley/crewline/actions/runs/42156448715) and [Preview checks](https://github.com/jrquigley/crewline/actions/runs/42156448701). All three application jobs succeeded: 56 Django tests/checks/migration validation on Python 3.13; no known runtime dependency advisories; actual Linux Docker build/start, authenticated browser/axe workflow, non-root UID, and persistent database/password/history after container replacement. The equivalent push-triggered run also passed. Downloaded browser evidence for inspection. This is real container validation, not just a prepared workflow.

Release PR: [#1](https://github.com/jrquigley/crewline/pull/1), attached to this task. Final documentation records the verified code checkpoint; latest PR/main Git state and subsequent workflow identify the final merged revision without embedding a commit's own SHA in itself. No runtime code changes follow this checkpoint in the documentation-only delivery update. The owner can build/reload with the documented private environment and persistent volume after main is updated. No production container, SMTP account, device calendar or server proxy was accessed or reloaded. Remaining production/client/policy work stays in ROADMAP.
