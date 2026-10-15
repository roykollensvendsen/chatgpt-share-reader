# ADR-CSR-003: How a change is made here

## Status

Accepted by Roy Kollen Svendsen, 2026-10-15.

## Context

The repository has one maintainer who works mostly through coding agents. The failure that
started it was an agent that took a plausible conclusion ("only the last message is on the
page") for a fact. The process has to make that kind of mistake hard to repeat, without
ceremony that one person would stop following.

## Options considered

- **Push to `main` directly.** This is fastest, but nothing runs before a change lands, and
  `CONTRIBUTING.md` would claim gates that nothing enforces.
- **Pull requests with squash merges.** These keep the history tidy, but they lose the
  individual commits that explain each step.
- **Pull requests that land by rebase, with protected `main` and required checks.** This is
  the option chosen.

## Decision

Every change goes through a pull request, and the checks must be green before it lands. It
lands by rebase, so every commit has to stand alone. A rule in the reader is a line marked
`# RULE:`, with a row in `scripts/mutations.toml` and a test named after it, so that switching
the rule off is shown to turn its test red. A change to the reader is copied into the skill
folder in the same commit (ADR-CSR-001). A change prompted by a new page format comes with a
change to the synthetic page that reproduces the new shape (ADR-CSR-002).

## Consequences

- A one-line fix still needs a branch, a pull request and a green run, which is slow for a
  tiny project.
- The forge settings that enforce this live outside the tree, so they are applied by
  `forge.py` from the `start-repo` skill rather than by anything the tests can see.
- A lesson learned from a failure belongs in `SKILL.md`, at the step it concerns. That is
  where the next agent will read it.

## Related

- [`CONTRIBUTING.md`](../CONTRIBUTING.md)
- [ADR-CSR-001](ADR-CSR-001-the-skill-ships-a-copy-of-the-module.md),
  [ADR-CSR-002](ADR-CSR-002-tests-use-a-synthetic-share-page.md)
