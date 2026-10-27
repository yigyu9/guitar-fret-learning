# 미흡점·대안·비교 기준

> 아래 대안은 후보군이다. 기존에 합의된 기준을 자동으로 대체하지 않는다. 제안은 동일 입력·초기조건·평가 지표로 비교한 뒤 선택한다.

## 우선순위가 높은 공백

| 우선순위 | 공백 | 영향 | 다음 판단 근거 |
|---|---|---|---|
| P0 | 단일 Isaac 시뮬레이터에서 Fret·Strike를 실행하는 physical G0가 없다. | 모듈 간 타이밍·action·검출 계약과 곡 전체 연주를 검증할 수 없다. | 고정 기타에서 짧은 구간 → 대표 phrase → 곡 전체 순으로, event 단위 trace와 재현 가능한 source bundle을 남긴다. |
| P1 | Fret·Strike source checkpoint 승급이 끝나지 않았다. | CPU runtime이 있어도 물리 결합에 넣을 신뢰 가능한 정책 기준이 부족하다. | 각 모듈의 균일·held-out event/full-song 평가, 안전·정확도·실패 원인과 checkpoint identity를 고정한다. |
| P1 | Stage1의 공통 schema·검수·provenance 계약이 완전히 봉인되지 않았다. | 입력 오류가 운지·정책·동기화 문제처럼 뒤 단계에 나타날 수 있다. | 곡 bundle 등록 시 원본 hash, 변환 버전, 수동 수정, 좌표/줄 convention 및 validation report가 추적되는지 확인한다. |
| P1 | lean StabilityAdapter의 접점·33관절 action·보상·종료·PPO는 계획 단계다. S2에는 일부 저수준 물리 제어 결과가 있다. | 3초 WAIT나 quiet feedback 진단을 그립·복원·연주 성능으로 오해할 수 있다. | lean 계획의 2단계 접촉 검증과 S2의 보유 자료를 구분한다. S2 신규 물리 실험은 재개 요청 전 중단한다. |
| P1 | StabilityAdapter 연구가 lean PPO 경로와 `stability_adapter_2/` 물리 진단 경로로 나뉘어 있다. | 서로 다른 목표·초기 pose·33D/66D action·WAIT 의미가 함께 현재 상태로 읽혀 중복 구현, 잘못된 수치 승계, 연구 주장 혼선이 생길 수 있다. | 당면 연구 질문에 따라 두 경로의 역할을 분리하거나 새 공통 계약으로 합친다. `stability_adapter_2/`의 물리 trial은 2026-10-08 요청에 따라 일시 정지 상태다. |
| P2 | 실행 경로와 연구 목표 사이의 선택/중단 기준은 프로그램 수준에서 미정이다. lean 계획에는 이번 보충으로 방법 비교 게이트를 추가했지만, 두 Stability 경로 중 어디를 우선·통합할지는 미결이다. | 한 방법 또는 두 branch를 관성적으로 유지하면 물리 G0·그립·연주 전환의 핵심 증거가 늦어질 수 있다. | 아래 후보를 실패 양상에 따라 비교하며, smoke만으로 변경을 채택하지 않는다. |
| P2 | 모듈별 지표와 전체 end-to-end 지표의 연결이 아직 실행되지 않았다. | 성능 향상·퇴행의 원인을 모듈 사이에서 분리하기 어렵다. | 동일 trace에서 입력 오류, Fret readiness, Strike crossing, event outcome, 기타 안정성을 함께 집계한다. |
| P3 | 곡별 정책 결과는 곡 간 일반화 주장을 뒷받침하지 않는다. | 논문 주장 범위가 실제 평가보다 커질 위험이 있다. | 우선 곡별 성능으로 보고하고, 일반화를 주장하려면 별도의 곡 분할·전이 조건·baseline을 사전 정의한다. |

## 설계 후보를 넓게 비교하기

| 영역 | 현재 기준선 | 비교할 수 있는 대안 | 장점·비용과 적용 신호 |
|---|---|---|---|
| 오디오→탭 | 현재 전사 pipeline + ACE/chord 보조 + 사람 검수 | 여러 전사 후보를 ensemble해 불일치만 검수, 곡별 수동 correction ledger, 고품질 구간/저신뢰 구간 분리 평가 | ensemble은 오류 후보를 줄일 수 있지만 운영 복잡도가 늘어난다. 사람 검수는 신뢰도를 높이지만 처리 시간이 든다. 우선 song bundle의 provenance와 불일치 목록을 표준화한다. |
| 운지 계획 | 규칙·beam search로 한 개 canonical fingering 선택 | 전역 DP/정수 최적화, 소수 후보 생성 후 물리 feasibility 검사, 사람이 지정한 hint를 constrained planner에 반영 | 최적화는 구간 간 비용을 넓게 볼 수 있지만 목적함수 가정과 계산비가 늘어난다. 동일 song에 후보별 이동량·충돌·압현 성공률을 비교하고 물리 성과가 나아질 때 확장한다. |
| Fret·Strike 학습 | 곡별 PPO skill, 단계형 curriculum | rule/IK/trajectory teacher로 초기 데이터 생성, behavior cloning 후 PPO, task phase별 policy/options, 현재 정책 유지 + 보수적 residual | teacher/BC는 탐색을 줄일 수 있으나 teacher 편향·보정 비용이 든다. phase 분리는 디버깅을 쉽게 하지만 경계 오류가 생긴다. 현재 학습이 특정 단계에서 정체하거나 전체곡으로 일반화되지 않을 때 비교한다. |
| Stability 접근·그립·복원 | 두 별도 경로: lean의 계획상 왼팔 33D 단일 PPO task, `stability_adapter_2/`의 root/하체 고정·양팔 66D 저수준 물리 진단 | (a) lean 단일 PPO, (b) 단계별 REACH/GRIP/TRANSPORT policy, (c) 기하·IK/힘 제어 baseline, (d) bounded residual RL, (e) demonstration/BC warm start, (f) S2 quiet feedback을 연주 goal 전환으로 확장 | 단일 PPO는 희소한 장기 return과 단계 credit assignment가 어렵다. 기하 baseline은 해석 가능하지만 접촉·모델 오차에 민감하다. S2는 native 물리 응답을 제공하지만 hand support·연주성·actor가 검증되지 않았고 lean과 task contract가 다르다. 먼저 연구 질문과 공통 평가 경계를 정한 뒤 소규모 baseline을 고른다. |
| Synchronizer | bounded safe delay를 갖는 결정적 rule supervisor | 규칙 보호구간 안의 learned timing residual 또는 offline threshold tuning | rule은 검증·재현이 쉽다. learned correction은 불확실성·데이터 비용이 추가된다. physical G0에서 규칙 baseline의 miss/delay 분포를 확보한 뒤에만 비교한다. hard event·safety gate는 두 경우 모두 유지한다. |
| Full 결합 | frozen Fret/Strike source + named action arbiter | source는 고정하고 coordinator만 학습, 제한된 end-to-end fine-tuning, 완전 통합 정책 | frozen source는 원인 분리와 성능 보존이 쉽다. joint tuning은 상호 적응 가능성이 있지만 source 퇴행과 재검증 비용이 크다. 먼저 G0에서 frozen baseline과 retention을 확보한다. |
| 실험 진행 순서 | StabilityAdapter 독립 환경을 현재 작업 기준으로 진행 | G0 물리 통합을 먼저 닫기, Stability를 독립 병렬 검증, 둘을 번갈아 진행 | G0 우선은 전체 연주 proof를 앞당기지만 그립 연구를 늦춘다. 독립 Stability 우선은 복원 연구를 진전시키나 최종 결합 공백은 남는다. 단기 논문 목표가 물리 연주인지 자유 기타 복원인지에 따라 우선순위를 정하되 두 결과의 증거를 혼합하지 않는다. |

## 후보 비교의 최소 규칙

1. **단계별 baseline을 보존한다.** 현재 구현의 성공률·실패 원인·실행비를 새 방법과 같은 bundle, 가능한 한 같은 초기조건에서 비교한다.
2. **smoke와 성능 평가를 구분한다.** smoke/짧은 연결 실행은 배관·유한성·저장 검증이고, 정책 성능의 채택 근거가 아니다.
3. **성공과 보존을 함께 본다.** 접근·그립·복원 성공만으로는 충분하지 않다. Fret/Strike의 event 성공, 안전, 접촉·미끄럼, 실패 원인, 실행 비용을 분리 보고한다.
4. **성능 퇴행을 감추지 않는다.** 평균 하나 대신 곡·event·방향·단계별 분포와 실패 표본을 보존한다. 승급 조건은 측정 분포를 본 후 각 모듈 계획에 기록한다.
5. **대안은 관측된 병목에 연결한다.** 학습 정체·단계 누락·물리 충돌·입력 오류 등 신호가 확인되기 전에는 새 기법을 동시에 추가하지 않는다.

## 우선 실행 제안

전체 기타 연주를 먼저 증명해야 한다면 다음 순서가 의존성에 맞는다.

1. Fret·Strike 승급에 사용할 source checkpoint와 song bundle identity를 확정한다.
2. `FullG0Task` 단일 simulator 물리 backend를 구현하고, 같은 physics step에서 source action·detector·event cursor를 연결한다.
3. G0에서 phrase와 full-song rollout을 평가해 event 실패·delay·source retention을 기록한다.
4. 별도로 StabilityAdapter의 접점·33관절·접촉 API를 검증하고, 복원 skill은 독립 task 성능으로 평가한다.
5. G0와 StabilityAdapter를 결합해 G1 retention·안정성·안전 비교를 수행한다.

이 순서는 선택지다. 자유 기타 복원이 당면 논문 질문이라면 StabilityAdapter를 먼저 진행하되, lean PPO task와 S2 저수준 진단은 같은 실험으로 합치지 않는다. S2 물리 trial은 2026-10-08 사용자 요청으로 멈춰 있으므로 이 문서 검토만으로 재개하지 않는다. [논문 연구 계획](../../PAPER_PLAN.md)의 RQ와 비교군에 맞춰 연구 경로·우선순위를 다시 정한다.
