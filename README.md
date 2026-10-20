# Claude Code plugins

Rolf Heij's Claude Code plugins, one folder per plugin under `plugins/`. They are distributed
through the Paratext team marketplace
([paranext/claude-plugins](https://github.com/paranext/claude-plugins)), which pins each plugin to a
tag here with a `git-subdir` source.

| Plugin | What it does |
| --- | --- |
| [`process-pr-feedback`](plugins/process-pr-feedback) | Works a reviewer's feedback round on PRs in any paranext GitHub repo end to end, with the user ruling at two hard stops |

## Releasing

Tags are per plugin: `<plugin>-v<version>`, for example `process-pr-feedback-v1.0.0`. To release,
tag the commit, push the tag, and open a PR in the team marketplace that moves the plugin's `ref`.

## Trying a change before release

```bash
claude plugin validate plugins/<plugin>
claude --plugin-dir plugins/<plugin>
```
