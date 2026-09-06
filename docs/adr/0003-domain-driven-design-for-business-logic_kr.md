*🇬🇧 English version: [0003-domain-driven-design-for-business-logic.md](0003-domain-driven-design-for-business-logic.md)*

# ADR-0003: 비즈니스 로직은 DDD 전술 패턴(Entity/Aggregate/Repository/UnitOfWork/Domain Event)으로 구성한다

- **Status**: Accepted
- **Date**: 2026-09-06
- **Deciders**: 프로젝트 오너 (사용자 명시적 요청) + Claude(설계 제안)

## Context (배경)

사용자 요청 2번: "어제는 통신과 DB가 중심이였다면 오늘은 통신과 db는 기본으로
하고 DDD개념이 통합되었으면해요." DDD는 "쓴다"는 결정만으로는 코드가 안
나오므로, 어떤 패턴을 실제로 채택할지 구체화가 필요했다.

## Decision (결정)

각 서비스(bounded context)를 4개 레이어로 나눈다:

- **domain/** — `Entity`, `AggregateRoot`(도메인 이벤트를 모았다가 커밋 후
  드레인), `ValueObject`(불변, 값 비교), `Repository`(추상 포트) —
  `libs/netframework-core/src/netframework_core/ddd/`에 기반 클래스로 존재.
  이 레이어는 SQLAlchemy/FastAPI 등 어떤 인프라도 import하지 않는다.
- **application/** — 유스케이스 하나당 메서드 하나. `UnitOfWork`를 열고
  트랜잭션 경계를 정의. 비즈니스 규칙은 여기 두지 않는다 (전부 도메인에).
- **infrastructure/** — SQLAlchemy ORM 모델 + Repository 구현체. domain의
  추상 인터페이스를 구현한다.
- **interfaces/** — REST(FastAPI router), TCP 등 프로토콜별 어댑터.

의존 방향은 항상 `interfaces → application → domain ← infrastructure`
(domain은 아무것도 모른다, infrastructure가 domain에 맞춘다 — Clean
Architecture/Hexagonal Architecture와 같은 방향).

Order 애그리게이트가 실제 예시: `Order.create()`가 불변식("최소 한 줄 이상")을
강제하고 `OrderCreated` 도메인 이벤트를 기록하며, `SqlAlchemyUnitOfWork`가
커밋 성공 후에만 그 이벤트를 드레인해서 발행한다.

## Alternatives considered (검토했던 대안)

- **트랜잭션 스크립트 (서비스 레이어에 로직을 다 몰아넣기)** — 어제 C
  프로젝트의 서비스 파일들이 사실 이 방식에 가까웠다. 빠르게 짜기는 쉽지만
  "DDD 개념 통합"이라는 요청과 어긋남.
  - **분석용 노트**: 이 코드베이스는 이 판단을 스스로 검증하지 않았다 —
    사용자가 명시적으로 DDD를 요청했으므로 대안 비교보다 요청 이행이 우선이었다.
- **애그리게이트 없이 ORM 모델을 도메인 객체로 그대로 사용(Active Record)** —
  구현은 더 짧아지지만, "불변식은 어디서 강제하는가"가 모호해지고
  인프라(SQLAlchemy)가 도메인에 스며든다.
- **CQRS(Command/Query 분리, 별도 read model)** — 지금 규모(주문 CRUD 수준)엔
  과도한 복잡도. 조회가 늘어나고 read model이 필요해지면 별도 ADR로 재검토.

## Consequences (결과 / 트레이드오프)

- 작은 기능(예: 필드 하나 추가)도 4개 폴더를 오가야 해서 초기 진입 장벽이
  있다 — `CONTRIBUTING.md`의 "자주 하는 작업" 섹션으로 완화 시도.
- 도메인 규칙이 한 곳(Aggregate)에 모이므로, 같은 규칙이 REST 핸들러와 TCP
  핸들러에서 중복 구현될 위험이 줄어든다.
- `Order` 하나만 이 패턴으로 구현되어 있어 "패턴이 실제로 두 번째 도메인에도
  잘 맞는지"는 아직 검증되지 않았다 — README "Planned next steps"의
  `delivery-service` 추가가 이 가설을 검증하는 시험대다.

## References (근거 자료)

- Eric Evans, *Domain-Driven Design: Tackling Complexity in the Heart of
  Software* (2003) — Entity/Value Object/Aggregate/Repository 개념의 원전.
- Vaughn Vernon, *Implementing Domain-Driven Design* (2013) — Aggregate 설계
  규칙(작게 유지, 트랜잭션당 하나), Domain Event를 커밋 이후에만 발행하는
  패턴의 실무 가이드.
- Robert C. Martin, *Clean Architecture* (2017) / Alistair Cockburn,
  *Hexagonal Architecture* — "domain은 infrastructure를 모른다"는 의존 방향
  규칙의 근거.
