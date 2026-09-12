# 문서 관리 안내

이 파일은 연구 문서를 찾기 위한 단일 진입점이다. 현재 계약을 확인할 때는 아래의 **현재 정본**만 읽고, 과거 선택의 근거가 필요할 때만 **보관소**를 연다.

## 가장 먼저 읽을 문서

1. [`README.md`](../README.md) — 프로젝트 실행 진입점과 전체 디렉터리 지도
2. [`PROJECT_CONTEXT.md`](../PROJECT_CONTEXT.md) — 현재 상태, 결정 로그, 주의사항
3. [`master_plan/README.md`](../master_plan/README.md) — 오디오부터 FullBodyPlayer까지의 연구 설계 정본
4. [`docs/PAPER_PLAN.md`](PAPER_PLAN.md) — 그래픽스 논문 목적·질문·기여·실험 지표
5. [`tab2body/TRAINING.md`](../tab2body/TRAINING.md) — 학습·평가·checkpoint 실행 계약
6. [`tab2body/STRUCTURE.md`](../tab2body/STRUCTURE.md) — 실제 코드 구조

계약이 충돌하면 `master_plan → 실제 코드·자동 검사 → 모듈 README → 보관소` 순서로 판단한다.

## 현재 연구 문서

| 연구 영역 | 먼저 읽을 문서 | 상세·실행 문서 |
|---|---|---|
| 전체 설계 | [`master_plan/README.md`](../master_plan/README.md) | `master_plan/00~10_*.md` |
| Stage1 오디오·탭·운지 | [`tab2fingermapping/README.md`](../tab2fingermapping/README.md) | [`fingermapping/ALGORITHM.md`](../tab2fingermapping/fingermapping/ALGORITHM.md), [`SETUP.md`](../tab2fingermapping/SETUP.md) |
| Fret-v2 | [`fret/README.md`](../fret/README.md) | [`fret/01_finger_mapping/README.md`](../fret/01_finger_mapping/README.md), [`fret/03_training/README.md`](../fret/03_training/README.md), [`fret/training/README.md`](../fret/training/README.md) |
| Strike-v2 | [`strike/README.md`](../strike/README.md) | [`strike/QUICK_RULES.md`](../strike/QUICK_RULES.md), [`strike/RIGHT_HAND_RULES.md`](../strike/RIGHT_HAND_RULES.md), [`strike/01_goal_contract/README.md`](../strike/01_goal_contract/README.md), [`strike/02_physical_control/README.md`](../strike/02_physical_control/README.md), [`strike/03_training/README.md`](../strike/03_training/README.md) |
| Full G0 | [`full/README.md`](../full/README.md) | [`full/01_goal_contract/EVENT_TIMELINE.md`](../full/01_goal_contract/EVENT_TIMELINE.md), [`full/03_implementation/README.md`](../full/03_implementation/README.md), [`full/03_implementation/STATUS.md`](../full/03_implementation/STATUS.md), [`full/IMPLEMENTATION_CHECKLIST.md`](../full/IMPLEMENTATION_CHECKLIST.md), [`full/RULE_TRACEABILITY.md`](../full/RULE_TRACEABILITY.md) |
| Full 평가·checkpoint | [`full/04_training/CHECKPOINT_CONTRACT.md`](../full/04_training/CHECKPOINT_CONTRACT.md) | [`full/05_evaluation/JOINT_METRICS.md`](../full/05_evaluation/JOINT_METRICS.md) |
| StabilityAdapter | [`master_plan/06_stability_adapter.md`](../master_plan/06_stability_adapter.md) | [`stability_adapter/02_world_recovery/README.md`](../stability_adapter/02_world_recovery/README.md), [`REWARD_DESIGN.md`](../stability_adapter/02_world_recovery/REWARD_DESIGN.md), [`SETTLE_RECOVER_RESULTS.md`](../stability_adapter/02_world_recovery/SETTLE_RECOVER_RESULTS.md) |
| 하체 선행 검증 | [`lower_body/README.md`](../lower_body/README.md) | [`lower_body/CONTACT_MODEL_AUDIT_20260908.md`](../lower_body/CONTACT_MODEL_AUDIT_20260908.md) |
| Strap 물리 | [`strap_sim/README.md`](../strap_sim/README.md) | [`strap_sim/RESULTS.md`](../strap_sim/RESULTS.md) |
| 논문 실험 기준 | [`PAPER_PLAN.md`](PAPER_PLAN.md) | 목적·질문·환경·ablation·지표·결과 형식 |
| 실험 변경 관리 | [`TRAINING_IMPROVEMENT_PROCESS.md`](TRAINING_IMPROVEMENT_PROCESS.md) | Fret 이력 [`FRET_EXPERIMENT_HISTORY.md`](archive/dated/2026-08-24/FRET_EXPERIMENT_HISTORY.md), Strike 이력 [`strike/03_training/EXPERIMENT_HISTORY.md`](../strike/03_training/EXPERIMENT_HISTORY.md) |

## 보관소

| 위치 | 내용 | 현재 사용 여부 |
|---|---|---|
| [`docs/archive/`](archive/README.md) | Master Plan 이전 계획, 초기 환경 분석, 과거 설계 | 현재 계약에 사용하지 않음 |
| [`fret/archive/`](../fret/archive/README.md) | Fret-v1 425D 구조·규칙·학습 기록 | Fret-v2와 비호환 |
| [`full/archive/`](../full/archive/README.md) | 75D coordinator, residual prototype, 초기 Full 후보 | 현재 105D rule supervisor와 비호환 |
| [`strike/archive/`](../strike/archive/README.md) | 초기 Strike 확장안·감사·pilot | Strike-v2 현재 계약에 사용하지 않음 |
| [`stability_adapter/archive/`](../stability_adapter/archive/README.md) | WSR-001·ArmRecovery 초기 baseline | WSR-002 현재 계약에 사용하지 않음 |
| `docs/2026-*` | 날짜별 미팅 기록 `정리.txt`와 영상·렌더·JSON 산출물 | 출력·현황 경로 보존용; 나머지 날짜별 문서는 `docs/archive/dated/`에 보관 |

날짜별 디렉터리는 도구의 기본 출력 경로와 기존 영상·렌더·JSON 산출물을 보존하기 위해 유지한다. 미팅 기록 `정리.txt`는 원래 날짜별 디렉터리에 남기고, 나머지 문서 파일은 `docs/archive/dated/`로 이동했다. 그 안의 “현재”라는 표현은 작성 당시를 뜻하며, 현재 차원·관절 계약·네트워크 구조의 근거로 사용하지 않는다.

## 문서 운영 규칙

- 현재 설계·계약은 `master_plan/`, 각 모듈의 현재 `README.md`, `tab2body/` 문서에만 추가한다.
- 실험 결과는 해당 모듈의 append-only 이력 또는 날짜별 산출물에 기록한다.
- 폐기된 설계는 삭제하지 않고 해당 모듈의 `archive/`로 이동하며, 상단에 `HISTORICAL` 또는 `SUPERSEDED`를 유지한다.
- 동일한 내용의 복사본을 만들지 않는다. 다른 위치에서 접근해야 하면 링크만 추가한다.
- 문서를 새로 만들면 이 인덱스의 현재 문서 표 또는 보관소 표에 경로와 역할을 추가한다.
- 숫자·관절 순서·observation/action 차원이 바뀌면 [`PROJECT_CONTEXT.md`](../PROJECT_CONTEXT.md)와 관련 정본을 함께 갱신한다.
