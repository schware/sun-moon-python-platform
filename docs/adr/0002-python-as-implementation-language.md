*🇰🇷 한국어 버전: [0002-python-as-implementation-language_kr.md](0002-python-as-implementation-language_kr.md)*

# ADR-0002: Use Python (3.11+) as the implementation language

- **Status**: Accepted
- **Date**: 2026-09-06
- **Deciders**: Project owner (explicit user request)

## Context

The previous day's work (`../C`) was a libuv-based C server framework.
Today's request was the user's explicit instruction to "build a
Python-based framework," with additional conditions: integrate DDD
concepts, include an AI Agent, aim for extensibility/common modules multiple
developers can use, and open-source use is permitted.

## Decision

Adopt Python 3.11+ as the implementation language. This machine also has
Anaconda Python 3.8, but 3.8 doesn't support `X | None` type hints,
`list[T]`/`dict[K, V]` builtin generics, or the modern typing features
pydantic v2 requires — WSL's Python 3.12 is used as the dev/test baseline
(see README "Quick start").

## Alternatives considered

- **Keep using C** — already done yesterday, and the user explicitly asked
  for a different language. The DDD/AI-Agent ecosystem (SQLAlchemy,
  FastAPI, Anthropic SDK, etc.) essentially doesn't exist for C, meaning
  everything would need to be hand-rolled.
- **TypeScript/Node.js** — strong for the comms layer (async I/O), but the
  user explicitly specified "Python-based," so this was out of scope.
- **Go** — common for microservices, but likewise diverges from the user's
  explicit choice.

## Consequences

- Gets to reuse a mature open-source ecosystem (FastAPI/SQLAlchemy/
  Pydantic/Anthropic SDK), matching request condition #5.
- This code does **not** run on Python 3.8 (Anaconda, this machine's
  default `python`) — a developer who accidentally uses the older
  interpreter gets an immediate error at pydantic model definition time.
  `CONTRIBUTING.md` calls out the version check explicitly to guard against this.
- The GIL means no true parallelism for CPU-bound work — the assumption is
  that this framework's actual workload (I/O-heavy: HTTP/TCP/DB/Redis/LLM
  calls) is well served by a single-threaded asyncio event loop. If a
  CPU-bound need shows up later, a separate ADR should evaluate a process
  pool or an offload service in another language.

## References

- User instruction (2026-09-06 conversation: "오늘은 python 기반의
  framework를 만들어 볼려고해요")
- PEP 604 (`X | Y` union syntax, 3.10+), PEP 585 (built-in generic
  collections, 3.9+) — the minimum-version basis for the type-hint syntax
  used throughout this codebase.
