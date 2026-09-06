*🇬🇧 English version: [CONTRIBUTING.md](CONTRIBUTING.md)*

# 기여 가이드 — 사람이 직접 이 코드에 손댈 때

이 문서는 "Claude 없이 내가 직접 코딩해야 할 때"를 대비해서 쓴다. 왜 이렇게
구성됐는지의 근거는 [`docs/adr/`](docs/adr/)에 있고, 여기서는 "실제로 뭘
어디에 어떻게 짜야 하는가"에 집중한다.

## 0. 시작 전 확인할 것

- **Python 3.11 이상.** `python3 --version`으로 확인. 이 프로젝트를 만든
  머신은 기본 `python`이 Anaconda 3.8이라 그대로는 동작하지 않는다(pydantic
  모델 정의 단계에서 바로 에러) — WSL의 `python3.12` 같은 걸 써야 했다
  (근거: [ADR-0002](docs/adr/0002-python-as-implementation-language_kr.md)).
- **[uv](https://docs.astral.sh/uv/)** 설치돼 있는지: `uv --version`.
  없으면 `pip install uv`.
- 처음이라면 루트에서 `uv sync --all-packages --extra dev` 한 번 — 이후엔
  `services/*/pyproject.toml`을 바꿀 때만 다시 실행하면 됨.

막히면: [README_kr.md](README_kr.md)의 "Quick start"가 실제로 실행 가능한
명령어 시퀀스를 담고 있다(이 저장소를 만들면서 직접 실행해 검증함).

## 1. 코드가 어디로 가야 하는지 결정하는 법

```
이 변경이...
├─ 한 서비스 안에서 끝나는가?
│   ├─ 비즈니스 규칙(불변식, 상태 전이) → services/<x>/domain/
│   ├─ 유스케이스 흐름(트랜잭션 경계, DTO 변환) → services/<x>/application/
│   ├─ DB/외부 API 접근 → services/<x>/infrastructure/
│   └─ REST/TCP 등 프로토콜 핸들러 → services/<x>/interfaces/
├─ 여러 서비스가 똑같이 필요로 하는 재사용 코드인가?
│   → libs/netframework-core (설정/로깅/DDD 기반형/DB/이벤트버스),
│      libs/netframework-comms (프로토콜 어댑터),
│      libs/netframework-ai-agent (에이전트 루프)
│   ⚠️  libs/ 변경은 모든 소비 서비스에 영향 → ADR 필요 (CODEOWNERS 참고)
├─ 서비스 간에 주고받는 새 이벤트/DTO인가?
│   → libs/netframework-contracts에 pydantic 모델 추가
│   ⚠️  이것도 ADR 필요 — 계약이 깨지면 다른 서비스가 조용히 망가진다
└─ 새로운 bounded context(도메인) 전체인가?
    → services/<new-service>/ 새로 생성. README.md "Adding a new service" 참고
```

의존 방향 규칙(어기면 안 됨, [ADR-0003](docs/adr/0003-domain-driven-design-for-business-logic_kr.md)):
`interfaces → application → domain ← infrastructure`.
**domain/ 안의 코드는 SQLAlchemy도 FastAPI도 몰라야 한다.** import 문에
`sqlalchemy`나 `fastapi`가 보이면 레이어를 잘못 짠 것이다.

## 2. 자주 하는 작업

**새 REST 엔드포인트 추가** (예: order-service에 `PATCH /orders/{id}/cancel`)
1. `application/services.py`에 유스케이스 메서드 추가 (`OrderApplicationService.cancel_order`) —
   UnitOfWork 열고, 도메인 메서드(`order.cancel()`) 호출, 커밋.
2. `interfaces/rest.py`에 라우트 추가, 그 메서드 호출.
3. `tests/test_order_api.py`에 성공/실패 케이스 추가.

**도메인에 새 불변식 추가** (예: "총액이 100만원 넘으면 승인 필요")
1. `domain/entities.py`의 애그리게이트 메서드 안에서 체크,
   위반 시 `netframework_core.exceptions.DomainError` 발생.
2. `tests/test_order_domain.py`에 `pytest.raises(DomainError)` 케이스 추가.
   — application/infrastructure는 안 건드려도 되는 게 정상이다(그게
   불변식을 domain에 모아둔 이유).

**AI 에이전트에 새 도구 추가**
1. 그 능력을 가진 서비스의 `module.py`/구성 코드에서
   `ToolRegistry.register(ToolSpec(name=..., description=..., parameters=<JSON
   schema>, handler=<async fn>))`.
2. 다른 서비스에서 그 도구를 쓰게 하려면, order-service의 `get_order`
   패턴처럼(`ai_agent_service/application/order_client.py`) HTTP 클라이언트를
   만들어 그 서비스의 공개 API를 호출하게 한다 — **절대 그 서비스의 코드를
   import하지 않는다.**

**서비스 간 새 이벤트 추가** (예: `OrderCancelled`)
1. 먼저 `docs/adr/000N-...md`로 ADR을 쓴다 (Status: Proposed) — 어떤 서비스가
   왜 이 이벤트가 필요한지.
2. `libs/netframework-contracts/`에 pydantic 모델 + 토픽 상수 추가.
3. 발행하는 서비스: 도메인 이벤트를 커밋 후 이 계약 모델로 변환해서
   `integration_events.publish(TOPIC, ContractModel(...))`.
4. 구독하는 서비스: `events/` 패키지에 핸들러 추가,
   `bus.subscribe(TOPIC, ContractModel, handler)`.
5. ADR Status를 `Accepted`로 바꾸고 병합.

**새 서비스 추가**: README.md의 "Adding a new service" 섹션을 그대로 따르면 된다.

## 3. 코딩 컨벤션

- 모든 새 파일 상단에 `from __future__ import annotations`.
- 타입 힌트는 항상 — 함수 시그니처에 인자/반환 타입 없는 PR은 반려 대상.
- 주석은 **왜**만 쓴다. 코드가 이미 말해주는 **무엇**은 쓰지 않는다
  (이름을 잘 짓는 게 우선).
- 테스트는 실제 Redis/다른 서비스 없이 돌아가야 한다 — Fake/Stub을
  생성자로 주입 (근거: [ADR-0008](docs/adr/0008-testing-with-fakes-instead-of-real-infra_kr.md)).
  `services/order-service/tests/conftest.py`의 `LocalEventBus` 패턴 참고.
- 커밋/PR 전에 최소한: `uv run --package <service> pytest <service>/tests`.

## 4. 개인 → 팀 → 프로젝트로 확장하기

이 저장소는 세 단계 모두를 염두에 두고 설계됐다
([ADR-0005](docs/adr/0005-monorepo-of-independent-services-via-uv-workspace_kr.md)):

**혼자 개발할 때**: 서비스 하나만 로컬에서 돌리면 된다. `AI_PROVIDER=echo`
(API 키 불필요), sqlite, `scripts/dev_redis.py`(Docker 불필요)로 전체
스택을 노트북 하나에서 실행 가능. 다른 서비스가 없어도 그 서비스의 pytest
스위트는 완결적으로 돈다.

**팀 단위로 늘어날 때**: 팀 하나가 서비스 하나(또는 여러 개)를 전담
소유한다. **그 서비스의 domain/application/infrastructure/interfaces
내부는 팀 재량** — 다른 팀 승인 없이 자유롭게 리팩터링 가능. 단, 그
서비스의 **공개 계약**(REST 응답 형태, `netframework-contracts`에 실린
이벤트 모양)은 마음대로 못 바꾼다 — 다른 서비스가 그 모양에 의존하고
있기 때문. `CODEOWNERS` 파일이 "이 경로는 누구 승인이 필요한가"를 코드로
못박아둔다 (지금은 자리표시자 팀명 — 실제 담당자가 정해지면 그 파일의
`@team-*`를 실명/실제 GitHub 팀으로 바꿔라).

**프로젝트(여러 팀) 단위로 늘어날 때**: `libs/`나
`netframework-contracts`처럼 여러 팀이 같이 쓰는 것을 바꾸는 결정은 한
팀이 단독으로 못 한다 — **ADR을 쓰고, 영향받는 모든 서비스 오너의 동의를
받는다** ([ADR-0001](docs/adr/0001-use-adrs-for-decisions_kr.md)의 프로세스
그대로). 이게 "기본적인 방향성에 대한 규칙을 정하는" 절차의 답이다:
문서 한 줄로 정하는 게 아니라, **제안(ADR 초안) → 이해관계자 리뷰 →
합의 → Status를 Accepted로 변경**의 반복이다. 새 규칙이 필요하면 이
사이클을 새로 돌리면 된다.

## 5. Claude에게 다시 맡길 때

새 대화에서 이 프로젝트를 다시 Claude에게 맡긴다면, 이 파일과
`docs/adr/` 전체를 먼저 읽게 하는 게 좋다 — 이미 검토하고 기각한 대안을
Claude가 다시 처음부터 제안하는 걸 막아준다. "ADR-0005/0006을 먼저 읽고
시작해줘" 같은 한 줄이면 충분하다.
