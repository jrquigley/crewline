# Current handoff — resume here

**Author:** Codex. **Checkpoint:** November 5, 2026, America/Los_Angeles — GitHub import completed; production foundation is next. Source sample week remains November 2–8.

**Source:** [jrquigley/gig](https://github.com/jrquigley/gig), private. **Default branch:** `main`. **Verified initial application checkpoint:** `5d97d5ad4acb3bd9c8388a839a6bb2bfe35b1e03`. **Initial CI:** [passed](https://github.com/jrquigley/gig/actions/runs/42096161232). The follow-up task branch `codex/CL-010-repository-handoff` records this evidence; inspect current Git history for its merge and latest HEAD rather than assuming this initial SHA is still the tip.

## Actual state

The interactive manager/staff reference is preserved and now uses Event terminology throughout. A standalone generated document and dependency-free Node preview server are packaged with shared project documentation and prepared GitHub CI. This is a web-server starter for reviewing the interface; production application services remain unimplemented.

The owner supplied `https://github.com/jrquigley/gig`. On November 5, 2026, Codex verified that it was private and empty and authenticated GitHub access has admin permission. The canonical checkout is now `C:\Users\jrqui\Documents\Codex\2026-11-04\i-n\outputs\gig`, branch `main`, with origin set to that repository. The starter was committed and pushed to `origin/main`; the first GitHub preview CI run completed successfully. There is no deployment. The prior `outputs/crewline` folder and ZIP remain historical pre-connection snapshots.

## Start in this order

1. Read AGENTS.md and docs/START-HERE.md; inspect the latest WORKLOG and ROADMAP rather than relying on the chat.
2. Inspect actual files/Git state. If now inside a repository, record `git status --short --branch`, remote, HEAD and uncommitted changes; the state may have changed since this handoff.
3. Run `npm run build` and `npm test`. Run optional browser smoke only with available Playwright/browser; setup and limitations are in TESTING.md.
4. CL-010 is complete. Verify the import and CI checkpoint in the latest WORKLOG. The repository already exists; do not create another or change visibility. Use `git fetch`/`git status` and the remote CI result to establish current state.
5. Claim **CL-101** for the production foundation decision. Review the open questions in DECISIONS.md. Ask only what is necessary: hosting environment, existing stack/auth requirements, initial scale and single-organization vs multi-tenant intent. Continue independent local planning while waiting.
6. Record accepted technical decisions, then implement CL-102–105 with proper database/auth foundations. Preserve the preview as an executable design reference during migration.

## Completed work and important files

- Prototype: `prototype/crewline.fragment.html` — canonical UI/sample interaction source. Current host state schema is version 3; earlier saved prototype state is intentionally incompatible after terminology update.
- Standalone export: `scripts/build-preview.mjs` → `public/index.html`; no chat runtime or external icon/font download required.
- Server: `server/index.mjs`; only public preview/health/favicon routes, no scheduling API. Default loopback port 3000.
- Tests: `tests/preview.test.mjs`; optional `scripts/browser-smoke.cjs`.
- Documentation: requirements, 11 milestone sections, stable task IDs/dependencies, proposed architecture/data model, decision register, access/deployment/testing instructions, this handoff and append-only work log.
- Agent coordination: `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, PR template and prepared CI.

## Validation checkpoint

Build freshness and all 9 Node tests passed. The optional Microsoft Edge browser suite passed, including simulated offboarding/history and 24 responsive combinations with no JavaScript exceptions. npm was not on PATH in the current shell; direct Node commands were used. Exact results are recorded in WORKLOG.md. Re-run checks in the next checkout. The initial GitHub CI run also passed; the documentation follow-up PR has its own checks. Browser evidence does not prove backend security.

## Outstanding limitations / do not misrepresent

- No production auth, shared database, actual email, scheduler, live calendar feed or external Event importer.
- Offboarding is simulated; a production server must revoke sessions/invites/calendar tokens, suppress deliveries and retain historical revisions transactionally.
- All fixed dates/data are samples. No overnight/DST production handling.
- No deployment target, production framework/provider choices, retention policy or license selected.
- Calendar subscription client instructions require real-device testing. Direct Google OAuth is optional/deferred.
- No work was performed by Claude and no second-agent review has occurred.

## Suggested next ownership

CL-010: completed by Codex with an initial source import and passing remote CI. CL-101: next available agent, unassigned. CL-011 branch protections and collaboration policy remain planned; repository settings were not changed. Once schema/API contracts are accepted, one agent may build server/domain services while the other implements staff/manager screens against those contracts, in separate branches/worktrees. Either agent can switch roles.

## How to leave the next handoff

Update this file with owner/task/branch, actual changed files, exact commands/results, partial work and next action. Append WORKLOG rather than erasing earlier work. Update roadmap task status and decisions/contracts. Commit and push through the authorized workflow so another computer can see the checkpoint. Do not replace substantive state with only a chat link or issue number.
