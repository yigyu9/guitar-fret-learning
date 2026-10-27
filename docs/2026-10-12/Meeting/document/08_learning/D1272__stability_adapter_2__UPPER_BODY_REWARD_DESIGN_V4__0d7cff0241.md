# StabilityAdapter 2 — 음악 결과 우선 보상 정리 v4

2026-10-11. 상태: **PROPOSED — 설계와 합성 수식 검사, 환경 적용·물리 시험·학습 전**. [v3.1](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:1)은 보존한다. 이번 버전은 보상 집계·음악 의미·종료 설계를 대체하며, 상체81관절·Actor/Critic512→256·부위별 행동 범위는 유지한다.

## 작업 계획과 범위

- [x] 전체 연구·Fret·Strike·시간/시선·평가 계획과 v1/v2/v3.1 설계 대조.
- [x] 음악 결과 / 기타 범위 / 작은 자세·접근 선호로 보상을 재분류.
- [ ] 합성 수식 검사·설명 이미지·독립 검수·변경 색인·보존 감사. 완료는 main PLAN에 추가한다.
- [ ] 별도 단계: 현재 기타 기준 detector/음악 tracker/회전 범위 구현·행동 시험·짧은 pilot.

이번에는 기존 런타임·체크포인트·자산·물리 조건을 변경하지 않는다. 과거 master_plan의 몸통9 유지·66관절/residual 제안보다 최신 사용자 결정인 상체81 공동 정책과 작은 몸통 움직임을 우선한다. 원본 source 평가 의미와 새 정책의 학습 보상 의미는 구분해 모두 기록한다.

## 참고한 계획과 수정 이유

| 근거 | v3.1에서 수정할 점 | v4 결정 |
|---|---|---|
| [Fret 음악·접촉 의미](/home/ajou/yigyu/3/master_plan/03_fret.md:122) | 지정 손가락 성공/wrong_press를 음악 성공과 동일시 | 타현 대상 현의 effective sounding fret와 실제 누름을 우선. 원래 운지 지표는 별도 유지 |
| [Fret 보상 우선순위](/home/ajou/yigyu/3/master_plan/03_fret.md:286) | 유지+2/초·접근+0.5/초가 긴 음에서 무제한 누적 | 유지 보상은 원래 eligible 구간으로 정규화. 접근·자세는 사전 고정된 보조 예산 안에서 집계 |
| [유효 프렛/현 영역](/home/ajou/yigyu/3/master_plan/03_fret.md:141) | 점·현 중앙 거리 최적화가 유효 영역 내부도 차별 | 유효 cell 내부는 동일 접근 점수. press 단계는 누름과 양립하는 깊이 영역 사용 |
| [Strike 보상·판정](/home/ajou/yigyu/3/master_plan/04_strike.md:243) | pick 목표점 접근·현별 hit pulse만으로 대체 | 인정 crossing·현·방향·순서·시간 및 전체 gesture 완료 사용. 기하 접근은 작은 보조항 |
| [공통 clock](/home/ajou/yigyu/3/master_plan/08_shared_contracts.md:19) | 기다리기/재시도로 보상 구간을 늘릴 위험 | 시간표·분모·horizon을 시작 전 고정. 실패로 score clock을 멈추거나 되감지 않음 |
| [기타 허용범위](/home/ajou/yigyu/3/stability_adapter_2/PLAYABLE_ENVELOPE_CONTRACT.md:5) | 초기 복원·접촉 증가를 성공으로 착각할 위험 | 범위 안 비용0. 손바닥/엄지 영구 접촉·접촉력 증가 보상 없음 |
| [평가·승급](/home/ajou/yigyu/3/master_plan/09_curriculum_and_evaluation.md:152) | scalar 상승만으로 학습 성공 판단 | 음악·범위·물리 안전의 AND 평가, 항별 결과·worst subgroup 별도 보고 |
| [Fret 접근 커리큘럼](/home/ajou/yigyu/3/fret/03_training/fingertip-approach-curriculum.md:62) | 매우 가까운 곳에서만 Gaussian 신호가 커지는 접근 | 유효 영역까지 거리의 넓은 선형 접근 후보. 초기 거리 분포를 native 환경에서 재측정 |
| [Goal Pair 시간/평가 계획](/home/ajou/yigyu/3/docs/plans/fret_goal_pair_structural_fix_20260929.md:1) | 유지 ramp·readiness dwell·eligible 분모를 혼동할 위험 | 실제 평가 창의 warm/cold oracle, 미관측·획득/이탈을 별도 검사 |

기존 구현은 assigned-finger press_success와 [현/fret 기준 wrong_press](/home/ajou/yigyu/3/tab2body/env/tasks/task_fret.py:2912), [원본 sustain tracker](/home/ajou/yigyu/3/tab2body/env/metrics.py:379)를 사용한다. master_plan의 sounding-fret readiness가 현재 native 환경에 구현·연결됐다고 가정하지 않는다. **새 음악 판정기는 구현 gate**이며 원본 metrics/termination/teacher qualification을 조용히 바꾸지 않는다.

## 합산 구조와 고정 분모

`R_episode = Σ_e F_e + Σ_e S_e − 2·N_ref·(Σ_t Δt/T_phys · C_g,t) + β·(R_continuity + R_aux)`.

F와 S는 각 기술의 **원래 음악 event**별 점수다. 음악 검사대상/required target이1개 이상인 event만 N_F/N_S에 포함한다. REST/idle의 F/S/A/K는0이며 가짜 성공 event를 만들지 않고 원래 timeline/전환은 유지한다. 개방현 음은 required string이 있으므로 음악 평가에 포함한다. source의 NO_PRESS/목표변경을 새 음악 event와 자동으로 일대일 대응시키지 않는다.

같은 PRESS가 여러 strike에 이어지면 Fret event를 복제하지 않고 해당 event의 검사점들을 집계한다. N_F/N_S는 시작 전 고정하고 `N_ref=max(N_F,N_S,1)`이다. 후속 곡에서도 범위 비용의 상대 규모가 event 수 때문에 자동으로 줄지 않게 한다. event별 현 수로 평균하므로6현 strum을 단순6배 보상하지 않는다. 서로 다른 곡의 scalar 합계는 직접 성능 비교에 사용하지 않는다.

`m_max=max(6,각 Fret O의 검사점 총수,각 Strike required target 수)`, `β=6/m_max`를 시작 전 고정한다. 유지·timing·접근·자세의 전체 예산을 β로 제한해 반복 검사점이 많은 긴 PRESS에서도 하위항이 한 음의 상위 결과를 덮지 않도록 한다. event가 없으면 m_max=6이다. 실제 manifest/검사점 수는 학습 전에 봉인하며 정책이 조절할 수 없다.

T_phys는 고정 준비2초+계획된 음악 구간의 **시뮬레이션 초**다. PREP에는 음악/접근/경로 보상이 없고 범위·작은 자세 항만 계산한다. PLAY의 단일 score clock은 원본 frame0부터 단조 증가한다. 2초는 이번 연결/평가 조건이며 필수 운반 단계가 아니다. phase/음악 구간의 정확한 경계와 준비 중 제어권은 구현 전에 manifest에 봉인한다.

연속 항은 Δt 또는 해당 창과 제어 구간의 겹침 길이를 곱한다. 완료 시점 항에는 Δt를 곱하지 않는다. 분모는 실제 실행 길이·현재까지 성공 수·남은 활성 손가락 수로 바꾸지 않는다. source 총 reward를 다시 더하지 않는다. 아래 숫자는 **새 pilot 후보**이며 v3.1의 초당 계수와 단위가 다르다.

## Fret: 실제 음악 상태 → 유지 → 필요한 해제

`F_e = 2·(2O_e−1)`. 유지·해제·간섭·early release는 아래 2차 음악 예산으로 별도 집계한다.

| 값 | 정의 | 범위/반영 |
|---|---|---|
| O_e | 필요한 현별 검사점에서 sounding fret가 목표와 같고 실제 press-depth/cell 및 원래 readiness dwell 조건이 유효한 비율. 개방현은 해당 현의 fretted interference가 없어야 함 |0~1. 완전 성공+2, 완전 누락/오음−2. event 검사점 집계 후1회 |
| U_e | fretted PRESS의 원래 eligible 시간에 각 필수 현이 유효한 음악 상태였던 비율의 **최솟값** |0~1. 현재 유효 상태를 원래 eligible 길이로 정규화. 아래+0.10·β 예산에서 지급 |
| L_e | 다음 목표의 개방현/낮은 fret/필요 운지 이동을 위해 음악적으로 필요한 해제를 실제로 수행한 비율 |0~1. 필요 없는 해제·idle NO_PRESS는0 |
| I_e | 원래 감독 창에서 타현될 현의 음높이를 바꾸는 압현의 시간 비율 |0~1. 정상 엄지/손바닥 지지·무해한 추가 압현은 제외 |
| E_e | 원래 필요한 sustain을 끊은 검증된 early-release 사건 |0/1. event당1회. 원래 요구 시각/의미를 보존 |

O의 검사대상/분모·허용 창은 canonical/source 계약에서 사전 확정한다. **양손 모드의 O는 해당 target의 원본 인정 crossing 시각에서 sounding-state와 readiness dwell을 평가한다.** 앞선 오음 crossing 이후 deadline에 손가락을 고쳐도 O 성공으로 바꾸지 않는다. crossing이 없거나 거부되면 해당 O 항0과 joint failure로 처리하고, Fret 단독 readiness를 성공 타현으로 보고하지 않는다. Fret-only pilot은 원래 press/readiness deadline의 검사점을 쓰고 이를 음악 타현 성공으로 부르지 않는다. 정책이 검사대상·현 수·시간 창을 선택하지 않는다. accepted subframe crossing과 실제 press snapshot의 시각 대응/직전 dwell은 native 구현 gate이며 다음 제어frame의 상태로 대신하지 않는다.

다른 손가락이 목표 프렛을 눌러도 음높이/실제 누름이 유효하면 음악 상태는 인정한다. 원래 assigned-finger 압현/아치/지정 운지 성공률은 별도 출력하고 약한 계획 운지 선호를 넣을지는 후속 비교로 남긴다. 목표보다 낮은 추가 press·현재 타현되지 않는 현의 press는 master_plan의 무해한 추가 압현 규칙을 따른다. 물리적 위험은 별도 평가한다.

U는 현재까지의 실제 표본만 누적한다. 각 required fretted target j의 원래 eligible 길이 T_j를 분모로 u_j를 누적하고, `ΔU=min_j u_j(now)−min_j u_j(previous)`로 지급한다. 일부 현만 잘 유지해도 chord 전체 유지 만점을 얻지 못한다. 원래 eligible 창을 확보하지 못하면 유효 실패로 처리하며 분모를 줄이지 않는다. 모든 현이 개방현/휴식이면 U=0이고, 열린 현 준비 O와 간섭 I로 평가한다. eligible 시간0인 유지 항은 지급하지 않고 capability/계약 문제인지 확인한다.

유지 성공은 보상 U와 별개로, 유효 표본·원본 hold_threshold/longest-dropout 조건을 적용한 별도 음악 tracker에서 판정한다. 현재 source 기본0.90/3 control frames를 후보로 계승하되 현별 sounding-state tracker와 원본 finger tracker는 구분한다. 짧은 dropout이 평균에 가려지는지 보고하고, 실제 구현 전에는 tracker 동등성을 주장하지 않는다.

## Strike: 인정된 타현과 gesture 완료

`S_e = 2·(2h_e−1) − w_e`. gesture 완료와 timing 품질은 아래 2차 음악 예산으로 집계한다.

- h_e: 원본이 인정한 required target/현 hit 수÷manifest의 required target/현 수. 올바른 현·방향·phase/permission·시각 조건을 보존한다. hit당 `+4/m_e`를 지급하고 원래 deadline에 기본−2를1회 정산한다. hit/miss를 별도 pulse로 다시 더하지 않는다.
- f_e: 전체 required target을 방향·순서·gesture 완료 조건까지 충족하면1, 아니면0. picking도 원래 full-event 조건을 따른다. partial strum은 full completion 보조점을 받지 못한다.
- τ_e: 원본 허용 창 안에서 인정된 hit의 원본 per-string timing quality를 required target 수로 평균한 값0~1. 누락/거부는0이며 deadline을 넘긴 hit를 보너스로 살리지 않는다. timing quality의 실제 field·단위·offset 계약은 구현 전에 대조한다.
- w_e: 원본 고유 invalid crossing 수. wrong string·중복·역방향·permission 위반 등 원본 분류를 보존한다. **동일 crossing은1번**, 같은 event에서 서로 다른 wrong crossing은 각각−1. hit와 같은 crossing을 중복 오류 분류로 다시 벌하지 않는다.

가상 피크는 음악 판정 geometry이며 타현 반력을 기타에 가하지 않는다. 실제 오른손/팔–기타 충돌은 별도 물리 상태다. K 접근 보상이 높더라도 인정 crossing이 없으면 h=0이다. [Strike phase·recovery](/home/ajou/yigyu/3/master_plan/04_strike.md:180)를 사용하고 현재 기타의 entry/exit/clearance 목표를 검증한다. 경로·grip·recovery를 각각 무제한 보너스로 추가하지 않는다.

## 2차 음악 예산: 유지·전환·gesture·timing

`R_continuity = 0.10Ū + 0.02L̄ − 0.05Ī − 0.05Ē + 0.05f̄ + 0.03τ̄`.

Fret의 각 값은 사전 고정 N_F, Strike의 각 값은 N_S로 평균한다. 해당 기술이 없으면 항0이며 예산을 재배분하지 않는다. Ū의 온라인 누적 차분에0.10·β/N_F를 곱하고, I도 원래 창의 겹침 Δt로 누적한다. L/E/f/τ는 해당 고유 event에1회 반영한다. 전체 예산은 **β·[−0.100,+0.200]**, 폭0.300·β다.

v3.1의 긴 hold+2/초와 최초 v4 초안의 event별U+1은 상위 음높이 결과를 덮을 수 있어 채택하지 않는다. 예를 들어6현 검사점 정음/U=0의2점보다,5현 정음/U≈1의2.333점이 높아질 수 있었다. v4는 유지와 해제도 별도 하위 예산으로 제한한다. 지속 유지·전환은 여전히 필수 평가 gate이며 작은 coefficient가 실패를 허용한다는 뜻은 아니다.

## 기타 범위: 내부0, 외부 거리 비용

`C_raw = 0.5·[max_axis ρ(d_axis/0.02m)+ρ(d_SO3/5°)]`, `C_g=min(1,C_raw)`.

ρ는 [v3.1의 무차원 Huber](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:55)다. d_axis는 사용자 world actor-root 상자 밖 거리, d_SO3는 허용 Euler 상자가 만드는 회전집합까지의 최단 SO(3) 거리다. 20mm/5°는 **비용 척도**이고 범위를 축소하거나 팀원의 body-center 허용표로 바꾸지 않는다. 범위 내부 C_raw=C_g=0, 초기 p/q 복원·범위 내 속도·정지·복귀 pulse 보상은 없다.

학습용 비용만1에서 포화시켜 event 예산·실패 return을 계산 가능하게 한다. 실제 raw 거리/비용·최대 이탈·지속/복귀·slip/drop은 포화 없이 저장하며, 큰 이탈을 허용한다는 뜻이 아니다. 심각한 실패 문턱은 별도 native 검증 후 정한다. 회전집합 판정은 미구현이므로 초기 quaternion 오차나 Euler 단일 분해값으로 대체하지 않는다.

경계 여유와 바깥으로 향하는 속도는 관측/예상 이탈 진단으로 유지한다. 첫 pilot에는 별도 내부 경계 비용을 넣지 않는다. 예방 항을 검토할 때도 깊은 내부/작은 정상 흔들림의 비용0을 유지하며 OFF/ON 비교한다. 접촉 개수·raw lambda 증가·손바닥 또는 엄지의 영구 접촉을 안정화 성공 보상으로 쓰지 않는다.

## 3차 접근·자세 예산: 전체 episode −0.074 ~ +0.076

`R_aux = 0.05·Ā + 0.025·K̄ + 0.001·Ḡ − 0.025·B̄ − 0.005·V̄ − 0.025·X̄ − 0.010·J̄ − 0.009·D̄`.

각 값은0~1이다. Ā는 각 Fret 접근 창의 시간 평균을 **사전 고정 N_F**로 평균, K̄는 각 Strike 유효 phase 창의 시간 평균을 **사전 고정 N_S**로 평균한다. 해당 기술이 없으면 그 항0이며 남은 항에 예산을 재배분하지 않는다. 각 창 T_e는 시작 전 고정하고, 겹치는 창도 event별 겹침 Δt/T_e와1/N을 사용한다. 정책의 성공 여부·조기 종료로 분모를 바꾸지 않는다. 길이0 창은 기하 보너스0으로 기록하고 음악 event를 삭제하지 않는다.

나머지는 T_phys의 시간 평균이다. B/V/J/D는 v3.1의 몸통 자세/몸통 속도/native 한계/실제 제출 목표 변화 비용을 각각 `min(1,C)`로 제한한 학습용 값이다. X는 검수된 비허용 native body-pair 접촉 존재0/1. 정상 손–넥·허벅지–기타 지지는 제외한다. 비용을 포화해도 원래 q/qdot/Chest 회전·한계초과·포화·접촉 로그는 그대로 남긴다. 심각한 물리 실패는 이 작은 보상으로 대체하지 않는다.

G는 정면 또는 지정한 점을 바라보는 v3.1의 좌표 교정·단위벡터 정렬값이다. **전체 episode 최대+0.001·β**이므로 긴 준비/음에서 시선만으로 보상을 쌓지 못한다. 지정점 기본 후보는 [공통 GazeTarget strike_zone](/home/ajou/yigyu/3/master_plan/08_shared_contracts.md:195)이며 기타에 부착된 고정 구역 중앙을 추적한다. 개별 현/event마다 목표를 바꾸지 않는다. 정면/사용자 custom 모드는 최신 사용자 허용에 따른 선택이고 source gaze ABI와 혼동하지 않는다. 목표/축 무효는 G=0+미유효 로그이며 임의 local+Z를 정면으로 가정하지 않는다.

A는 현재 기타 좌표의 **유효 press cell/깊이 영역까지 거리**에 대해 `clamp(1−d_region/0.25m,0,1)`을 사용한다. 넓은 선형 접근은 기존 Fret coarse-reach 계획을 참고한 첫 후보이고 25cm는 native 초기 거리 분포와 비교해 조정할 척도다. 프렛10~90%/현 중점 영역과 유효 press-depth 조건은 source geometry 계약에서 가져온다. 유효 영역 안 점수1, hover면 실제 누름 성공은0이다. 깊이 상한·패드 marker·원본 영역이 미확정이면 먼저 검증한다. 누름 단계에서 손끝을 줄 위 hover 점으로 끌어당기지 않는다. 필요한 target 중 최소 품질을 사용하고 계획 운지와 음악 성공을 혼동하지 않는다.

K는 검증한 현재 phase의 pick entry/exit/clearance 목표 영역까지 거리 d에 대해 `exp[−(d/0.03m)²]`인 품질0~1이다. 실제 가상 피크 자세·현재G 및 phase validity를 사용한다. 세부 heading/grip/아치 선호는 first pilot의 별도 항으로 추가하지 않는다. 손가락 분포·pressed-drag/손등접촉·과한 교차는 진단에 남기고 필요성과 신호가 확인될 때 **기존 보조 예산 안에서** 추가한다.

2·3차를 합한 전체 폭은 `0.450·β=2.700/m_max < 4/m_max`다. **다른1차 음악 항·기타 비용이 같을 때 모든 하위항이 가장 좋게 바뀌어도 required hit/음높이 검사점 하나의 성공→실패 손실을 상쇄하지 못한다**는 undiscounted 비교다. Fret event의 검사점이6개보다 많아도 고정 β로 이 관계를 유지한다. 상위 음악 항끼리의 거래, 기타 안전 비용과의 거래, 할인된 PPO 목적/탐색에 대한 전역 최적성 보장은 아니다. discount는 초 단위 시간척도로 봉인하고 native 항별 분포·학습에서 다시 확인한다.

## 움직임 분배와 제약의 역할

상체81/512→256, root·하체 고정, 몸통9 requested 목표 native∩q_ref±5° 후보를 유지한다. 실제 q±2°/Chest 상대회전3°는 자세 deadband이며 actual 각도 보장이나 관절 고정이 아니다. 부위별 요청 목표 속도 후보 body0.10/head0.50/arm1.00/finger1.50rad/s와 탐색 후보는 native 행동 시험 전 미검증이다. q_ref/Chest 기준은 reset 시 한 번 기록하며 episode 중 재설정하지 않는다.

Thorax부터 손가락66은 native 범위를 사용한다. 초기 팔/손 자세 복원·많이 움직일수록 보상·손바닥/엄지 영구 접촉·의미 없는 모든 손가락 동시 지지를 추가하지 않는다. 머리에는 강한 초기각 복원 비용이 없다. 관절 한계·단일 목표 제출·free guitar 조건은 실행 구조로 보장하고, 보상만으로 보장한다고 설명하지 않는다.

## 조기 종료와 미유효 신호

새 정책의 음악 실수는 원래 deadline에서 점수/metric으로 기록하고 계획된 음악 horizon까지 진행하는 계약을 후보로 둔다. score clock을 늦추거나 실패 음을 성공할 때까지 재시도하지 않는다. source 체크포인트 비교는 원래 first done 계약 그대로 유지한다. 새 runtime에서 source 실패 신호를 계속 실행 가능한 음악 오류/물리 fatal로 구분하기 전에는 이 후보를 적용하지 않는다.

물리 fatal은 실제 시뮬레이션을 안전 중단하고 남은 계획 구간을 **가상 실패 return 계산**으로 처리하는 후보다. Fret의 앞선 유효 검사점과 Strike의 인정 hit/타이밍 증거는 유지하고 **미래의 미관측 검사점/hit만0**으로 둔다. 미정산 O/h/τ는 원래 고정분모로 원래 deadline에서 정산한다. 이후 U/L/완료 f의 새 성공은0이며 이미 유효하게 완료·지급한 항은 유지한다. 이미 지급한 hit/U를 이중 차감하지 않는다. 이후 C_g=1, B/V/X/J/D=1, A/K/G=0인 흡수 비용을 남은 각 Δt/T_phys에 적용한다.

이 비용만으로 미래 wrong-crossing 비용 회피까지 막는다고 주장하지 않는다. w는 event당 고유 crossing 수이므로 상한 없이 event 벌점이 증가할 수 있다. **새 detector 실행 계약의 control-bin별 고유 crossing 최대수 M_cross와 남은 ledger의 최저 보상을 먼저 검증해야 한다.** fatal tail 후보에는 남은 bin별−M_cross, 미지급2차 음수항의 최악 잔여 예산과 위 범위/자세 흡수 비용을 포함한다. 이 가상 tail은 source의 실제 wrong/early-release counter를 만들어내는 방식이 아니며 별도 `failure_return_proxy`로 기록한다. 보수적 tail의 규모/학습 분산도 작은 pilot 전에 확인한다. 상한·γ·ledger가 미확정이면 종료 처리가 봉인되지 않은 것이므로 학습을 시작하지 않는다.

discounted return은 남은 계획 control bins의 실패 보상에 실제 γ를 적용해 계산한다. 아직 지급하지 않은 기본−2와 남은 hit 점수를 정산하고 과거 유효 검사점/누적값·deadline을 보존해야 한다. 임의−5 terminal bonus나 time-limit 방식의 정상 value bootstrap으로 대체하지 않는다. 실제 catastrophic 중단step 보상과 다음 bin부터의 tail을 분리해 같은 step을 두 번 계산하지 않는다. 치명 중단 시각 뒤에 물리가 계속된 것처럼 영상을 만들지 않으며 실제 종료 시각/이유·실패 return을 분리한다. 이 처리는 runtime/PPO 구현 gate이고 이번 수식 검사가 구현 인증은 아니다.

필수 detector/범위/clock/geometry 신호가 없거나 timestamp가 어긋나면 **측정 실패**로 pilot을 중단한다. 미유효를 정상0 비용·성공 상태·물리 fatal로 몰아 학습하지 않는다. 선택적 gaze만 마스크0을 허용한다. 정상 무접촉과 접촉 조회 실패는 구분한다.

## 구현 전 검증과 채택 기준

1. CPU 합성 검사: 긴 음/다른 frame rate의 U 예산, chord 최솟값, 개방현/idle 해제0, 프렛 영역 plateau/먼 거리 접근 단조성, 부분 strum/고유 wrong crossing, 기타 내부0/외부 증가·학습 cap, 보조 예산 및 terminal ledger/할인 합산. 실제 창의 warm/cold oracle로 readiness1-frame과 source6/12-frame hold ramp의 목적 차이도 확인한다.
2. Native 신호 매핑: 실제 pad/press-depth와 sounding fret, source/fresh 음악 tracker 비교, 현재G 속도·phase/permission·canonical string 변환·단일 clock, SO(3) 포함/거리·q와−q·특이점, 접촉 whitelist·시선 축과 timestamp. D manifest에 실제 tracker/ledger 상태와 필요 예산 분모·clock 정보를 포함한다.
3. 무학습 행동/짧은 이벤트: 초기값·실제5초 전신/손 영상, 항별 원값/포화값/가중값/유효율, body 실제움직임·target rate 포화·기타 이탈과 음악 판정. checkpoint 시험은2초 준비부터 원본 종료까지 녹화한다.
4. 짧은 PPO: 같은 초기 배치/event/seed/예산에서 무학습·scratch 공동 정책 및 자격 있는 source/prior 비교. 첫 pilot은 한 음/해제, 다음 전환·타현/짧은 구절이며 행동 차원은 처음부터81이다. reward 상승 외에 음악·범위·안전의 AND와 worst subgroup을 확인한다.

v3.1 대비 U 정규화/유효영역 접근/작은 보조 예산의 효과는 단계별 ablation으로 확인한다. 초기 목표·PD·스트랩·자산을 동시에 바꿔 보상 효과를 주장하지 않는다. 기존 source 성공/실패와 원래 finger-based 지표를 보존하고, 새로운 sounding-state 지표 개선만으로 원본 운지 정확도가 개선됐다고 쓰지 않는다.

산출물·수식 검사·비교 이미지·검수는 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/`에 저장한다. main PLAN/README에는 추가 기록만 남긴다. 현재 숫자·종료 후보는 pilot 전에 검증해야 하며 학습 성능 검증 결과가 아니다.
