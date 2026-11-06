# Working release implementation plan

Kind: software — authenticated staff scheduling application, not a marketing landing page.

Owner direction, November 5, 2026: build the functioning website with secure login, five fictional employees, intuitive manager and phone staff workflows, test thoroughly, apply Taste design review, upload to `jrquigley/crewline`, and provide Docker reload readiness for `https://shifts.quigspace.com`.

Active owner: Codex. Branch: `codex/CL-101-authenticated-app`. The owner supplied a new empty public repository; preserve its visibility and keep credentials/data out of source. The previous `jrquigley/gig` repository remains unchanged.

## Implementation choices

- Django 5.2 LTS (current security patch), server-rendered HTML and progressive enhancement. Built-in authentication, CSRF, forms, ORM and sessions reduce custom security code.
- A single-container small-team deployment with SQLite in a persistent `/data` volume, short serialized write transactions and a production Waitress WSGI server. PostgreSQL remains the scaling path, not a false claim of current support.
- Explicit draft and published Event revisions, server-side scheduling validation and retained audit/revision history.
- Database outbox plus background delivery/digest service; SMTP is configurable and no fictional recipient is contacted without real mail configuration. Calendar feeds use revocable hashed tokens.
- Non-root Docker image, persistent generated secret, environment/bootstrap admin password, secure cookies/HTTPS by default and explicit local-development exceptions.

## Build sequence and acceptance

1. Foundation/auth/data: migrations, first-admin bootstrap, five synthetic employee records, secure session login, password change/invitation, throttling and access checks.
2. Manager workflows: upcoming Event board, create/edit Event, coverage slots, candidate selection, hours, publish confirmation, requests, staff administration and settings.
3. Staff workflows: next shift, own/team published schedule, time off, availability, personal details, open shifts and calendar/phone guidance.
4. Lifecycle/integrations: offboard with record retention and immediate denial, audit revisions, SMTP outbox/retry, weekly digests, private `.ics` feed.
5. Design: Taste-derived green/bone system and Outfit type, clear hierarchy, obvious labeled actions, 44px+ targets, advanced controls under details. No distracting marketing shaders in operational screens. Test authenticated screens as product UI; record marketing-check false positives rather than forcing screen-sized marketing sections into forms.
6. Verification: Django unit/integration/security and concurrency cases; real headless browser flows at desktop/tablet/phone; Taste consistency/layout/performance checks and screenshot review; Docker build/run/persistence checks through GitHub CI if no local Docker engine exists; dependency audit and deployment checks.
7. Delivery: update roadmap/decisions/work log/handoff and Docker runbook, push the release through a PR, verify CI and merge to main. Report exact reload commands, configuration prerequisites and any limits.

No production server credentials were provided. Do not claim to have reloaded the owner's container or verified public HTTPS until actually observed. Docker reload must retain the `/data` volume.


## Implementation checkpoint

Steps 1–5 are implemented with stated roadmap limits. Step 6 passed locally (56 Django tests, complete browser/axe and dependency audit) and on a6a4ed6 in GitHub Docker/UID/browser/persistence checks. Subsequent targeted-publication hardening is under the same full CI gate. Step 7 is in progress through release PR 1; see WORKLOG for final run evidence. Owner production reload and live provider/device acceptance remain separate.
