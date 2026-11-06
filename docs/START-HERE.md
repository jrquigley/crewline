# Start here

Crewline 1.0.0 is a Django server application, stored in the owner-supplied **public** [jrquigley/crewline](https://github.com/jrquigley/crewline) repository. Intended HTTPS host: `shifts.quigspace.com`. The earlier private repository and interface preview are historical. Do not change repository visibility or add private information to source.

Read AGENTS.md, HANDOFF.md, the latest WORKLOG.md entry, ROADMAP.md and DECISIONS.md before changing code. Inspect Git rather than assuming a recorded checkpoint is still current. The owner requested complete shared documentation so either Claude or Codex can resume without this chat.

## Source map

| Path | Responsibility |
| --- | --- |
| `app/config/` | Django settings, URLs, WSGI |
| `app/scheduling/models.py`, `migrations/` | Persistent schema and upgrade history |
| `app/scheduling/services.py` | Scheduling, scope, publication, offboarding and token rules |
| `app/scheduling/forms.py`, `views.py` | Validated server workflows and authorization |
| `app/scheduling/delivery.py`, `calendar.py` | SMTP outbox/digests and private calendar feed |
| `app/scheduling/tests.py` | Security, workflows, interval rules and real concurrent transactions |
| `app/templates/`, `app/static/` | Production manager/staff UI, local font and Taste motion assets |
| `Dockerfile`, `compose.yaml`, `docker-entrypoint.sh` | Non-root single-container runtime and persistent `/data` |
| `.env.example`, `requirements.txt` | Configuration names and pinned runtime dependencies |
| `scripts/app-browser.cjs` | Authenticated end-to-end, responsive and optional axe audit |
| `.github/workflows/application.yml` | Django checks, Docker/browser/persistence validation |
| `prototype/`, `public/`, `server/` | Archived executable design preview; never production auth |
| `docs/` | Requirements, decisions, roadmap, tests, operation and handoff |

Run the [test commands](TESTING.md). Use [deployment instructions](DEPLOYMENT.md) for Docker. Read [architecture](ARCHITECTURE.md) before altering a transaction or permission boundary. Planned work is tracked in the [roadmap](ROADMAP.md); do not mark client/provider/production checks done from a simulation.
