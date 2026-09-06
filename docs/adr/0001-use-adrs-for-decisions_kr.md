*🇬🇧 English version: [0001-use-adrs-for-decisions.md](0001-use-adrs-for-decisions.md)*

# ADR-0001: 아키텍처/방향성 결정은 ADR로 기록한다

- **Status**: Accepted
- **Date**: 2026-09-06
- **Deciders**: TBD (현재는 프로젝트 오너 1인 — 사람이 늘어나면 이 필드를 갱신)

## Context (배경)

이 프로젝트는 Claude(AI)가 초기 설계와 구현 대부분을 작성했다. 프로젝트 오너가
"Claude가 왜 이렇게 코딩했는지 근거를 남겨서, 나중에 검토하고 방향을 고치고
싶다"고 요청했다. 또한 앞으로 여러 사람/여러 팀이 이 코드베이스에 참여할
예정이므로, 코드만 보고는 알 수 없는 "왜"를 어딘가에 기록해두지 않으면:

- 같은 논쟁을 반복하게 되고
- 새로 합류한 사람이 "이거 그냥 이렇게 짜여있길래 따라했다"는 식으로 관행을
  베끼기만 하고
- Claude나 사람이나, 나중에 실수로 이미 검토하고 기각한 대안을 다시 시도하게
  된다.

## Decision (결정)

**구조에 영향을 주는 결정은 `docs/adr/NNNN-제목.md` 파일로 남긴다.**
형식은 `0000-template.md`를 따른다 (Context/Decision/Alternatives
considered/Consequences/References). 이번 대화에서 이미 내려진 결정들을
ADR-0002 ~ 0008로 소급 작성했다 — Claude가 그 순간 무엇을 근거로 판단했는지를
사후적으로 정리한 것이다.

**"규칙을 정하는" 절차는 이것 자체다**: 새로운 방향을 정하고 싶으면

1. `docs/adr/000N-제목.md`을 새로 쓴다 (Status: Proposed).
2. 영향받는 서비스/라이브러리 소유자와 상의한다 (`CODEOWNERS` 참고).
3. 합의되면 Status를 `Accepted`로 바꾼다. 기존 ADR과 충돌하면 그 ADR의
   Status를 `Superseded by ADR-000N`으로 바꾸되 **내용은 지우지 않는다**.
4. 코드/README/CONTRIBUTING이 그 결정과 어긋나면 같은 변경에서 함께 고친다.

이미 내려진 결정을 뒤집고 싶을 때도 기존 파일을 고치는 게 아니라 새 ADR을
쓴다 — 그래야 "왜 예전엔 이렇게 안 했는지"와 "왜 지금은 바뀌었는지"가 둘 다
남는다.

## Alternatives considered (검토했던 대안)

- **README 한 파일에 전부 서술** — 짧게는 편하지만, 결정이 쌓일수록 어떤 문단이
  "지금 유효한 결정"이고 어떤 게 "예전 결정의 흔적"인지 구분이 안 된다.
- **커밋 메시지에만 근거를 남긴다** — git log를 뒤져야 하므로 검색성이 낮고,
  아직 git 저장소도 아니다.
- **아무 기록도 안 남긴다** — 사용자가 명시적으로 원하지 않는다고 밝힘.

## Consequences (결과 / 트레이드오프)

- 결정 하나마다 파일 하나 — 결정이 많아지면 파일도 많아진다. 대신 각 파일은
  짧고 목적이 하나뿐이라 찾기/리뷰하기 쉽다.
- ADR을 쓰는 습관이 없으면 금방 안 지켜질 수 있다. `CONTRIBUTING.md`에서
  "공유 라이브러리(`libs/`)나 서비스 간 계약(`libs/netframework-contracts`)을
  바꿀 때는 ADR 필수"로 못박아 최소한의 강제력을 둔다.
- 이 저장소에 아직 CI가 없어서 "ADR 없이 병합되는 것"을 자동으로 막지는
  못한다 — 사람이 리뷰에서 챙겨야 한다 (향후 과제).

## References (근거 자료)

- Michael Nygard, *Documenting Architecture Decisions* (2011) — ADR 포맷의
  원조. ThoughtWorks Tech Radar에서 "Adopt"로 권고된 이후 업계 표준처럼 쓰임.
- AWS Prescriptive Guidance, *Architecture decision records (ADRs)* — 같은
  패턴을 조직 단위로 어떻게 운영하는지에 대한 실무 가이드.
