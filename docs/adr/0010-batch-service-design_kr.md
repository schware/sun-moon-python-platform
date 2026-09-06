*🇬🇧 English version: [0010-batch-service-design.md](0010-batch-service-design.md)*

# ADR-0010: `batch-service` 설계 — 공유 Job/Step/Chunk 라이브러리, 진짜 HTTP 페이지네이션, JSON이 아니라 환경변수로 설정

- **Status**: Accepted
- **Date**: 2026-09-06
- **Deciders**: 본인

## Context

[`alignment`](https://github.com/schware/alignment) 저장소의 ADR-0006이
같은 Batch 설계(Spring Batch의 Job → Step → Chunk, Reader/Processor/
Writer)를 C(`sun-moon-c-server`, 이미 완료 — 그 저장소의 ADR-0001
참고)와 Python 양쪽에, 같은 `order-service` REST 계약을 상대로 만들기로
했다. C 쪽을 만들 당시엔 `order-service`의 `GET /orders`에
`limit`/`offset` 쿼리 파라미터가 없어서, 그 구현은 한 번에 전부 받아와
클라이언트 쪽에서 chunk로 나눈다(인정된, 임시적인 gap —
`sun-moon-c-server`의 ADR-0001 "Consequences" 참고).

## Decision

- **새 공유 라이브러리 `libs/netframework-batch`**(코드를
  `batch-service`에 바로 넣지 않음): `Reader`/`Processor`/`Writer`
  `Protocol`과 `run_step()` — `sun-moon-c-server`의
  `batch.h`/`batch.c`에 대응하는 Python 쪽. C는 interface가 없어서 함수
  포인터를 구조체에 묶어야 했지만, Python은 진짜 `Protocol` 제네릭을
  쓴다; chunk 루프와 chunk 단위 내결함성(`JobResult.chunks_failed`/
  `records_failed`, 실패한 chunk는 로그 남기고 건너뜀, job을 중단하지
  않음)은 그 외엔 같은 설계다. `batch-service`에 바로 넣지 않고 별도
  `libs/` 패키지로 둔 이유는, 나중에 두 번째 batch job이 생겼을 때 엔진을
  중복 구현하지 않게 하기 위해서다 — 이 monorepo의 기존 libs/services
  분리(ADR-0005)와 같은 맥락.
- **`order-service`의 `GET /orders`에 `limit`/`offset` 쿼리 파라미터
  추가**(기본값은 기존 하드코딩 값과 동일하게 둬서 `ai-agent-service`나
  다른 기존 호출자에 영향 없음). 이걸로 `batch-service`의 reader가 HTTP
  위에서 진짜로 chunk에 bound되게 됐다 — `sun-moon-c-server`의 임시
  fetch-everything 방식보다 실제로 나아진 부분인데, 이게 가능했던 건
  이 작업이 별도 저장소 간 API 변경 없이 같은 Python monorepo 안에서
  이뤄지기 때문이다.
- **새 서비스 `services/batch-service`**(`order-service`의 모드가 아니라):
  `OrderServiceReader`(페이지네이션된 HTTP 읽기), `OrderSummaryProcessor`
  (`total_cents` 합산, 취소된 주문 제외 — C job과 동일한 규칙, 직접
  비교를 위해), `NdjsonWriter`(주문마다 JSON 한 줄씩 스트리밍, 쓰기
  쪽도 C처럼 chunk에 bound됨). 출력 모양은 `sun-moon-c-server`와 정확히
  같다: NDJSON records 파일 하나, JSON summary 객체 하나, JSON execution
  report 하나.
- **환경변수 + `.env`로 설정**(`BatchServiceConfig`, ADR-0007에 따라
  `BaseServiceConfig` 상속) — `sun-moon-c-server`의 `batch_runner`가
  JSON으로 설정되는 것과 달리 **JSON이 아니다.** 이건 일관성이 없는 게
  아니라 의도적인 것이다: JSON 설정 지시는 "C의 경우"로 명시적으로
  범위가 한정돼 있었다; 이 저장소 안에서는 모든 서비스가 이미 같은
  방식으로 설정되고 있고(ADR-0007), `batch-service`도 여기서 두 번째
  설정 방식을 새로 들이는 대신 그걸 따른다.
- **별도 entrypoint**(`batch_service/main.py`, `asyncio.run()` 호출 한 번,
  FastAPI 앱 없음) — `sun-moon-c-server`의 별도 `batch_runner` 바이너리와
  그 저장소 ADR-0001의 근거를 그대로 반영한다: 일회성·순차적 job은
  장수 서버와 실행 모델 자체가 다르고, 억지로 하나에 욱여넣으면 안 된다.

## Alternatives considered

- **Job/Step/Chunk 엔진을 새 `libs/` 패키지 대신 `batch-service`에 바로
  넣는다** — job 하나만 있을 땐 격식이 덜 필요하지만, 이 작업 전체의
  요점(`alignment`의 ADR-0004에 따라)이 *재사용 가능한* 패턴이라는
  것이다; 나중에 batch job이 하나 더 생기면 엔진을 중복 구현하거나
  어색한 리팩터링을 강제하게 된다. 지금 약간의 비용을 치르는 게 낫다.
- **대칭을 위해 `order-service`의 reader 쪽 gap을 C와 똑같이 안 고친다**
  — 두 구현을 한 줄 한 줄 더 직접 비교할 수 있게 되지만, 이 작업이
  Python monorepo 안에서 이뤄지기 때문에 가능한 실제 개선을 그냥
  포기하는 것이다. 그 차이는 Consequences에서 명시적으로 다룬다.
- **`batch-service`도 C처럼 JSON으로 설정** — 위 범위 지정에 따라 기각;
  게다가 ADR-0007의 환경변수 방식으로 이미 통일된 저장소에 JSON으로
  설정되는 첫 서비스가 되는 셈이었을 것이다.

## Consequences

- **`sun-moon-c-server`의 order-summary job과 직접 비교**(ADR-0006이
  요구한 구체적 산출물): 같은 job 의미(취소 안 된 `total_cents` 합산),
  같은 출력 모양(NDJSON + JSON summary + JSON execution report), 같은
  내결함성 모델(실패한 chunk는 로그·카운트만, 치명적이지 않음) — 다만
  Python reader는 HTTP 위에서 진짜로 chunk에 bound되고, C reader는
  아직 한 번에 전부 받아온다. 그 차이는 이제 순수하게
  `sun-moon-c-server` 쪽의 후속 작업일 뿐이고(그 저장소 README에 이미
  추적됨), 여기 어떤 것에도 막혀 있지 않다.
- `order-service`의 공개 REST 계약이 이제 소비자 둘이 아니라
  셋(`ai-agent-service`, `batch-service`, `sun-moon-c-server`의
  `batch_runner`)이다 — `GET /orders` 응답 모양을 셋 다 확인하지 않고
  바꾸는 데 대한 기준이 더 높아진다, ADR-0006에서 이미 짚은 "계약엔
  버전 관리 규율이 필요하다"는 것과 같은 지점.
- `netframework-batch`는 지금 소비자가 정확히 하나(`batch-service`)다
  — 이 Protocol 기반 설계가 모양이 다른 두 번째 job에도 잘 맞는지는
  아직 검증 안 됐다; 그 전까지는 "하나로 검증됨" 정도로 취급한다.
- `batch-service`엔 데이터베이스 의존성이 전혀 없다 — 상태는 HTTP로
  읽는 주문 데이터와 쓰는 파일들뿐이다; 마이그레이션할 것도, 백업할 것도
  없다. 나중에 진짜 Spring-Batch식 `JobRepository`(내구성 있는 실행
  이력)가 필요해지면, 그건 기본값이 아니라 의도적으로 추가해야 할 것이다.

## References

- `alignment/docs/adr/0006-dual-language-batch-via-shared-contract_kr.md` —
  이게 구현하는 저장소 간 결정.
- `sun-moon-c-server/docs/adr/0001-batch-job-design_kr.md` — 이게 따르고
  비교하는 C 구현.
- `docs/adr/0006-inter-service-communication-http-and-redis_kr.md`(이
  저장소) — 이 ADR의 Consequences가 세 번째/네 번째 소비자로 확장하는
  REST 계약 규율.
- `docs/adr/0007-config-via-environment-variables_kr.md`(이 저장소) —
  `batch-service`가 JSON이 아니라 환경변수를 쓰는 이유.
