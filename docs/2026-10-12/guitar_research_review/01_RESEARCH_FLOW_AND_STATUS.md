# 연구 흐름과 현재 상태

> 2026-10-09 기준. 설계 상태와 성능 검증 상태를 분리해 기록한다.

## 연구 목표와 범위

기타 오디오에서 연주 목표를 만들고, 물리 시뮬레이터에서 앉은 humanoid의 왼손 압현과 오른손 타현을 실행한 뒤, 자유 기타 조건까지 확장하는 연구다. 현재 기준은 곡별 기술 prior와 규칙 기반 timing supervisor를 조합하는 구조다. 각 곡에 별도 Fret·Strike 정책을 학습하므로 현재 결과는 **곡별 성능**이며, 보지 못한 곡으로의 일반화를 입증하지 않는다.

```text
오디오
  → 음·탭 추정 및 검수
  → 운지·오른손 주법 계획
  → 검수된 song bundle
  → 곡별 Fret / Strike skill
  → Canonical PlayEvent + Synchronizer
  → 단일 시뮬레이터 G0
  → 자유 기타 StabilityAdapter / G1·G2
```

G0는 고정 기타에서 음악 skill과 동기화를 검증하는 단계, G1/G2는 기타가 물리적으로 움직이는 조건을 다루는 목표 단계다. 전체 설계의 모듈 경계는 [Master Plan](../../../master_plan/README.md)에 있다.

## 주요 전개

- Stage1 오디오 전사·코드 분석에서 시작해 곡 단위 song bundle과 finger mapping을 만들었다.
- 왼손 Fret-v2와 오른손 Strike-v2를 각 곡에 맞춰 독립 학습하는 구조를 정리했다. source 정책 승급과 실제 결합 rollout은 별도 gate로 남아 있다.
- Full 영역에서 Canonical PlayEvent, rule Synchronizer, frozen source loader와 named action ABI의 CPU 계약을 구현했다.
- 2026-10-05 새 `stability_adapter/` lean 계획으로 reset·strap·노이즈·3초 WAIT 기본 환경을 다시 구성했다.
- 2026-10-06부터 별도 `stability_adapter_2/` 물리 진단 경로를 만들었고, 2026-10-08에는 quiet pose feedback 요약과 정적 기타 배치 도구·시각 범위 비교를 정리했다. 물리 실험은 같은 날 사용자의 요청으로 멈췄다.

두 StabilityAdapter 경로는 같은 과제의 두 코드 버전이 아니다. lean 경로는 33개 왼팔 관절을 대상으로 단계형 단일 PPO task를 계획한다. `stability_adapter_2/`는 root와 하체를 고정하고 양팔·손 66개 관절의 저수준 목표를 비교해 온 진단 task다. 초기 기타 pose, 관절 소유권, WAIT 의미와 목표가 달라 같은 성능표에 넣거나 수치·정책을 바로 이식할 수 없다.

## 단계별 정리

| 단계 | 현재 구조·구현 | 확인된 근거 | 남은 핵심 공백 |
|---|---|---|---|
| 1. 오디오→탭·음악 입력 | Conformer 기반 탭 전사, ACE 보조 결과, chord track 융합, note/fingering 산출 및 검수 후 song bundle 등록 | [Stage1 안내](../../../tab2fingermapping/README.md), 곡 단위 입력 구조 | 공통 입력 schema가 정식 봉인되지 않았다. 전사 오차·코드 불일치의 사람 검수와 provenance가 곡마다 일관되게 운영되는지 점검이 필요하다. |
| 2. 탭→왼손 운지·오른손 계획 | 왼손 finger mapping은 규칙·빔 탐색 기반 canonical 계획이다. 오른손은 별도 `strike_plan`에서 공격 여부, agent, 방향, timing 등을 정한다. | [운지 알고리즘](../../../tab2fingermapping/fingermapping/ALGORITHM.md), [Strike 계획 규칙](../../../strike/RIGHT_HAND_RULES.md) | 단일 선택 계획이 불확실한 입력·대체 운지·물리적으로 어려운 화음에 얼마나 견고한지 측정과 사람 수정 흐름이 필요하다. 두 계획을 공통 event로 합치는 schema 계약도 완전히 봉인되지 않았다. |
| 3. 검수된 곡 입력 | `data/song_bundles/<song_id>/`가 실행 입력의 경계다. 원본, mapping, training target과 provenance를 곡별로 보관한다. | [song bundle 안내](../../../data/song_bundles/README.md) | Stage1 작업 산출물에서 등록 bundle까지 변환·검수·재현 절차를 자동화하고, 입력 변경과 checkpoint의 연계를 유지해야 한다. |
| 4. 왼손 Fret | Fret-v2는 곡별 30-action/420-observation PPO 기술 prior다. 획득·유지·해제, lookahead와 물리 readiness를 다룬다. | [Fret 학습 안내](../../../fret/03_training/README.md), [Master Plan Fret 계약](../../../master_plan/03_fret.md) | full-song source 승급은 미완료다. 문서에 기록된 중지의 연속 압현 획득·유지가 병목 후보이며, 학습 평균을 음악적 완주로 간주할 수 없다. 화음·바레 지원도 제한적이다. |
| 5. 오른손 Strike | Strike-v2는 곡별 30-action/303-observation 정책으로 pick·strum·recovery를 하나의 조건부 정책에서 다룬다. 물리 detector가 실제 crossing을 판정한다. | [Strike 안내](../../../strike/README.md), [Strike 계약](../../../master_plan/04_strike.md) | full-song 평가 기록은 있지만 source 승급은 미완료다. 긴 학습 성능·사람다운 동작·현재 코드에서의 재현 가능성을 별도로 확인해야 한다. |
| 6. 공통 event·Synchronizer | Canonical PlayEvent compiler, 규칙 기반 timing supervisor, frozen source loader와 named action 합성은 CPU 계약 범위에서 구현됐다. readiness와 detector 결과로 실행·delay·skip을 관리한다. | [Full 구현 상태](../../../full/03_implementation/STATUS.md), [Synchronizer 설계](../../../master_plan/05_synchronizer.md) | 고정 기타 물리 rollout은 아직 없다. 별도 Fret/Strike 환경과 단일 물리 step 사이의 clock·action·detector 경계가 실제로 맞는지 확인해야 한다. |
| 7a. StabilityAdapter lean 경로 | 공용 기타·humanoid, 원본 strap, reset/noise와 자세 유지 기반 환경을 만들었다. 3초 WAIT 및 부분 reset이 저장 결과로 확인됐다. | [환경 검증 안내](../../../stability_adapter/README.md), [lean 계획](../plans/LEAN_STABILITY_ADAPTER_EXECUTION_PLAN.md) | 접점·33관절 학습·REACH/GRIP/TRANSPORT는 미구현이다. 짧은 WAIT는 장기 안정성이나 복원 성능의 증거가 아니다. |
| 7b. StabilityAdapter 2 진단 경로 | 기타 자유·root/하체 고정·양팔 66관절 조건에서 5초 quiet feedback/제어 비교와 정적 배치 도구를 구축했다. 최근 요약상 baseline/wrist/feedback 조건의 5초 끝점은 대략 13.6–13.8mm 및 2.89–2.92° 오차이며, palm의 양의 raw lambda 지지 접촉은 관측되지 않았다. | [10-08 세션 요약](../stability_adapter_2/SESSION_WRAP_UP_2026-10-08.md), [누적 결과·영상 목차](../stability_adapter_2/README.md) | 결과는 quiet 조건 5초와 정적 시각 비교에 한정된다. Fret/Strike 목표 전환·연주성·policy 학습·자연 배치의 동적 유지에는 근거가 없다. 2026-10-08 이후 물리 trial은 재개 요청 전까지 중단 상태다. |
| 8. FullBodyPlayer·최종 평가 | 105 named ABI slot(실제 이동 가능한 97 DOF)의 G0 action bridge 및 CPU 조립 계약이 있다. | [Full 상태](../../../full/03_implementation/STATUS.md), [Full 목표](../../../master_plan/07_full_body_player.md) | one-simulator Isaac `FullG0Task`, 실제 고정 기타 연주, StabilityAdapter와 G1 결합이 미구현이다. end-to-end 연주 성능과 기술 보존을 아직 입증하지 못했다. |

## StabilityAdapter 계획에서 확인된 범위

계획서는 환경 배치·원본 strap·초기 노이즈·33개 왼팔 action 순서·단일 프레임 관측·단계·힘 기반 grip gate·종료·PPO 초기값·산출물을 구체화한다. 현재 1단계 결과에는 단일 환경 16개 검사, 노이즈 8개 환경의 21개 검사, strap 단위 검사 7개 통과가 기록돼 있다. 이 수치는 환경 초기 검증의 근거로만 사용한다.

계획서가 의도적으로 남긴 확정 전 항목은 손바닥 기준점과 접근 영역, PD/토크/목표각 제한, force 집계, 관측 차원과 회전 noise 합성, reward/termination return, 안전 경계와 운영 주기다. 이 항목은 계획대로 해당 단계의 물리 측정 후 정해야 한다.

## 현재 증거로 말할 수 있는 것

1. Stage1과 곡별 Fret·Strike 학습 배관은 존재한다.
2. Full event/synchronizer/action 계약은 CPU 수준에서 상당히 구현돼 있다.
3. lean 자유 기타 환경은 짧은 초기화·WAIT 조건을 통과했으며 학습 가능한 그립은 아직 없다. 별도 진단 경로에는 실제 5초 저수준 feedback 결과가 있으나 palm 지지와 연주 전환은 검증되지 않았다.
4. 실제 전신 연주를 물리적으로 연결한 G0 rollout이 없으므로, 연구 전체의 최종 성공은 아직 판단할 수 없다.
5. 문서상 과거 checkpoint·결과가 있어도 현재 계약과 맞지 않거나 실행 폴더가 없으면 현행 성능 근거로 승격할 수 없다.

## 핵심 참조

- [루트 README](../../../README.md): 현재 실행 구조
- [Master Plan](../../../master_plan/README.md): 설계 정본과 모듈 역할
- [Full 구현 상태](../../../full/03_implementation/STATUS.md): CPU와 물리 통합 경계
- [StabilityAdapter 실행 기준](../plans/LEAN_STABILITY_ADAPTER_EXECUTION_PLAN.md): 현재 독립 복원 환경
- [논문 연구 계획](../../PAPER_PLAN.md): 질문·평가 지표·비교군
