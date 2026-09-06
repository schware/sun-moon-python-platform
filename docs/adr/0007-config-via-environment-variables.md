*🇰🇷 한국어 버전: [0007-config-via-environment-variables_kr.md](0007-config-via-environment-variables_kr.md)*

# ADR-0007: Configure services via environment variables (+.env), not a shared YAML

- **Status**: Accepted (Supersedes: the first draft's single
  `config/app.yaml` file approach)
- **Date**: 2026-09-06
- **Deciders**: Claude (design proposal, a follow-on to adopting ADR-0005)

## Context

In the modular-monolith draft, everything (HTTP/TCP/UDP ports, DB URL, AI
provider, the list of modules to load) lived in one `config/app.yaml` —
a natural choice when there was only one process. Once ADR-0005 split
things into multiple processes, keeping that approach would mean multiple
services awkwardly reading slices out of one shared YAML.

## Decision

Each service inherits its own settings class from
`netframework_core.config.BaseServiceConfig` (a pydantic-settings
`BaseSettings`) — `order_service.config.OrderServiceConfig`,
`ai_agent_service.config.AiAgentServiceConfig`. Values are read from
environment variables plus a local `.env` file. Each service directory
ships a `.env.example` documenting which variables it needs.

## Alternatives considered

- **Keep a shared YAML, split into per-service sections** — convenient for
  seeing the whole picture in one file, but once services are deployed
  independently (separate containers/servers), that YAML would still need
  to be split apart for deployment anyway, so the convenience disappears.
  It also risks accidentally changing another service's config while
  deploying one.
- **Per-service YAML files (instead of env vars)** — fine for local dev,
  but container orchestration (Docker Compose/Kubernetes) standardly deals
  in environment variables, so env vars were prioritized to reduce friction
  with the deployment pipeline.

## Consequences

- `docker-compose.yml`'s `environment:` block becomes each service's
  config source directly — no separate config mount or templating engine needed.
- Running multiple services locally in one terminal session's habits
  (global env pollution) risks variables bleeding across services —
  mitigated in README/CONTRIBUTING by showing inline per-service env vars
  in run examples (`REDIS_URL=... uv run --package order-service ...`).
- Config values are now scattered (`order-service/.env.example`,
  `ai-agent-service/.env.example`) — seeing "the entire config surface" at
  a glance is less convenient than before. Worth revisiting as the number
  of services grows.

## References

- Adam Wiggins (Heroku), *The Twelve-Factor App*, specifically "III.
  Config: Store config in the environment" — the direct basis for this decision.
- pydantic-settings official documentation — how `BaseSettings` reads
  environment variables together with a `.env` file.
