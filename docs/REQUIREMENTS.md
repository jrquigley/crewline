# Product requirements and traceability

Confirmed requirements come from the owner's requests in this project. Implementation notes and acceptance criteria below translate those requests into verifiable work; unresolved policy choices are listed in [Decisions](DECISIONS.md).

Status legend: **preview** = interactive sample-data behavior only; **planned** = requires production work; **confirmed direction** = owner instruction. No preview entry means production complete.

| ID | Requirement | Current state | Production acceptance / tasks |
| --- | --- | --- | --- |
| R-01 | Web-server application, source stored on GitHub | Confirmed direction; local preview server exists | Shared server application deployed with database and worker; CL-101–104, CL-901–906 |
| R-02 | Multiple departments | Preview | Department membership and scoped access enforced server-side; CL-201–203 |
| R-03 | Multiple locations | Preview | Locations carry time zones and visibility scopes; CL-201–202, CL-404 |
| R-04 | Staff list and personal records | Preview | Validated staff directory, lifecycle and ownership; CL-203, CL-301 |
| R-05 | Staff skills | Preview | Required skills validated at assignment and publication; CL-204, CL-402 |
| R-06 | Open shifts | Preview | Staff request eligible shifts; manager approves; atomic assignment prevents double claims; CL-405 |
| R-07 | Availability limitations | Preview | One-time and recurring restrictions, explicit exceptions and conflict handling; CL-303, CL-402 |
| R-08 | Email staff when a shift changes | Template/flow preview | Only affected active recipients; reliable delivery, retries, cancellation handling; CL-601–604 |
| R-09 | Weekly upcoming-schedule email | Configuration/template preview | Week boundary and send time defined; timezone-aware, idempotent scheduled delivery; CL-603 |
| R-10 | Terminate access while retaining records | Simulated UI and retained sample historical rows | Offboarding transaction revokes account/session/invite/calendar access, reopens future shifts, suppresses queued delivery, preserves history; CL-502 |
| R-11 | Google, Android, iPhone, other calendars and add-to-phone | Setup screens preview | Private revocable published-shift feed, calendar onboarding and phone home-screen guidance verified on actual clients; CL-701–704 |
| R-12 | Manager/admin interface for desktop | Preview | Scoped Event/shift management, hours, requests and settings work with server data; CL-401–407 |
| R-13 | Extremely simple phone-browser staff interface | Preview | Next shift, near-term list and time-off action accessible with large targets and plain language; CL-301–304, CL-902 |
| R-14 | Staff can submit contact information | Preview, pending email verification simulated | Owner-scoped update, validation and verified sign-in/contact address changes; CL-301 |
| R-15 | Staff time-off requests | Preview | Private reason, approval workflow, atomic conflict/coverage handling and notification; CL-302 |
| R-16 | Staff full schedule with coworkers | Preview, scoped by assigned locations | Published names/assignments only, policy-scoped; no coworker contact details or private absence reasons; CL-304, CL-503 |
| R-17 | External Event context and modular expansion | Sample external Event toggle | Disabled-by-default module, read-only context, safe import and explicit conversion into staffed Event; CL-801–803 |
| R-18 | Managers see scheduled hours per employee | Preview | Totals across scope and all relevant assignments; overnight/DST/break policy correct; CL-404, CL-407 |
| R-19 | Irregular Event scheduling | Preview limited to sample week | Arbitrary dates and overnight Events; no recurring schedule assumed; CL-401, CL-404 |
| R-20 | Coverage overlap, pre-Event and post-Event rules | Preview | Interval-based headcount and skill coverage, explicit handovers, travel, overlap and hours policy; CL-402–403 |
| R-21 | Use Event terminology throughout | Completed in delivered prototype and starter | Keep terminology check passing; CL-002 |
| R-22 | Document everything done and planned, full roadmap | Initial documentation completed | Every meaningful change updates work log, handoff, tasks and applicable contracts; CL-004; AGENTS.md |
| R-23 | Interchangeable Codex/Claude handoff | Shared files and instructions prepared | Either agent can resume from a clean checkout and documented state, with separate branches for simultaneous work; CL-004, CL-011 |

## Shared acceptance scenarios

1. An Event includes Guest services and Production. A Production slot requires AV skills. A staff member missing those skills cannot be assigned by changing a browser request.
2. A manager working in one location cannot read or mutate private staff records outside the permitted scope. Direct API and export requests obey the same authorization.
3. A staff member requests time off that intersects an assignment. The manager sees the impact before approval; approval and future coverage updates are consistent and auditable.
4. Staff never see unpublished shift edits. Publishing moves a consistent revision into staff schedules and records notifications to affected recipients.
5. Two managers try to assign an overlapping shift at the same time. Only a valid transaction commits; the other gets an actionable conflict.
6. Termination immediately prevents an existing browser session and private calendar token from reading new data; previous worked-shift records remain accessible to authorized administrators.
7. Canceling or moving a published shift updates the staff screen, notification payload, audit entry and calendar revision coherently. No duplicate email after a job retry.
8. Overnight and daylight-saving transitions produce correct instants, durations, weekly totals and emails. Display includes the correct location timezone where needed.
9. A staff member can use the three primary screens at 320px without horizontal scrolling or hidden essential actions; real Safari and Android Chrome checks also pass.

## Boundaries and policy questions

The first production release should support a single organization with multiple departments and locations; whether this becomes a multi-tenant commercial product remains open. Skills, weekly-hour limits, handover duration and travel buffers need organization policy. The prototype's numbers are examples, not approved legal or operational policy. Payroll, attendance, auto-scheduling optimization and native mobile apps are future options, not current MVP commitments.
