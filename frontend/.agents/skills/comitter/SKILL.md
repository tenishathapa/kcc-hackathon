---
name: committer
description: Writes and makes git commits that read like a real developer wrote them under normal time pressure, not like an AI summarized a diff. Use this whenever the user asks to commit, save, or log their current changes, says "git commit", asks for a commit message, or asks to clean up/rewrite an existing commit message. Trigger this even if they just say "commit this" or "save my progress" with no other detail. Do not use plain `git commit` with a generic message without consulting this skill first — the whole point is avoiding the generic, over-explained, AI-sounding commit message that Claude defaults to.
---
 
# Committer
 
Write commit messages the way a decent human engineer would: short when the change is short, only as detailed as the change actually warrants, in their own voice rather than a template. Never over-explain a one-line fix, never let an AI "voice" show through.
 
## Prerequisites
 
- Staged changes must exist. Run `git diff --cached --stat` to confirm. If it's empty, check `git status` for unstaged/untracked changes and ask the user whether to stage them (or stage them yourself if they say to) — don't just fail silently.
- If the user hasn't staged everything they meant to (e.g. `git status` shows unstaged changes plainly related to the same task), point it out before writing the message rather than committing a partial change.
## Step 1: Read the actual diff
 
Run, in this order:
1. `git status`
2. `git diff --cached`
3. If the repo has recent history, `git log --oneline -15` — read this to match the *existing* project's commit voice (do they use conventional commits? scopes? Are messages terse one-liners or do they write bodies? Sentence case or lowercase?). Mirror the house style over any default in this skill if the two conflict.
Do not write the message from the file names or the user's description of what they did — read the real diff. Small unrelated changes (formatting, an unrelated import fix) that ride along shouldn't be invented as a big feature.
 
## Step 2: Decide how much message this change actually deserves
 
This is the step people skip, and it's the main reason AI-written commits feel off. Real engineers scale effort to the change:
 
- **Trivial / mechanical** (typo, bump a version, formatting, rename, tiny config tweak): one line, no body. Example: `Fix typo in readme install command`
- **Small, self-explanatory fix or feature**: one-line subject, maybe one short sentence of body only if the *why* isn't obvious from the subject. Most small commits do not need a body at all — don't manufacture one.
- **Non-obvious change**: fixing a bug whose cause isn't visible from the diff, a workaround for a weird constraint, a deliberate tradeoff, a breaking change. This is the only tier that earns a real body explaining why.
Default assumption: most commits should NOT have a body. Only add one when it carries real information a future reader would otherwise have to dig for (a linked issue, a reason a non-obvious approach was chosen, a warning about a side effect). If you can't say something in the body that isn't just a rephrasing of the diff, leave it out.
 
## Step 3: Format
 
- Subject: `<type>(<scope>): <description>` if the repo/user uses Conventional Commits; otherwise just a plain imperative sentence if that's the house style from `git log`. Don't impose Conventional Commits on a repo that clearly doesn't use it.
- Types: feat, fix, docs, style, refactor, perf, test, chore, build, ci — pick the one that actually fits; don't force "chore" onto everything, don't force "feat" onto small stuff.
- Imperative mood ("Fix", "Add", "Remove" — not "Fixed", "Added", "Adds").
- Subject under ~50 chars where reasonable, no trailing period, capitalize first letter after the type prefix.
- If there's a body: blank line after subject, wrap around 72 chars, plain paragraph or a couple of short bullet points — not a bulleted breakdown of every file changed.
## Step 4: Strip anything that sounds like an AI wrote it
 
Before showing the message to the user, check it against this list and fix anything that matches:
 
- **No restating the diff as a list.** "This commit adds X, updates Y, and removes Z" is a summary, not a commit message — it's the single biggest AI tell. Say what the change *does* for the codebase/user, once, plainly.
- **No filler openers.** Cut "This commit...", "This change...", "This PR...". Start with the verb: "Add", "Fix", "Refactor".
- **No marketing/enthusiasm language.** No "robust", "seamless", "powerful", "comprehensive", no exclamation points, no emoji unless the project's own log history uses them.
- **No hedging or meta-commentary.** No "This should fix the issue", "Attempts to address...", "Hopefully resolves". State it plainly, like the person actually knows what they changed (they wrote the diff, after all).
- **No over-explaining the obvious.** If the diff is `fix off-by-one in pagination loop`, the subject line already says it — don't add a body walking through why off-by-one errors happen in general.
- **Vary sentence rhythm and length across a session.** If you're generating several commits in a row, don't make every single one the same length/shape — humans don't.
- **Don't pad with disclaimers or questions in the message itself** ("let me know if this needs changes") — that belongs in your chat reply to the user, never inside the commit message.
- **Lowercase vs sentence case, period vs no period at end of subject** — match whatever the repo's own history does; don't default to a house style the project doesn't use.
## Step 5: Present for approval, then commit
 
Show the user the exact message (subject + body if any) before running anything. Once approved:
 
```
git commit -m "<subject>" -m "<body>"
```
 
(omit the second `-m` entirely if there's no body — don't pass an empty string).
 
If the user wants to tweak wording, adjust and reconfirm rather than committing immediately.
 
## Quick before/after
 
**Bad (AI-sounding):**
```
feat(auth): Implement comprehensive user authentication improvements
 
This commit adds robust password validation, updates the login
endpoint to handle edge cases, and implements comprehensive error
handling for authentication failures. This change also adds new
tests to ensure the authentication flow works correctly.
```
 
**Good (human, same diff):**
```
fix(auth): Reject weak passwords on signup
 
Validation only checked length before. Users were hitting the
"password too weak" error from the DB constraint instead of a
useful message, so check the same rules client-side first.
```
 
Notice the good version is shorter, states one clear reason, and doesn't list every file touched.