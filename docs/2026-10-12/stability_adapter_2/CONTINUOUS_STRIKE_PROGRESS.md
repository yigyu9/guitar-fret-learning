# 연속 타현 연결 진단 현황

이 문서는 현재 연속 작업의 sealed 5초 진단을 나란히 요약한다. 각 실행은 1200 physics steps와 151 native video frames이며, free guitar/no strap, fixed root·하체, torso PD, self-collision, frozen checkpoint `strike_010000`, learning update 0이라는 큰 실행 범위를 유지했다. 조건별 READY/phase/recovery 제어는 서로 다르다.

| 진단 | READY / hit / accepted | 회복·종료 관측 | 최대 기타 회전 변화 | PLAY actor steps |
|---|---:|---|---:|---:|
| [READY P+I](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/README.md:1) | 1 / 0 / 0 | 타현 인정 없음 | 8.991° | 251 |
| [Phase-target 잔차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/README.md:1) | 0 / 1 / 1 | clearance 미달성, terminal 2.6667초 | 44.171° | 111 |
| [Soft orientation 잔차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/README.md:1) | 0 / 0 / 0 | 5초 내 terminal 없음 | 45.290° | 251 |
| [Recovery priority, gain 0.5](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/README.md:1) | 1 / 1 / 1 | clearance reached 3.2667초, phase 2→1 3.35초, terminal 3.85초 | 9.020° | 182 |
| [Recovery speed, gain 1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/README.md:1) | 1 / 1 / 1 | clearance reached 3.15초, phase 2→1 3.35초, terminal 3.8167초 | 9.020° | 180 |
| [Recovery speed, gain 2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/README.md:1) | 1 / 1 / 1 | clearance reached 2.95초, phase 2→1 3.0333초, terminal 3.25초 | 9.020° | 146 |
| [Timed EXIT gate](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/README.md:1) | 1 / 1 / 1 | clearance lifted 4.5833초, reached/scheduled completion 없음, 5초 내 terminal/HOLD 없음 | 9.075° | 251 |

모든 진단은 5초 내 full-song completion을 보이지 않았다. partial F1은 실행마다 PLAY 길이와 관측 가능한 이벤트 수가 다르므로 성능 순위로 비교하지 않는다. source terminal 이후의 HOLD는 목표를 유지한 채 physics를 계속 기록한 상태이지, 물리적 평형이나 원본 연주 정책의 자연 종료를 입증하지 않는다.

추가 점검에서 adapter의 진입 거리 기준 6 mm 이하가 source approach가 열리기 전에 EXIT 전환을 유발한 두 사례를 확인했다. 각각 event 1/2에서 source approach-open보다 236.5/524.1 ms 빨랐다. helper 대조상 시간 gate는 adapter에만 적용됐고 source flag·시간·phase를 덮어쓰지 않았다. 후속 [timed-EXIT 진단](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/README.md:1)은 5초 동안 source terminal이나 HOLD 없이 PLAY를 이어갔지만, clearance reached/scheduled completion은 관측되지 않았다. 이는 별도 saved-result 관측이며 전체 연속 작업의 완료를 뜻하지 않는다.

## Native 영상

각 행은 해당 진단의 저장된 5초 native 영상이다. 영상은 151 frames, 30 fps, stream duration 5.033333초다.

### READY P+I

![전신 READY P+I](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/data/images/whole_body.mp4)

![손 근접 READY P+I](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/native/data/images/hands.mp4)

### Phase-target 잔차

![전신 phase-target](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/data/images/whole_body.mp4)

![손 근접 phase-target](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/native/data/images/hands.mp4)

### Soft orientation 잔차

![전신 orientation 잔차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/data/images/whole_body.mp4)

![손 근접 orientation 잔차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_orientation_residual_v1/native/data/images/hands.mp4)

### Recovery priority, gain 0.5

![전신 recovery priority](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/data/images/whole_body.mp4)

![손 근접 recovery priority](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_priority_v1/native/data/images/hands.mp4)

### Recovery speed, gain 1

![전신 recovery speed gain 1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/data/images/whole_body.mp4)

![손 근접 recovery speed gain 1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v1/native/data/images/hands.mp4)

### Recovery speed, gain 2

![전신 recovery speed gain 2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/data/images/whole_body.mp4)

![손 근접 recovery speed gain 2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_recovery_speed_v2/native/data/images/hands.mp4)

### Timed EXIT gate

![전신 timed EXIT](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/whole_body.mp4)

![손 근접 timed EXIT](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/images/hands.mp4)

### EFFORT 활성화 확인 (무정책 진단)

오른팔 12축을 첫 네 physics step 동안 EFFORT로 설정한 OFF/ON 비교를 별도로 완료했다. 두 실행은 각각 1,200 step, 151 native 영상 프레임이며 9개 검사 모두 통과했다. 초기 상태·POSITION PD 목표·초기 질량행렬은 일치했고, ON의 첫 요청은 `R_Shoulder_z`에 10.000001907 Nm였다. 이 값은 명령이지 측정 토크가 아니다. 네 step 뒤 ON−OFF 좌표 차이는 최대 0.039242268 rad, 속도 차이는 3.846986488 rad/s였으며 이후 원래 POSITION PD를 복원했다. 이는 해당 환경에서 짧은 EFFORT 텐서 제출에 대한 응답 관측이다. 무정책 물리 진단으로 연주 성공이나 EFFORT 제어 채택을 뜻하지 않으며, 다음으로 POSITION damping-only 비교를 검토할 수 있다. [상세 결과와 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/README.md).

### PLAY 오른팔 damping 진단

PREPARE 설정을 유지하고 PLAY handoff(0.816667초)에서만 오른팔 shoulder/elbow/wrist 9축 damping을 기존값의 0.25배로 낮춘 단일 요인 진단을 완료했다. 요청값과 native getter readback은 정확히 일치했다. 5초·1,200-step 실행에서 PREPARE/PLAY/HOLD는 49/11/240 control step이었고, 1초에 source terminal 뒤 HOLD로 전환됐다. target hit과 accepted release는 0, physical release와 wrong crossing은 각각 4였다. HOLD 진입 때 `pick_behind_guitar_body`는 false였다. 기타 최대 위치 변화는 59.193 mm, 최대 회전 변화는 8.843°였다. 이 damping 변경은 채택하지 않았으며 연주 성공도 관측되지 않았다. [상세 결과와 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_play_damping_v1/README.md).

### 실제 APPROACH 진입 뒤 오른팔 damping

timed EXIT baseline 상태에서 실제 source motor phase 1을 처음 관측한 1.266667초까지 감쇠를 유지한 뒤, R shoulder/elbow/wrist 9축의 damping만 0.25배로 낮췄다. 별도 대조에서 전환 전 controls 76개와 switch 시점을 포함한 native 전체 상태 trace 39개가 baseline과 정확히 일치했다. 이는 전체 1200 physics steps가 일치한다는 뜻은 아니다. 5초 기록/1200 steps/151 frames/20 checks, 1051 closure 변경 0이다. PREPARE/PLAY/HOLD는 49/54/197 control samples였고 PLAY handoff는 0.816667초였다.

source READY1, accepted hit1 및 physical target hit1을 얻었다. 1.350000초 타현은 adapter event key `[0, 2, 1]`의 zero-based event 0, 첫 음표 string 2 DOWN이며 타현 후 event index는 1이다. +44.484798 ms timing error다. 이전 timed EXIT의 2.783333초 hit는 event 3이어서 더 이른 clock hit를 같은 scheduled event 성능 비교로 보지 않는다. 첫 wrong crossing은 damping 전 1.033333초 string 3에서 이미 발생했고 RECOVER 중 1.500000초 string 1, 1.683333초 string 1, 1.700000초 string 0 wrong이 더 발생해 source가 1.716667초에 terminal 됐다. physical release5/miss1/wrong crossing4였다.

낮은 damping은 RECOVER까지 유지됐고 첫 RECOVER command 1.366667초부터 clearance lifted/reached/scheduled completion은 모두 0이다. 최대/종료 기타 회전 변화 7.095455°/5.414131°, 위치 변화 46.353646/39.461086 mm; 범위 내 표본 292/300(정책49/54)이다. 마지막 running F1 0.285714는 조기 terminal로 짧아진 PLAY 노출에서 얻은 부분 점수다. 이 damping schedule은 채택하지 않고 full music completion으로 판정하지 않는다. 다음 비교는 APPROACH에만 0.25 damping을 적용하고 RECOVER 첫 명령 전에 baseline damping을 복구한다.

[결과·저장 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/README.md:1), [APPROACH-only 후속 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_APPROACH_ONLY_DAMPING_PLAN.md:1).

![전신 APPROACH damping 진단](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/images/whole_body.mp4)

![손 근접 APPROACH damping 진단](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/images/hands.mp4)

### APPROACH-only damping 진단

APPROACH(source phase 1)에서만 오른팔 shoulder/elbow/wrist 9축 damping을 0.25배로 낮추고 phase 2 전환 때 기준값으로 복원한 5초 saved native 진단이다. 1,200 physics steps, 151 camera frames, 20/20 checks였다. native 실행 입력 closure 1,056개는 변경 0이며, 분석기 입력은 별도 7개 파일로 before/after SHA가 동일하다. PREPARE/PLAY/HOLD는 49/135/116 control samples다. 네 native readback 전환은 1.266667초 phase 1→0.25, 1.366667초 phase 2→1, 2.383333초 phase 1→0.25, 2.766667초 phase 2→1이며 property/state 보존 검사는 정확히 통과했다. 첫 baseline 복원 1.366667초 직전 controls 82개와 해당 시점까지의 native 전체 trace 42개는 직전 APPROACH-damping 실행과 exact prefix였다(6개 비교 입력 SHA 불변). 이는 prefix 근거이며 전체 1,200 step 상태가 같다는 뜻은 아니다.

첫 타현 1.350000초는 첫 음표(event index 0) string 2 DOWN, timing +44.484798 ms로 timely `target_hit`였다. 두 번째 physical/geometry hit 2.750000초는 event index 3 string 2 DOWN이며 premature, timing −64.536217 ms라 `target_hit`는 아니었다. 합계 READY1, target_hit1, physical target hit2, accepted release mask2, physical release6, miss3, wrong4였다. READY wrong 1.033333초 string3 뒤 RECOVER wrong 2.783333초 string1, 3.016667초 string2, 3.050000초 string1이 이어져 source는 3.066667초 terminal 됐다. clearance lifted/reached/scheduled completion은 1.400000/2.183333/2.366667초였고 실제 recovery가 완료됐지만, 오교차로 종료되어 전체 연주 성공이 아니다. Partial F1 0.400000006은 짧은 PLAY 노출의 값이며 성능 완료 판정에 쓰지 않는다. 최대/종료 회전 변화 7.095455°/4.927969°, 위치 변화 46.353646/36.393910 mm, playable region 제어 287/300·policy125/135다.

이 결과는 APP 구간의 damping만 낮춘 diagnostic이다. 음악 성공은 false, 학습 업데이트는 0이다. 후속 timed-ENTRY는 geometry acceptance와 timely target hit를 분리하며 현재 계획은 [STRIKE_TIMED_ENTRY_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_ENTRY_PLAN.md:1)이다. [결과 문서 및 저장 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_only_damping_v1/README.md:1).

### Timed ENTRY 대기 waypoint 진단 (완료 retry)

source APPROACH가 닫혀 있는 동안 adapter가 원본 READY geometry 3을 사용하도록 한 timed-ENTRY 진단을 `native_retry_v1`로 완료했다. 5초/1,200 physics step/151 camera frame/21 checks 통과이며 native input closure 1,059개 변경 0, 분석기 입력 별도 7개 파일의 SHA도 before/after 동일하다. PREPARE/PLAY/HOLD는 49/172/79 control sample이었다. 닫힌 phase 1에서 geometry 3 waypoint 명령 16회가 있었지만, 첫 음표 event 0의 1.350000초 string 2 DOWN hit(+44.484798 ms)는 유지됐다. event index 3의 2.750000초 string 2 DOWN은 geometry accepted/physical hit였으나 premature(−63.5116 ms)여서 추가 timely target hit가 아니다. READY1, timely target hit1, physical target hit2, physical release6, miss6, wrong4; partial F1=0.307692319다. source는 wrong-crossing count로 3.683333초 terminal 됐다. clearance lifted/reached/scheduled completion은 1.400000/2.183333/2.366667초로 완료됐지만 전체 연주 성공은 아니다. 최대/종료 회전 변화 7.095455°/3.690350°, 위치 변화 46.353646/28.895391 mm이며 playable region 제어 241/300, policy162/172다. 이 geometry crossing/acceptance는 source sensor 기록이지 실제 음향 또는 줄 힘 측정이 아니다.

최초 run은 94 전신·손 프레임 뒤 exit 143으로 중단됐고 wrapper finalization/report가 없었다. partial 산출물은 보존했으나 성공 근거나 결과 영상으로 사용하지 않는다. 재실행은 별도 output 경로에서 같은 실행기 hash로 완료했다. 다음 단계는 source APPROACH에서 R9 damping owner를 기다리는 우선순위 분리 검토이며 [timed-ENTRY 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_ENTRY_PLAN.md:1)에 기록돼 있다. [완료 retry 결과·영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/README.md:1).

### Timed wait priority: 닫힌 시간창 R9 READY goal ownership

5초/1,200 physics steps/151 camera frames/21 checks 완료. Native closure 1,063개 변경 0이며 analysis input은 별도 7개 파일 SHA 불변이다. PREPARE/PLAY/HOLD=49/130/121. source wrong-crossing count로 2.983333초 terminal. 닫힌 source phase 1에서 22개 command는 actual I를 유지하고 READY geometry 3을 썼으며 R9 goal은 previous goal + 2×bounded IK correction 방식이었다. 기존 damping schedule은 유지했다. 첫 event0 hit 1.350000초(+44.484798 ms), READY1/target hit1/physical hit1, 첫 scheduled recovery 2.366667초 완료. physical release5/miss3/wrong4, partial F1=0.222222239. 최초 READY wrong 1.033333초 string3/physical direction code +1, 이후 source phase1 wrong은 2.716667초 string2/−1, 2.950000초 string3/−1, 2.966667초 string4/−1. 회전 max/end 8.126144°/5.421837°, position max/end 46.353646/41.235741 mm; playable-region controls235/300, policy120/130. Geometry sensor hit는 실제 줄 힘·음향 측정이 아니며, 이번 trajectory는 goal ownership의 단독 인과효과를 입증하지 않는다. 다음 [WAIT-REBASE 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_WAIT_REBASE_PLAN.md:1)은 actual-angle IK-fit을 검토하며 독립 사전검수 대기다. [결과 문서와 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_priority_v1/README.md:1).

### Timed wait rebase: R9 대기 목표를 actual angles에서 재기준화

5초/1,200 physics steps/151 camera frames/21 checks 완료. PREPARE/PLAY/HOLD=49/178/73, source wrong-crossing terminal=3.783333초. Native closure 1,066개 변경 0, 별도 analysis input 7개 파일 SHA 불변. source phase 1의 닫힌 대기 sample 42개에서 actual angles + bounded IK delta로 READY 목표를 계산하고 I를 유지했다. RECOVERY는 previous goal + 2×delta였다. 첫 event0 string2 DOWN hit는 1.350000초, +44.484798 ms. READY/timely/physical/accepted each1; 첫 scheduled recovery 2.366667초. Native aggregate physical release4, miss6, wrong4, partial F1=.166666672. 2.750000초 actual pick Gz=97.983354 mm, READY reference=20.3 mm. 기타 max/end rotation=7.095455°/5.416182°, position=46.353646/39.772717 mm; playable region control283/300, policy164/178. Geometry hit는 실제 줄 힘이나 음향 측정이 아니며 timely hit 1개는 full-song success가 아니다. Prefix comparison과 독립 검수는 아직 작성 전. [phase 결과와 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/README.md:1).

### POSITION shoulder goal pulse 진단

원본 81-DOF POSITION PD 조건에서 OFF/X/Y/Z 어깨 단일축 goal pulse 네 native trial을 완료했다. 각 trial 1,200 physics steps·151 frames·7 checks 통과; initial states와 PD properties는 exact, 81 target readback exact. 첫 4 step(0–3)에만 지정 shoulder 축 +0.02 rad를 주고 step4부터 baseline 목표로 복원했다. Actor/music/learning 0. Native closure는 OFF1069/X1070/Y1074/Z1074로 조건별 상이하나 각각 변경 0, 별도 analysis input33 SHA 불변. step4 shoulder-relative response matrix 행 actual x/y/z, 열 target x/y/z는 [[0.00114428252,0.000235922635,-0.0000808611512],[-0.000147730112,0.001002937555,-0.000537902117],[0.0000243186951,0.000623136759,0.00088134408]] rad. Native state FK max error 1.832856931e−5°. 자기축 양의 반응과 교차축 연성은 관측했지만 축 permutation, dynamic coupling 전체, 더 큰 tracking error의 단일 원인은 인증하지 않는다. DOF force getter는 합성 force이며 drive-only torque가 아니다. Mass matrix는 read-only, control usage0. 각각 영상 차이는 4-step pulse라 작을 수 있다. 이는 prepared-strike/music baseline이 아니라 joint response probe다. Source plan pre-review PASS, final review 예정. 다음 HUMAN EFFORT damping 분리 plan도 별도 사전검수 PASS지만 native는 미실행. [phase README 및 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_position_goal_probe_v1/README.md:1).

### HUMAN EFFORT damping 4조건 probe

동일 native 초기 상태에서 오른팔 12 DOF를 첫 4 physics step EFFORT/stiffness0으로 둔 뒤 original POSITION properties를 복원한 네 조건을 완료했다. damping 0/기존값 유지와 requested torque OFF0/ON nominal10Nm를 교차했다(실제 float32 요청은 10.000001907Nm). step4 이후 requested torque는 명시적으로 0이지만 `R_Shoulder_z` 목표는 초기값이 아니라 +0.05rad 변경 목표를 유지했다. 각 실행은 1,200 steps·151 native frames·9 checks, closure d0_off1074/d0_on1075/d1_off1075/d1_on1075 모두 changed0. 별도 analyzer 입력27 SHA 불변. 네 초기 상태 exact이며 기존 zero-damping OFF/ON 자료와 각각 152/152 native state를 exact 재현했다. Actor/music/learning0.

step4 shoulder scalar DOF q/qdot 차이는 raw/README에 정리했다. ON−OFF Shoulder_z 차이는 damping0에서 +0.0392422676086rad/+3.84698648750782rad/s, damping retained에서 +0.00228708982468rad/+0.04414859227836rad/s로 요청 조건별 응답 차이가 관측됐다. 이는 관절 scalar q 차이이지 body-relative rotation 또는 측정된 drive torque가 아니다. 전체 관절의 damping 효력·hybrid 동등성·연주 성공을 인증하지 않는다. Mass matrix는 read-only. [결과·native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/README.md:1), [분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_damping_probe_v1/analysis/summary.json).

후속 Strike EFFORT spring/damping 실행은 별도 [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_EFFORT_DAMPED_ARM_PLAN.md:1)과 [사전검수 PASS](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_effort_damped_arm_v1/pre_review.md)에서 다룬다. 본 4조건 probe는 그 연주시험 결과가 아니다.
