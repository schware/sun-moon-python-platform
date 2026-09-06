*🇬🇧 English version: [0004-ai-agent-as-first-class-module.md](0004-ai-agent-as-first-class-module.md)*

# ADR-0004: AI Agent는 provider-agnostic 툴콜링 루프 + 별도 서비스로 통합한다

- **Status**: Accepted
- **Date**: 2026-09-06
- **Deciders**: 프로젝트 오너 (사용자 명시적 요청) + Claude(설계 제안)

## Context (배경)

사용자 요청 3번: "AI Agent가 포함되었으면 합니다." 요구사항 자체는 "AI
기능을 넣어달라" 정도로만 명시됐고, 구체적 설계(어느 LLM, 어떻게 도메인과
연결할지)는 정해지지 않아 Claude가 판단해야 했다.

## Decision (결정)

1. **Provider를 추상화한다** — `LLMProvider` 프로토콜(`complete(messages,
   tools) -> AgentResponse`) 뒤에 `EchoProvider`(오프라인, 키 불필요, 결정론적
   — 테스트/데모용)와 `AnthropicProvider`(실제 Claude, `anthropic` SDK를
   optional extra로 지연 import)를 둔다. 어느 쪽을 쓸지는 환경 변수
   (`AI_PROVIDER`)로 결정 — 코드 변경 없이 전환 가능.
2. **Agent 루프는 하나** (`netframework_ai_agent.base.Agent.run`) — "생각 →
   필요하면 도구 호출 → 결과를 다시 넣고 생각 → 최종 답변" 루프를 provider와
   분리해서, 어떤 provider를 붙여도 같은 루프가 재사용된다.
3. **AI Agent를 별도 서비스(`ai-agent-service`)로 둔다** — Order 도메인
   코드를 직접 import하지 않고, (a) 동기 조회는 order-service의 공개 REST API를
   HTTP로 호출, (b) 비동기 알림은 `OrderCreated` integration event를 Redis로
   구독. (근거는 ADR-0005/0006 — monorepo/통신 결정과 얽혀 있다.)
4. **도구(tool)는 각 서비스가 스스로 등록** — order-service를 흉내내려는
   어떤 서비스든 `ToolSpec`을 만들어 자신의 능력을 노출할 수 있다. AI Agent
   서비스는 "무슨 도구가 있는지" 미리 알 필요가 없다.

## Alternatives considered (검토했던 대안)

- **LangChain/LangGraph 같은 기성 에이전트 프레임워크 사용** — 기능은
  풍부하지만 (a) 의존성이 무겁고 (b) "여러 개발자가 이용할 수 있는 확장성/공통
  모듈" 요구와 맞물려, 이 프로젝트 자체가 향후 공통 모듈이 될 것이므로 외부
  프레임워크에 깊이 종속되기보다 필요한 만큼만 직접 구현하는 쪽을 택함.
  프로젝트가 커지면 `netframework-ai-agent` 내부 구현을 LangGraph 등으로
  교체하는 것도 가능 — Provider/Agent 인터페이스만 유지하면 서비스 코드는
  안 바뀐다.
- **AI 기능을 Order 서비스 안에 내장(같은 프로세스)** — 더 간단하지만,
  "여러 도메인이 생겨도 AI 어시스턴트는 하나"라는 그림과 안 맞고, LLM 호출
  지연(초 단위)이 주문 처리 지연 시간에 섞이는 문제가 생김.
- **동기 REST 대신 처음부터 gRPC** — 실제 프로덕션이라면 고려할 만하지만,
  이 단계에서는 curl로 바로 확인 가능한 REST가 디버깅/온보딩에 유리하다고
  판단.

## Consequences (결과 / 트레이드오프)

- `echo` provider는 진짜 추론을 하지 않는다 — 데모/테스트에서 "배관이
  맞는지"는 검증하지만 "AI가 실제로 똑똑한 답을 하는지"는 `anthropic`
  provider로 바꿔야 확인 가능. **이 부분은 아직 실제 Claude API로
  검증되지 않았다** — API 키가 이 환경에 없어 `echo`로만 end-to-end 테스트함.
- 도구 호출 프로토콜(`call:<tool> {json}`)은 Echo provider 전용 임시 규약이다
  — 실제 Anthropic provider는 진짜 tool_use 블록을 쓰므로 이 규약과 무관하다.
  이 비대칭을 모르면 헷갈릴 수 있어 코드 주석/README에 명시해둠.
- max_tool_iterations로 무한루프는 막았지만, 재시도/백오프/비용 제한 같은
  실운영 안전장치는 없다 — 실제 트래픽을 받기 전에 추가해야 함(다음 ADR감).

## References (근거 자료)

- Anthropic, *Tool use (function calling)* 공식 문서 — tool_use/tool_result
  메시지 형태의 근거 (AnthropicProvider의 메시지 변환 로직이 이 스펙을 따름).
- ReAct 패턴(Yao et al., *ReAct: Synergizing Reasoning and Acting in Language
  Models*, 2022) — "생각→행동(도구 호출)→관찰→다시 생각" 루프의 개념적 원류.
