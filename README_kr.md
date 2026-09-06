*🇬🇧 English version: [README.md](README.md)*

# netframework monorepo — DDD 서비스, 통신, DB, 그리고 AI Agent

[uv workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/)로
관리되는 **독립 배포 서비스들의 진짜 monorepo**다: `libs/` 아래 공유
라이브러리, `services/` 아래 독립 배포 가능한 bounded-context 서비스들,
서비스 간 통합 이벤트를 위한 Redis 하나, 그리고 로컬 개발을 위해 전체
워크스페이스를 묶어주는 루트 `pyproject.toml` 하나 — 하지만 각 서비스는
각자 배포되고, 버전이 매겨지고, 스케일링된다.

이 구조는 같은 아이디어의 이전 "모듈러 모놀리스" 초안(프로세스 하나, 인메모리
이벤트 버스, 플러그인으로 로드되는 모듈들)을 대체한다. 그 버전은 한 팀이
하나의 코드베이스에서 일할 땐 괜찮지만, 이번 버전은 실제 요청 —
여러 개발자, 여러 팀이 각자 서비스 하나씩을 처음부터 끝까지 소유하는 것 —
을 위한 것이다.

## 문서 — 근거자료 / 직접 코딩할 때 / 규칙을 정하는 법

이 코드 대부분은 Claude가 작성했다. **왜 이렇게 판단했는지**를 검토하거나
바꾸고 싶다면 아래를 먼저 보는 게 이 README 전체를 다시 읽는 것보다 빠르다:

- **[`docs/adr/`](docs/adr/)** — 결정마다 배경/대안/근거 문헌을 기록한
  Architecture Decision Record. 언어 선택(ADR-0002), DDD 적용
  방식(ADR-0003), AI Agent 설계(ADR-0004), monorepo 전환의 계기와 그
  순간의 대화 맥락(ADR-0005), 서비스 간 통신 방식(ADR-0006), 설정
  방식(ADR-0007), 테스트 전략(ADR-0008)이 각각 한 파일이다. **동의하지
  않는 결정이 있으면 그 ADR의 "Alternatives considered"부터 반박하면 된다**
  — 이미 검토했던 대안인지, 아니면 놓친 대안인지 바로 드러난다.
- **[`CONTRIBUTING_kr.md`](CONTRIBUTING_kr.md)** — Claude 없이 직접
  코딩해야 할 때를 대비한 가이드: 코드를 어디에 둘지 결정하는 법, 자주
  하는 작업 레시피, 코딩 컨벤션, 그리고 **개인 → 팀 → 프로젝트로 규모가
  커질 때 누가 무엇을 결정하는지**(새 규칙을 정하는 절차 포함).
- **[`CODEOWNERS`](CODEOWNERS)** — 경로별 소유자 템플릿(현재는
  자리표시자 `@team-*` — 실제 담당자가 정해지면 채워 넣을 것).

**새로운 방향성/규칙을 정하고 싶다면**: `docs/adr/0000-template_kr.md`을
복사해서 새 ADR을 쓰고, 관련 있는 서비스/라이브러리의 `CODEOWNERS` 항목과
상의한 뒤 Status를 `Accepted`로 바꾼다. 기존 결정을 뒤집을 때도 그 파일을
고치지 말고 새 ADR을 써서 "Supersedes"로 연결한다 — 무엇을 왜 바꿨는지가
남아야 다음 사람(사람이든 Claude든)이 같은 시행착오를 반복하지 않는다.

## 구조

```
pyproject.toml                 # 가상 워크스페이스 루트 — 코드 없음, [tool.uv.workspace]만 있음
docker-compose.yml             # redis + 두 서비스, 환경변수로 연결
scripts/dev_redis.py           # fakeredis 기반 redis:// 대체제 — 노트북 개발용 (Docker 불필요)

libs/                          # 공유 라이브러리 — 모든 서비스가 의존할 수 있음
  netframework-core/           #   설정, 로깅, 예외, DDD 기반형, SQLAlchemy 헬퍼,
                                #   두 종류의 이벤트버스 (인프로세스 DomainEventBus + 서비스 간 EventBus)
  netframework-comms/          #   FastAPI 앱 팩토리, asyncio TCP 라인 프로토콜, asyncio UDP 에코
  netframework-ai-agent/       #   provider-agnostic 툴콜링 Agent 루프 + ToolRegistry
  netframework-contracts/      #   서비스 간 메시지를 위한 순수 pydantic 모델만 — 로직 없음,
                                #   이 저장소의 다른 어떤 것에도 의존하지 않음
  netframework-batch/          #   범용 Job/Step/Chunk 엔진(Reader/Processor/Writer Protocol) —
                                #   sun-moon-c-server의 batch.h/batch.c에 대응하는 Python 쪽

services/                      # 독립 배포 — 별도 프로세스, 별도 포트, 별도 DB
  order-service/                #   domain/ application/ infrastructure/ interfaces/ + main.py
  ai-agent-service/              #   application/ interfaces/ events/ + main.py
  batch-service/                 #   jobs/ + main.py — 장수 서버가 아니라 일회성 CLI
```

## 왜 이게 모듈러 모놀리스가 아니라 monorepo인가

| | 프로세스 하나 (이전 초안) | 이 저장소 |
|---|---|---|
| 배포 단위 | 전부 한 프로세스 | **서비스당 프로세스 하나** — `order-service`와 `ai-agent-service`가 독립적으로 배포/스케일/재시작됨 |
| 모듈 → 모듈 호출 | Python 함수 호출, 같은 메모리 | **HTTP**(동기 조회) 또는 **Redis pub/sub**(비동기 알림) |
| 공유 코드 | `netframework` 패키지 하나 | `libs/*` — 각각 독립적으로 버전이 매겨져 다른 서비스가 `uv add`로 가져다 쓰는 패키지 |
| 팀 간 결합 | 공유 `AppContext` 객체 | `libs/netframework-contracts` — 모델만 담은 패키지; **어떤 서비스도 다른 서비스의 코드를 import하지 않음** |
| 서비스 추가 | 모듈 추가 + 설정 한 줄 | `services/<name>/` 패키지 추가 + 루트 `pyproject.toml`의 `[tool.uv.workspace] members`에 한 줄 |

이걸 가능하게 하는 규칙: **`order-service`와 `ai-agent-service`는 서로를
절대 import하지 않는다.** 둘 사이의 모든 의존은 (a) `libs/netframework-contracts`
(공유되는 건 코드가 아니라 *모양*) 이거나 (b) 상대 서비스의 공개 REST API에
대한 네트워크 호출뿐이다. 이것이 서로 다른 두 개발자가 이 두 서비스를
소유하면서도 서로의 pull request를 절대 건드릴 필요가 없게 해준다.

## 서비스를 잇는 이음매들

1. **동기 조회 — HTTP.** `ai-agent-service`의 `get_order` 도구
   (`services/ai-agent-service/src/ai_agent_service/application/order_client.py`)는
   order-service의 공개 `GET /orders/{id}`를 그냥 `httpx`로 호출하는
   것이다. order-service가 다운되면 이 도구 호출은 우아하게 실패한다 —
   에이전트는 크래시 대신 에러 문자열을 받는다.

2. **비동기 알림 — Redis pub/sub.** 새 주문을 커밋한 뒤, order-service는
   `order.created` 토픽으로 `OrderCreatedEvent`(`netframework-contracts`에
   한 번만 정의됨)를 발행한다
   (`services/order-service/src/order_service/application/services.py`).
   `ai-agent-service`는 시작할 때 같은 토픽을 구독해서
   (`services/ai-agent-service/src/ai_agent_service/events/order_events_handler.py`)
   자신의 에이전트에게 한 줄짜리 운영 노트를 작성하게 시킨다. 어느
   서비스도 상대의 도메인 모델을 import하지 않는다 — 공유된
   `OrderCreatedEvent` 모양만 알 뿐이다.

3. **Chunk 단위 동기 조회 — HTTP, 페이지네이션.** `batch-service`의
   `OrderServiceReader`(`services/batch-service/src/batch_service/jobs/order_summary.py`)는
   order-service의 공개 `GET /orders?limit=&offset=`을 chunk 단위로
   페이지네이션하면서 범용 Job/Step/Chunk 엔진(`libs/netframework-batch`)에
   먹인다 — [`sun-moon-c-server`](https://github.com/schware/sun-moon-c-server)의
   `batch_runner`와 같은 설계, 같은 REST 계약이다(직접 비교는 그 저장소의
   ADR-0001과 이 저장소의 [ADR-0010](docs/adr/0010-batch-service-design_kr.md) 참고).

도메인 이벤트 vs. 통합 이벤트를 구체적으로 보면:
`order_service.domain.events.OrderCreated`(내부용, `UnitOfWork`가 드레인,
order-service 자체 로직에 필요한 어떤 필드든 늘어날 수 있음)와
`netframework_contracts.order_events.OrderCreatedEvent`(외부용,
ai-agent-service가 실제로 필요로 하는 두 필드뿐)는 **서로 다른 클래스**다.
Application 레이어가 커밋 후 전자를 후자로 명시적으로 매핑한다 —
`OrderApplicationService.create_order` 참고. 이건 의도적이다: 내부 도메인
모델은 자유롭게 바뀔 수 있어야 하고, 다른 팀이 의존하는 wire contract는
훨씬 신중하게 바뀌어야 한다.

## Quick start (Docker 불필요)

**Python 3.11+** 와 [uv](https://docs.astral.sh/uv/)(`pip install uv`)가 필요하다.

```bash
uv sync --all-packages --extra dev      # 워크스페이스 전체를 한 번에 resolve + install

# 터미널 1 — 실제 프로토콜을 구현하는 인메모리 Redis 대체제 (`pip install fakeredis` 필요)
python scripts/dev_redis.py 6399

# 터미널 2
REDIS_URL=redis://127.0.0.1:6399/0 \
  uv run --package order-service python -m order_service.main

# 터미널 3
REDIS_URL=redis://127.0.0.1:6399/0 ORDER_SERVICE_BASE_URL=http://127.0.0.1:8081 \
  uv run --package ai-agent-service python -m ai_agent_service.main
```

직접 시험해보기(이 저장소를 만들면서 실제로 검증함 — 진짜 OS 프로세스 두
개가 진짜 HTTP + 진짜 Redis 와이어 프로토콜로 통신):
```bash
curl -X POST http://localhost:8081/orders \
  -H 'Content-Type: application/json' \
  -d '{"lines":[{"sku":"WIDGET","quantity":2,"unit_price_cents":500}]}'

curl -X POST http://localhost:8082/assistant/ask \
  -H 'Content-Type: application/json' -d '{"question":"hello agent"}'

printf 'hello\nORDER_COUNT\n' | nc localhost 8090   # order-service의 TCP 어댑터
```
위의 `curl -X POST /orders` 이후 ai-agent-service의 터미널을 보면 —
`ai_agent_order_note` 로그 라인이 나타난다, 순전히 Redis를 통해 전달된 것이다.

Batch job 실행(일회성 — 끝나면 종료, 계속 띄워둘 터미널 필요 없음):
```bash
uv run --package batch-service python -m batch_service.main
cat reports/order_daily_summary_summary.json   # {"order_count": N, "total_revenue_cents": ...}
```

## Quick start (Docker Compose — 진짜 Redis)

```bash
docker compose up --build
```
같은 세 서비스(`redis`, `order-service`는 `:8081`/`:8090`,
`ai-agent-service`는 `:8082`)가 수동 export 대신 환경변수로 연결된다.
*(표준적인 uv-workspace-in-Docker 패턴으로 작성했지만, 이 환경엔 Docker가
없어 실제 빌드 테스트는 못했다 — 처음 쓸 때 확인 필요.)*

## 테스트

```bash
uv run --package order-service pytest services/order-service/tests
uv run --package ai-agent-service pytest services/ai-agent-service/tests
uv run --package batch-service pytest services/batch-service/tests
uv run --package netframework-batch pytest libs/netframework-batch/tests
```
모든 스위트가 **Redis도, 진짜 order-service도, 서비스 간 네트워크
호출도 없이** 돌아간다 — `order-service`의 테스트는
`netframework_core.eventbus.local_bus.LocalEventBus`를 갈아끼워서 실제로
무엇을 발행하려 했는지 검증하고, `ai-agent-service`의 테스트는 진짜
HTTP/에이전트 호출 대신 `FakeOrderClient`/`RecordingAssistant`를 쓰고,
`batch-service`의 테스트는 진짜 HTTP 연결 대신 `httpx.MockTransport`로
만든 `OrderServiceReader`를 주입한다. 이게 가능한 이유는 위의 모든
이음매가 생성자로 주입되는 인터페이스라서다 — 하드코딩된 게 아니다.

## 새 서비스 추가하기

1. `order-service`와 같은 모양(`domain/ application/ infrastructure/
   interfaces/ + main.py + pyproject.toml`)으로 `services/<your-service>/`를
   만든다. 루트의 `[tool.uv.workspace]`가 이미 `services/*`를 글롭으로
   잡고 있어서 자동으로 인식된다 — 루트 파일을 고칠 필요 없음.
2. 필요한 `libs/*`에 `[tool.uv.sources]` + `{ workspace = true }`로
   의존한다(기존 서비스의 `pyproject.toml` 패턴을 그대로 복사).
3. 다른 서비스의 이벤트에 반응해야 하나? `libs/netframework-contracts/`에
   토픽 + pydantic 모델을 추가하고(또는 기존 걸 재사용) 자신의 `events/`
   패키지에서 `bus.subscribe(...)` — 절대 상대 서비스의 코드를 import하지 않는다.
4. 다른 서비스의 데이터를 동기적으로 읽어야 하나? 그 서비스의 공개 REST
   API를 호출하는 작은 HTTP 클라이언트를 만든다(`order_client.py`의
   모양을 그대로 복사).
5. 로컬에서 인식시키려면 `uv sync --all-packages`; 컨테이너 경로를 위해
   `docker-compose.yml`에 추가.

## 오픈소스 의존성

uv(워크스페이스/의존성 관리), FastAPI + Uvicorn(HTTP/WS), asyncio(TCP/UDP),
SQLAlchemy 2.0 async + aiosqlite(DB — 서비스별로 URL을 Postgres/MySQL로
교체 가능), Redis(서비스 간 pub/sub) + fakeredis(진짜 Redis 없이 로컬
개발), Pydantic v2(DTO/계약/설정), structlog, httpx(서비스 간 HTTP),
Anthropic SDK(선택, 실제 에이전트 추론용).

## 다음 계획

- `batch-service`의 자체 문서에 `sun-moon-c-server`의 order-summary
  job과의 직접 비교 메모 추가(둘 다 같은 설계를 구현함 —
  [ADR-0010](docs/adr/0010-batch-service-design_kr.md) 참고)
- `sun-moon-c-server`의 reader가 `batch-service`와 함께 새로 추가된
  `order-service`의 `limit`/`offset` 페이지네이션을 쓰도록 갱신 — 한
  번에 다 받아오는 대신(그 저장소 쪽에서 추적 중)
- 서비스별 Alembic 마이그레이션(지금은 시작할 때 `create_all`)
- 세 번째 서비스(예: `delivery-service`) 추가 — 세 서비스의
  이벤트/계약이 쌍끼리 결합 없이 잘 조합되는지 검증
- 두 서비스의 HTTP 포트 앞에 API 게이트웨이/BFF — 어제 C의
  "combined-server"가 주던 "공개 포트 하나" 편의성을 재현
- TCP 어댑터에 TLS, 서비스별 uvicorn에 HTTPS
- CI: 실제로 바뀐 서비스(또는 그 서비스가 쓰는 `libs/` 의존성)만
  테스트하는 서비스별 잡
- `order-service`의 통합 이벤트 발행에 트랜잭션 아웃박스 적용 — 지금은
  커밋은 성공했는데 뒤이은 Redis 발행이 조용히 실패할 수 있음
  ([ADR-0006](docs/adr/0006-inter-service-communication-http-and-redis_kr.md)의
  Consequences 참고)
- 담당자가 정해지면 [`CODEOWNERS`](CODEOWNERS)에 실제 이름/팀 채워 넣기
- `docs/adr/` 항목 없이 `libs/`나 `netframework-contracts` 변경이
  병합되는 걸 막는 CI 체크(지금은 [`CONTRIBUTING_kr.md`](CONTRIBUTING_kr.md)에
  따른 리뷰 규율로만 지켜짐)
