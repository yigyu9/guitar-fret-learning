# 제공된 오른손 규칙 반영표

> **상태: HISTORICAL REQUIREMENT TRACE.** 2026-08-03 당시 R1~R28을 구현 항목으로 내린
> 기록이다. 현재 single/strum 구현 및 보류 상태는 [`RIGHT_HAND_RULES.md`](../RIGHT_HAND_RULES.md),
> [`02_physical_control/status.md`](../02_physical_control/status.md)를 따른다. 특히 본문의
> “strum 미구현” 표기는 현재 상태가 아니다.
>
> 기준 자료: 2026-08-03 제공된 `R1~R28`, 성공 조건, 초기 학습 단계.  
> 실행 판정 갱신: 2026-08-04.  
> 목적: 내용을 누락하지 않으면서 현재 구현 가능 범위를 명확히 한다.

| 제공 규칙 | 실행 판정 | 구현·진단 owner / 승격 조건 |
|---|---|---|
| R1 박자 정렬 | **구현** | RH-C01/02/17/44. `time` 정본과 subframe RELEASE timing을 평가한다. |
| R2 방향 | **구현** | RH-C05/06/15. v1 down=`5→0=+x_g`; up 입력 전에는 확장하지 않는다. |
| R3 목표 현 집합 | **보류** | RH-X01~12. `audible/traversal/muted/protected` mask가 있는 strum v2 입력이 선행돼야 한다. |
| R4 Protected String | **부분 구현** | v1 non-target RELEASE는 FP. strum별 protected mask는 R3 입력 이후 구현한다. |
| R5 시작 위치 | **구현+진단** | READY/entry-side shaping과 `entry_ready`, `entry_distance_m` 로그를 사용한다. |
| R6 피크 자세 | **제어·연속 gate 구현+일부 보류** | 엄지·검지/자유 손가락 residual, mean/p05/min/bad-streak는 구현. 피크 면 각도·뒤집힘은 rigid pick geometry 전까지 측정 불가다. |
| R7 깊이 | **최소 gate 구현·최대값 진단** | detector 최소 depth 적용. RELEASE depth 분포는 `audit_strike_motion.py`로 수집 후 최대값을 정한다. |
| R8 속도 | **최소 gate 구현·최대값 진단** | 최소 횡단 속도 적용. RELEASE/tip speed p95·max를 수집한 뒤 상한을 정한다. |
| R9 현 간 속도 일관성 | **보류** | 단현에는 정의되지 않는다. R3 strum 구현 뒤 줄별 RELEASE 간격·속도 분산을 계산한다. |
| R10 접촉력 | **보류** | marker pick/string에는 pair contact force가 없다. 물리 pick과 collision string이 선행조건이다. |
| R11 Follow-Through | **구현+gate+진단** | `RELEASE_RECOVER`, 12 clean frame, re-arm 종료 gate를 구현했다. 추가 RELEASE/blocked crossing은 count를 초기화하며 completion/reset rate를 수집한다. |
| R12 복귀 중 비접촉 | **재타현 gate 구현·경로 진단** | reverse/duplicate/blocked crossing은 FP이고 recovery reset이다. recovery corridor·역방향 crossing은 motion audit에서도 수집한다. |
| R13 손목 중심 | **진단** | shoulder/elbow/wrist/hand phase별 속도·가속도를 수집한다. 성공 rollout 전 hard 비용을 넣지 않는다. |
| R14 distal/proximal 비용 | **진단** | 관절군별 분포를 비교한 뒤 불필요한 proximal 운동에만 작은 phase-aware 비용을 검토한다. |
| R15 가속·jerk | **진단** | phase·관절군별 acceleration/jerk p95·max와 action saturation을 수집한다. |
| R16 관통 금지 | **진단 monitor 구현** | 오른팔·손 analytical guitar penetration을 매 frame/swept 경로로 기록한다. 현재 termination은 calibration 전 `false`다. |
| R17 피크 파지 | **운동학 파지 구현·물리 파지 보류** | 21-DOF 기준과 A0~S3 residual/gate를 구현. slip·회전·파지력은 rigid pick 이후다. |
| R18 현재 코드 유지 | **보류** | RH-B03. 현재 StrikeTask에는 왼손 goal/state가 없으므로 full-task coordinator가 선행돼야 한다. |
| R19 코드 해제 시점 | **보류** | RH-B04/06. fret sustain/transition 분포로 plan deadline을 정한 뒤 구현한다. |
| R20 다음 코드 완료 | **보류** | RH-B02/05/06. 공통 event와 `delta_stabilize` 측정이 선행조건이다. |
| R21 전환 우선순위 | **보류** | RH-B04. fret anchor/pre-shape plan을 full task에 연결할 때 구현한다. |
| R22 너무 이른 변경 | **보류·후속 진단** | RH-B03/06. sustain과 readiness deadline을 같은 공통 event에서 측정해야 한다. |
| R23 너무 늦은 변경 | **보류** | RH-B05/09. 결합 실패로 기록하되 RH timing 오류와 분리하는 evaluator가 필요하다. |
| R24 FretReady Gate | **실험 보류** | detector hard gate는 금지한다. planned Attack gate와 ungated/soft 방식을 full-task ablation에서 비교한다. |
| R25 공통 이벤트 | **보류** | RH-B01. fret/strike가 공유할 `event_id,target_time` coordinator schema가 필요하다. |
| R26 양손 phase 정렬 | **보류** | RH-B02~06. 두 손 상태기는 독립 유지하고 공통 deadline으로만 연결한다. |
| R27 박자 우선 | **설계 확정·결합 구현 보류** | RH-B08/09. RH timing은 항상 별도 보존하고 combined failure를 추가한다. |
| R28 다음 박 예측 | **RH 일부 구현·양손 보류** | Strike S3 lookahead는 구현. 다음 fret goal·transition time은 공통 coordinator 이후 추가한다. |

R7·R8·R11~R16의 진단은 학습 종료 시 자동 생성되는
`evaluations/strike_*.motion_diagnostics.json`을 정본으로 사용한다. 수치 임계값은 성공/실패 checkpoint
여러 개의 분포가 분리되기 전에는 reward·termination으로 승격하지 않는다.

## 성공 조건의 분해

제공된 하나의 `PerformanceSuccess`는 학습 원인을 보존하기 위해 세 층으로 분해했다.

1. `RightHandSuccess`: timing·direction·ordered strings·zone.
2. `LeftHandReady`: 목표 압현·release·안정화.
3. `CombinedPerformanceSuccess`: 두 결과, 공통 event 정렬과 안전의 결합.

이렇게 해야 왼손이 늦어서 난 잘못된 음을 오른손 timing 오류로 오인하지 않고, 반대로 오른손이 박자를
놓친 사실을 왼손 readiness가 가리지 않는다.

## 초기 학습 단계의 반영

| 제공 단계 | 새 위치 | 판단 |
|---|---|---|
| 고정 코드 + 반복 down | 확장 B0 | strum X0~X2의 오른손 순서 검증 뒤 결합 |
| 두 코드 전환 | 확장 B1 | 느린 transition부터 |
| 매 박 코드 전환 | 확장 B2 | deadline·sustain 분포가 확보된 뒤 |
| 다양한 목표 현 집합 | 확장 X1/X2 | 양손 결합 전에 먼저 오른손 단독으로 구현 |
| Up stroke | 현재 `phrase_dp_microtiming_v3` | plan 방향·줄별 offset, 경로 교차 비용, 양방향 detector, 준비/통과/회복 궤적과 lookahead로 구현 |

현재 A0~A4는 피크 자세→ready→single crossing→timing→실제 strum 문맥 clean recovery를 안정화하고,
S0~S3에서 2~6줄 strum과 timing/zone/곡 통합을 진행한다.
