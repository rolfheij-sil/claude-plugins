# process-pr-feedback

`/process-pr-feedback <pr>… [--scout-only]` works one reviewer's feedback round on PRs in any repo
of the `paranext` GitHub org (paranext-core, the extension repos, and the rest) from start to finish:

1. It reads every comment, checks each claim against the code, and asks you what is real and what
   to act on. This is the first hard stop.
2. It implements what you ruled, reviews and verifies its own diff, and drafts the replies and PR
   description updates.
3. It shows you everything it is about to push and post. This is the second hard stop.

Nothing is pushed or posted before you approve at the second stop.

`--scout-only` runs only as far as the first stop and changes nothing, so it is safe to schedule.

## Install

From the Paratext team marketplace:

```
/plugin marketplace add paranext/claude-plugins
/plugin install process-pr-feedback@paratext-team
```

## Requirements

- A checkout of the PRs' repo, with `origin` pointing at it, and an authenticated `gh` CLI. Replies
  are posted as that account.
- The `superpowers` plugin is recommended for the design and TDD step.
- [roborev](https://github.com/kenn-io/roborev) is optional. When it is installed, its
  per-commit reviews are settled as part of the round.
- `tools/app-guard.py` stops the live-test step from killing another Claude session's dev app. It
  needs Linux or WSL. Run its tests with `python3 tools/test-app-guard.py`.

In paranext-core the skill runs paranext-core's own checks, e2e and live app run. In other repos it
uses that repo's own equivalents, read from its CI workflows, scripts and README. Extension repos
still get the live run in the Platform.Bible dev app.

Notes for each round go in `.review/<pr>-<date>/` inside the checkout. paranext-core already ignores
that folder for git, prettier and eslint. In other repos the skill drops a `.gitignore` containing
`*` into `.review/`, so git ignores the notes, and it leaves the folder out of its own format check.
