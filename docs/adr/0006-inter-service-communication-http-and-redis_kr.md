*🇬🇧 English version: [0006-inter-service-communication-http-and-redis.md](0006-inter-service-communication-http-and-redis.md)*

# ADR-0006: 서비스 간 통신은 동기 HTTP(조회) + Redis pub/sub(비동기 통합 이벤트)로 하고, 도메인 이벤트와 통합 이벤트를 분리한다

- **Status**: Accepted
- **Date**: 2026-09-06
- **Deciders**: Claude(설계 제안, ADR-0005 채택에 따른 후속 결정)

## Context (배경)

ADR-0005에서 "서비스는 서로의 코드를 import하지 않는다"고 정했다. 그럼 두
서비스가 실제로 정보를 주고받으려면 무엇으로 대체할지 정해야 했다:
`ai-agent-service`가 특정 주문을 조회해야 하는 경우(요청-응답)와,
`order-service`가 "주문이 생겼다"는 사실을 알려야 하는 경우(발생-통지)는
성격이 다르다.

## Decision (결정)

**두 가지 통신 방식을 용도별로 분리한다:**

1. **동기 조회 = HTTP.** `ai-agent-service`의 `get_order` 도구는
   order-service의 공개 REST API(`GET /orders/{id}`)를 `httpx`로 호출한다
   (`ai_agent_service/application/order_client.py`). 실패 시 예외를 던지지
   않고 에러 문자열을 반환해 에이전트가 우아하게 실패하도록 함.

2. **비동기 통지 = Redis pub/sub.** `order-service`는 주문 생성을 커밋한
   뒤 `order.created` 토픽으로 `OrderCreatedEvent`를 발행하고,
   `ai-agent-service`는 시작 시 그 토픽을 구독해 알림을 받는다
   (`netframework_core.eventbus.redis_bus`).

3. **도메인 이벤트 ≠ 통합 이벤트, 명시적으로 분리.**
   `order_service.domain.events.OrderCreated`(내부, `UnitOfWork`가
   같은 서비스 안에서만 드레인)와
   `netframework_contracts.order_events.OrderCreatedEvent`(외부, 다른
   서비스가 실제로 받는 것)는 서로 다른 클래스다. Application 레이어
   (`OrderApplicationService.create_order`)가 커밋 성공 후 전자를 후자로
   명시적으로 변환해서 발행한다 — 자동 변환/공유 클래스를 쓰지 않는다.

4. **계약(contract)은 `libs/netframework-contracts`에만 존재.** 순수
   pydantic 모델과 토픽 이름 상수만 담고, 어떤 서비스 코드도 import하지
   않는다.

## Alternatives considered (검토했던 대안)

- **모든 서비스 간 통신을 HTTP로 통일** — "주문이 생겼다"는 사실도
  ai-agent-service가 주기적으로 폴링하거나, order-service가 알고 있는 모든
  구독자 URL에 웹훅을 쏘는 방식. 구현은 더 단순하지만, order-service가
  "누가 내 이벤트를 구독하는지" 알아야 해서 결합도가 높아지고, 구독자가
  늘어날수록 order-service 코드를 계속 고쳐야 한다. Pub/sub은 이 결합을
  없앤다(order-service는 구독자 수/신원을 전혀 모른다).
- **Kafka/RabbitMQ 같은 정식 메시지 브로커** — 배달 보장(at-least-once),
  재생(replay) 등 실운영에 필요한 기능이 있지만, 이 단계엔 인프라 비용이
  과하다고 판단. `RedisEventBus`는 `EventBus` 프로토콜 뒤에 숨어 있으므로,
  나중에 필요해지면 서비스 코드 변경 없이 구현체만 교체 가능하도록 설계함.
- **도메인 이벤트를 그대로 다른 서비스에 발행(변환 없이)** — 더 적은 코드로
  되지만, order-service 내부 도메인 모델이 바뀔 때마다 다른 서비스와의
  계약도 같이 깨진다. 두 이벤트를 분리해서 "내부 자유, 외부는 신중하게"라는
  원칙을 지킴.
- **트랜잭션 아웃박스 패턴(Transactional Outbox)** — DB 커밋과 이벤트 발행을
  하나의 트랜잭션으로 묶어 "커밋은 됐는데 이벤트 발행에 실패" 같은 틈을
  없애는 정석적인 방법. 이번엔 구현하지 않았다 — 아래 Consequences에 리스크로
  명시.

## Consequences (결과 / 트레이드오프)

- **알려진 리스크(아웃박스 미적용)**: `create_order`에서 `uow.commit()`은
  성공했는데 그 직후 `integration_events.publish(...)`가 실패하면(Redis 다운
  등) 주문은 저장됐지만 알림은 유실된다. 지금은 이 실패를 잡지 않는다 — 실제
  트래픽을 받기 전에 아웃박스 패턴이나 재시도 큐 도입을 검토해야 한다
  (README "Planned next steps"에 추가 필요).
- Redis pub/sub은 구독자가 없을 때 발행된 메시지를 버린다(재생 불가) — 알림을
  "놓쳐도 되는" 용도로만 써야 한다. "반드시 처리해야 하는" 이벤트가
  생기면 이 ADR을 대체하는 새 ADR에서 브로커를 바꿔야 한다.
- 테스트가 실제 Redis 없이도 가능해졌다 — `EventBus` 프로토콜을
  `LocalEventBus`로 교체해서 검증(ADR-0008 참고).
- 이 통신 계층은 order-service ↔ ai-agent-service 단 두 서비스로만
  검증됐다. 세 번째 서비스가 생겼을 때도 이 패턴이 그대로 확장되는지는
  아직 실증되지 않음(README "Planned next steps"의 `delivery-service`가
  이걸 검증하는 목적도 겸함).

## References (근거 자료)

- Chris Richardson, microservices.io — *Database per Service*, *Domain
  Event*, *Saga* 패턴. "서비스는 서로의 DB/코드를 직접 보지 않는다"는
  원칙의 근거.
- Martin Fowler, *What do you mean by "Event-Driven"?* (martinfowler.com) —
  event notification vs. event-carried state transfer 구분. 이 프로젝트는
  "event notification"에 가깝다(알림만, 전체 상태 전달은 안 함).
- Chris Richardson, *Pattern: Transactional outbox* — 위에서 "적용하지
  않았다"고 명시한 패턴의 원 출처. 다음 단계에서 검토할 대상.
