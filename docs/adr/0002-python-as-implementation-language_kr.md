*🇬🇧 English version: [0002-python-as-implementation-language.md](0002-python-as-implementation-language.md)*

# ADR-0002: 구현 언어로 Python(3.11+)을 쓴다

- **Status**: Accepted
- **Date**: 2026-09-06
- **Deciders**: 프로젝트 오너 (사용자 명시적 요청)

## Context (배경)

전날 작업(`../C`)은 libuv 기반 C 서버 프레임워크였다. 오늘 요청은 "python
기반의 framework를 만들어보자"는 사용자의 명시적 지시였고, 추가로 DDD 개념
통합, AI Agent 포함, 여러 개발자가 쓸 수 있는 확장성/공통 모듈 방향, 오픈소스
활용 허용이 조건으로 붙었다.

## Decision (결정)

Python 3.11+ 를 구현 언어로 채택한다. 이 머신엔 Anaconda Python 3.8도 있지만,
`X | None` 타입 힌트, `list[T]`/`dict[K, V]` 제네릭, pydantic v2가 요구하는
최신 타이핑 기능 때문에 3.8은 부적합 — WSL의 Python 3.12를 개발/테스트
기준으로 삼는다 (README "Quick start" 참고).

## Alternatives considered (검토했던 대안)

- **C 계속 사용** — 어제 이미 했고, 사용자가 명시적으로 다른 언어를 요청함.
  DDD/AI-Agent 생태계(SQLAlchemy, FastAPI, Anthropic SDK 등)가 C엔 사실상 없어
  전부 직접 구현해야 했을 것.
- **TypeScript/Node.js** — 통신 계층(비동기 I/O)엔 강점이 있지만, 사용자가
  명시적으로 "python 기반"을 지정했으므로 검토 대상에서 제외.
- **Go** — 마이크로서비스에 흔히 쓰이지만 마찬가지로 사용자 지정과 다름.

## Consequences (결과 / 트레이드오프)

- FastAPI/SQLAlchemy/Pydantic/Anthropic SDK 등 성숙한 오픈소스 생태계를 그대로
  활용 가능 (요청 조건 5번과 부합).
- Python 3.8(Anaconda, 이 머신의 기본 `python` 명령)로는 이 코드가 동작하지
  않는다 — 개발자가 실수로 구버전 인터프리터를 쓰면 pydantic 모델 정의 단계에서
  바로 에러가 난다. `CONTRIBUTING.md`에 버전 확인 절차를 명시해 대비한다.
- GIL 때문에 CPU-bound 작업의 진짜 병렬성은 얻기 어렵다 — 이 프레임워크가
  다루는 워크로드(I/O 위주: HTTP/TCP/DB/Redis/LLM 호출)엔 asyncio 단일 스레드
  이벤트 루프로 충분하다는 전제. CPU-bound 작업이 필요해지면 별도 ADR로
  프로세스 풀/다른 언어 서비스를 검토해야 한다.

## References (근거 자료)

- 사용자 지시 (2026-09-06 대화: "오늘은 python 기반의 framework를 만들어
  볼려고해요")
- PEP 604 (`X | Y` 유니온 문법, 3.10+), PEP 585 (제네릭 내장 컬렉션, 3.9+) —
  이 코드베이스가 광범위하게 쓰는 타입 힌트 문법의 최소 버전 근거
