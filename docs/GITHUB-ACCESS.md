# GitHub source and agent access

Current owner-supplied source: [jrquigley/crewline](https://github.com/jrquigley/crewline), verified PUBLIC and empty before this release import. The earlier private repository is historical. Visibility and account settings were not changed. Public source must never contain credentials, live staff data, backups or private calendar/invite URLs.

For another computer/agent, clone this repository and authenticate using that environment's GitHub integration or `gh auth login`. Never paste a personal access token into chat or a tracked file. A browser login alone does not necessarily authorize shell Git. Give Claude access through its own authenticated workspace, then ask it to read CLAUDE.md, AGENTS.md and docs/HANDOFF.md. Both agents use the same durable roadmap and docs; there is no automatic cross-product memory sync.

Use task branches and PRs. The empty repository received its preserved initial baseline on main; implementation proceeds through a PR with Actions checks. Do not overwrite history. Branch protection and collaborator policy remain CL-011; no account settings were changed without need. No project license was selected.

In the initial Windows sandbox, normal GitHub credentials/config were unavailable; normal-user Git/gh commands worked with existing authenticated account jrquigley. No global safe.directory or author setting was changed. Commits use that account's standard GitHub no-reply identity per command. Future agents should inspect their own actual environment, not copy a local authentication workaround blindly.
