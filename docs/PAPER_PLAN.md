# 그래픽스 논문 연구 계획

## 연구 목표

본 연구의 목표는 **물리적으로 자유롭게 움직이는 기타를 스트랩으로만 지지하면서, 전신 휴머노이드가 실제 기타 연주 동작을 생성·복귀하는 방법**을 그래픽스 분야 논문으로 제시하는 것이다. 논문에서는 단순히 학습이 실행되었다고 보고하지 않고, 동일한 시뮬레이터·자산·초기 조건에서 재현 가능한 환경 정의와 정량 결과를 제시한다.

현재 연구의 기본 조건은 다음과 같다.

- humanoid root는 고정한다.
- 기타의 fixed base는 해제한다.
- 기타는 중력·신체/의자 접촉·tension-only strap의 영향을 받는다.
- 손바닥 spring, 기타 pose servo, weld, root assist는 사용하지 않는다.
- 월드 시작 직전 기타의 위치·회전을 immutable target으로 저장한다.
- 기타가 자연스럽게 정착한 뒤 정책이 전신으로 그 시작 pose로 복귀한다.
- 복귀 정책은 손가락을 포함한 91 action을 학습한다.
- 105개 authored ABI slot 중 zero-range fixed hold 8개를 제외한 실질 가동 관절은 97개다.

## 논문에서 답할 질문

| 질문 | 검증 방법 | 핵심 지표 |
|---|---|---|
| 스트랩만으로 자유 기타의 낙하와 과도한 이탈을 억제할 수 있는가? | strap/no-strap 물리 비교 | 위치·회전 오차, 높이, 장력, 신장률 |
| 자연 정착 후 전신 정책이 월드 시작 pose로 복귀할 수 있는가? | WAIT_SETTLE → RECOVER 환경 | 복귀 성공률, 위치·회전 오차, 복귀 시간, 속도 |
| 손가락까지 포함한 91D 제어가 물리적으로 학습 가능한가? | 손가락 포함 정책과 관절별 진단 | joint limit, 비유한 상태, 접촉/관통, action cap |
| Fret·Strike skill prior와 안정화 정책을 분리하는 구조가 필요한가? | fixed-guitar, free-guitar, staged ablation | 음악 정확도와 안정성의 독립 지표 |
| 제안 환경이 보조력에 의존하지 않는가? | palm/root/tether assist ablation | 보조력, strap force, 복귀 성능, 실패 양상 |

## 실험 환경 정의

### 시뮬레이터와 자산

- 시뮬레이터: Isaac Gym Preview 4, 60 Hz control, 프로젝트의 공용 PhysX substep 설정
- humanoid: SMPL/MPL hands 기반 기타 연주 자산
- 기타: `tab2body/assets/guitar_asset.xml`의 독립 rigid body
- 지지물: seated chair와 기타·신체 충돌 형상
- 좌표계·관절 순서·충돌 필터·PD 설정: [`tab2body/env/README.md`](../tab2body/env/README.md)와 [`PROJECT_CONTEXT.md`](../PROJECT_CONTEXT.md)에 고정

### 정책과 단계

| 단계 | 기타 | 정책 | 목적 |
|---|---|---|---|
| G0 | fixed | Fret-v2 + Strike-v2 source prior, rule Synchronizer | 음악 기술과 공통 event 계약 검증 |
| G1 | free + strap | StabilityAdapter, 91D | 자연 정착 후 월드 시작 pose 복귀 |
| G2 | free + strap | G0 source + StabilityAdapter + ActionArbiter | 기타 안정성과 실제 연주를 함께 평가 |

G1의 현재 구현 문서는 [`stability_adapter/02_world_recovery/README.md`](../stability_adapter/02_world_recovery/README.md), 보상 계약은 [`REWARD_DESIGN.md`](../stability_adapter/02_world_recovery/REWARD_DESIGN.md), 결과는 [`SETTLE_RECOVER_RESULTS.md`](../stability_adapter/02_world_recovery/SETTLE_RECOVER_RESULTS.md)에 둔다.

### G1 상태 전이

```text
초기 배치 저장
  → WAIT_SETTLE: humanoid PD hold, free guitar, strap, 정책 action 무시
  → 저속·strap-safe 상태 30 frame 연속
  → RECOVER: 91D 정책 활성화
  → 원래 world-start 위치·회전과 속도 조건을 30 frame 연속 만족
```

정착 위치를 복귀 목표로 다시 저장하지 않는다. WAIT와 RECOVER의 시간·보상·학습 표본을 분리한다.

## 평가 지표

### 안정성·물리 지표

- world-start target 대비 기타 위치 오차와 회전 오차
- 선속도·각속도, 정착 시간, 복귀 시간
- 30 frame 연속 성공률과 timeout/reset 비율
- strap 최대 장력·신장률·경로 안전 여유
- humanoid–guitar·chair 접촉력, 비정상 끼임, 관통 깊이
- 관절별 초기 pose 편차·hard limit 위반·action cap 포화·NaN/Inf

### 연주 지표

- Fret: 지정 손가락 PRESS 정확도, NO_PRESS 정확도, 오압현율, sustain 유지율
- Strike: audible string accuracy, ordered traversal accuracy, release timing, 방향별 성공률
- Full: event 성공률, partial/missed event, delay·rescue rate, 음악 실패와 안정성 실패의 분리율

### 자연스러움 지표

그래픽스 논문에서 자연스러움을 주장할 때는 시각 영상만으로 결론내리지 않고, joint velocity/acceleration/jerk, 불필요한 동작량, 접촉 지속성, 관절별 힘·토크 분포를 함께 보고한다. 사람 동작 데이터와의 비교가 없으면 “human-like” 대신 “물리·운동학적 plausibility”로 표현한다.

## 비교군과 ablation

최소 비교군은 다음과 같이 고정한다.

1. passive seated PD: 정책 residual 0
2. no strap: 기타 fixed base 해제, strap만 제거
3. strap-only: 현재 제안 조건
4. artificial assist ablation: palm/tether/root 보조를 각각 추가한 진단용 상한선
5. fixed-guitar G0: 기타를 고정한 source skill 기준선

각 비교군은 동일한 초기 기타 교란, seed, episode 길이, asset·collision 설정을 사용한다. 인공 보조군은 제안 방법의 구성요소로 주장하지 않고, 보조력 의존 여부를 확인하는 ablation으로만 보고한다.

## 기여 후보와 주장 조건

아래 항목은 결과가 확보된 뒤에만 논문의 기여로 확정한다.

- 스트랩 장력과 실제 신체·환경 접촉을 이용하는 자유 기타 지지 환경
- 자연 정착과 immutable world-start target을 분리한 전신 복귀 프로토콜
- 손가락을 포함한 91D StabilityAdapter와 105D named action ABI의 명시적 관절 소유권
- Fret·Strike 기술 prior, rule-based timing supervisor, 안정화 정책을 분리한 단계적 학습 구조

각 기여에는 반드시 환경 정의, 재현 가능한 설정, 비교군, 평균과 분산, 실패 사례, 동영상 또는 시각화가 대응되어야 한다. 구현 또는 CPU contract test만 통과한 항목은 논문 기여가 아니라 시스템 구현 상태로 기술한다.

## 결과 기록 형식

모든 본 실험은 다음 정보를 함께 저장한다.

- experiment ID, git commit 또는 코드 지문, asset·strap·collision hash
- simulator/control/substep, seed, 병렬 환경 수, iteration, checkpoint
- action/observation manifest와 관절 순서
- 초기 교란과 episode 종료 조건
- 평균·표준편차·95% 구간, 성공률, timeout/reset, failure reason
- deterministic rollout 영상과 frame-level JSON trace
- 기존 결과와 비교할 때 사용한 평가 스크립트 버전

결과 문서에는 `PASS/FAIL`만 쓰지 말고, 성공률과 물리 실패 원인을 분리해 기록한다. 현재 G1 결과는 아직 복귀 성능 미검증 상태이므로, 환경·배관 검증 통과를 학습 성공으로 표현하지 않는다.

## 논문용 읽기 순서

1. 이 문서의 연구 목표·질문·기여 후보
2. [`master_plan/README.md`](../master_plan/README.md)의 전체 시스템 설계
3. [`stability_adapter/02_world_recovery/README.md`](../stability_adapter/02_world_recovery/README.md)의 G1 환경
4. [`stability_adapter/02_world_recovery/REWARD_DESIGN.md`](../stability_adapter/02_world_recovery/REWARD_DESIGN.md)의 단계·보상 계약
5. [`stability_adapter/02_world_recovery/SETTLE_RECOVER_RESULTS.md`](../stability_adapter/02_world_recovery/SETTLE_RECOVER_RESULTS.md)의 현재 검증 결과
6. [`lower_body/CONTACT_MODEL_AUDIT_20260908.md`](../lower_body/CONTACT_MODEL_AUDIT_20260908.md)의 물리 실패·접촉 분석
7. Fret·Strike 독립 결과와 [`full/05_evaluation/JOINT_METRICS.md`](../full/05_evaluation/JOINT_METRICS.md)의 공동 지표

논문 초안의 실험표·그림·주장 문장은 이 문서의 질문과 지표에 대응시켜 작성한다.
