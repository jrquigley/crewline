# Shared agent instructions

Applies to Codex, Claude, and any other contributor working on this repository. User instructions take precedence. This file is the shared operating agreement; model-specific entry points should reference it rather than maintain competing rules.

## Before work

1. Read `docs/START-HERE.md`, `docs/HANDOFF.md`, `docs/ROADMAP.md`, and the latest `docs/WORKLOG.md` entries.
2. Inspect the actual checkout: `git status --short --branch`, current branch, latest commits, and relevant source. The handoff is a recorded snapshot, not a substitute for inspecting current files.
3. Select an unclaimed roadmap task. Record task ID, owner, branch, scope, acceptance criteria and current status before making substantial changes. If simultaneous work is authorized, use separate branches/worktrees and separate task scopes. Never have two agents mutate the same working checkout concurrently.
4. Consult `docs/REQUIREMENTS.md`, `docs/DECISIONS.md`, and relevant architecture/data-model sections. Distinguish user-confirmed requirements from proposed implementation choices.
5. Do not fabricate tests, deployed services, repository URLs, credentials or another agent's review.

## Product rules

- Use Event / Events for the scheduling unit; use Shift for an individual staff assignment.
- Preserve the simple phone-first staff experience. Administrative complexity stays in manager/admin views.
- Events may be irregular, cross departments and locations, and require coverage before and after the Event with overlapping handovers.
- Employee records and login access are separate concerns. Termination revokes access and preserves required history.
- Real authentication, authorization, assignment validity and publishing must be enforced on the server. The current browser checks are a design reference only.
- Staff must see published data, not manager drafts. Do not expose coworker contact details, private availability notes or time-off reasons in team schedules.
- Never add real staff records, credentials, production backups, tokens or private calendar feed URLs to source or logs.

## While working

- Keep changes scoped to the selected task. Prefer a modular monolith until evidence justifies greater infrastructure complexity.
- Document work completed AND work planned. Record the reason for material decisions, affected files, dependencies and unresolved limitations. Store engineering facts and decisions, not private reasoning transcripts.
- For UI changes, edit `prototype/crewline.fragment.html` and regenerate the standalone preview while this prototype is canonical. Production framework work must have an explicit migration plan; do not silently replace the working reference.
- Do not add dependencies or providers merely to finish a diagram. Any proposed stack, service or release date remains provisional until recorded appropriately.
- Test meaningful behavior and failure paths. Mark unrun checks as unrun. A generated UI, a passing HTTP check, or a browser-only guard is not proof of production security.
- User authorization may permit repository operations, external services or deployments. Otherwise, prepare reviewable work before asking for any required final approval; do not infer permission to send staff emails from a UI design request.

## Required completion and handoff updates

Every meaningful task must update these files in the same change:

1. `docs/WORKLOG.md`: task IDs, author/agent, date, actual changes, validation commands/results, limitations, next work.
2. `docs/HANDOFF.md`: current phase, branch/commit when available, exact resumption steps, incomplete work, changed contracts, known issues.
3. `docs/ROADMAP.md`: task status, owner and dependencies; do not mark simulated features as production complete.
4. `docs/DECISIONS.md`: material decisions and rationale; mark proposed vs accepted vs superseded.
5. Relevant requirements, API, schema, operational and testing documentation when behavior changes.

Do not overwrite another agent's newer handoff silently. Reconcile it against Git history and preserve any unfinished task. If a handoff is stale, fix it and record the discrepancy.

## Git collaboration

- Use task branches such as `codex/CL-101-foundation` or `claude/CL-301-staff-home`. These prefixes describe ownership, not permanent specialization.
- The implementer can be either agent; the other can review when available. Do not claim the other reviewed without evidence.
- Push committed work to a task branch and use a PR. An entirely empty owner-supplied repository may receive its first baseline commit on `main` so it has a default branch; document that bootstrap. All subsequent changes use task branches/PRs. Never overwrite shared history or discard unrelated changes to resolve conflicts.
- Use GitHub issues/PRs for coordination once connected, but retain essential state in repository documentation. A chat or issue link alone is not a sufficient handoff.
- Keep docs accurate at task boundaries. Append work-log records; update the current handoff; supersede decisions instead of erasing their context.

## Current commands

```text
npm run build
npm test
npm start
```

Optional browser checks: `npm run test:browser`; see `docs/TESTING.md` for setup. Production checks will expand when the production stack is chosen.

If npm is unavailable, run `node scripts/build-preview.mjs`, `node --test tests/preview.test.mjs`, and `node server/index.mjs` directly. Do not treat a missing npm executable as a passing test or a reason to install dependencies the starter does not need.
