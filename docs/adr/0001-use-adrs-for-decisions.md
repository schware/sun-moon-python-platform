*🇰🇷 한국어 버전: [0001-use-adrs-for-decisions_kr.md](0001-use-adrs-for-decisions_kr.md)*

# ADR-0001: Record architecture/direction decisions as ADRs

- **Status**: Accepted
- **Date**: 2026-09-06
- **Deciders**: TBD (currently a single project owner — update this field once more people join)

## Context

Most of this project's initial design and implementation was written by
Claude (AI). The project owner asked to have the reasoning behind Claude's
choices recorded, so it can be reviewed and redirected later. Multiple
people/teams are also expected to join this codebase going forward. Without
somewhere to record the "why" that isn't visible from the code alone:

- the same debates get re-litigated,
- new joiners copy existing patterns just because "that's how it's already
  written" without knowing why,
- Claude or a human ends up re-trying an alternative that was already
  considered and rejected.

## Decision

**Any decision that affects the architecture gets a
`docs/adr/NNNN-title.md` file.** Format follows `0000-template.md`
(Context/Decision/Alternatives considered/Consequences/References). The
decisions already made earlier in this project were written retroactively
as ADR-0002 through 0008 — a post-hoc record of what Claude actually based
those calls on at the time.

**This process itself is the answer to "how do we set new ground rules"**:

1. Write a new `docs/adr/000N-title.md` (Status: Proposed).
2. Discuss it with the owners of the affected services/libraries (see `CODEOWNERS`).
3. Once agreed, change Status to `Accepted`. If it conflicts with an
   existing ADR, change that ADR's Status to `Superseded by ADR-000N` —
   **without deleting its content**.
4. If code/README/CONTRIBUTING now disagrees with the decision, fix them in
   the same change.

Even reversing an earlier decision means writing a *new* ADR, not editing
the old file — that way both "why we didn't do it that way before" and "why
it changed now" stay on record.

## Alternatives considered

- **Write everything into one README** — convenient short-term, but as
  decisions pile up it becomes unclear which paragraph is a currently-valid
  decision and which is a leftover trace of an old one.
- **Rely on commit messages only** — poor discoverability (has to be dug
  out of `git log`), and this wasn't even a git repository yet at the time.
- **Keep no record at all** — the user explicitly said this wasn't what
  they wanted.

## Consequences

- One file per decision — more decisions means more files, but each file
  stays short and single-purpose, so it's easy to find and review.
- Without the habit, ADR-writing can lapse quickly. `CONTRIBUTING.md` puts
  minimal teeth into it: "changing a shared library (`libs/`) or a
  cross-service contract (`libs/netframework-contracts`) requires an ADR."
- This repo has no CI yet, so nothing automatically blocks "merged without
  an ADR" — that's on human reviewers for now (future work).

## References

- Michael Nygard, *Documenting Architecture Decisions* (2011) — the
  original source of the ADR format, since treated as near-industry-standard
  after ThoughtWorks Tech Radar recommended "Adopt."
- AWS Prescriptive Guidance, *Architecture decision records (ADRs)* — a
  practical guide to running the same pattern at an organizational scale.
