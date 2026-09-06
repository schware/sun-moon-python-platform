*🇰🇷 Korean version: [0009-pivot-framework-to-platform_kr.md](0009-pivot-framework-to-platform_kr.md)*

# ADR-0009: Pivot the project's identity from a Framework to a Platform

- **Status**: Proposed — the repositioning itself is settled; the concrete
  component topology is a deliberately ongoing direction-setting process
  (see "Open questions" below), not a gate blocking further work
- **Date**: 2026-09-06
- **Deciders**: Project owner (explicit confirmation in this conversation)

## Context

Through ADR-0002–0008, this project was framed as a **Framework**: a
shared kernel (`libs/*`) that other developers build bounded-context
*services* on top of, with `order-service`/`ai-agent-service` as the
worked example of that pattern.

In this conversation, the user proposed a different shape entirely:

```
Platform
├── Core Runtime (Go)
├── Agent Runtime (Python)
├── Domain SDK (Python)
├── Transport Layer (Go)
├── Event Bus (Go)
├── Dashboard (TypeScript)
└── CLI (Go)
```

Claude asked two clarifying questions about this diagram (still open, see
below) and separately noted that this shape reads less like "a framework
with two example apps on it" and more like an infrastructure **Platform** —
comparable to how Temporal, NATS, or Kubernetes are structured (a core
engine + one or more SDKs + a CLI + an operational Dashboard, all treated
as the product itself). The user confirmed explicitly: yes, the direction
is moving from Framework to Platform.

## Decision

Record the repositioning itself now, while the concrete architecture is
still being worked out, so the shift in framing doesn't get lost or
re-litigated later. Specifically:

- **What counts as "the product" changes.** Under the Framework framing,
  `order-service`/`ai-agent-service` were the product (example bounded
  contexts) and `libs/*` was supporting infrastructure underneath them.
  Under the Platform framing, this flips: the Core Runtime, Domain SDK,
  Event Bus, Transport Layer, Dashboard, and CLI *are* the product.
  `order-service`-style business logic becomes something built **on** the
  Platform — a reference implementation/example, not part of the Platform itself.
- This ADR does **not** yet decide the Go/Python/TypeScript Polyglot split,
  nor whether Core Runtime/Transport Layer/Event Bus are three
  independently deployable services or three internal modules of one Go
  process. Those are separate, still-open decisions (tracked below) and
  belong in a follow-up ADR once resolved.

## Open questions — ongoing direction-setting, not one-time gates

The project owner is deliberately treating these as a continuing line of
inquiry rather than decisions to force closed right now. The working style
for this project is additive: Claude builds a piece, the owner reflects on
it and layers something onto it, repeat — so none of the three below need
an answer before more of the Platform gets built. They're tracked here so
the reasoning trail survives between sessions, and revisited/refined as
that additive process continues, not resolved in one sitting.

1. **Are Core Runtime, Transport Layer, and Event Bus three independently
   deployable services, or three internal modules inside one Go
   binary/process?** This is the single biggest lever on how much this
   pivot actually raises operational complexity — three separately
   deployed Go services is a very different management burden than one Go
   process internally organized into three modules.
2. **Is Domain SDK a library or a service?** The owner is exploring a
   candidate lens for this, first raised 2026-09-06: a Library is
   something *you call*; a Service is something that *calls you*. Worth
   noting out loud that this framing maps closely to the classic
   **Library vs. Framework** distinction (Inversion of Control — "you call
   a library; a framework calls you"), which is a different axis from the
   usual **Library vs. Service** distinction (process/deployment boundary
   — does it run inside your process, or its own). Domain SDK may need an
   answer on both axes independently, and could plausibly end up a hybrid
   (an outbound call surface that behaves like a library, plus an inbound
   callback/event surface that behaves more like a framework calling back
   into consumer code). Not decided — first day of thinking about it, no
   rush to decide.
3. **What should the Go/TypeScript Polyglot split look like?** Per the
   owner's correction (2026-09-06): this isn't a confirmed-vs-exploratory
   binary — it's an ongoing direction-setting process. What this ADR
   actually settles is the *Framework → Platform* repositioning (see
   Decision above); the concrete language split is something to keep
   shaping over time as pieces get built and added to, not a pending yes/no.

## Consequences (once this ADR is Accepted)

- `README.md`/`README_kr.md` and `CONTRIBUTING.md`/`CONTRIBUTING_kr.md`
  need rewriting: "a Framework two example services sit on" language stops
  being accurate — they'll need to describe a Core Runtime, an SDK,
  a CLI, and a Dashboard as the actual deliverables.
- The individual → team → project scaling model from
  [ADR-0005](0005-monorepo-of-independent-services-via-uv-workspace.md)/[CONTRIBUTING.md](../../CONTRIBUTING.md)
  still applies, but "a team owns a service" reframes to "a team owns a
  Platform component" — `CODEOWNERS` will need updating once the component
  list is final.
- `order-service`/`ai-agent-service` likely get relocated (e.g. into an
  `examples/` directory) once the actual Platform core exists, so it's
  clear they're built on the Platform rather than being the Platform.
- Cross-language contracts (once/if Go and TypeScript components exist)
  can no longer rely on pydantic models as the source of truth — this
  will very likely require its own ADR superseding parts of
  [ADR-0006](0006-inter-service-communication-http-and-redis.md).

## References

- This conversation — the direct source of this decision (the user's
  explicit confirmation: "저는 Framework에서 Platform으로 방향성을 고쳐가고
  있어요").
- Structural precedent for "core + SDK(s) + CLI + Dashboard" as a Platform
  shape: Temporal, NATS, Kubernetes, and most HashiCorp products all follow
  this pattern — cited here as the shape being aimed at, not as a
  commitment to copy any of their specific architectures.
