---
name: Issue
about: Bug, defect or improvement, with a severity prefix in the title
title: "[Severity] Short description of the defect"
labels: bug
---

<!-- Title: replace [Severity] with one of Critical, High, Medium, Low.
     Critical = data loss or corruption; High = wrong content shown to users;
     Medium = robustness, security or tooling; Low = polish, edge cases, hygiene. -->

## Problem

<!-- What is wrong, with file:line references (`app/forum/models.py:12-20`). Use a list for several related defects. -->

## Why it matters

<!-- The user-visible or data impact. If reasoned from code and not reproduced, say so. -->

## Proof

<!-- Optional. Command and output from a scratch copy of the database, or a failing test. -->

## Proposed fix

<!-- Concrete steps or a short snippet. Name the existing function to reuse if there is one. -->

## Acceptance criteria

- [ ] <!-- Observable behaviour that proves the fix -->
- [ ] The CI test suite (`.github/workflows/test.yml`) passes.

## Recommended model

**Claude Haiku 5.5 | Claude Sonnet 5.5 | Claude Opus 5.5** — one line on why this size of model fits.

---
From <!-- where this came from, e.g. "the code review at commit `abc1234`" -->. No real user data (names, emails, posts, IPs) is included.
