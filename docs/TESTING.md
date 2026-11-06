# Validation and reproducibility

Production app commands, from repository root after installing requirements in an activated Python 3.12+ virtual environment:

```sh
python -m pip check
python app/manage.py collectstatic --noinput
python app/manage.py check
python app/manage.py check --deploy --fail-level ERROR
python app/manage.py makemigrations --check --dry-run
python app/manage.py test scheduling --noinput
```

Collectstatic is required before rendering with the production hashed-asset manifest. The test runner creates a dedicated disk test database under DATA_DIR and destroys it afterward; use a scratch DATA_DIR, never a production one. Tests use a fast test-only password hasher; a separate assertion checks the actual production hasher policy.

## Recorded local results — November 5, 2026

- 52 Django tests passed on Python 3.12.14 / Django 5.2.19. Includes actual two-thread write contention, assignment eligibility/interval/DST/hours rules, stale versions, scope denial, draft publication, open-shift approval races, one-use/revocable tokens, valid browser-style HTTPS CSRF, termination of active sessions and calendar access, encrypted outbox and duplicate digests.
- Authenticated Playwright 1.62.1 / Chromium 151 browser flow passed: create/assign/publish, invite and set password, staff login, private calendar, hidden draft edit, publication update, time-off approval and termination with retained history/token denial.
- 72 page/width checks across 1440, 1024, 820, 768, 390 and 320 pixels: no horizontal overflow, runtime errors or failed static assets. Manager and staff screenshots were visually inspected.
- axe-core 4.14.0, WCAG 2 A/AA and 2.1 AA tags: no automated violations on 16 key manager/staff/login screens. Incomplete/manual rules remain; this does not certify full accessibility.
- `pip-audit -r requirements.txt` found no known vulnerabilities in the nine pinned runtime packages. Result is a point-in-time advisory check, not a security guarantee.
- Taste consistency/layout/performance scripts were attempted. Their raw Chrome/CDP transport did not complete on this Windows environment; they are explicitly **unverified**, not passing. See DESIGN-REVIEW.md. Actual browser workflow/axe/screenshot checks ran through Playwright instead.
- Local Docker executable/engine was unavailable. Real Linux image build, startup, browser and volume replacement checks run in GitHub Actions; inspect the release PR/main workflow result for their actual outcome.

## Browser harness

Use an isolated freshly migrated/bootstrap database with the five sample employees. The harness mutates data: Avery is invited, requests leave and is terminated. Never run against production. The script rejects a non-loopback hostname.

Install Playwright 1.62.1 and axe-core 4.14.0 in a separate tools directory and install Chromium with Playwright. Set PLAYWRIGHT_MODULE to that module path if it is not resolvable normally, AXE_PATH to axe-core/axe.min.js, TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD and optional TEST_BASE_URL (default http://127.0.0.1:8300). Start the isolated app at that URL. Run:

```sh
node scripts/app-browser.cjs
```

TEST_OUTPUT selects an output directory (default .local/browser, ignored by Git). BROWSER_CHANNEL=msedge can use installed Edge; PLAYWRIGHT_BROWSERS_PATH selects a task-owned browser cache. The first complete suite passed in Edge; the final accessibility suite passed in downloaded Chromium. Axe is injected via DevTools without weakening production CSP. AXE_PATH is mandatory in CI; omitting it locally skips accessibility only and does not imply an audit ran.

## Continuous integration

`.github/workflows/application.yml` checks dependencies, deployment settings, migration drift and Django tests; builds the actual Dockerfile; boots a synthetic deployment; executes Playwright/axe; asserts UID 10001; replaces the container with its original volume and no bootstrap credentials; verifies five retained staff, one ended employee and unchanged owner password. Browser screenshots/reports upload as workflow artifacts. `.github/workflows/preview-checks.yml` retains the historical preview checks. No production credentials are used in CI.

The only Django deployment warnings intentionally retained are HSTS includeSubDomains and preload, to avoid imposing a policy on other owner domains. Correct production TLS/proxy setup is still required.

## Archived preview checks

```sh
node scripts/build-preview.mjs --check
node --test tests/preview.test.mjs
```

These nine Node tests check the old executable design reference and documentation links. `scripts/browser-smoke.cjs` tests that sample preview only. Neither is a substitute for the server security suite.

## Still to validate

Real Safari/iPhone and Android Chrome, real calendar refresh/update/removal behavior, screen-reader/manual keyboard/zoom and slow-network usability, representative production load, SMTP provider acceptance/bounces, proxy headers/TLS, complete-day digest outage behavior, isolated backup restoration and owner pilot acceptance. No independent/Claude review or full penetration test occurred. Record exact evidence and limitations when completing those roadmap gates.
