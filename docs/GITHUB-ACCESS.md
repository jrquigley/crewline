# GitHub setup and access for Codex and Claude

## Current facts

The owner supplied [jrquigley/gig](https://github.com/jrquigley/gig) on November 5, 2026. Verified: private repository, initially empty, authenticated GitHub account `jrquigley`, admin permission. Authentication works in the normal Windows account context; the sandbox could not read CLI config or use Windows HTTPS credentials even after a scoped permission grant. No need to create another repository or log in again. The starter was pushed to `main` at `5d97d5ad4acb3bd9c8388a839a6bb2bfe35b1e03`; [initial GitHub CI passed](https://github.com/jrquigley/gig/actions/runs/42096161232). No additional sign-in or new repository is needed on this workstation when the authorized account context is available.

Agents do not have a separate GitHub identity that you need to add as a collaborator for local development. They operate in the local checkout using the tools and Git authentication available to the session. A different computer or cloud-hosted agent needs its own authorized connection to the same repository.

## Existing repository: resume work

```powershell
git clone https://github.com/jrquigley/gig.git
cd gig
```

Open that checkout in Codex or Claude Code, read AGENTS.md / CLAUDE.md and docs/HANDOFF.md, then inspect Git state and claim a task. On the original workstation, the active checkout is `C:\Users\jrqui\Documents\Codex\2026-11-04\i-n\outputs\gig`. Other machines need their own authenticated GitHub session with access to this private repository. Keep the remote private unless the owner asks otherwise.

The following setup instructions are retained for reference; repository creation and reauthentication are not currently required. Do not run commands that create a second repository or replace an existing origin.

## Original setup workflow (reference only)

1. In a normal PowerShell terminal on your computer, run:

   ```powershell
   gh auth login --hostname github.com --git-protocol https --web
   gh auth setup-git
   gh auth status
   ```

   Complete the sign-in in your browser. Do not paste a password, token, private key or recovery code into chat. If already authenticated, inspect `gh auth status` first and avoid unnecessary sign-in changes.

2. On GitHub, create a new repository. `crewline` is a suggested name, not a created repository. Private visibility is a sensible starting point while building staff-related software; the owner decides visibility. Keep the new remote empty if using this starter, so there is no conflicting README/license commit. Do not choose a license without considering the intended ownership/distribution.

3. Open the actual project folder in Codex as a local project:

   ```text
   C:\Users\jrqui\Documents\Codex\2026-11-04\i-n\outputs\crewline
   ```

   Point Claude Code at that same project for sequential work, or at a separate Git worktree for simultaneous work. If you use a ZIP on another computer, extract it first and open the extracted `crewline` folder. Do not use two agents to edit the same checkout simultaneously.

4. Share the repository URL in chat and identify this local folder. An agent can then inspect the configured remote and test permitted read/write operations. If its sandbox cannot access local credentials or the network, it must request the specific needed permission; logging into GitHub does not automatically override sandbox restrictions.

5. After reviewing local files, initialize/commit/push. These commands are instructions for the owner or an explicitly authorized agent, not actions already performed by this handoff. Replace `YOUR-USERNAME` and the repository name with the real values:

   ```powershell
   # Run inside the project folder. Skip init if .git already exists.
   git init -b main
   git status --short
   git add .
   git commit -m "Add Event scheduling preview and shared implementation roadmap"
   git remote add origin https://github.com/YOUR-USERNAME/crewline.git
   git push -u origin main
   ```

   If Git asks for author identity, configure your real name/email or GitHub no-reply address before committing. If `origin` already exists, inspect `git remote -v` before changing it. Do not replace an existing remote or rewrite history blindly.

Alternatively, after authentication and a reviewed initial local commit, the owner can create a new private remote directly with GitHub CLI:

```powershell
gh repo create crewline --private --source . --remote origin --push
```

Use either remote-creation route once, not both. Organization repositories require appropriate organization permissions and may require SSO authorization.

## Working from two agents or computers

- GitHub holds shared commits; uncommitted files on one computer are not available to the other agent.
- Each implementation task gets a roadmap ID, owner and branch. Use a PR for integration and record actual review evidence.
- Use distinct worktrees if working simultaneously. Share contracts before changing them; coordinate migrations to avoid conflicts.
- Each handoff updates WORKLOG, HANDOFF, ROADMAP and relevant decisions/contracts. The next agent reads those files and inspects Git state before editing.
- If Claude is used through a hosted website rather than local Claude Code, use that product's authorized GitHub repository connection. A plain chat conversation does not inherently have access to your local files or GitHub credentials.
- If using Codex cloud later, authorize the repository in its environment separately. Local `gh` authentication does not automatically authorize a cloud environment.

## Source hosting versus application hosting

GitHub can store code, issues, PRs and CI. GitHub Pages hosts static HTML/CSS/JavaScript; it does not run the planned database, server API, email worker or scheduler. Choose production application hosting during CL-101/901. Publishing the static preview does not create a secure staff scheduling service.

## Sources checked for these instructions

- [GitHub CLI browser authentication](https://cli.github.com/manual/gh_auth_login)
- [Configure Git to use GitHub CLI credentials](https://cli.github.com/manual/gh_auth_setup-git)
- [Create a repository from a local source folder](https://cli.github.com/manual/gh_repo_create)
- [Official OpenAI documentation: local environments and built-in Git controls](https://learn.chatgpt.com/docs/environments/local-environment)
- [GitHub Pages is static hosting](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)

Access must be verified in the actual session; these instructions are not proof of account permissions.
