# Docker deployment and operations

Target supplied by owner: `https://shifts.quigspace.com`, source [jrquigley/crewline](https://github.com/jrquigley/crewline). This runbook prepares a new container; no access to the owner's server or proxy has been provided. GitHub Pages cannot run this app.

## First start

Use a Linux Docker host with Compose v2 and a local persistent disk. Clone or update the repository on the server:

```sh
git clone https://github.com/jrquigley/crewline.git
cd crewline
cp .env.example .env
```

Edit `.env` privately. Set ADMIN_EMAIL to your real login email and ADMIN_PASSWORD to a unique 15+ character password; the placeholder is rejected. Leave APP_BASE_URL=https://shifts.quigspace.com and TRUST_PROXY=true behind the trusted HTTPS proxy. Leave SEED_SAMPLE_DATA=true for the requested five sample employees. They receive no working password until invited. Set it false before the first start if an empty workspace is preferred. Seeding only occurs when no Employee records exist; restart never adds duplicates.

Keep `.env` private (for example `chmod 600 .env` on Linux); never commit it. Compose interpolates `$` in environment files: use single-quoted values for passwords containing `$` or other interpolation syntax. Do not paste production secrets into GitHub issues or chat.

```sh
docker compose up -d --build
docker compose ps
docker compose logs --tail 50 crewline
curl --fail http://127.0.0.1:3000/healthz/
```

Startup migrates the schema, creates the first owner if needed, seeds samples once, collects static files and starts Waitress plus the email/digest worker. Initial owner credentials are required only if no active superuser exists. Changing ADMIN_PASSWORD later does not reset an existing account. After successful setup, remove the bootstrap password from `.env` and recreate the container to remove it from container environment metadata. Use the website's Change password screen for normal changes. Emergency operator recovery: `docker compose exec crewline python manage.py changepassword your-email@example.org` (interactive, never command-line password).

## HTTPS reverse proxy

Configure DNS and a valid certificate for shifts.quigspace.com. The default Compose port binds **127.0.0.1:3000**; it is for a reverse proxy on the same host. The app trusts X-Forwarded-Proto only when TRUST_PROXY=true, so the proxy must overwrite that header and untrusted clients must not reach the app port.

Nginx example inside an existing TLS-enabled server block:

```nginx
server_name shifts.quigspace.com;
# Your existing listen 443 ssl and certificate directives go here.
location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

If the proxy is another Docker container, its 127.0.0.1 is a different container. Connect both to a shared private Docker network and proxy to `crewline:3000` using a Compose override appropriate to your proxy. Do not expose port 3000 publicly to make that work. Keep TRUST_PROXY=false unless trusted proxy headers are controlled. The app currently throttles the immediate network peer; proxy-wide abuse protection at the edge complements account throttling.

Use HTTPS for login. Without the correct forwarded protocol, secure redirects can loop. Wrong APP_BASE_URL can cause CSRF rejection or bad emailed/calendar URLs. Requests for the configured host, localhost and 127.0.0.1 are allowed; `/healthz/` intentionally permits the local HTTP Docker health probe. HSTS is enabled for this host; includeSubDomains/preload are intentionally omitted to avoid changing policy for other owner subdomains.

Private routes include bearer URLs: `/access/`, `/verify-email/`, `/calendar/`. Redact/disable those paths in proxy request/error logs and analytics. Application log messages redact them, but a proxy has separate logging policy. Do not publish screenshots containing live invitation/calendar links. Application logs avoid email bodies and provider credentials.

## Update / reload

Back up the current data and retain the current image before upgrading. On the checkout's main branch with no local changes:

```sh
git pull --ff-only
docker compose up -d --build
docker compose ps
docker compose logs --tail 50 crewline
```

The existing named `crewline_data` volume is reused. **Do not run `docker compose down -v` or delete the volume.** Keep the same Compose project name/directory (or explicitly set the original project name with `-p`) so a new project does not create an empty volume. If you have an existing custom Docker configuration, preserve its data mapping and adapt these image/environment settings rather than launching a second production instance.

## Data, backup and recovery

Container user/group is 10001. `/data` contains `crewline.sqlite3`, its transaction files and generated `secret.key`. A new named volume inherits the image directory's ownership. An existing bind mount must be owned/writable by UID/GID 10001. Use a local disk, not NFS/SMB. Run one app container; SQLite write serialization is not a horizontal-scaling architecture.

For a simple consistent backup, briefly stop the app and archive the volume. Run from the existing Compose project directory; this archive contains personal data and secrets:

```sh
mkdir -p backups
docker compose stop crewline
docker compose run --rm --no-deps --entrypoint python -v "$PWD/backups:/backup" crewline -c "import tarfile; t=tarfile.open('/backup/crewline-backup.tar.gz','w:gz'); t.add('/data',arcname='data'); t.close()"
docker compose start crewline
```

Use a dated, access-controlled name instead of overwriting your last good archive; encrypt off-host copies. Save the matching release Git SHA and `.env` separately in your secret store. A backup policy is not complete until a restore is rehearsed.

Restore rehearsal: stop scheduling writes, restore the archive's `data` contents into a **new isolated test volume** using a trusted helper/container, ensure ownership 10001, and attach it to an isolated app with SMTP disabled. Keep the matching secret and DB together. Verify login, employee count/history, current publications and calendar revocation. Never test against production or send real emails from a restored test copy. Once verified, document timing and owner-approved recovery steps. Automated encrypted backup/restore and RPO/RTO are still roadmap work.

Migration rollback: retain the previous image/commit and a matching pre-upgrade data backup. Newer schemas may not work with older code. Prefer a corrective forward release; if rollback is required, stop writes and restore the entire matching data snapshot with the older image, accounting for records created after the backup. No destructive schema rollback has been validated for this release.

## SMTP and weekly email

Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD and a verified SMTP_FROM sender. For STARTTLS use SMTP_TLS=true/SMTP_SSL=false (normally port 587); for implicit TLS use false/true (normally 465). Never enable both. Secrets stay in `.env`/your deployment secret store. The background service checks every 30 seconds; a separate worker container is unnecessary for this deployment.

Without SMTP_HOST the site remains usable and pending jobs remain queued. Review queued stale invitations/changes before enabling transport after a long disabled period. `.example` and `@example.com` recipients are always blocked. Only an authorized administrator can inspect delivery status/retry through Activity. `review` means a provider error or ambiguous crash outcome: check the provider before retrying to avoid duplicate mail. No live provider credentials or real sends were used in development.

Default digest: Sunday 17:00 America/Los_Angeles, upcoming Monday–Sunday; configurable in Settings. An empty week sends a no-shifts message. The worker must run on the configured day; complete-day outage catch-up is not implemented. Set weekly policy/timezone before a real pilot. Clearing browser state does not stop server jobs; disabling digest settings does.

## Pilot acceptance and monitoring

1. Confirm HTTPS/cookie/proxy settings, health and container restart/persistence.
2. Sign in as owner, review sample data/rules, create scoped manager and staff accounts with private invites.
3. Create/edit/publish an Event; verify staff sees only published changes and correct local hours.
4. Configure a verified sender and authorize a small real delivery test; verify shift update, invitation/recovery and weekly email.
5. Test subscription/moved/canceled shift in Google Calendar, iPhone/Apple Calendar and Android; refresh timing belongs to each client. Confirm add-to-home-screen separately.
6. Terminate a test staff account: active browser access and calendar link fail, future coverage reopens, history remains.
7. Rehearse isolated restore; agree retention, backup ownership and recovery objectives. Record actual manager/staff feedback.

Monitor `/healthz/`, Docker health/restarts, disk space, backups and Activity delivery states. Full metrics/alerts, live-provider bounce handling and independent security review remain planned. Do not treat passing CI as proof that the owner's proxy, SMTP or calendar clients are configured.

## Isolated local development

Use a virtual environment, install requirements, run collectstatic/migrate/bootstrap. Set a scratch DATA_DIR, APP_BASE_URL=http://127.0.0.1:3000, ALLOW_INSECURE_HTTP=true and synthetic ADMIN_EMAIL/ADMIN_PASSWORD. Run `python app/manage.py runservice --host 127.0.0.1 --port 3000 --no-worker`. The HTTP switch is only for isolated loopback testing; leave it unset in production. No Django debug mode or default credential is provided.
