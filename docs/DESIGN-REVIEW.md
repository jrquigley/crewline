# Design implementation and review

Owner brief: intuitive for managers who are not computer savvy; extremely simple phone staff experience, with advanced options still available. Kind: authenticated software application. The established Crewline name and working UI reference were retained, not treated as a newly cleared commercial trademark.

## Taste application

Applied the local design-taste-frontend skill (tasteskill 2.5.0): green-black-bone palette, variable Outfit type, soft radius, consistent green action/secondary button system, quiet motion and large labeled controls. Printed palette tokens are retained in app.css. Outfit is locally hosted with its OFL license/source note. Taste motion.css and motion.js are copied unchanged; reduced-motion support is included. No external font CDN or decorative stock photography is needed for this operational UI.

The desktop workspace uses a stable sidebar, a single Create event action, readable Event rows with setup/Event/close status and a staff-hours column. Instructions follow the real workflow: create, choose people, publish. Advanced shift times, additional coverage, split shifts and destructive actions are separated with explicit labels/details/confirmation rather than crowding everyday controls.

The phone staff home prioritizes one large next-shift card, Request time off, Pick up a shift, a short upcoming list and Home/Schedule/Me navigation. Calendar, contact and availability settings are secondary. Forms use native inputs, visible labels, error messages and large targets. Information is never encoded by color alone.

Full-screen marketing sections, product hero renders, shader effects and sales-copy checks do not fit an authenticated scheduling application. Applying them literally would lengthen forms and obscure staff actions. These are documented applicability exceptions, not claims that the marketing checker passed. Hallmark was inspected but not applied as an unnamed redesign/audit of an already established design; the applicable review used Taste plus real product/browser/a11y checks. No second-agent review is claimed.

## Actual checks

Taste consistency.mjs was attempted first using Edge (Chrome exited early) and then downloaded Chromium (CDP socket closed, all probes incomplete). Layout check.mjs and perf.mjs likewise did not produce a completed report in this environment and were stopped after no progress. These tool runs are **incomplete**; zero findings with skipped probes is not a pass. The skill's scripts were not modified to suppress failures. No Taste performance score is claimed.

Playwright provided the working browser fallback: 72 responsive route/width checks, complete authenticated workflows, no horizontal overflow/errors/missing assets, and final screenshots at 1440/1024/820/768/390/320. Axe found no automated WCAG-tag violations on 16 key screens; manual/incomplete rules remain. Final desktop, phone login and staff home screenshots were inspected for hierarchy, spacing, legibility and target clarity. One staff header alignment issue was corrected. No actual nontechnical manager usability study or real phone Safari test has been performed.

Selected synthetic-data screenshots and machine reports are in [evidence](evidence/browser-results.json): [manager](evidence/manager-desktop.png), [staff](evidence/staff-phone.png), [login](evidence/login-phone.png), [accessibility](evidence/accessibility.json), [dependency audit](evidence/dependency-audit.json). The timestamped browser-test Event title is synthetic; it is not production data. Never capture live private calendar/invitation links in committed evidence.

Next review: actual manager/staff pilot, keyboard/screen reader and 200–400% zoom, low-end phone/slow network, actual phone safe areas, representative longer names/lists, and completed Taste performance checks on a compatible runner if needed.
