*🇬🇧 English version: [0007-config-via-environment-variables.md](0007-config-via-environment-variables.md)*

# ADR-0007: 서비스 설정은 환경 변수(+.env)로 하고, 공유 YAML은 쓰지 않는다

- **Status**: Accepted (Supersedes: 첫 초안의 `config/app.yaml` 단일 파일 방식)
- **Date**: 2026-09-06
- **Deciders**: Claude(설계 제안, ADR-0005 채택에 따른 후속 결정)

## Context (배경)

모듈러 모놀리스 초안에서는 `config/app.yaml` 하나에 모든 설정(HTTP/TCP/UDP
포트, DB URL, AI provider, 로드할 모듈 목록)을 담았다 — 프로세스가 하나였으니
자연스러운 선택이었다. ADR-0005로 서비스가 여러 프로세스로 쪼개지면서, 이
방식을 유지하면 "하나의 YAML을 여러 서비스가 나눠 읽는" 어색한 구조가 된다.

## Decision (결정)

각 서비스가 `netframework_core.config.BaseServiceConfig`(pydantic-settings
`BaseSettings`)를 상속해 자신만의 설정 클래스를 갖는다
(`order_service.config.OrderServiceConfig`,
`ai_agent_service.config.AiAgentServiceConfig`). 값은 환경 변수 + 로컬
`.env` 파일에서 읽는다. 각 서비스 디렉터리에 `.env.example`을 둬서 어떤
변수가 필요한지 문서화한다.

## Alternatives considered (검토했던 대안)

- **공유 YAML 유지, 서비스별 섹션으로 분리** — 파일 하나로 전체 그림을 보기는
  편하지만, 서비스를 독립 배포(각자 다른 컨테이너/서버)하려면 결국 그 YAML도
  서비스별로 쪼개 배포해야 해서 이점이 없어짐. 게다가 한 서비스 배포 시
  다른 서비스 설정까지 실수로 같이 바뀔 위험이 생김.
- **서비스별 YAML 파일 유지(환경 변수 대신)** — 로컬 개발엔 나쁘지 않지만,
  컨테이너 오케스트레이션(Docker Compose/Kubernetes)이 표준적으로 다루는
  방식은 환경 변수이므로, 배포 파이프라인과의 마찰을 줄이기 위해 환경 변수를
  1순위로 택함.

## Consequences (결과 / 트레이드오프)

- `docker-compose.yml`의 `environment:` 블록이 그대로 각 서비스의 설정
  소스가 된다 — 별도 설정 마운트/템플릿 엔진이 필요 없다.
- 로컬에서 여러 서비스를 한 터미널 세션 관습(전역 env 오염)으로 실행하면
  변수가 섞일 위험이 있다 — README/CONTRIBUTING에서 서비스별로 인라인
  환경 변수를 붙여 실행하는 예시를 명시해 이를 완화함
  (`REDIS_URL=... uv run --package order-service ...`).
- 설정 값이 흩어져 있어(`order-service/.env.example`,
  `ai-agent-service/.env.example`) "전체 설정 목록"을 한눈에 보기는
  이전보다 불편해졌다 — 서비스가 많아지면 이 트레이드오프를 재검토할 필요.

## References (근거 자료)

- Adam Wiggins (Heroku), *The Twelve-Factor App*, 특히 "III. Config: Store
  config in the environment" — 이 결정의 직접적 근거.
- pydantic-settings 공식 문서 — `BaseSettings`가 환경 변수 + `.env`를 함께
  읽는 동작 방식.
