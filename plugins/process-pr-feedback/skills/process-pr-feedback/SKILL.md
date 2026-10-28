---
name: process-pr-feedback
description: "Use when a reviewer has left feedback on a PR in a paranext GitHub repo (paranext-core, the extension repos, any repo in the paranext org) — review comments, a review round, reviewer findings, or a feedback document tied to a PR — and the round needs working end to end with the user ruling at two hard stops. Also use, as `--verify-only <branch>`, to verify a branch before opening its PR: the same verification pass (battery, whole test suites, e2e, a live run with evidence per scenario) on a branch that has no PR yet, ending in a table of checks."
---

# Process PR feedback

```
/process-pr-feedback <pr>… [--scout-only]
/process-pr-feedback --verify-only <branch> [--base <base>] [--scenarios <path>]
```

Pass every PR the round covers — one reviewer's round routinely spans a stack, and splitting it
into one run per PR makes the user rule on half an argument twice. Run it from a checkout of the
repo the PRs belong to; one run covers PRs in one repo. The second form takes a branch instead of
PRs: it verifies a branch that has no PR yet, before the PR is opened — see **`--verify-only`**
at the end of this file.

**Eleven steps. Two hard stops: 4 and 9** — unconditional; every other stop in this file is a
condition that may not arise. Nothing is pushed or posted before 10. Approval is per-gate and
explicit — a general "keep going" crosses neither stop. `--verify-only` runs a reduced step 0 and
then step 7 (with the roborev settling of step 6 that step 7 leans on), nothing else; it reaches
neither gate, and pushes and posts nothing.

## Requirements

- A checkout of a repo in the `paranext` GitHub org, with `origin` pointing at it, and the `gh`
  CLI signed in to an account that can push to the PR branches and comment on the PRs. The flow
  posts under that account's name.
- **superpowers** plugin (`superpowers@claude-plugins-official`) for step 5's design → plan → TDD
  flow. Without it, do the same by hand: present a design and stop for approval, write a plan,
  then red-first tests.
- **roborev** — optional. Where `command -v roborev` finds it and `roborev status` succeeds, the
  roborev parts of steps 1, 6, 7, 9 and `--scout-only` run as written. Otherwise skip every
  roborev part and `roborev.md`, and say at gate 9 — or in `--verify-only`'s table — once, that
  roborev was not available.
- **The bundled `app-guard`** (step 7) reads `/proc`, so it runs on Linux and WSL only. Elsewhere,
  check the app's ports yourself (`lsof -i :8876 -i :1212 -i :9223 -i :9222`) and ask the user
  before anything that runs `npm stop`.
- **The Atlassian MCP server** — optional, and only for `--verify-only` without `--scenarios`,
  which reads the branch's Jira ticket through it. Without it, the mode asks the user for the
  ticket's acceptance text instead.

## The repo

Step 0 reads the repo from the checkout's `origin` remote, never from `gh`'s own choice of
default, which can land on another remote — paranext-core checkouts often carry an
extension-template remote as well:

```bash
git remote get-url origin | sed -E 's#^.*github\.com[:/]##; s#/$##; s#\.git$##'
```

The answer must be `paranext/<name>`, with no `.git` or slash after the name. Anything else — a
fork as `origin`, another host — is a stop: put it to the user. Every `origin` in this file (the
fetch, `origin/<branch>`, the push) means that remote, so it has to be the repo the PRs are in.
Record the answer at the top of `findings.md` as `REPO` and use it wherever this file writes
`<REPO>`. Add `--repo <REPO>` to every `gh pr …` command, including any shown below without it, for
the same reason. Read it back from `findings.md` in a later session rather than trusting a shell
variable, which does not survive between commands.

**"In paranext-core" means `REPO` is `paranext/paranext-core`**; every other `REPO` is "another
repo". Parts of steps 5, 7 and 10 name paranext-core's commands, files and standards. **In
paranext-core, follow them exactly as written.** In another repo, keep the rule and use that repo's
own equivalent, as each of those places says.

## Working notes

Keep the round's notes in a directory named `<pr>[-<pr>…]-<YYYY-MM-DD>`, dated by the day the round
started (a second round the same day gets `-2`), under a parent that keeps them out of the diff
under review and out of step 7's format check. This file calls that directory `<notes>`. (In
`--verify-only` mode there is no PR number, so it is `<branch>-<YYYY-MM-DD>`, with the same `-2`
rule and any `/` in the branch name written as `-`, found later with `ls -d .review/<branch>-20*`.)

- **In paranext-core:** under `.review/`, which git, prettier and eslint already ignore. A later
  session finds the round with `ls -d .review/<pr>*`.
- **In another repo:** under `.review/` as well, which most of those repos do not ignore. Before
  the first note, create `.review/.gitignore` containing the single line `*`: git then ignores the
  folder and everything in it, with no change to any tracked file. Prettier does not read that
  nested `.gitignore`, so step 7's format check excludes the folder itself. A later session finds
  the round with `ls -d .review/<pr>*`. Keep notes out of `.git/` and `.claude/`: Claude Code
  treats both as protected, so every write there waits for approval, which stalls an unattended
  run.

Six files, plus a pair per PR whose description the round changes, written as you go:

- `findings.md` — steps 0–3, opening with `REPO` and step 0's branch table. Steps 5 and 10 update the
  table's `pin` column and nothing else in it; anything else they learn goes below the table.
- `rulings.md` — the step 4 presentation as sent, followed by the user's answer **verbatim**, and
  the same for any question steps 5–7 put to the user. Appended, never overwritten: a ruling
  refers to the numbering of the presentation it answered, and a later session has neither
  without this file.
- `verification.md` — steps 6–8: refuted review findings with the reason, each battery result,
  the live reproduction, and the adversarial review of the drafts; then step 10's re-check,
  `reviewDecision` comparison, read-back and CI outcome. Conflict hunks saved by step 5 sit beside it as `conflict-<branch>-<nn>.diff`.
- `replies.md` — step 8, the index: one line per draft with its target, and after step 10 the id
  of the comment it became. Each body is its own `reply-<nn>.md`, posted byte-for-byte.
- `approval.md` — the step 9 presentation and the answer verbatim, and the same for anything
  step 10 has to ask or re-present; appended per pass, and step 10 reads the last entry.
- `roborev.md` — only with roborev (see **Requirements**); step 6's ledger: per roborev finding on this round's commits (and any leftover
  step 1 found), the job id, the claim in plain words, the verdict, and what was done — the commit,
  the reason for no change, or the ruling it went to. Step 9 presents from it.
- `pr-body-<pr>-live.md` and `pr-body-<pr>-new.md` — step 8, per PR of ours whose description the
  round makes inaccurate: the description as fetched, and the updated draft that step 10 sends
  byte-for-byte.

The gates can take days, and the session that takes a ruling is rarely the one that implements
it — step 10 pushes and posts under the user's name on the strength of `approval.md`, so its
absence has to mean "ask again". Superpowers' specs and plans, and screenshots, go in the same
directory. `--verify-only` writes `findings.md` (its reduced step 0 and the scenario list with each
scenario's source), `verification.md`, `roborev.md` where roborev is available, and `rulings.md`
only if it had to ask the user something — for the requirement, or a struck or added scenario —
with the answer verbatim, as the normal flow does.

---

## 0. Is the branch in good shape?

**This step measures.** It runs one `git fetch`, which updates remote-tracking refs and nothing
else — no branch moves, no rebase, no push, no checkout. What it finds is a stop, a decision item
for step 4, or a warning carried to step 4.

```bash
git remote get-url origin          # REPO, per "The repo"
git fetch origin
git rev-parse --abbrev-ref HEAD     # which branch this checkout is on
git status --porcelain              # tracked modifications
```

**In `--verify-only` mode this step stops here, reduced to one row.** The REPO rule, the fetch and
the two checkout stops below apply unchanged — `<branch>` is the only branch in the table, so HEAD
must be on it, and the tree must be clean. There is no PR to walk, so the row is: `<branch>` · its
base · `headRefOid` from `git rev-parse <branch>` · remote-only and local-only, in that order, from
`git rev-list --left-right --count origin/<branch>...<branch>` where `origin/<branch>` exists,
else "not pushed". Local-only commits need no ruling here: the local tip is what is verified, and
the table says it is ahead of `origin`. The base is `--base <base>` when given — a branch stacked on an unmerged one
— and `main` otherwise, and it must exist on `origin`, since every range below is built on
`origin/<base>`: a base that was never pushed is a stop, put to the user. It is what step 7's `origin/<baseRefName>` and "shown red on the base"
mean, and the round's diff, wherever step 7 says "the round's diff" or "the area the round
changed", is `origin/<base>...<branch>`. Remote-only commits are not a stop here, since nothing
will be pushed, but they are a line in the table the mode ends with: the tip verified is the local
one. Run `gh pr list --repo <REPO> --head <branch> --state open --json number` once: an open PR is
not a stop either, but the table says so, because the normal flow is what works a PR's review.
Then the scenario list (see **`--verify-only`**), then step 7.

Then per branch, for **every branch in every stack the round touches — from the branch directly
above `main` to the top**, whether or not it has feedback. A fix routinely lands below the PR that
was commented on, and every branch we own above a changed one gets restacked and pushed, so each
needs a row. Walk down from a PR's `baseRefName` with
`gh pr list --repo <REPO> --head <baseRefName> --state all` until `main`, and up from its
`headRefName` with `gh pr list --repo <REPO> --base <headRefName> --state all` until nothing
answers — every PR, open or not,
because a merged or closed one is where its branch's `baseRefName` and `author` still live. A
branch with several PRs is read from the open one, else the most recently updated:
`--json number,state,baseRefName,author,updatedAt --jq 'sort_by(.state == "OPEN", .updatedAt) | last'`
with `--limit 20`. Only
**open** PRs join the stack that step 5 restacks and step 10 pushes. A merged or closed PR below
ours ends the stack there and is decision item one at step 4: our branch's real base is now
whatever that PR merged into. A closed PR above ours is simply not in the stack:

```bash
gh pr view <pr> --repo <REPO> --json \
  headRefName,baseRefName,headRefOid,state,mergeable,mergeStateStatus,reviewDecision,author
gh api repos/<REPO>/compare/<baseRefName>...<headRefOid> --jq '{ahead_by,behind_by}'
git rev-list --left-right --count origin/<headRefName>...<headRefName>   # remote-only, local-only
```

Record a row per branch in `findings.md`: PR · branch · base · `headRefOid` · `pin` ·
`reviewDecision` · behind-count · mergeable · local-only · remote-only · owner (`.author.login`
versus `gh api user --jq .login`). `pin` starts equal to `headRefOid` and is the only column
steps 5 and 10 change; `headRefOid` itself is never overwritten, because step 5 may need the tip
this
round started from. Take both from the API, not from `git rev-parse origin/<branch>`, which
reports only what was last fetched. A base branch with no PR at all gets a row from
`git rev-parse origin/<branch>` — fresh, after the fetch above — with empty PR fields, and is ours
only if `git log -1 --format=%ae origin/<branch>` equals
`git config user.email`; step 5 re-checks it the same way. `main` itself
has no row: it is never rewritten, so
plain `merge-base` is always right against it.

**Stop — about this checkout, which is ours whoever owns the PR:**

- **HEAD is detached, or on none of the branches in the table.** Every fix lands somewhere no
  PR in the round displays, and nothing later in the flow notices.
- **Tracked modifications in the working tree.** They get folded into this round's commits and
  into step 10's push. Untracked and ignored files are fine; the notes directory is one. This is
  what "a clean tree" means everywhere below.

**On a branch we own:**

- **Remote-only commits — stop.** Someone pushed to it. Step 10's lease is pinned to the remote
  head *including* those commits, so the force-push would pass and delete them. Put it to the
  user; integrating them is a step 5 action if the user rules it.
- **`behind_by > 0` or `mergeable: CONFLICTING` — decision item one at step 4.** The fixes are
  being sized against a tree that will change; every estimate below it is provisional. Moving a
  branch onto a new base is the user's call and no step here does it unasked; restacking a
  branch onto its own base's new tip is part of whatever moved the base, and needs no ruling — so
  a ruling to leave a behind child alone holds only while its base goes untouched this round.
- **Local-only commits — decision item at step 4: do they ride along?** The reviewer read
  something older than this tree, so some items may already be fixed; step 2 checks each one
  against both refs. If they ride, step 10 pushes them with the rest; if not, the ruling says what
  step 5 does with them, since step 10 pushes the branch as it stands.

**On a branch someone else owns**, those three are warnings, listed at step 4 under "No decision
needed". It is not ours to tidy, and this flow never restacks or pushes such a branch: where one
sits above a branch we will change, that is a fourth warning for step 4, step 9 lists it again,
and its owner restacks it.

Three traps:

- **`mergeable: UNKNOWN` is a non-answer, not a pass.** GitHub computes it lazily, so the first
  query on a PR usually returns `UNKNOWN` and an agent reads "not `CONFLICTING`" as "fine";
  re-query until it settles. `behind_by` from the compare call is always computed, so prefer it.
  On a merged or closed PR (`state`, which is why it is in the query) `UNKNOWN` is permanent and
  correct.
- **`mergeStateStatus` cannot answer the behind-question.** It reports `BEHIND` only where branch
  protection requires branches to be up to date; where that is not enabled, a badly stale branch
  reads `BLOCKED` or `CLEAN` instead. `behind_by` from the compare call is the authority.
- **A conflicted PR silently stops CI.** GitHub cannot compute a merge ref, so no `pull_request`
  workflow runs at all. "No checks reported" is not "checks passed".

## 1. Read the feedback

Per PR, all three surfaces:

```bash
gh api repos/<REPO>/pulls/<pr>/reviews  --paginate   # review bodies
gh api repos/<REPO>/pulls/<pr>/comments --paginate   # inline threads
gh api repos/<REPO>/issues/<pr>/comments --paginate  # conversation comments
```

Then drop threads the reviewer already resolved — REST cannot see resolution state, so a second
round re-collects everything round one answered. GraphQL can see it (`<name>` is `REPO` without
its `paranext/`):

```bash
gh api graphql --paginate --slurp -f query='
query($owner: String!, $name: String!, $pr: Int!, $endCursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100, after: $endCursor) {
        nodes { id isResolved isOutdated
          comments(first: 50) { nodes { databaseId author { login } } } }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}' -f owner=paranext -f name=<name> -F pr=<pr>
```

`--slurp` returns one array element per page; read the threads from every element. `gh` refuses
`--slurp` together with `--jq`, so filter by piping the output to `jq`. The thread
`id` is what closes a thread of ours at step 10, and the root author is how we tell ours from
theirs — guessing that later resolves a reviewer's thread in public. (paranext-core's
`.claude/commands/triage-feedback.md` carries a narrower form of this query; **never run that file
as a command** — its own later steps post and resolve with no gate in between.)

**An item is one of:** an inline thread — its root comment *and every reply in it*, the reviewer's
follow-ups included; a review body; a conversation comment; a piece of off-PR feedback (see
**Feedback that arrived off-PR**). Record per item, in `findings.md`: the PR, the surface, the
verbatim text, and the id the reply goes to — a thread's **root** comment id (the REST
`in_reply_to_id` of any reply, or the first `databaseId` in the GraphQL thread) plus its author
and thread id; a review's id; a conversation comment's id; nothing yet for off-PR. For threads
also record the revision the reviewer read: `original_commit_id`, **not** `commit_id`, which
GitHub rewrites as it repositions comments under force-pushes. Reviews carry the reviewed head as
`commit_id`; conversation comments and off-PR items carry no revision and are read at the head.

Feedback arrives off-PR routinely — a document, a DM, Discord. The list of surfaces you collected
from is a decision item at step 4: were there others? Do not call the list complete before then.
Reviewable-native "no related file" discussions are invisible to every API; say "none were
reported", never "there are none".

**roborev leftovers — a check that should find nothing** (only with roborev; see
**Requirements**). roborev reviews every commit in this
repo in the background, and step 6 settles every review of a round's own work before gate 9. An
open review on a branch in step 0's table therefore means an earlier round, or work done outside
this flow, left one unprocessed. Check per branch:

```bash
roborev list --branch <branch> --json --limit 200 | jq -r '.[] | select(.closed == false)
  | "\(.id) \(.status) \(.verdict) \(.git_ref[0:11]) \(.commit_subject)"'
git rev-list origin/<baseRefName>..<branch>      # this PR's own commits
```

Always through that `jq`: the raw JSON embeds each review's whole prompt. An open job whose
`git_ref` is no longer one of this PR's commits is stale. Whatever turns up — stale or not — is
listed at step 4 under "No decision needed" as leftovers that step 6 settles with this round's
reviews; only a finding that would change what this round does is a decision item instead. If
`roborev status` fails, say so there and carry on; repairing roborev is not this flow's job.

## 2. Verify each item is real

Read the code at the ref the reviewer read and decide what it actually does, rather than whether
their story is plausible. That ref is usually one a force-push orphaned, so `git checkout` on it
fails and the tempting fallback — reading the working tree — silently answers a different question:
`gh api repos/<REPO>/contents/<path>?ref=<sha> --jq .content | base64 -d` reads any
commit GitHub still holds. Where step 0 found local-only commits, check the item at the reviewer's
ref *and* at the local tip: it may be fixed already, and the reply should say so.

When you need a PR's own changes, the range depends on the command, and its ends are **that PR's
base and head branches** — not `main`, and not `HEAD`, or the branches below get attributed to it,
or the ones above do. For `git diff` the range is `origin/<base>...<branch>` — **three dots** —
because the two-dot form diffs the endpoint trees and renders the base's later changes as
spurious deletions. For `git log` and `git rev-list` it inverts: three dots is the symmetric
difference and pulls the base's own commits in alongside ours, so there `origin/<base>..<branch>`
— **two dots** — is the form that means "ours".

- **Run runtime claims instead of arguing about them.** Ten lines in the real runtime settles what a
  page of reasoning cannot, and is usually cheaper.
- Check: already fixed upstream · right conclusion, wrong mechanism · self-refuting · two reviewers
  contradicting each other · a suggested fix that does not do what it claims.
- Not everything is a claim. Questions, offers and status reports need an answer, not a verdict —
  and an unanswered question is a debt that is invisible if you only track fixes. A review body
  that only points at inline comments ("one concern below") needs no answer of its own; record
  that disposition rather than replying to a pointer.
- Say plainly what you could not settle and name the measurement that would settle it.

## 3. Decide what is real, and whether we act on it

Per item, two questions and no others: **is the concern real**, and **do we act on it in this
round** — fix it here, record it somewhere durable, or decline it. Sort into: act here · design
preferences (you recommend, the user rules) · cross-reviewer conflicts (present both, never pick a
side) · declines and deferrals, each with where the residue is recorded · no reply needed. Note
**which branch** an item would land on — on a stack, often not the PR the comment appeared on —
since that is scope, not mechanism.

**Do not decide *how* yet.** The shape of the fix is step 5's question, and answering it here spends
the ruling before the investigation that would inform it: sizing a change from the reviewer's
comment alone routinely misses a second consumer of the thing being changed, an existing seam that
makes a different fix cheaper, or a constraint that only reading the call sites reveals — and a
mechanism the user has already ruled on is the expensive kind of wrong, because reopening it costs a
second gate. Where scope genuinely turns on cost — "fix it here" only makes sense if it is small —
give a bounded estimate ("a few lines in one file", "a new abstraction across three"), never a
design.

Before sizing a reviewer's "do it properly" suggestion, check whether anything needs it. A reviewer
proposing a general mechanism — a config knob, an interface, a second implementation — is reasoning
from the diff in front of them, not from the call sites. Grep for real usage first, and where there
is exactly one, "the narrow fix, plus a note that the general one is a one-caller change if a
second arrives" belongs at step 4 alongside the general one. That pair is a scope question — how
much to build — which is why it belongs at step 4 rather than with the mechanisms at step 5. It is
an **option to present, never a decline to take** — the reviewer asked, so the user rules.

A deferral needs a not-yet-started ticket. **Never create a Jira ticket** — propose it, and the
reply names the ticket only once the user has created it.

**Attack your own recommendations before the gate.** Steps 2, 6 and 8 put the reviewer's
findings, the code and the replies in front of a fresh reviewer; the options this step proposes
need the same, because the user rules on them at step 4, and a recommendation nobody tried to break
is one they approve blind. Before presenting, hand each option you recommend — and every option
that goes beyond what the reviewer asked: dropping a feature, a structural rewrite, a decline — to
a fresh agent that did not write it, with the brief to break it: concrete scenarios where it fails,
what it leaves dangling, which of the reviewer's items it makes worse, and how the alternatives
compare. Keep the attack at the level of scope — "does this option hold" — not mechanism, which is
step 5's. Record the result in `findings.md`. At step 4 the question carries what the attack found
— the conditions the option needs, or why the recommendation changed — and an option that failed
is presented as failed, or dropped. A plain "fix this here" item whose cost is a line or two needs
no attack.

## 4. STOP — present 0–3

Present per **Presenting a gate** below, and do not start implementing in the same turn. The list
carries step 0's decision items first, then the items, then the surfaces question; step 0's
warnings go under "No decision needed".

**Every item here is a verdict and a scope decision, never a mechanism.** What the user is being
asked is "is this real, and do we act on it in this round" — not "which of these three
implementations". If an option reads like a design — an approach, a signature, which files change —
it belongs at step 5, and asking it here buys a ruling on a solution nobody has investigated yet.
Step 5's brainstorming exists to answer that question *after* reading the code, and it has its own
gate for it. A cost estimate is fine and often necessary to settle scope; a design is not.

**Run this gate as an interactive interview, not a wall of text.** Collect the
rulings with the `AskUserQuestion` tool: one question per decision item, up to four items per call,
in the order they matter. Each question is self-contained and jargon-free — it carries the context,
the trade-offs or pros/cons where they exist, and every option as a thing the user can pick — so
the user can rule from that question alone, without the notes. Put your recommendation in the
option label when you have one; when you are unsure, say so and recommend nothing rather than
guess. The user can always type a free answer instead of picking: when that answer is a question
or a counter-proposal (for example "would dropping it altogether be better?"), answer it honestly
in a sentence or two — including "yes, that is better than what I proposed" — and re-ask that item
with the revised options before moving on. Do not implement between the interview's calls; the
interview is the gate. If you are running as a sub-agent with no direct line to the user, return
the gate items to the coordinator in the four-part form below and let the coordinator run the
interview; do not treat a relayed "proceed" as a ruling on items it does not name.

Write the presentation and then the ruling into `rulings.md`, the ruling **verbatim** (for an
interview, the exact option chosen plus any typed text). A paraphrase is how a decision gets
quietly widened three steps later. Approval covers only the items it names: anything unanswered
stays unimplemented, and if the answer settles some items and reopens others, re-present the
remainder rather than reading silence as assent.

## 5. Implement

**Before any code is written here, two things happen in this order — a check, then a handoff — and
neither is optional.**

**First, confirm the branch has not moved.** Read `rulings.md`, then `git fetch origin` and re-query
`headRefOid` for every row. The gate may have taken days. On a branch we own, a value that differs
from the row is step 0's remote-only stop, and it goes to the user before anything is built on the
branch; on someone else's branch it is a warning, noted below the table. It comes first because a
design reasoned against a tree that has since moved is as wasted as an implementation built on one.

**Finishing that read is not permission to start implementing** — it is the single place this step
goes wrong. The ruling you just received describes work, the instruction above this one is a git
command, and running it feels like the work has begun. It has not.

**The first thing that acts is the Superpowers flow** — `superpowers:brainstorming` →
`superpowers:writing-plans` → `superpowers:test-driven-development`, scaled to the ruling; a
one-line correction needs the TDD skill and nothing above it. Point their specs and plans at the
notes directory: they default to `docs/superpowers/` inside the working tree, which is the one place
this flow works to keep clean.

**Step 4 ruled what and whether; this flow rules how**, and it is the first thing here that has read
the code the change touches. The rulings are fixed constraints on it, not inputs to it —
brainstorming widens a solution space, and step 4 closed a different one. Its approval gate is its
own and is **not** covered by step 4's: a ruling to fix an item is not a ruling on the design that
fixes it, so present the design and stop, however small it is. If the design work surfaces a reason
a ruling is wrong — a second consumer, a cheaper seam, a cost the estimate missed — stop, put it
back to the user as a new decision, and append the exchange to `rulings.md`.

**Attack the design before its gate.** Step 3's attack judged scope and deliberately left
mechanism here, and brainstorming's builder check asks only whether a design is complete enough to
plan from, not whether it is a good one — and skips small changes entirely. So before presenting a
design, hand it, the ruling it serves and the code it touches to a fresh agent that did not write
it, with the brief to break it: concrete scenarios where it fails; consumers or call sites of the
changed thing that it missed; an existing seam or pattern in the codebase that would make a
different fix cheaper or more conventional; whether it fully settles the reviewer's item as ruled,
or only the instance they pointed at; what it leaves dangling; and how it compares with the
obvious alternative. The agent reads the code itself rather than taking the design's account of
it. Record the result below the table in `findings.md`. The design you present carries what the
attack found — the conditions it needs, what changed because of it, and any alternative that now
looks better, stated as such; an attack that shows a ruling is wrong is the stop-and-ask case
above, not a design tweak. A one- or two-line correction whose mechanism is obvious from the
ruling needs no attack, as at step 3.

Implement only what was ruled. A ruled rebase goes onto the branch's **own** base, using the
block under **Finish the stack** with `origin/<baseRefName>` as `<base>` — a plain
`git rebase <upstream>` uses `merge-base` and fails the way that block describes when the base was
rewritten. Ruled integration of remote-only commits is `git rebase origin/<branch> <branch>`. After
that ruling — and equally after a ruling to overwrite them — the row's `pin` becomes the
re-queried `headRefOid`, or step 10's lease can only fail.
Red-first for every behaviour change. Never `--no-verify`. As each fix lands, append
"item → commit → branch" below the table in `findings.md`; step 9 presents from that.
In paranext-core and any repo that builds a Platform.Bible extension, new public API needs the `@experimental` marker on
**both** surfaces — TSDoc on the type-visible one and `'x-experimental': true` in the
registration's OpenRPC docs; the authoritative table is paranext-core's
`.context/standards/Paranext-Core-Patterns.md` § Experimental APIs. From another repo, read it in
the sibling `../paranext-core` checkout, or with
`gh api repos/paranext/paranext-core/contents/.context/standards/Paranext-Core-Patterns.md --jq .content | base64 -d`.
The rule covers anything that reaches the Platform.Bible API — `papi.d.ts`, an extension's `.d.ts`,
or a registration on the network; a repo that adds none of these has nothing to mark.

**Finish the stack before leaving this step.** Every branch we own that sits above a branch this
round rewrote or added a commit to — anywhere in the stack, a rewrite or a plain commit, it makes
no difference — gets restacked, bottom up, once the last commit of the round has landed. The same
applies again to any commit added at step 6 or 7. Run it with a clean tree; the block checks out
each child in turn and leaves HEAD on the last one:

```bash
FORK=$(git merge-base --fork-point <base> <child>) \
  || echo "STOP: reflog cannot place <child> on <base>"
[ -n "$FORK" ] && git rebase --onto <base> "$FORK" <child>
```

`--fork-point` reads the base's reflog for the tip the child was actually built on, so it is right
whether the base gained commits or was rewritten, and nothing needs capturing beforehand. Plain
`merge-base` is wrong after a rewrite: it falls below the base's own commits, the rebase replays
the base's work onto the child, stops on a conflict inside the base's change, and resolving that
undoes the rewrite. When the reflog cannot answer — a fresh clone, an expired reflog — the first
line prints STOP and the second does nothing; the block's exit status of 1 is that STOP, not an
error. The upstream then is the tip the child was last built on: plain
`git merge-base <base> <child>` where the base has only gained commits since the child last sat
on it, or the base's `headRefOid` from step 0's table — the column that is never overwritten —
for a child never restacked this round, provided that base had no local-only commits. Neither
applies? There is no safe value; it goes to the user.

A restack that conflicts does so here, in front of you. The rule for the hunk: the base's lines
win, and only the child's own insertion is the child's — resolving the other way reverts the
base's change on the child's PR. In a rebase the `<<<<<<< HEAD` side *is* the base, and
`git show REBASE_HEAD -- <file>` marks the child's own lines with `+`. Before touching anything,
save the conflict: `git diff > <notes>/conflict-<child>-<nn>.diff`. Then resolve, `git add`,
`git rebase --continue`; never blanket `--continue || --skip` in a loop, since `--skip` silently
drops real commits and an untracked-file collision or a hook failure looks exactly like an empty
commit. Every saved conflict is shown at step 9, with its resolution, as content the user has not
seen. A restack triggered from step 6 or 7 follows this whole section, saving included. The stack
is finished before step 8, so the commits step 8 cites are the commits that will be on the PRs.

## 6. Review your own diff

`/code-review` at `high`, or `max` for a large or risky round, over the range the branch was
rebased onto: `<base>...<branch>` where this round changed `<base>` locally — rewrote it or added
to it, since nothing is pushed yet and `origin/<base>` is still what the round started from — and
`origin/<base>...<branch>` otherwise, `main` included, since local `main` is whatever was last
checked out. Its findings are
hypotheses: verify each before acting, and write the ones you refuted into `verification.md` with
the reason. A verified defect in this round's own changes is fixed here, and a fix on a branch
with branches above it re-runs **Finish the stack**. Anything beyond what was ruled stops now and
goes back to the user as a new decision
item in the form step 4 uses, appended to `rulings.md`.

**Then settle roborev — here, so that gate 9 reports on it rather than asks about it** (only with
roborev; see **Requirements** — without it, go straight to the mutation check below). roborev
reviewed every commit steps 5 and 6 made, in the background (a restack remaps its reviews onto the
new SHAs; it does not re-review). Those reviews are weighed and closed in this step, together with
any leftovers step 1 found. Per branch this round changed, and per branch step 1 found leftovers
on, run step 1's query:

```bash
roborev list --branch <branch> --json --limit 200 | jq -r '.[] | select(.closed == false)
  | "\(.id) \(.status) \(.verdict) \(.git_ref[0:11]) \(.commit_subject)"'
```

**First check that roborev saw every commit at all.** The query above finds only *open* jobs, and a
commit roborev never received leaves no job, so it would slip past unseen. The hook that hands
roborev each commit is local to the main checkout (untracked, deliberately kept out of the repo), and
a git worktree runs its own hook folder, which does not have it, so commits made in a worktree
regularly never reach roborev. Per branch this round changed, list every commit of the round that has
no job, open or closed:

```bash
reviewed=$(roborev list --branch <branch> --closed --json --limit 500 | jq -r '.[].git_ref'
  roborev list --branch <branch> --json --limit 500 | jq -r '.[].git_ref')
git -C <worktree> rev-list <headRefOid>..<branch> | grep -vxF "$reviewed"
```

`<headRefOid>` is step 0's column, the tip the round started from, so the range is exactly this
round's commits. Queue each SHA it prints, one at a time, and wait for it:
`roborev review --repo <worktree> <sha> --wait`. Then run the open-jobs query again: the new jobs
are settled below like the rest. Record in `roborev.md` which commits needed queuing by hand.

`roborev wait --job <id>` any job still queued or running (exit status 1 is a failing verdict, not
an error). A job with verdict `P` has nothing to weigh and is simply closed. Read each `F` job with
`roborev show --job <id>` — plain, not `--json`, which embeds the whole prompt.

Weigh every finding as you weigh `/code-review`'s: it is a claim from a reviewer that saw one
commit's diff and nothing after it. Check it at the branch tip — a later commit often fixed it
already — and against the rule file it cites rather than the review's paraphrase of it; its
severity is a guess.

**A true finding is not yet a reason to edit.** The failure this guards against is the goose
chase, and it has happened here: roborev flags something small, it gets patched on the spot, the
patch draws the next finding, and a few rounds later the branch carries a string of local fixes to
what was one structural mistake — or to nothing that mattered. Before deciding any finding, answer
these four and write the answers into `roborev.md`:

- **Does fixing it fix anything?** Name the concrete failure it prevents: wrong behaviour, a reader
  misled about what the code does, a rule this repo actually enforces. "Theoretical", "cleaner",
  or "roborev asked" is an answer, and it means decline.
- **Is it one instance of a pattern?** Look for the same shape elsewhere in the round's change and
  its neighbours. Patching one occurrence of something that should change structurally is worse
  than patching none: it hides the pattern and leaves the rest.
- **Is it this round's business?** Code this round wrote or changed, within what the user ruled —
  or something pre-existing that the diff merely sits next to.
- **Has it been raised before?** Read this PR's roborev history: earlier rounds' `roborev.md`
  (found as **Working notes** says) and the branch's closed jobs with the comments they were closed with
  (commands below). The same finding or a cousin of it returning after a fix, or each fix drawing
  a fresh finding in the same area, means the fixes are wrong in kind. Stop patching, name the
  pattern in one plain sentence, and treat the pattern as the finding.

```bash
roborev list --branch <branch> --closed --json --limit 200 \
  | jq -r '.[] | "\(.id) \(.verdict) \(.git_ref[0:11]) \(.commit_subject)"'
roborev show --job <id> --json | jq -r '(.comments[]? | "comment: \(.response)"), .output'
```

Then it is one of three:

- **Real, worth fixing, and inside what the user ruled** — fix it here, red-first, like any verified
  defect in this round's own change. Where it is one instance of a pattern, fix the pattern, not the
  instance — provided that stays inside the ruling and small; otherwise it is the third case.
- **Not a defect, not worth fixing, already fixed, stale, or a preference this repo does not hold**
  — no change; the reason is the disposition.
- **Real but outside the ruled scope, a structural fix beyond it, a recurring pattern, or a change
  to a design the user approved at step 5** — do not act. It goes to the user as a new decision item
  in step 4's form, appended to `rulings.md`, with the global deferral rule deciding what to
  recommend; for a recurring pattern, say what keeps recurring, what the fixes so far had in
  common, and what you think the underlying mistake is. This should be the exception: most findings
  land in the first two, and you decide those yourself.

Write each finding and its disposition into `roborev.md` as you go. Then settle the job — comment
first, close only after the comment succeeded, one job at a time; a job with a finding waiting on
the user stays open until the ruling, then is settled the same way:

```bash
roborev comment --commenter process-pr-feedback --job <id> -m "$(cat <<'ROBOREV_COMMENT'
<per finding: fixed in <sha> | not a defect: <reason> | stale | ruled by the user: <ruling>>
ROBOREV_COMMENT
)"
roborev close <id>
```

The comment is not bookkeeping: roborev feeds earlier reviews and their comments into later
reviews' prompts, so a stated reason is what stops it raising the same false positive on the next
commit. This is all local to roborev — nothing reaches GitHub — so it needs no gate of its own;
gate 9 is where the user sees it and can overrule it.

Fixes made here are commits and get reviewed in turn, so repeat until no open job is left on the
round's branches. Every pass must shrink the list. One that does not — as many findings raised as
it closed, or a second pass flagging the area the first one fixed — is the "raised before?"
question answered yes: step back and name the pattern rather than run a third pass.

**A guard is not done until breaking it turns a test red.** Mutate the thing you just fixed and
confirm the suite fails; a test that passes either way is not evidence. The same applies to every
check in this flow — a diff that errored, a poll that read a network error as green, a watcher that
concluded over an incomplete list. A check that cannot observe its subject reports success.

## 7. Verify it works

**Every command and script this step names is paranext-core's, and in paranext-core this step is
followed exactly as written.** In another repo, every rule here still holds — the
three parts, the full run at the top tip, capped test runs, one at a time, a red test counting as
pre-existing only once shown red on the base, evidence for every claim, and anything not run
listed at gate 9 with the reason — but the commands are that repo's own:

- **The battery** is what that repo's CI gates on. Read `.github/workflows/` and run the same lint,
  typecheck, format and build steps locally — in the extension repos that is `npm run lint`,
  `npm run format:check`, `npm run typecheck` where the script exists, and `npm run build`. A CI
  check you cannot run locally is listed at gate 9 as not run. Run the format check with the notes
  excluded — where it is `prettier --check .`, as `npm run format:check -- '!**/.review/**'` — and
  read any warning that remains against `git status`: a file git does not track is local clutter
  that CI's clean checkout never has, not the round's, and gate 9 lists it as such. The same goes
  for any other linter in the battery that scans markdown or the whole tree.
- **The test suites** are whatever that repo has and its CI runs, run whole and capped: vitest
  with `--maxWorkers=4`, never bare. A repo with no tests is listed at gate 9 as having none.
- **E2E** only where that repo has e2e specs; otherwise gate 9 says it has none.
- **The live run** for an extension repo is the Platform.Bible dev app with the extension loaded:
  the repo's `npm start` — check its `package.json` — watches the extension and runs
  paranext-core's `npm start` from a sibling `../paranext-core` checkout. Everything below about the dev app applies to it unchanged — the
  ports are the same, so `app-guard` comes first, and the repo's own `npm run stop` runs
  paranext-core's `npm stop`, so it is treated exactly like `npm stop`. Neither `npm start` stops
  anything first, so no `npm stop` shim is needed to start. The repo's `npm start` sets `MAIN_ARGS`
  itself and leaves out CDP, so for a live run driven over CDP start the two halves yourself, the
  way paranext-core's `refresh.sh` starts the app: `npm run watch` in the repo, in the background
  and stopped by pid when the live run ends, then in
  `../paranext-core`, `unset ELECTRON_RUN_AS_NODE` and
  `xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" env MAIN_ARGS="<the argument the repo's start script passes, with its dist path made absolute> --remote-debugging-port=9223 --maximize" npm start`
  — without `xvfb-run` where it is missing, which shows a window. The `visual-verification`,
  `log-inspector` and `papi-client` skills live in paranext-core's `.claude/skills/`; from another
  repo, read their `SKILL.md` there and follow it. For a repo that is not a Platform.Bible
  extension, the live run is whatever its README or `CLAUDE.md` documents for running it locally;
  where nothing does, gate 9 lists the live run as not run, with that reason.

It has three parts — the battery, the test suites, the live run — and a green subset satisfies none
of them. **They run in full once per round, at the top tip of each stack the round changed**: that
tip contains every change the round made anywhere in the stack, so checking each branch below it
again would mostly repeat the same run. Below the top:

- a branch whose **own** commits changed this round gets the cheap checks on what it changed —
  `npm run typecheck`, and the tests that import its changed files —
  `npx vitest run --maxWorkers=4 --changed origin/<baseRefName>` for core, and per workspace it
  touched `npm test --workspace=<workspace> -- --run --maxWorkers=2 --changed origin/<baseRefName>`;
- a branch that was **only restacked** gets nothing extra — its code is checked at the top.

**A later pass** — anything that changes code after this step, a defect step 8's reply review
exposes or a finding overruled at gate 9 — re-runs the battery at the top and the related tests
for what changed since the full run (`--changed <sha of that run>`), and repeats an e2e subset or a
live scenario only where the change reaches it. The full suites are not repeated for a follow-up
fix: CI runs them on three platforms after the push — for a PR whose base is another feature
branch, only once it targets `main`, which is why the full run before the first gate-9 presentation
is not optional.

**The battery**, at the top tip:

```bash
npm run build:types    # state the expected papi.d.ts delta BEFORE running
npm run build:main     # writes buildInfo.json, which typecheck imports
npm run typecheck && npm run lint && npm run format:check
```

Keep `format:check` named: `lint` is eslint over script files plus stylelint over styles, so a JSON
or YAML change is checked by nothing but the separate prettier pass that CI gates on.

**The test suites, whole, at the top tip** — not just the files the round touched: a change to
shared code breaks a test the diff never mentions, and a targeted run cannot see it. TypeScript
always. C# when the round's diff anywhere in the stack touches `c-sharp/` or `c-sharp-tests/` —
decided from `git diff --name-only`, not by judging what a change could reach: the C# tests exercise
only C# code, so a round with no C# change cannot turn them red. Gate 9 says when C# was skipped
and why.

```bash
npx vitest run --maxWorkers=4                                        # core
npm run test --workspaces --if-present -- --run --maxWorkers=2       # extensions and libs
dotnet test c-sharp-tests/                                           # only when C# changed
```

**Always capped, never bare `npm test`** — the `test-runner` skill's table shows the bare form; do not
follow it here. Uncapped, vitest forks a jsdom worker per CPU, exhausts the machine's memory (WSL's especially) and takes the
whole machine down, the user's desktop with it. `npm test -- <path>` does not narrow the run either:
the core half runs unfiltered first. `ERR_IPC_CHANNEL_CLOSED`, or an exit 1 with every test line
green, is a worker killed for memory, not a flake — re-run that workspace at `--maxWorkers=1`, never
uncapped. Run these one at a time, not as parallel tool calls.

A red test is not "flaky" or "pre-existing" until shown to be: run the same test on the branch's base.
Red there too means pre-existing — listed at gate 9 as such, neither fixed silently nor dismissed.
Green there means this round broke it — back to step 5. Run it on the base without touching this
checkout: a temporary worktree of `origin/<base>` with its dependencies installed — in paranext-core
under `.claude/worktrees/`, the one place there Claude Code's own worktree tool writes without a
prompt; in another repo, a sibling directory outside the checkout — removed afterwards; where that is too costly for one test, the
row says "not shown on the base" rather than "pre-existing".

**E2E for the area the round changed.** Find the specs that cover it (`git grep` under
`e2e-tests/tests` for the feature's names) and run them per `.context/standards/Testing-Guide.md`
§ Running E2E Tests exactly, standalone and headless — specs live beside `tests/isolated/` too, and
that section says which mode and flags each needs. The isolated form is
`./e2e-tests/run-e2e-wsl.sh --wrap npm run test:e2e:isolated tests/isolated/<dir>/ -- --workers=1`.
Run every e2e command with `--list` first and check the count: far more than you asked for means the subset name
also matched the worktree path and the run covers the whole suite; zero means nothing ran. Either
way a green proves nothing about the area. No spec covers it? Say so at gate 9.

**The live run — headless, and required** for every round whose change reaches a runtime path:
anything but tests, docs, comments or the notes. At the top of the stack, start the app headless and
reproduce each reviewer scenario the round fixed — in `--verify-only` mode, each scenario on the
list that mode showed the user before running, which comes from the requirement and never from
the code (see **`--verify-only`**). On Linux `./.erb/scripts/refresh.sh` starts it
under `xvfb-run` with CDP on port 9223 — but never run it before `app-guard` below, which also says
how to start it without its `npm stop`. Drive the app with `visual-verification`, read
`log-inspector` for errors the scenario raised, and call commands directly with `papi-client`. Per
scenario, record in `verification.md` what you did, what you saw against what you expected, and the
evidence — a screenshot, the PAPI response, the log lines. "Verified live" without evidence is not
verified.

**Never take the app from another session — check with `app-guard` first.** The app's ports (8876,
1212, 9223, 9222) are machine-wide, and `refresh.sh` begins with `npm stop`, which kills by name
every Electron and every `dotnet` on the machine plus any webpack, vite, esbuild or extension-host
process: other sessions' apps, e2e runs, `dotnet test` runs and builds alike. Before starting the
app, and before a standalone e2e run, run `python3 "${CLAUDE_PLUGIN_ROOT}/tools/app-guard.py"` (Linux and WSL only; see
**Requirements**). It names the
Claude session behind every such process — exactly, from the session id each session's commands
carry in their environment — and its verdict is its exit status:

- **CLEAR (0) or START_ONLY (3)** — nothing of a live peer's holds the ports. First stop, by pid,
  any process of ours or of an ended session that holds a port (the report prints the `kill` line).
  Then start the app **without** `npm stop`:
  `PATH="$(python3 "${CLAUDE_PLUGIN_ROOT}/tools/app-guard.py" --no-stop-path):$PATH" <worktree>/.erb/scripts/refresh.sh`
  — the same script, with `npm stop` turned into a no-op. This is the normal start, every time.
- **WAIT (4)** — a live peer session holds the ports or is running e2e. Never kill it: coordinate,
  actively. The report gives the session's name; find it with `ListAgents` and `SendMessage` it with
  `notify_when_idle: true`, asking a question it can answer in one reply, first line self-contained (in `--verify-only`
  mode, name the branch where this says PR <n>):
  "PR <n> needs the dev app (ports 8876/1212/9223) for a live test of about <m> minutes, and you
  hold it (pid <p>). If you are done with it, stop it by pid — not `npm stop` — and reply
  'released'; if not, reply with roughly how long you still need it." Then:
  - **A time** — wait about that long, then re-run `app-guard`.
  - **"released", or an idle notice** — re-run `app-guard`. A session that went idle with its app
    still up has usually just forgotten it: ask once more, plainly, for it to stop the app.
  - **Silence** — re-run `app-guard` every ten minutes or so. A session waiting on its own user
    cannot answer at all, so after half an hour of silence, or an hour of waiting in all, ask the
    user, naming the session. Never let the live run lapse silently, and never kill a peer's app
    yourself.

  Two sessions that both see CLEAR can still race for the ports: if the start fails with
  `EADDRINUSE`, re-run `app-guard` — it will now say WAIT — rather than reaching for `npm stop`.
- **ASK (5)** — a process no live session owns holds a port: perhaps the user's own app in a
  terminal, perhaps a leftover. Ask the user; do not guess.

**`npm stop` is the way to get unstuck**, not the way to start: when the app will not come up or a
port stays held by something that will not die, plain `./.erb/scripts/refresh.sh` (or `npm stop`)
resets everything reliably. Use it only when `app-guard` says CLEAR — nothing of anyone else's would
die. On START_ONLY it would kill the processes the report lists: clear it with their owners first
(the same message route), or with the user for processes no session owns. Record every stop, by pid
or by `npm stop`, in `verification.md`.

Standalone e2e and the live app compete for the same ports, so run e2e first. When finished, stop
only the app this session started, by pid.

**What gate 9 shows is the checks, not a verdict.** `verification.md` carries, per branch tip: each
command with its exit status and its pass/fail/skip counts; the papi delta stated and observed; each
e2e subset with its listed count; and the live run per scenario with its evidence. Screenshots worth
showing go beside it. Anything not run — a suite skipped, a live run blocked — is listed at gate 9 as
not run, with the reason. "Everything green" is the headline only when every row says so.

Not working? Back to 5, including **Finish the stack**. **Committing is fine here. Pushing is
not.** With roborev, every commit made here needs a roborev review like the rest: run step 6's coverage check
again and its settling covers the new jobs too. In `--verify-only` mode there is no step 5 to go
back to and nothing is committed: a red check, a scenario that did not behave as expected, or a
`papi.d.ts` the build changed is a row in the table the mode ends with, stated as found, and
fixing it is the caller's — who then runs the mode again, in full: the later-pass shortcut above
rests on CI running the suites after the push, and nothing has been pushed yet. A changed
`papi.d.ts` is left in the tree for the caller to commit (it belongs on the branch, which is why
the row exists); every row after the battery then describes `headRefOid` plus that file, and says
so. It is the one tracked modification a re-run of the mode will find, and the caller commits it
before that re-run rather than the mode committing it.

**With roborev, leave this step with it settled:** for every branch of the round, step 6's coverage check
prints no commit and its open-jobs query prints nothing — every commit has a review, none open, none
still queued. Gate 9 presents that state; it does not weigh reviews.

**In `--verify-only` mode** — a branch about to get a PR is exactly where an unsettled review
matters — step 6's roborev part is the one piece of another step the mode runs: the coverage check
over `origin/<base>..<branch>` (there is no `headRefOid` column from an earlier tip; every commit
of the branch is the round's, and `<worktree>` is the checkout the mode runs in), then the
settling with its four questions ("within what the user ruled" reads here as "within the
requirement") and `roborev.md`. The mode fixes nothing and takes no ruling, so
the state it leaves and the table shows is not the one above but this: every commit has a review,
none is queued or running, every `F` job has been read, and each finding has a disposition in
`roborev.md`. Step 6's second kind — not a defect, not worth fixing, already fixed, stale, or a
preference this repo does not hold — is commented and closed as step 6 says (`roborev comment` and
`roborev close` are local to roborev; nothing reaches GitHub), and the table lists those declines
compactly, as gate 9 does, since the reader overrules there. Step 6's first and third kinds — a
real defect, in scope or beyond, small or structural — are one kind here: commented ("open: in the
verification table of <date>, for the caller") and **left open**, each a row in the table, and
the headline is not "everything green" while one exists. The caller fixes it; the next run of the
mode finds the fix commit reviewed and settles the job. Closing a real finding unfixed would lose
it.

## 8. Draft replies

One draft per item that gets one; on a later pass, posted drafts keep their numbers and files, and
new drafts take new numbers. The body goes in its own `reply-<nn>.md`; `replies.md` indexes
them, one line each: number, PR, surface, the id from step 1's record, the endpoint, and for an
off-PR thread its anchor — `path` and `line`, the `commit_id` being supplied when posted. What is
approved at step 9 is the body
file, and step 10 posts it unchanged.

`🤖 Claude: ` once at the top. Verdict in the first sentence, then what is confirmed, then the
correction, then the disposition. Concede before correcting. Never attribute a reversal to the
reviewer; when the sequencing was ours, say so.

- Cite a revision with every claim. The stack was finished before this step and step 10 rewrites
  nothing, so a SHA cited now is the one that will be on GitHub. Where the fix landed on a
  different PR
  from the one commented on — routine on a stack — say which, or the reviewer looks for the commit
  in the wrong PR.
- Use only labels the reviewer has seen — their own numbering is ideal; ids that exist only in our
  notes are jargon to them.
- Endpoints: an inline thread through
  `POST repos/<REPO>/pulls/<pr>/comments/<root id>/replies` — it rejects a
  reply-to-a-reply, and a reviewer's own comment *is* a reply whenever they answered inside a
  thread. A review body or a conversation comment has no thread; answer it with
  `POST repos/<REPO>/issues/<pr>/comments`, quoting enough to anchor it. Off-PR
  items become new threads per **Feedback that arrived off-PR**.
- **Feedback that came in through Reviewable** (a discussion that exists only in a Reviewable
  review body, with no GitHub thread) is answered the same way: a regular PR conversation comment
  quoting the discussion text, always. Never hand the user text to paste into Reviewable, and never
  leave such an item for the user to answer there. Reviewable will keep showing
  the discussion as open and "waiting on" us, and its resolutions never reach GitHub; both are the
  reviewer's to close, and the step 9 list may include one line asking them to.

**Then the PR descriptions.** The description is what the reviewer and the team review against.
A round that changes, adds or removes behaviour leaves it promising something the code no longer
does, and nothing else in this flow would notice. Per PR in the round **that we authored** (step
0's owner column — someone else's description is never edited), compare what the round changed
with what the description says. Where it now says something false, or leaves out behaviour the
round added, fetch the **live** description —
`gh pr view <pr> --json body --jq .body > <notes>/pr-body-<pr>-live.md` — not a copy from
memory or from an earlier round, since the user or a bot may have edited it since. Draft
`pr-body-<pr>-new.md` from it: correct and extend, never rewrite from scratch, and keep every block
that is not ours — the Reviewable block, anything the user wrote — byte-for-byte. The description
says what the PR does now, not how the round got there: "removed after review" belongs in a reply.
Where the round changes nothing the description describes, write that as one line in
`replies.md`, so the gate can say so.

**Then review the drafts adversarially, before they reach the gate.** Step 6 reviewed the code;
the replies are a second artifact, written last and under the same blind spots, and they go out
under the user's name. Hand every body, every `pr-body-<pr>-new.md` with its `-live` beside it, the
index and the step 9 presentation to a fresh reviewer
(an agent that did not write them) with the brief to break them: every claim in a new description
holds at the branch tip, and nothing outside our edits differs from the live text; every cited SHA exists on the
branch and does what the sentence says; every quoted symbol, constant, number and test exists and
behaves as claimed; every correction of the reviewer's mechanism is re-derived from the code at
the ref they read; every claim about another artifact — a ticket, a sibling PR, a doc page — is
read back from that artifact; the rules above (verdict first, concede before correcting, no
internal labels, the cost of a decline stated) hold; and the replies and descriptions agree with
each other and with the disposition table. A defect in a reply is fixed in the reply; a defect it exposes in the
code goes back to step 5 and through every step after it. Record the refuted objections and the
corrections in `verification.md`, the same way step 6's are. A draft the gate has not seen
reviewed is a draft the user approves blind.

## 9. STOP — present the changes and the drafts

Present per **Presenting a gate** below. Per item: disposition, fix, commit, branch. The contents of
`verification.md`. **What roborev raised and what you did about it**, from `roborev.md`: per
finding, the claim in plain words (without roborev, the one line saying it was not available) and whether it was fixed (which commit), declined (why), or
ruled by the user — the declines compactly, since the user reads this section to overrule you —
and, first, any pattern you named (a structural fix made in place of an instance, or a finding that
kept recurring) with what you did about it. An overruled finding reopens its job (`roborev close --reopen <id>`) and goes back to step 5. Every
conflict resolved by hand at steps 5–7: the saved diff, and
`git show <replayed commit> -- <file>` as the resolution. The **full reply texts** with
their targets, flagging each that refutes the reviewer, asks them for something, retracts something
already posted, announces a decline, or names a deferral with no ticket — those are the ones to
read word for word. **Each PR description to replace**: what changes in it —
`git diff --no-index --word-diff pr-body-<pr>-live.md pr-body-<pr>-new.md` — or the full new text
when it is short; and for each PR of ours whose description the round leaves accurate, one line
saying so. Then everything step 10 will do under the user's name, as a list they can
strike from: the branches to push — every branch we own that was touched, restacked, or carries
local-only commits, stack by stack — any branch of someone else's that now needs restacking by
its owner, each PR description to replace, the replies, any threads to open, whether to
re-request review, and any of our own threads to close.

Write the presentation and then the approval into `approval.md`, the approval **verbatim**. A
partial approval covers only what it names. Branches are named by stack: naming any branch names
every branch we own in its stack that was rewritten below it or restacked above it, because
pushing a child without its base — or a base without its restacked children — makes a PR display
another branch's commits as its own diff, and striking any one of them strikes the stack — a
strike beats a name. A PR names its branch. Replies may be named one by one or as "PR <n>'s
replies"; descriptions, threads, re-requests and closures one by one. Anything not named stays unpushed and
unposted. A reply that must change — because it cites something now unpushed,
or for any other reason — is re-presented, not reworded on the way out. Anything agreed in a
thread that belongs somewhere durable — an ADR, a standards entry — is proposed here, because
review threads die with the squash-merge; it is not committed silently after step 10.

## 10. Re-check, push, post

0. **Check the approval before anything else.** Open `approval.md` and read its last entry.
   Missing means stop and ask: a session running step 10 days later has no other record that
   this round was approved. Act only on what it names.
1. **Re-check the stack, without touching it.** The tree must be clean, and every branch we own
   above a changed one must sit on its base's tip — a plain read, no reflog involved:

   ```bash
   [ "$(git merge-base <base> <child>)" = "$(git rev-parse <base>)" ] \
     && echo "<child> sits on <base>" || echo "STOP: <child> does not sit on <base>"
   ```

   Every child must print the first message. A STOP means the stack moved since approval, and
   step 10 does not rebase: record it in `verification.md`, then back to step 5 and through
   every step after it, with a fresh approval entry at 9. This is the reason step 8 can cite
   SHAs: nothing in step 10 rewrites a commit.
2. **Push** every branch we own in every stack the approval names — never one of someone
   else's — bottom of the stack first, one command at a time:

   ```bash
   git -C <worktree> push --force-with-lease=<branch>:<pin> origin <branch>
   ```

   The pin is the row's `pin` column; after a successful push, overwrite it with the SHA you
   pushed, so a second pass through this step leases against it. Name the branch in the
   refspec: a push carrying only a lease flag pushes the **current** branch under
   `push.default=simple`, so the one you meant silently does not go and the one that does carries
   a lease naming a different ref. Keep the `git -C` form: paranext-core's settings ask on a
   bare `git push --force-with-lease…`, a prompt only a human can answer, which stalls this step.
   Never plain `--force` / `-f` / `+refspec`, and never a bare `--force-with-lease` — with no
   expected value it is checked against the remote-tracking ref, which the fetch at step 0
   already advanced. A rejected lease means one of two things: the row's pin was not overwritten
   after an earlier push this round — check that first — or someone else moved the branch. Never
   re-pin to the current remote, which is the defeated form; read the remote back and put it to
   the user as a new decision. A ruling to integrate or overwrite is step 5's, so it goes back
   there and through every step after it. A push with nothing to send does not evaluate the lease
   at all, so
   "Everything up-to-date" proves nothing about the pin. A force-push can dismiss approvals:
   compare `reviewDecision` against the row afterwards and note the result in `verification.md`.
3. **Replace the PR descriptions** the approval names — after the push, so a description never
   describes code that is not on the PR yet, and before the replies, which may point at it. First
   fetch the live description again and compare it with `pr-body-<pr>-live.md`. If it differs,
   someone edited it after the draft was made, and replacing it would silently discard their
   edit: stop, fold their change into the draft, and re-present it at 9. Otherwise:

   ```bash
   gh pr edit <pr> --body-file <notes>/pr-body-<pr>-new.md
   gh pr view <pr> --json body --jq .body | diff - <notes>/pr-body-<pr>-new.md
   ```

   `gh pr edit --body-file` can exit 0 and change nothing, so the read-back diff is the result,
   not the exit status: empty, a trailing newline aside, is a pass. It goes in `verification.md`.
4. **Post** — one comment at a time, no automatic retries, **spaced a second or two apart**, each
   body
   wrapped mechanically from its file and sent to the target its index line names; a new thread
   for an off-PR item adds the index line's `path` and `line` to the same payload, with
   `commit_id` set to that branch's remote head as read back after 10.2.
   Record each new comment's id on its index line as it lands, and on a second pass through this
   step post only lines that have none:

   ```bash
   jq -Rs '{body: .}' reply-<nn>.md | gh api --method POST <endpoint> --input -
   ```

   If a POST fails with `422` and `"code":"abuse"` in the body, that is the secondary rate limit
   and not a malformed body — however much "Validation Failed" invites it, do not edit a reply
   the user has already approved to get past it. Stop and read the live state back. An approved
   body that landed despite the failure gets its id written to its index line first, so it is
   not posted twice; every comment now on the PR that is *not* an approved body is a stray, and
   only an empty stray list licenses a re-post. A `gh` failure does **not** prove nothing was
   created.
5. **Read back** what landed and compare it against the body files. "Posted successfully" without
   a read-back is not a result. The comparison goes in `verification.md`.
6. **Watch CI to a conclusion.** A watcher must report every terminal state, treat an incomplete
   check list as incomplete rather than passed, and say whether it ended by completion or by its
   own timeout; the outcome goes in `verification.md`. Red means back to step 5 and through every
   step after it, with a fresh approval entry at 9 — and any posted reply whose cited commit that
   pass rewrote gets a follow-up draft naming the new one, since posted text is never edited.
   Green: where the approval named them, re-request review
   (`gh pr edit <pr> --add-reviewer <login>`) and close the threads *we* opened — by thread id,
   re-running step 1's query first so threads opened this round have one. Both outcomes go in
   `verification.md`.

**Do not resolve the reviewer's threads.** paranext-core's `.context/standards/Code-Review-Guide.md` does allow an
author to self-resolve items the reviewer marked *Discussing*; this flow declines that latitude on
purpose. Resolving someone else's thread by mistake is public and awkward, and leaving one open
costs nothing.

---

## Presenting a gate

Steps 4 and 9 are where a human decides. The notes are the evidence; the gate is the **ask**, and it
is read by someone who has not read the notes, has not read the reviewer's text, and has been
elsewhere while the run worked. Write every item as if that is literally true, because it is.

**A stop is a conversation, not a handoff.** Expect part of the plan to come back changed;
re-present what changed and stop again, until the user says it is settled. One presentation and
one answer is the lucky case, not the shape to design for.

**Every decision item carries four parts, in this order:**

1. **Context** — one or two plain sentences on what happened or what the reviewer said. This is the
   part that gets dropped, and dropping it is what makes a gate unanswerable.
2. **The question** — one interrogative sentence that can be answered as asked. A topic, a noun
   phrase, or "thoughts?" is not a question.
3. **Options** — lettered, one line each, each one a thing the user can say yes to by naming it,
   with the trade-off or pro/con that separates it from its neighbours when there is one.
4. **Recommendation** — which option and why, in a line, whenever you actually have one; design
   preferences included. When you are unsure, say "no recommendation" and why, rather than
   manufacturing one — a confident-sounding guess is worse than an honest blank. A cross-reviewer
   conflict is always a blank: say what each reviewer is owed under each option and state that you
   are not choosing.

At step 4 these four parts become the text of an `AskUserQuestion` item (see step 4); at step 9
they may be presented as prose or as an interview, whichever fits the number of decisions.

**Banned:** internal ids or labels as the *subject* of an item, reviewer shorthand, a bare file or
symbol name standing in for an explanation, and "as discussed" / "as above". An id may trail an item
as a pointer; it may never be the thing the reader has to decode first.

**Pure information is not a decision.** Facts worth carrying go under their own **"No decision
needed"** heading *after* the list. Mixed in, the user has to sort the list before they can answer
it, and the items needing an answer are the entire reason for stopping.

**The test:** read the item with only that message in front of you. Can you say what happened, what
is being asked, what the choices are, and what is recommended? **If the user has to ask "what are
you asking me?", the gate failed** — and a gate they cannot read is one they approve blind.

> **Bad** — every word of context lives somewhere the reader is not:
>
> 1. **R3-04 / the cache staleness — which option?** A, **B + A′ (recommended)**, or C. And: do the
>    XS logging fix regardless?

> **Good** — same item, self-contained:
>
> **A reviewer found that a value we cache is never invalidated when the user switches projects, so
> the second project can be shown the first project's data.** We reproduced it. The cache predates
> this PR — the bug is on `main` today.
>
> **Do we fix it here, or keep the PR to its stated scope and record the bug for you to place?**
>
> - **A.** Fix this instance here — contained, one file and a test, on the order of fifteen lines.
> - **B.** Keep this PR scoped, record the bug, and tell the reviewer that is what we did.
> - **C.** Fix the whole class of it here, not just this instance — substantially larger, and a
>   design change we would want the lead dev on.
>
> **Recommendation: B** — it ships on `main` today, so it is not a regression this PR introduces,
> and A adds an unrelated behaviour change to a round that is otherwise ready to land.

Note what those options do *not* say: how the cache gets invalidated. Each is a scope the user can
rule on, sized well enough to rule on it, and the mechanism is left to step 5 — which is the only
step that will have read the cache's call sites before choosing one.

## `--scout-only`, and running this as a routine

Runs **steps 0–3 and stops at gate 4 without waiting for an answer** — nobody is there to give one.
Read-only outside the notes directory, step 0's fetch aside: no commits, no pushes, no comments, no
app, no e2e. Step 1's roborev leftover check is included where roborev is available; step 6's settling is not.

That is the subset that is safe to schedule unattended — run to the gate, write the notes, stop, and
let a later interactive session pick it up. Since such a run cannot wait for anyone, its **digest is
the deliverable**: the run header (each PR, its branch and base state, every ref with its SHA), item
counts, and **the full gate-4 decision list in the form above** — written to `rulings.md` as the
presentation and also into the routine's own run log on claude.ai/code, not a pointer to notes the
user may never see.

Where a verdict genuinely turns on something scout mode may not do — running the app, running e2e —
state it **conditionally** and name the measurement exactly, rather than guessing or downgrading it
to "needs investigation". A conditional verdict is a decision item: the options are the branches of
the condition.

## `--verify-only`: verify a branch before its PR exists

```
/process-pr-feedback --verify-only <branch> [--base <base>] [--scenarios <path>]
```

Runs **step 0 reduced, then step 7, and nothing else**, on a branch that has no PR yet, and ends by presenting the table step 7
describes under **What gate 9 shows** — the checks, not a verdict — then stops. It exists so that
the verification a feedback round gets happens *before* a PR is opened as well: a build flow
verifies code against the tests it wrote and a reviewer's reading of the diff, and nothing in it
checks the feature against its requirement in the running app. paranext-core's `pr-creator` skill
runs this mode first, where the plugin is installed, and puts the table in the PR body; a human
can run it on any branch for the same reason. It is one entry point on this file, not a copy of step 7, so step 7
evolves once.

**What runs, and what does not.** Step 0 reduced to the one-row form its text describes, which
also fixes the base (`--base`, else `main`); then the scenario list below; then step 7 exactly as
written — the battery with the expected `papi.d.ts` delta stated before `build:types`, the whole
test suites capped, e2e for the area with the `--list` count, the live run per scenario with
evidence, `app-guard` before the app, `verification.md` as the ledger of every command with its
exit status and counts and of everything not run with the reason, a red test counting as
pre-existing only once shown red on the base, and roborev in the state step 7 describes for
this mode (its part of step 6 is the one piece of another step the mode runs). Steps 1–5 and 8–10
do not run: there is no feedback to read, nothing is implemented, nothing committed, nothing
pushed, no reply drafted, no comment posted. What the mode leaves behind: the notes directory,
named `<branch>-<YYYY-MM-DD>` as **Working notes** says; whatever the battery's builds write —
`buildInfo.json` is ignored by git; a changed `papi.d.ts` is a row and the caller's to commit, as
step 7 says; and roborev's local records — reviews queued for commits it had not seen, comments,
closed jobs. `<branch>` is checked out in the current checkout with a
clean tree, or the mode stops: step 0's checkout stops apply.

**Where the scenarios come from.** The normal flow takes its live-run scenarios from the
reviewer's items; this mode has none, so it takes them from the requirement:

- With `--scenarios <path>`, the file is the requirement — a design document, a plan, a ticket's
  text saved to a file. Each scenario is stated from what that text asks for.
- Without it, the requirement is the branch's ticket: the key from the branch name
  (`pt-4805-…` → `PT-4805`), read through the Atlassian MCP server where it is available. The
  source is the ticket's acceptance-criteria field where the project has one, else the section of
  its description headed "Acceptance", "Acceptance criteria" or the like, else the description's
  list of what the feature must do. Where the server is not available, or the branch name carries
  no key, or the ticket has none of those, ask the user for the requirement and **wait**, since a run with
  no requirement has nothing to verify against — never guess one, and never fall back to the
  diff. (Step 7's own stops — `app-guard`'s WAIT and ASK — and step 0's REPO rule apply as written.)
  Running as a sub-agent with no line to the
  user, return the question to the caller instead and stop; a caller that has the requirement
  passes it as `--scenarios <path>` on the next call.

**A scenario is stated from the requirement, never from the code.** A scenario written by reading
what the branch does — "the button appears", because the diff adds a button — passes by
construction and verifies nothing; a scenario written from what was asked — "a user with an
editable project sees the Sync item enabled; one with a resource sees it disabled" — can fail.
So write the list before reading the branch's diff: step 7's own reading of it (the `papi.d.ts`
delta, the e2e specs for the area) comes after the list is written down. A plan given as
`--scenarios` is read for what it says the feature must do, not for how it is built. Each
scenario records its source: the acceptance line or document sentence it comes from, quoted. A
refactor's requirement is that nothing changes, so its scenarios are the area's existing
behaviour as the ticket states it, and the live run is still required (step 7: every change that
reaches a runtime path). Only a change with no runtime path — docs, tests, comments — has no
scenario, and the live run is listed as not run for it, with that reason.

**Show the list before running step 7.** After step 0 and before step 7's first command, present
the scenarios — numbered, each with its quoted source, what will be done and what is expected to
be seen — and write the same into `findings.md`. This is so that a scenario nobody asked for
cannot masquerade as verification: the reader sees what was tested against what. With a user to
answer, present it as one `AskUserQuestion` — run as listed, or change it — and wait; the answer
goes into `rulings.md` verbatim, as step 4 does. Running as a sub-agent, in a routine, or anywhere
no one can answer, show the list, run, and let the table at the end repeat it; a scenario struck
afterwards stays in the table **marked struck**, with who struck it and why, its evidence kept —
it is never removed, since a struck failure that vanished would be a table that lies; one added
afterwards is run live on its own by the same session, once it has re-checked that `headRefOid`
and the clean tree are unchanged, with its evidence added — that re-run covers only the added
scenarios. Anything that moved the tip since the table — a fix, the `papi.d.ts` commit — makes it
the full re-run instead, which is what a fresh invocation always is.

**How it ends.** The table under **What gate 9 shows**, per row of step 0's table: each command
with its exit status and its counts; the papi delta stated and observed; each e2e subset with its
listed count; the live run per scenario with its evidence (a screenshot, the PAPI response, the
log lines — "verified live" without evidence is not a row); roborev's state in one line, its
declines compactly, and a row per real finding it left open; and everything not run, with the
reason. Rows that failed are stated as found — the mode never fixes, and never softens a red row
into a note. "Everything green" is the headline only when every row says so and no roborev
finding is open. Then stop. The caller — the `pr-creator` skill, or the user — decides what the table
means.

## Feedback that arrived off-PR

A document or a DM answered in kind keeps the conversation off the PR, and the next reader of the
code sees none of it. Convert it instead: at step 8, draft each off-PR item as a new review thread
anchored on the code it is about — `POST repos/<REPO>/pulls/<pr>/comments` with
`commit_id`, `path` and `line`. They are presented at step 9 with the replies and posted at 10.4
with them.

Anchor at the docblock or declaration the question is about, not an arbitrary line inside an
implementation. Verify each anchor resolves at the PR head before posting. Each thread must stand
alone: someone opening it cold sees the code, the question, and what we propose — never "see the
doc".
