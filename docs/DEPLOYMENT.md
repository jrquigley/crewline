# Deployment and operations

## Implemented now: local sample-data preview

Requirements: Node.js 22+; no application dependencies, database or provider accounts.

```powershell
npm run build
npm test
npm start
```

Without npm: `node scripts/build-preview.mjs`, then `node --test tests/preview.test.mjs`, then `node server/index.mjs`.

Default address: `http://127.0.0.1:3000`. `GET /healthz` reports `mode: interface-preview` and `productionReady: false`. The server rejects mutations, serves only the generated document plus health/favicon routes, disables caching and disallows outbound browser connections through CSP. No authentication is implemented. All UI switching and simulated offboarding run in the browser.

Optional local port override:

```powershell
$env:PORT = '3100'
npm start
```

The default loopback binding is intentional. Do not expose this preview to real staff or enter real personal information. Setting `HOST=0.0.0.0` makes a server network-reachable according to local firewall/network rules; it does not add security or production services.

No production website, GitHub Pages deployment, Docker image, cloud project, database, worker or scheduler has been created. No host has been selected. Stop the local server with Ctrl+C. A refresh resets sample data in the standalone preview.

## Planned production topology

- HTTPS application server with supported Node/runtime/framework under the accepted architecture decision.
- PostgreSQL with least-privilege application and migration credentials, encrypted connections where appropriate, migrations, backups and restore testing.
- Worker process from the same versioned release for email outbox and external Event ingestion.
- Scheduler that triggers idempotent weekly digest jobs with explicit timezone semantics.
- Mail provider with verified sending identity and authenticated delivery callbacks.
- Secret injection from deployment environment/secret store, never source control.
- Separate staging environment with synthetic data and provider sandbox/sink.
- Safe logging, operational dashboards/alerts and documented incident/rollback procedures.

These are requirements/proposals, not configured infrastructure. A reverse proxy, managed ingress or platform handles TLS under the chosen host. Do not choose a Windows service, Linux unit or container recipe until the hosting environment is known.

## Proposed configuration contract

Names below are design placeholders, not currently read by the preview except HOST/PORT. Finalize with the production scaffold and add a secret-free `.env.example` then.

| Setting | Purpose |
| --- | --- |
| `NODE_ENV`, `HOST`, `PORT` | Runtime and bind configuration |
| `APP_BASE_URL` | Canonical HTTPS links in staff emails and calendar setup |
| `DATABASE_URL` | Runtime database connection; separate migration role if selected |
| `SESSION_SECRET` or provider-specific settings | Session integrity/provider credentials under chosen auth architecture |
| `EMAIL_PROVIDER`, provider key, sender identity | Operational email transport |
| `SCHEDULING_TIMEZONE`, workweek configuration | Defaults for organization setup; location timezones stored in DB |
| `WORKER_CONCURRENCY`, retry policy | Bounded job execution and recovery |
| Calendar token hashing/rotation secret if design requires | Protect private feed credentials |
| External source credentials | Module-specific encrypted settings, not general UI data |

## Required release checklist

1. CI and owner acceptance pass for the release commit; dependencies locked and migration compatibility reviewed.
2. Back up data and verify that restore instructions actually work. Agree recovery time/data-loss objectives.
3. Apply migrations using the documented strategy. Test old/new app compatibility during rollout; use forward fixes when destructive schema rollback would lose data.
4. Deploy app and compatible worker/scheduler versions. Liveness alone is insufficient; verify DB readiness, worker progress and scheduler registration.
5. Verify login, scoped manager access, staff draft isolation, assignment concurrency, one weekly digest per intended recipient/week and private calendar access.
6. Terminate a test user with an already-active browser session and calendar token. Confirm immediate denial and preserved historical records.
7. Exercise provider failure/retry and stale import behavior. Confirm no duplicate emails and no secrets in logs.
8. Record release tag/commit, operator, configuration revision, migration versions and rollback/roll-forward decision point.

## Operational runbooks to complete before pilot

- Worker stalled / dead-letter queue growing / duplicate delivery suspected.
- Weekly digest missed or sent for wrong week/timezone.
- Mail bounce, invalid contact address or provider outage.
- Calendar token exposed or terminated staff still receiving data.
- Scheduling conflict after concurrent edits or policy change.
- Database restore, migration failure, suspected access violation and lost administrator access.
- External feed parse failure or upstream source change.

Each runbook needs detection, owner, safe diagnosis, recovery steps and validation. Do not label this section operationally complete until rehearsed; see CL-903–904.
