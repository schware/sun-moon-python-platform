*🇬🇧 English version: [0008-testing-with-fakes-instead-of-real-infra.md](0008-testing-with-fakes-instead-of-real-infra.md)*

# ADR-0008: 테스트는 실제 인프라(Redis/타 서비스) 대신 페이크/스텁으로 격리한다

- **Status**: Accepted
- **Date**: 2026-09-06
- **Deciders**: Claude(설계 제안)

## Context (배경)

ADR-0005/0006으로 서비스가 분리되고 통신이 HTTP/Redis로 바뀌면서, "테스트를
실행하려면 Redis와 다른 서비스가 다 떠 있어야 하는가?"를 정해야 했다. 이
개발 환경 자체에도 Docker/Redis가 설치돼 있지 않아, 실제로 이 질문에 먼저
부딪혔다(개발 중 직접 겪은 제약).

## Decision (결정)

- **단위/서비스 테스트는 Fake를 주입한다.** `order-service`의 테스트는
  `RedisEventBus` 대신 `netframework_core.eventbus.local_bus.LocalEventBus`를
  생성자에 주입해서, 실제로 무엇을 발행하려 했는지를 인메모리로 검증한다
  (`services/order-service/tests/test_order_api.py`의
  `test_create_order_publishes_integration_event`). `ai-agent-service`의
  테스트는 `OrderServiceClient`(진짜 HTTP) 대신 `FakeOrderClient`를,
  `AssistantService`(진짜 에이전트) 대신 `RecordingAssistant`를 씀.
- **이게 가능한 이유는 두 결합 지점이 전부 생성자 주입 인터페이스이기
  때문이다** — `EventBus` 프로토콜, `get_order` 시그니처, `.ask()`
  시그니처. 테스트가 이 방식으로 짜인다는 것 자체가 "결합 지점이 잘
  추상화됐는지"를 검증하는 부작용도 있다.
- **로컬 수동 검증(진짜 프로세스 간 통신 확인)은 별도로, 더 무겁게 한다** —
  `fakeredis.TcpFakeServer`(실제 Redis 와이어 프로토콜을 구현하는 순수
  Python 서버)를 띄워 두 서비스 프로세스를 실제로 실행하고 HTTP/Redis가
  진짜로 오가는지 확인했다(`scripts/dev_redis.py`). 이건 자동화된 테스트
  스위트에는 포함하지 않았다 — 수동/CI 통합 테스트 단계의 몫으로 남겨둠.

## Alternatives considered (검토했던 대안)

- **testcontainers로 진짜 Redis를 띄워 테스트** — 더 사실적이지만 Docker가
  필요해 이 환경에서 바로 못 씀. 나중에 CI 환경에 Docker가 있다면 계약
  테스트 단계에서 추가하는 걸 권장(README 다음 단계).
- **모든 통신을 목(mock) 라이브러리(unittest.mock)로 패치** — 클래스
  내부 구현에 의존하게 돼 리팩터링에 취약. Fake 객체(진짜 동작하는 최소
  구현)가 인터페이스 계약을 더 잘 검증한다고 판단.
- **통합 테스트를 아예 안 만든다** — 서비스 분리 이후 "실제로 네트워크로
  붙는지"를 검증할 수단이 전혀 없어지므로 기각. 대신 자동화 스위트 밖에서
  수동 스크립트로 최소한의 증거를 남김(이 대화의 실행 로그).

## Consequences (결과 / 트레이드오프)

- pytest 스위트(9개, 서비스당 각각)는 **Redis도 Docker도 없이 몇 초 안에
  끝난다** — 사용자가 직접 코딩할 때도 무거운 인프라 설치 없이 바로
  `pytest`를 돌릴 수 있다는 뜻(`CONTRIBUTING.md` 참고).
- 반대급부로, "Fake가 진짜 Redis/HTTP의 동작을 정확히 흉내내고 있는가"는
  사람이 계속 신경 써야 한다 — 예를 들어 `LocalEventBus`는 순서 보장이나
  네트워크 실패 시나리오를 흉내내지 않는다. 진짜 Redis 특유의 실패 모드
  (연결 끊김, 재연결)는 이 테스트들로 잡히지 않는다.
- 자동화 스위트에 "두 서비스가 실제로 붙는지"를 검증하는 테스트가 없다 —
  현재는 이 대화 중 수동으로 한 번 확인한 것이 유일한 증거다. 프로젝트가
  커지면 CI에 `docker-compose`(또는 testcontainers) 기반 통합 테스트 잡을
  추가해야 한다(README "Planned next steps").

## References (근거 자료)

- Martin Fowler, *Mocks Aren't Stubs* (martinfowler.com) — 목/스텁/페이크
  구분과 각각의 트레이드오프.
- fakeredis 프로젝트 문서 — `TcpFakeServer`가 실제 Redis 프로토콜을
  구현하는 범위/한계.
