# Contributing and shared ownership

Read [AGENTS.md](AGENTS.md) first. Codex and Claude use one roadmap, one work log, one current handoff, and one decision register.

## Task lifecycle

`planned → ready → in-progress → review → done`

Use `blocked` only with a recorded dependency and a next action. Use `deferred` for intentionally postponed work. A task is done only when its acceptance criteria pass, required documentation is updated, and limitations are explicit.

Before a task, record its owner and branch in the roadmap. During concurrent development, work in different worktrees and nonoverlapping task areas. Communicate interface changes through the API/schema documents before another task depends on them.

At handoff, commit code, tests and docs together. Record the branch and available commit reference. Do not try to put a commit's own final SHA inside that commit; use the preceding checkpoint or resolve `git rev-parse HEAD` at handoff time.

## Definition of done

- Applicable requirement and roadmap IDs are named.
- Intended behavior and error paths are implemented at the required layer.
- Appropriate checks pass, with unrun checks explicitly identified.
- Documentation and the current handoff match the source.
- No secrets, private staff data or production dumps were added.
- Generated files are current.
- Database migration, deployment and rollback consequences are documented where applicable.

## Suggested division of work

After CL-101 defines the production structure and contracts, one agent can work on scheduling/domain services while the other builds staff UI components against agreed contracts. Either agent can take either role. Schema migrations, publishing, offboarding and authorization need focused review because they cross feature boundaries.

Suggested first handoff prompt:

> Read AGENTS.md and docs/START-HERE.md, then inspect docs/HANDOFF.md, the roadmap, work log and current Git state. Summarize the actual state, claim the next ready task, and continue it. Update the shared documentation with code and validation results before handing off.

## License

No project license has been selected. Do not add an open-source license or third-party code without checking ownership and the owner's intended distribution.
