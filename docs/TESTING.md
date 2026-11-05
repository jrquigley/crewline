# Verification and release tests

## Current starter checks

```powershell
npm run build
npm test
```

When npm is unavailable, use the dependency-free equivalents:

```powershell
node scripts/build-preview.mjs
node scripts/build-preview.mjs --check
node --test tests/preview.test.mjs
```

`npm test` first checks that `public/index.html` matches its source, then runs Node's built-in test runner. No dependency installation is needed for the default suite.

The default suite checks HTTP preview delivery, honest health response, HEAD behavior, restricted file access, method rejection, preview headers, script parsing, Event terminology, and local documentation links. These tests validate the starter, not production scheduling security.

## Optional browser smoke suite

The application runtime has no dependency on Playwright. To run optional browser verification, supply an existing Playwright module or install it as local development tooling. The module must have a compatible browser available.

On the original workstation, the bundled Playwright module and installed Microsoft Edge were used. For any machine:

```powershell
# Supply your actual existing module path if Playwright is not resolvable locally.
$env:PLAYWRIGHT_MODULE = 'ABSOLUTE-PATH-TO-PLAYWRIGHT-MODULE'
# Optional: use an installed browser channel. Omit for Playwright Chromium.
$env:BROWSER_CHANNEL = 'msedge'
npm run test:browser
```

Alternatively, make `require('playwright')` resolvable in your local development environment and install the matching Chromium browser using that Playwright installation. These tools are optional and not vendored in the archive. Do not commit machine-specific module paths. The harness exits with a nonzero error if the module/browser is missing; that is a setup issue, not a passed test.

The browser harness starts the preview server on a random loopback port and closes it afterwards. It verifies:

- Coverage gap correction and missing-skill assignment rejection.
- Staff see the old published shift until explicit publication, then the new time.
- Open-shift request followed by manager approval.
- Multiple departments/headcounts within one Event.
- Creation of a new Event with coverage slots.
- Contact email change remains pending verification in the prototype.
- Correct conditional visibility of one-time vs weekly availability fields.
- Simulated termination removes staff navigation while preserving a historical shift row.
- Main manager and staff pages at 1024px, 360px and 320px with no horizontal overflow: 24 page/viewport combinations.
- No browser JavaScript exceptions during the exercised flows and a dark-mode render sanity check.

This is Chromium/Edge automation, not evidence of actual iPhone/Android calendar integration, full WCAG conformance, real session revocation or simultaneous-user transaction correctness.

## Evidence register

See [Work log](WORKLOG.md) for executed commands and outcomes. Record the exact test environment and whether a check ran locally or in GitHub CI. A workflow file in `.github` is prepared configuration; it is not evidence that GitHub ran it.

At the packaged checkpoint: build freshness passed; all 9 Node tests passed; the optional browser smoke suite passed on installed Microsoft Edge, including 24 responsive combinations and no JavaScript exceptions. Node version was v24.22.1. npm was not exposed on PATH in the Codex shell, so direct Node equivalents were executed. Remote CI, real phones, real calendar providers and production-service tests have not run.

## Mandatory production test categories

| Area | Required cases |
| --- | --- |
| Authorization | Direct API requests across accounts/organizations/manager scopes; export/calendar routes; field-level privacy; inactive accounts |
| Sessions/lifecycle | Active-session termination; invite/recovery invalidation; token rotation; rehire with fresh access; queued and in-flight delivery boundary |
| Scheduling | Skills/membership/availability/leave; same-time and adjacent intervals; interlocation travel; headcount and skill gaps across time segments |
| Time | Overnight, week boundaries, cross-timezone display, DST nonexistent/ambiguous times, all-day leave, actual elapsed duration and break policy |
| Concurrency | Competing assignments, simultaneous claims, stale draft writes, publish during edit, leave approval and termination racing assignment |
| Publication | Draft isolation, atomic snapshot+audit+outbox, move/reassign/remove/cancel diffs, expected-version errors, empty/open coverage policy |
| Email | Duplicate worker/scheduler runs, retries after provider ambiguity, bounce callbacks, recipient status recheck, old/new assignee, next-week digest correctness |
| Calendar | Private feed authorization and revocation, stable UID, revisions and cancellation, refresh behavior on real target clients, no private coworker data |
| External Events | Source allowlist, SSRF/network restrictions, malformed/oversized feeds, dedup, stale sources, explicit conversion and provenance |
| UI/usability | Keyboard/focus and screen reader, touch targets, 320px, real Safari/iOS and Android Chrome, slow/interrupted network, clear loading/errors |
| Operations | Migration bootstrap/upgrade, deployment smoke, backup restore, worker recovery, scheduler visibility, safe logs, dependency configuration and rollback |

Use service/integration tests and real database concurrency tests for business invariants; browser checks alone are insufficient. No real email sends or staff data in automated fixtures. Use provider test transports and synthetic identities.

## Current known prototype limits

- Sample dates are fixed to one week, in Pacific time; arbitrary dates, overnight and DST behavior are not production-ready.
- Browser state, permissions and checks are demonstrative and editable by a user. No trusted server API exists.
- Candidate labels can be advisory until Save revalidates the edited times/requirements.
- Coverage slot counts and per-slot bounds are simpler than the planned interval/headcount engine.
- Primary staff department, simple skill strings and sample history are simplified relative to proposed many-to-many/schema design.
- Digest and calendar connection screens do not send email, authenticate providers or produce a live feed.
- Static prototype mail previews are examples, not proven next-week scheduler execution.
