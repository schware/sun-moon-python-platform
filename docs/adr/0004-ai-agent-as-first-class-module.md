*🇰🇷 한국어 버전: [0004-ai-agent-as-first-class-module_kr.md](0004-ai-agent-as-first-class-module_kr.md)*

# ADR-0004: Integrate the AI Agent as a provider-agnostic tool-calling loop, in its own service

- **Status**: Accepted
- **Date**: 2026-09-06
- **Deciders**: Project owner (explicit request) + Claude (design proposal)

## Context

User request #3: "I'd like an AI Agent included." The requirement itself
only said to add AI functionality — the concrete design (which LLM, how it
connects to the domain) was left to Claude to decide.

## Decision

1. **Abstract the provider.** Behind an `LLMProvider` protocol
   (`complete(messages, tools) -> AgentResponse`), there are two
   implementations: `EchoProvider` (offline, no API key, deterministic —
   for tests/demos) and `AnthropicProvider` (real Claude, lazily imports
   the `anthropic` SDK as an optional extra). Which one runs is chosen by
   an environment variable (`AI_PROVIDER`) — switchable with no code change.
2. **One agent loop.** (`netframework_ai_agent.base.Agent.run`) — the
   "think → optionally call a tool → feed the result back and think again →
   final answer" loop is separated from the provider, so the same loop is
   reused no matter which provider is plugged in.
3. **The AI Agent lives in its own service (`ai-agent-service`)** — it
   never imports Order's domain code. Instead: (a) synchronous reads go
   through order-service's public REST API over HTTP, (b) asynchronous
   notification is a subscription to the `OrderCreated` integration event
   over Redis. (This is entangled with the monorepo/comms decisions —
   see ADR-0005/0006.)
4. **Each service registers its own tools.** Any service that wants to
   expose a capability the way order-service does builds a `ToolSpec` for
   it. The AI Agent service never needs to know in advance what tools exist.

## Alternatives considered

- **Use an off-the-shelf agent framework (LangChain/LangGraph)** — rich in
  features, but (a) a heavy dependency, and (b) given the "extensibility /
  common modules for multiple developers" requirement, this project itself
  is meant to become the shared foundation — so a hand-rolled minimum
  footprint was preferred over deep coupling to an external framework. If
  the project grows, `netframework-ai-agent`'s internals could still be
  swapped for LangGraph etc. later — as long as the Provider/Agent
  interfaces are preserved, no service code needs to change.
- **Embed AI directly inside the Order service (same process)** — simpler,
  but doesn't fit a future where "many domains exist, one AI assistant"
  is the shape, and mixes LLM call latency (seconds) into order-processing
  latency.
- **gRPC instead of REST from the start** — worth considering for real
  production, but at this stage REST (verifiable directly with curl) was
  judged better for debugging/onboarding.

## Consequences

- The `echo` provider does no real reasoning — it verifies the "plumbing"
  in demos/tests, but whether the AI actually gives a smart answer can only
  be checked by switching to the `anthropic` provider. **This has not been
  verified against the real Claude API** — no API key was available in this
  environment, so end-to-end testing only used `echo`.
- The tool-call convention (`call:<tool> {json}`) is an EchoProvider-only
  stand-in — the real Anthropic provider uses actual `tool_use` blocks and
  is unrelated to this convention. This asymmetry is called out in code
  comments/README since it could otherwise be confusing.
- `max_tool_iterations` prevents an infinite loop, but there are no
  production safety nets yet (retry/backoff/cost limits) — needed before
  taking real traffic (candidate for a future ADR).

## References

- Anthropic, official *Tool use (function calling)* documentation — the
  basis for the tool_use/tool_result message shapes
  (`AnthropicProvider`'s message-conversion logic follows this spec).
- The ReAct pattern (Yao et al., *ReAct: Synergizing Reasoning and Acting
  in Language Models*, 2022) — the conceptual origin of the "think → act
  (tool call) → observe → think again" loop.
