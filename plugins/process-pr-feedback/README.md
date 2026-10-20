# process-pr-feedback

`/process-pr-feedback <pr>… [--scout-only]` works one reviewer's feedback round on paranext-core
PRs from start to finish:

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

- A paranext-core checkout and an authenticated `gh` CLI. Replies are posted as that account.
- The `superpowers` plugin is recommended for the design and TDD step.
- [roborev](https://github.com/kenn-io/roborev) is optional. When it is installed, its
  per-commit reviews are settled as part of the round.
- `tools/app-guard.py` stops the live-test step from killing another Claude session's dev app. It
  needs Linux or WSL. Run its tests with `python3 tools/test-app-guard.py`.

Notes for each round go in `.review/<pr>-<date>/` inside the checkout. Git, prettier and eslint
already ignore that folder.
