*🇬🇧 English version: [0009-pivot-framework-to-platform.md](0009-pivot-framework-to-platform.md)*

# ADR-0009: Framework에서 Platform으로 프로젝트 정체성을 전환한다

- **Status**: Proposed — 전환 자체는 정해졌지만, 구체적인 component topology는
  의도적으로 계속 다듬어가는 direction-setting 과정이다(아래 "Open
  questions" 참고) — 다음 작업을 막는 gate가 아니다
- **Date**: 2026-09-06
- **Deciders**: 프로젝트 오너 (이번 대화에서 명시적으로 확인)

## Context

ADR-0002~0008을 거치며 이 프로젝트는 **Framework**로 규정돼 있었다: 다른
개발자들이 그 위에 bounded-context *service*를 짓는 shared kernel
(`libs/*`)이 있고, `order-service`/`ai-agent-service`가 그 패턴의 예시
구현이었다.

이번 대화에서 사용자가 완전히 다른 그림을 제안했다:

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

Claude는 이 다이어그램에 두 가지 확인 질문을 던졌고(아래 참고, 아직 미해결),
별도로 이 구조가 "Framework 위에 예시 앱 두 개가 있는 모양"보다는
Temporal, NATS, Kubernetes 같은 인프라 **Platform**(core engine + SDK 하나
이상 + CLI + 운영용 Dashboard 전체가 곧 제품인 구조)에 더 가깝다고 짚었다.
사용자가 명시적으로 확인했다: 맞다, Framework에서 Platform으로 방향을
고쳐가고 있다.

## Decision

구체적인 architecture가 아직 정리되는 중이라도, 이 정체성 전환 자체를
지금 기록해서 나중에 이 방향이 흐려지거나 다시 논쟁거리가 되지 않게 한다.
구체적으로:

- **"제품"으로 취급되는 범위가 바뀐다.** Framework 관점에서는
  `order-service`/`ai-agent-service`가 제품(예시 bounded context)이었고
  `libs/*`는 그 밑을 받치는 인프라였다. Platform 관점에서는 이게 뒤집힌다
  — Core Runtime, Domain SDK, Event Bus, Transport Layer, Dashboard, CLI가
  제품 **자체**가 된다. `order-service` 같은 비즈니스 로직은 이제 Platform
  **위에** 지어지는 것 — Platform의 일부가 아니라 reference
  implementation/예시가 된다.
- 이 ADR은 Go/Python/TypeScript Polyglot 구성이나, Core
  Runtime/Transport Layer/Event Bus가 독립적으로 Deploy되는 서비스
  3개인지 아니면 Go 프로세스 하나 안의 내부 모듈 3개인지는 **아직 결정하지
  않는다.** 이건 별개의, 아직 열려 있는 결정이고(아래에서 추적), 해결되면
  후속 ADR로 남긴다.

## Open questions — 계속 다듬어가는 direction-setting, 일회성 gate가 아님

프로젝트 오너는 이 세 가지를 지금 억지로 결론짓기보다 **계속 이어지는
과제**로 다루고 있다. 이 프로젝트의 작업 방식 자체가 additive하다 —
Claude가 한 조각을 만들면, 오너가 그걸 보고 생각을 더해서 그 위에
얹는다, 그리고 반복한다. 그래서 아래 세 개 중 어느 것도 Platform을 더
만들기 전에 답이 나와야 하는 건 아니다. 세션 사이에 이 고민의 흐름이
끊기지 않도록 여기 기록해두는 것이고, additive한 과정이 계속되면서
다시 다듬어질 것이지 한 번에 정리되는 게 아니다.

1. **Core Runtime, Transport Layer, Event Bus가 독립적으로 Deploy되는
   서비스 3개인가, 아니면 Go 바이너리/프로세스 하나 안의 내부 모듈
   3개인가?** 이 전환이 실제로 운영 복잡도를 얼마나 올리는지를 결정하는
   가장 큰 변수다 — Go 서비스 3개를 따로 Deploy하는 것과 Go 프로세스
   하나가 내부적으로 모듈 3개로 나뉘어 있는 것은 관리 부담이 완전히 다르다.
2. **Domain SDK는 Library인가, Service인가?** 오너가 2026-09-06에 처음
   떠올린 후보 렌즈가 있다: Library는 *내가 호출하는 것*, Service는
   *나를 호출하는 것*. 이 구분이 사실 **Library vs. Framework** 구분
   (Inversion of Control — "Library는 내가 부르고, Framework는 나를
   부른다")과 맞닿아 있다는 점을 짚어둘 만하다 — 이건 보통 말하는
   **Library vs. Service** 구분(프로세스/Deploy 경계 — 내 프로세스 안에서
   도는지, 자기 프로세스를 따로 갖는지)과는 다른 축이다. Domain SDK는 이
   두 축 각각에 따로 답이 필요할 수도 있고, 실제로는 하이브리드(밖으로
   나가는 호출 표면은 Library처럼 동작하고, 안으로 들어오는
   callback/event 표면은 Framework처럼 동작하는)로 귀결될 수도 있다.
   아직 결론 안 났다 — 오늘 처음 고민을 시작한 것이라 서두를 필요 없다.
3. **Go/TypeScript Polyglot 구성은 어떤 모양이어야 하나?** 오너의 정정에
   따라(2026-09-06): 이건 confirmed-vs-exploratory 이분법이 아니라
   계속 이어지는 direction-setting 과정이다. 이 ADR이 실제로 정리하는 건
   *Framework → Platform* 전환(위 Decision)이고, 구체적인 언어 구성은
   조각들이 만들어지고 그 위에 더해지면서 계속 다듬어갈 것이지, 예/아니오로
   결정될 대기 항목이 아니다.

## Consequences (이 ADR이 Accepted되면)

- `README.md`/`README_kr.md`, `CONTRIBUTING.md`/`CONTRIBUTING_kr.md`를
  다시 써야 한다: "예시 서비스 두 개가 얹혀 있는 Framework"라는 서술이
  더는 맞지 않는다 — 실제 결과물인 Core Runtime, SDK, CLI, Dashboard를
  설명해야 한다.
- [ADR-0005](0005-monorepo-of-independent-services-via-uv-workspace_kr.md)/
  [CONTRIBUTING_kr.md](../../CONTRIBUTING_kr.md)의 individual → team →
  project 확장 모델은 그대로 적용되지만, "팀이 서비스 하나를 소유한다"가
  "팀이 Platform 컴포넌트 하나를 소유한다"로 바뀐다 — 컴포넌트 목록이
  확정되면 `CODEOWNERS`도 갱신해야 한다.
- 실제 Platform core가 만들어지면 `order-service`/`ai-agent-service`는
  아마 `examples/` 같은 디렉터리로 옮겨질 것이다 — 그래야 이게 Platform
  자체가 아니라 Platform 위에 지어진 것임이 명확해진다.
- (Go/TypeScript 컴포넌트가 실제로 생기면) 서비스 간 계약이 더는
  pydantic 모델만으로 충분하지 않다 — 이건 십중팔구
  [ADR-0006](0006-inter-service-communication-http-and-redis_kr.md)의
  일부를 대체하는 별도 ADR이 필요할 것이다.

## References

- 이번 대화 — 이 결정의 직접적 근거(사용자의 명시적 확인: "저는
  Framework에서 Platform으로 방향성을 고쳐가고 있어요").
- "core + SDK + CLI + Dashboard"가 Platform 구조로 쓰이는 사례: Temporal,
  NATS, Kubernetes, 대부분의 HashiCorp 제품들이 이 패턴을 따른다 —
  이들의 구체적인 architecture를 그대로 베끼겠다는 게 아니라, 지향하는
  "형태"의 근거로 인용.
