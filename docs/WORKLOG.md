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
