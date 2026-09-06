*🇰🇷 한국어 버전: [0005-monorepo-of-independent-services-via-uv-workspace_kr.md](0005-monorepo-of-independent-services-via-uv-workspace_kr.md)*

# ADR-0005: Structure as a monorepo of independently deployable services (uv workspace) — replacing the earlier "modular monolith"

- **Status**: Accepted (Supersedes this project's first draft structure —
  never committed, so it doesn't get its own ADR; summarized in "Context" below)
- **Date**: 2026-09-06
- **Deciders**: Project owner (explicit choice, see below)

## Context

User request #4: "please set direction for extensibility and common module
orientation so multiple developers can use it later." That sentence alone
could mean either "multiple people share one process, split into modules"
or "multiple people each own an independently deployed service."

Claude first implemented a **modular monolith**: one FastAPI process,
sharing an in-memory event bus/tool registry through an `AppContext`, with
a plugin registry loading bounded contexts from `config/app.yaml`'s
`modules:` list. The user then asked "is this actually structured as a
monorepo?" Claude explained the difference between the two concepts
(modular monolith vs. a real monorepo) and presented three options via
`AskUserQuestion`: (1) keep the modular monolith, (2) convert to a real
monorepo (multi-service), (3) merge with the C project into one git
repository. **The user explicitly chose (2).**

## Decision

- Split into `libs/` (shared libraries: `netframework-core`,
  `netframework-comms`, `netframework-ai-agent`, `netframework-contracts`)
  and `services/` (independently deployable units: `order-service`,
  `ai-agent-service`).
- Use **uv** as the workspace manager — the root `pyproject.toml` holds
  only `[tool.uv.workspace] members = ["libs/*", "services/*"]` (a virtual
  root, no code of its own), and each service references local libs via
  `[tool.uv.sources]`'s `{ workspace = true }`.
- **Services never import each other's code.** This is the core rule that
  separates "monolith" from "monorepo." How services connect is covered in ADR-0006.

## Alternatives considered

- **Keep the modular monolith** — had the advantage of zero operational
  complexity (no service discovery, network latency, or distributed
  transactions), but this alternative was rejected once the user chose "a
  real monorepo." (Kept here because it remains a reasonable choice for an
  early stage with few teams/services and no need to deploy separately —
  worth returning to via a new ADR if circumstances change.)
- **Poetry monorepo plugin** — an older approach in the Python ecosystem,
  but native workspace support is weak (depends on a third-party plugin)
  and installs more slowly than uv.
- **Fully separate repos per service (polyrepo)** — advantageous when teams
  are genuinely separate with different release cadences, but at this
  stage (a) there are few services and (b) shared contracts
  (`netframework-contracts`) will likely need frequent atomic
  review/changes together, favoring a monorepo for now.
- **General-purpose monorepo build tools (Nx/Turborepo/Bazel)** — mostly
  JS-ecosystem-centric or carry heavy setup cost. uv, being Python-native
  with a lightweight model similar to Cargo workspaces, fits this scale better.

## Consequences

- Running services locally now needs at least 2 processes (+ Redis) —
  mitigated with `scripts/dev_redis.py` so Docker isn't required, but the
  "just run one thing" bar is higher than the monolith was.
  `CONTRIBUTING.md` walks through this step by step.
- A PR changing `libs/netframework-contracts` effectively affects multiple
  services at once — this is exactly why ADR-0001 requires an ADR for
  shared-library changes.
- Adding another service (see README's "Adding a new service") requires no
  edit to any root config file — the `services/*` glob picks it up automatically.
- Docker Compose was written for this structure, but **this dev environment
  has no Docker, so `docker compose up --build` was never actually
  build-tested** — end-to-end verification only used uv-based local
  execution (including fakeredis). Needs re-verification the first time
  someone runs it under Docker.

## References

- uv official documentation, *Workspaces* — the basis for the
  `[tool.uv.workspace]`/`{workspace = true}` mechanism.
- Rachel Potvin & Josh Levenberg (Google), *Why Google Stores Billions of
  Lines of Code in a Single Repository*, CACM (2016) — a canonical case for
  the "atomically review shared code from one repository" monorepo argument.
- This conversation's `AskUserQuestion` response — the direct basis for
  this decision is **the user's explicit choice**, more than any literature.
