# Start here

Requirements first captured November 4, 2026; current preparation checkpoint November 4–5, America/Los_Angeles. Project name Crewline is a working name.

## What the owner wants

A web-server application for irregular Event-based scheduling across departments and locations. Managers need coverage, eligibility and employee-hour visibility. Staff need a very simple phone browser interface: next shift, upcoming schedule, time off, personal details, availability, open shifts and coworker schedules. Email updates, a weekly schedule email, personal calendars, record-preserving termination and modular external Event context are required. Source and coordination will be on GitHub. Codex and Claude must be able to resume each other's work.

## What exists

- An interactive sample-data UI with both interfaces, basic in-browser scheduling checks and draft/published snapshots.
- A self-contained browser export and dependency-free Node preview server.
- Automated checks for the preview server/build and an optional browser interaction harness.
- A full implementation roadmap, proposed architecture/data model, decisions, work log and handoff instructions.

## What does not exist

Production authentication/authorization, shared database, secure session revocation, scheduling APIs, durable audit history, actual emails, queued jobs, a weekly delivery scheduler, personal calendar feeds, live external Event ingestion, production infrastructure and an approved license. Browser sample data is not a database. The preview interface switch is not role-based security.

The owner supplied [jrquigley/gig](https://github.com/jrquigley/gig) on November 5, 2026. It was verified private and empty, and the authenticated account has admin access. The canonical local checkout is now `outputs/gig` in the original workspace; `outputs/crewline` and its archive are the earlier delivery snapshot. The initial import is being prepared on `main`. No production deployment exists.

## Reading order

1. [Handoff](HANDOFF.md): actual latest checkpoint and next task.
2. [Requirements](REQUIREMENTS.md): what must be delivered.
3. [Roadmap](ROADMAP.md): ordered tasks and release gates.
4. [Decisions](DECISIONS.md): accepted direction vs proposals and open questions.
5. [Architecture](ARCHITECTURE.md) and [Data model](DATA-MODEL.md).
6. [Testing](TESTING.md), [Deployment](DEPLOYMENT.md), [GitHub access](GITHUB-ACCESS.md), [Work log](WORKLOG.md).

## Current source map

| Path | Purpose |
| --- | --- |
| `prototype/crewline.fragment.html` | Canonical prototype UI, sample data and local interaction logic |
| `public/index.html` | Generated standalone UI; served by the preview server |
| `scripts/build-preview.mjs` | Standalone generator; no external runtime assets required |
| `server/index.mjs` | Preview server; only `/`, `/index.html`, `/healthz`, `/favicon.ico` |
| `tests/preview.test.mjs` | Node test suite |
| `scripts/browser-smoke.cjs` | Optional browser smoke checks |
| `docs/` | Shared project state, requirements and future implementation design |
| `AGENTS.md`, `CLAUDE.md` | Shared and agent entry instructions |
| `.github/` | Prepared CI and contribution templates |

## Working principles

- Event = real-world staffing occasion; Shift = staffing slot/assignment; External Event = read-only planning context until explicitly converted.
- Each Event can have multiple departments, skills and people in each coverage phase.
- Staff screens remain simple as modules are added.
- Publishing is explicit and must eventually be transactional.
- Preserve historical scheduling records independently of account access.
- Every material change includes documentation, evidence and a resumption point.
