---
name: changelog
description: Write the forum changelog in French BBCode for the geekattitude.org announcement thread. Given a commit (the version currently live), summarises everything merged to main since it. Use when the user asks for a changelog or release notes.
argument-hint: "<commit SHA live before this deploy> [target ref — defaults to origin/main]"
disable-model-invocation: true
---

# Changelog (French BBCode)

The user gives a commit: what was live **before** this deploy. Write the
changelog of everything after it, for members of the forum (not developers).

## 1. Collect

1. `git fetch origin main`.
2. `FROM` = the given commit (check it is an ancestor of the target:
   `git merge-base --is-ancestor <FROM> <TO>`; stop and say so if not).
   `TO` = the second argument, else `origin/main`. Use short SHAs in text.
3. `git log --no-merges --format='%h %s' FROM..TO`. Read the diff or PR
   (`gh pr view`, or `git show --stat`) when a subject is unclear. Use the
   ancestry range, not commit dates: dates can be out of order.
4. Version line: the short SHA of `TO` and its PR (`gh pr list --state merged
   --search <sha>` or the merge commit subject), plus today's date as
   `dd/mm/yyyy`. Don't claim it is deployed or give a time unless the user
   said so.

## 2. Write

Output one BBCode block in a code fence, in French, in exactly this layout:

```
[center][size=22][b]Changelog[/b][/size][/center]

[b]Version en ligne :[/b] <sha> (PR #<n>), déployée le <dd/mm/yyyy>.

[size=18][b]🔒 Sécurité[/b][/size]
[list]
[*] ...
[/list]
```

- Sections, in this order, each only if it has items: `🔒 Sécurité`,
  `📊 Sondages` (or another feature area when one clearly dominates),
  `🐛 Corrections de bugs`, `✨ Nouveautés`, `🌙 Apparence (thème sombre)`,
  `⚙️ Infrastructure`.
- One short sentence per item, past or present tense, ending with a period,
  describing the effect for a member. Merge related commits into one item.
  Keep issue numbers like `(#62)` only when useful.
- Leave out purely internal commits: merges, image maintainer or label
  tweaks, cache-busters on their own (fold them into the feature they
  serve), refactors with no visible effect (one line under Infrastructure at
  most).
- No `[spoiler]` "Prochainement" block unless the user asks for pending
  changes; then list `TO..origin/main` there, under
  `[b]Prochainement (sur main, pas encore en production) :[/b]`.

## 3. Report

After the block, add one or two lines in French, only if needed: commits you
were unsure about or left out, or items that may already have been live.
