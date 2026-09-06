*🇬🇧 English version: [0005-monorepo-of-independent-services-via-uv-workspace.md](0005-monorepo-of-independent-services-via-uv-workspace.md)*

# ADR-0005: 독립 배포 서비스들의 monorepo (uv workspace)로 구성한다 — 이전 "모듈러 모놀리스" 대체

- **Status**: Accepted (Supersedes 이 프로젝트의 첫 초안 구조 — 커밋되지 않아 별도
  ADR로 남기진 않음, 아래 "Context"에 그 구조를 요약)
- **Date**: 2026-09-06
- **Deciders**: 프로젝트 오너 (명시적 선택, 아래 참고)

## Context (배경)

사용자 요청 4번: "추후에 여러명의 개발자가 추후에 이용할 수 있도록 확장성 및
공통 모듈적인 방향성을 잡아주세요." 이 문장만으로는 "여러 명이 한 프로세스
안에서 모듈 단위로 나눠 쓰는 것"과 "여러 명이 각자 독립 배포되는 서비스를
갖는 것" 둘 다 해석 가능했다.

Claude는 처음에 **모듈러 모놀리스**(하나의 FastAPI 프로세스, `AppContext`를
통해 인메모리 이벤트 버스/툴 레지스트리를 공유, `config/app.yaml`의
`modules:` 목록으로 bounded-context를 로드하는 플러그인 레지스트리)로
구현했다. 사용자가 이후 "이거 Monorepo 방향으로 만든 게 맞냐"고 질문했고,
Claude가 두 개념(모듈러 모놀리스 vs. 진짜 monorepo)의 차이를 설명한 뒤
`AskUserQuestion`으로 세 가지 선택지를 제시했다:
(1) 모듈러 모놀리스 유지, (2) 진짜 monorepo(멀티서비스)로 전환,
(3) C 프로젝트와 하나의 git 저장소로 통합.
**사용자가 (2)를 명시적으로 선택**했다.

## Decision (결정)

- `libs/`(공유 라이브러리: `netframework-core`, `netframework-comms`,
  `netframework-ai-agent`, `netframework-contracts`)와 `services/`(독립 배포
  단위: `order-service`, `ai-agent-service`)로 나눈다.
- 워크스페이스 관리 도구로 **uv**를 쓴다 — 루트 `pyproject.toml`에
  `[tool.uv.workspace] members = ["libs/*", "services/*"]`만 두고(가상
  루트, 자체 코드 없음), 각 서비스는 `[tool.uv.sources]`의
  `{ workspace = true }`로 로컬 lib을 참조한다.
- **서비스는 서로의 코드를 import하지 않는다** — 이게 "모놀리스"와
  "monorepo"를 가르는 핵심 규칙이다. 서비스 간 연결은 ADR-0006에서 다룬다.

## Alternatives considered (검토했던 대안)

- **모듈러 모놀리스 유지** — 운영 복잡도(서비스 디스커버리, 네트워크 지연,
  분산 트랜잭션)가 없다는 장점이 있었지만, 사용자가 "진짜 monorepo"를
  선택함으로써 이 대안은 기각됨. (남겨둔 이유: 팀/서비스 수가 적고 배포를
  분리할 필요가 없는 초기 단계에는 여전히 합리적인 선택지이므로, 상황이
  바뀌면 이 ADR을 대체하는 새 ADR로 되돌아갈 수 있음을 기록해둔다.)
- **Poetry monorepo 플러그인** — Python 생태계에서 이전부터 쓰이던 방법이지만
  워크스페이스 네이티브 지원이 약하고(서드파티 플러그인 의존), uv 대비 설치
  속도도 느림.
- **서비스별 완전히 분리된 저장소(polyrepo)** — 팀이 실제로 나뉘어 있고 배포
  주기가 다르면 유리하지만, 지금은 (a) 서비스 수가 적고 (b) 공유 계약
  (`netframework-contracts`)을 원자적으로 함께 리뷰/변경해야 할 일이 잦을
  초기 단계라 monorepo가 유리하다고 판단.
- **Nx/Turborepo/Bazel 같은 범용 monorepo 빌드 도구** — JS 생태계 중심이거나
  설정 비용이 큼. Python 전용, Cargo workspace와 유사한 경량 모델을 가진
  uv가 이 규모엔 더 적합.

## Consequences (결과 / 트레이드오프)

- 로컬에서 서비스를 띄우려면 이제 최소 2개 프로세스(+ Redis)가 필요하다 —
  `scripts/dev_redis.py`로 Docker 없이도 가능하게 완화했지만, 모놀리스보다
  "일단 하나 실행" 진입장벽이 높아졌다. `CONTRIBUTING.md`에서 이 부분을
  단계별로 안내한다.
- `libs/netframework-contracts`를 바꾸는 PR은 사실상 여러 서비스에 동시에
  영향을 준다 — ADR-0001에서 "공유 라이브러리 변경엔 ADR 필수" 규칙을 둔
  이유가 이것이다.
- 서비스가 하나 더 늘어나도(`README.md`의 "Adding a new service" 참고)
  루트 설정 파일을 고칠 필요가 없다 — `services/*` 글롭이 자동으로 인식.
- 이 구조는 Docker Compose까지 작성했지만 **이 개발 환경엔 Docker가 없어
  `docker compose up --build`는 실제로 빌드 테스트하지 못했다** — uv 기반
  로컬 실행(fakeredis 포함)으로만 end-to-end 검증함. 사용자가 Docker
  환경에서 처음 띄울 때 재확인이 필요하다.

## References (근거 자료)

- uv 공식 문서, *Workspaces* — `[tool.uv.workspace]`/`{workspace = true}`
  메커니즘의 근거.
- Rachel Potvin & Josh Levenberg (Google), *Why Google Stores Billions of
  Lines of Code in a Single Repository*, CACM (2016) — "공유 코드를 하나의
  저장소에서 원자적으로 리뷰"하는 monorepo 논거의 대표 사례.
- 이번 대화의 `AskUserQuestion` 응답 — 이 결정의 직접적 근거는 문헌보다
  **사용자의 명시적 선택**이다.
