# 문서 목차

모든 문서를 순서대로 읽을 필요는 없다. 지금 필요한 목적의 문서에서 시작한다.

## 지금 필요한 문서

| 목적 | 먼저 읽을 문서 | 필요한 경우에만 읽을 상세 문서 |
|---|---|---|
| 프로젝트 실행·설치 | [루트 README](../README.md) | [현재 상태와 다음 과제](../PROJECT_CONTEXT.md) |
| 기타 자세 복원·유지 | [StabilityAdapter 사용 안내](../stability_adapter/README.md) | [통합 설계·검증 결과](2026-09-14/STABILITY_UNIFIED.md), [Fret·Strike 연주 결합 계약](../stability_adapter/INTEGRATION.md) |
| 전체 연구 흐름·모듈 책임 | [Master Plan](../master_plan/README.md) | [공통 계약](../master_plan/08_shared_contracts.md), [승급·평가](../master_plan/09_curriculum_and_evaluation.md) |
| 오디오→탭·운지 | [Stage1 안내](../tab2fingermapping/README.md) | [설치](../tab2fingermapping/SETUP.md), [운지 알고리즘](../tab2fingermapping/fingermapping/ALGORITHM.md) |
| 왼손 압현 | [Fret 안내](../fret/README.md) | [학습 안내](../fret/03_training/README.md) |
| 오른손 타현 | [Strike 안내](../strike/README.md) | [학습 안내](../strike/03_training/README.md), [규칙](../strike/RIGHT_HAND_RULES.md) |
| 전체 연주 결합 | [Full 안내](../full/README.md) | [구현 상태](../full/03_implementation/STATUS.md), [checkpoint 계약](../full/04_training/CHECKPOINT_CONTRACT.md) |
| 하체·스트랩 물리 | [하체 검증](../lower_body/README.md), [스트랩 검증](../strap_sim/README.md) | 각 모듈의 결과 문서 |
| 코드·공통 학습 운영 | [학습 안내](../tab2body/TRAINING.md) | [코드 구조](../tab2body/STRUCTURE.md), [물리 환경](../tab2body/env/README.md) |
| 논문·실험 개선 | [논문 계획](PAPER_PLAN.md) | [실험 변경 절차](TRAINING_IMPROVEMENT_PROCESS.md), [관련 연구](related_work_analysis/README.md) |

설계 의도와 향후 계약은 `master_plan/`, 실제 실행 방법·지원 범위는 모듈 README와 코드·검사 결과를
함께 확인한다. 설계가 문서에 있다는 이유로 구현 완료로 해석하지 않는다. 내용이 충돌하면
현재 안내를 코드·검사 결과와 대조해 수정하고, 과거 기록을 현재 설정으로 사용하지 않는다.

## 결과와 이전 기록

| 위치 | 찾을 내용 |
|---|---|
| [2026-09-14 목차](2026-09-14/README.md) | Stability 통합 결과, Fret 진단, 원본 근거 위치 |
| [이전 Stability 보고서](2026-09-14/archive/README.md) | 이전 문서·중간 근거를 담은 압축 보관 파일과 복원 안내 |
| [완료된 Stability 작업 계획](archive/plans/stability/README.md) | 재설계부터 통합까지의 체크리스트·결정 근거 |
| [초기 Stability 실험](../stability_adapter/archive/README.md) | static/arm/world recovery 및 통합 이전 검증 기록 |
| [이전 프로젝트 상태·결정 로그](archive/PROJECT_CONTEXT_PRE_UNIFICATION.md) | 기존 PROJECT_CONTEXT의 과거 본문·함정·사용자 결정 |
| [공통 보관소](archive/README.md) | 그 밖의 과거 설계와 날짜별 기록 |
| [Fret 보관소](../fret/archive/README.md), [Strike 보관소](../strike/archive/README.md), [Full 보관소](../full/archive/README.md) | 모듈별 이전 구현과 실험 |
| [2026-09-12 설명 자료](2026-09-12/README.md) | 당시 구조를 설명한 온보딩 자료; 최신 실행 안내는 위 표 참조 |

원본 학습 로그·checkpoint는 실행 폴더를 유지한다. 날짜별 문서에 복사한 중간 근거·영상은 압축 보관 안내를 따른다.
보관 문서의 “현재”, 성공률, 명령은 작성 당시 기준이다. 보관은 미검증 항목의 완료를 뜻하지 않는다.

## 문서 작성 규칙

- 실행 명령은 해당 모듈 README에서 관리하고, 다른 문서는 링크로 안내한다.
- 현재 상태는 PROJECT_CONTEXT에 짧게 갱신한다. 상세 실험 본문을 계속 덧붙이지 않는다.
- 같은 실험의 후속 결과는 기존 보고서에 추가한다. 계획·결과·분석을 매번 별도 문서로 늘리지 않는다.
- 완료 계획과 이전 계약은 보관소에 두고 현재 안내로 돌아오는 링크를 붙인다.
- 문서 이동 시 내부 상대 링크와 참조 문서를 함께 갱신한다. 실행 산출물의 경로는 보존한다.
- 현재 학습 안내로 읽어야 할 문서가 늘어나면, 새 문서 작성 전에 기존 문서에 합칠 수 있는지 확인한다.
