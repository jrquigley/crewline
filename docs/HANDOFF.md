# Current handoff — resume here

**Author:** Codex. **Date:** November 5, 2026. **Release:** Crewline 1.0.0, authenticated small-team Docker pilot. **Source:** [jrquigley/crewline](https://github.com/jrquigley/crewline), PUBLIC. **Host:** https://shifts.quigspace.com (owner deployment, not deployed by this agent). **Task branch:** codex/CL-101-authenticated-app; inspect Git/PR for latest merge/HEAD instead of assuming this branch is still active.

The owner changed the target from the earlier private repository to this new empty public one. Original main history was retained as the baseline; the earlier repository was not modified. Canonical local checkout during implementation: `C:\Users\jrqui\Documents\Codex\2026-11-04\i-n\outputs\crewline-app`. Do not resume in the old outputs/gig or outputs/crewline snapshots.

## Actual state

Django 5.2.19 server-rendered app with Waitress/WhiteNoise, persistent SQLite and secret in /data, five synthetic staff, secure login/invites/recovery, scoped manager and phone staff workflows, server eligibility and coverage rules, versioned publication, hours, open-shift requests, availability/leave, record-preserving termination, encrypted SMTP outbox/digests and revocable personal iCalendar feed. See README/ARCHITECTURE/DATA-MODEL for contracts. The earlier Node preview is retained as a historical design reference; it is not the running app.

All implementation in this release was by Codex. No Claude/independent review occurred. Read AGENTS.md and follow the same shared records when either agent takes over.

## Resume steps

1. Inspect `git status --short --branch`, remotes, HEAD and recent PR/main Actions; fetch safely and preserve unrelated work.
2. Read START-HERE, latest WORKLOG, ROADMAP and DECISIONS. Choose a remaining task and record owner/branch/acceptance. Do not re-scaffold a second app.
3. Create a Python virtual environment/install requirements; collectstatic; run checks, migration-drift and Django tests as in TESTING. For browser tests create a fresh isolated database; the harness ends Avery's employment.
4. Check GitHub Actions application + Docker/browser/persistence + preview results for the exact revision. Local Docker was unavailable; do not confuse configured CI with a passing run.
5. For owner deployment, follow DEPLOYMENT. Keep the named /data volume and matching secret. First start requires a private owner email/password; no default login exists. Production credentials are not in this repository or chat.

## Verification checkpoint

Local: 56 Django tests passed, complete authenticated Playwright workflows passed, 72 responsive checks, zero automated axe violations on 16 screens, no known vulnerabilities in pinned runtime packages. Screenshots/reports in docs/evidence. Application checkpoint **95773324a99047d3ac086f639d325ae32872f9e2** passed the real Linux Docker/browser/axe/non-root/volume-replacement and Python 3.13 checks in [run 42156448715](https://github.com/jrquigley/crewline/actions/runs/42156448715). Delivery is through [PR #1](https://github.com/jrquigley/crewline/pull/1); inspect its current merge/main SHA. Final delivery update changes documentation only. Taste raw-CDP checker scripts did not complete on Windows; no passing Taste score is claimed. No owner production reload occurred.

## Next work and limitations

Priority: owner Docker/proxy/HTTPS pilot, real SMTP sender/delivery approval, Google/Apple/Android calendar checks, isolated backup restore and retention/recovery policy, actual manager/staff accessibility/usability feedback. Scope-hardening/independent review is welcome. Broader planned tasks remain individually identified in ROADMAP: catalog editing/archive, staff CSV import, skill expiry, rehire, email provider receipts/bounces, digest outage catch-up, module registry/external adapters, PostgreSQL scaling and optional MFA/SSO.

One local-disk app container only. No multi-tenant isolation. Hour limits are planning policy, not legal/payroll advice; defaults need owner review. Availability/leave use workspace timezone. Changing coverage settings can affect validation of existing drafts. Open vacancies may be published; incomplete structural intervals cannot. SMTP jobs queue while disabled; review before enabling after a delay. Ambiguous SMTP outcomes require operator review before retry. Entire configured-day outages currently miss that digest. Calendar refresh is client-controlled; copied/downloaded data cannot be erased remotely. Production TLS, real emails, actual devices and backup restoration were not verified locally.

Keep WORKLOG append-only. At the next handoff update current state, roadmap ownership, decisions and validation with code. Never place live staff data/tokens/secrets in this public repository.
