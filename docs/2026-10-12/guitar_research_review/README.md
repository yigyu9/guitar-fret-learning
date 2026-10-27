# 기타 연구 전체 흐름 검토

> 기준일: 2026-10-09
> 범위: 오디오 입력부터 실제 시뮬레이터 연주까지의 전체 연구 흐름과 현재 구현·검증 공백

이 문서는 2026-10-05 기준의 [PROJECT_CONTEXT](../../../PROJECT_CONTEXT.md)를 2026-10-06~08의
별도 StabilityAdapter 2 결과와 연결해 보완한다.

## 요약

현재 연구는 오디오→탭·운지, 곡별 왼손 Fret, 오른손 Strike, 공통 이벤트·동기화, 자유 기타 안정화, 전신 실행기로 구성된다. 앞쪽 데이터·개별 skill·CPU 결합 계약에는 상당한 구현이 있지만, **Fret·Strike를 같은 Isaac Gym 환경에서 실행하는 고정 기타 G0 물리 rollout이 아직 없어 전체 연주를 처음부터 끝까지 검증한 결과는 없다.** StabilityAdapter에는 서로 다른 두 경로가 있다. `stability_adapter/`의 lean 경로는 환경·스트랩·reset·3초 WAIT까지 확인했으며 접근·그립 policy 학습은 미구현이다. `stability_adapter_2/`에는 5초 물리 제어 진단과 정적 배치 도구가 추가됐지만 정책 학습·연주 전환은 검증되지 않았고, 물리 실험은 2026-10-08 이후 일시 중단 상태다.

이번 검토에서는 기존 계약이나 수치를 임의로 바꾸지 않았다. 전체 흐름과 증거를 구분하고, 현재 계획에 없던 접근법 비교와 채택 조건을 보충했다.

## 읽는 순서

1. [연구 흐름과 현재 상태](/home/ajou/yigyu/3/docs/2026-10-12/guitar_research_review/01_RESEARCH_FLOW_AND_STATUS.md)
2. [미흡점·대안·비교 기준](/home/ajou/yigyu/3/docs/2026-10-12/guitar_research_review/02_GAP_ANALYSIS_AND_OPTIONS.md)
3. [계획서 보충 내역과 다음 순서](/home/ajou/yigyu/3/docs/2026-10-12/guitar_research_review/03_PLAN_SUPPLEMENTS_AND_NEXT_STEPS.md)
4. [구현·실험·학습 진행 계획](/home/ajou/yigyu/3/docs/2026-10-12/guitar_research_review/04_IMPLEMENTATION_EXPERIMENT_TRAINING_PLAN.md)
5. [현재 구현 및 실행 결과](/home/ajou/yigyu/3/docs/2026-10-12/guitar_research_review/05_IMPLEMENTATION_AND_EXPERIMENT_RESULTS.md)
6. [학습 자원 preflight 기록](/home/ajou/yigyu/3/docs/2026-10-12/guitar_research_review/training_preflight.json)

## 기준 문서

- 전체 설계: [Master Plan](../../../master_plan/README.md)
- 2026-10-05 기준 상태 요약: [PROJECT_CONTEXT](../../../PROJECT_CONTEXT.md)
- StabilityAdapter 실행 기준: [Lean StabilityAdapter 계획](../plans/LEAN_STABILITY_ADAPTER_EXECUTION_PLAN.md)
- StabilityAdapter 2의 최근 결과: [세션 요약](../stability_adapter_2/SESSION_WRAP_UP_2026-10-08.md)
- 실제 실행 안내: [루트 README](../../../README.md)
- 관련 연구 정리: [관련연구 분석](../../related_work_analysis/README.md)

## 증거를 읽는 기준

- **구현**은 코드나 실행 문서에서 확인되는 기능을 뜻하며, 성능 달성을 뜻하지 않는다.
- **검증**은 저장된 검사·평가 결과가 있는 범위까지만 인정한다. smoke, CPU 계약 검사, 짧은 WAIT는 장기 학습이나 연주 성공의 증거가 아니다.
- **미검증**은 설계가 있어도 실행 결과가 없거나, 과거 산출물을 현재 코드에서 재현하지 않은 항목이다.
- 과거 날짜의 계획·수치·checkpoint는 역사 자료로 구분한다. 최신 모듈 문서와 코드 상태가 다르면 차이를 기록하고 다시 확인한다.
