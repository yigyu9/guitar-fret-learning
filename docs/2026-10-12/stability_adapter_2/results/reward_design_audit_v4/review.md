# v4 학습 유인 독립 감사

요약 판정: **수정 권장 — 실제 학습에 투입할 최종 보상 명세는 미완료**. 음악 결과와 자유 기타 범위·자세 선호를 구분한 방향은 타당하지만, 필수 유지의 학습 유인과 실제 판정/시간/종료 연결은 먼저 확정해야 한다. 아래 Critical은 신규 학습 전 필수 해결 사항이며 현재 런타임에서 재현된 학습 버그라는 뜻은 아니다.

[root 감사 보고서](/home/ajou/yigyu/3/stability_adapter_2/REWARD_DESIGN_AUDIT_V4.md), CPU 계산과 최종 설명/그림의 정합성은 **문제없음**이다. 핵심 여섯 감사 항목을 지지하며, 가중치나 기존 v4를 이 단계에서 직접 수정하지 않는다.

## Critical — 학습 전 필수

1. **평균 유지 보상이 필수 연속 유지 평가를 구별하지 않는다.** [v4:60](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:60)의 U는 시간 비율의 최솟값이고, [metrics.py:379](/home/ajou/yigyu/3/tab2body/env/metrics.py:379)는 비율≥0.90와 최장 dropout≤3frames를 함께 요구한다. 54/60 정상 표본에서 분산된 1-frame dropout 6개와 연속된 6-frame dropout은 U=.90으로 같지만 실제 source CPU tracker의 성공은 1과 0으로 다르다. O=1/E=1/β=1/N_F=1 및 다른 항 동일이라는 가정에서는 해당 보상도 둘 다 2.04다. 제안: 획득 실패·획득 후 이탈·허용 dropout·early release를 분리하고, 필수 지속 평가의 차이가 학습 목적에도 나타나는 후보를 검증한다. E=1은 아직 구현되지 않은 판정의 조건부 가정이다.

2. **1차 보호식은 유지와 보조항 사이의 거래를 막지 않는다.** [v4:77](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:77)의 event별 U 이득은 0.100β/N_F, E 손실은 0.050β/N_F인 반면 [v4:95](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:95)의 3차 전체 폭은 0.150β다. N_F>1이면 U/E 합계 차이도 보조항 거래 폭보다 작다. 검사점에서만 정음이고 나머지 유지 구간은 놓는 선택을 평가 AND만으로 PPO 목적에서 제외할 수 없다. 제안: 필수 유지와 보조 선호의 우선순위를 별도로 정하고, 동일 O에서의 유지 포기 반례를 닫는다. 이 계산은 예산 수준의 빈틈이며 보조항 양끝을 동시에 달성하는 실제 native 궤적을 입증한 것은 아니다.

3. **중간 crossing 승인과 최종 인정 hit를 구분해야 한다.** [task_strike.py:3830](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:3830)의 accepted_release는 [순서/방향 누적](/home/ajou/yigyu/3/tab2body/env/strike_events.py:416)을 통과한 증거다. timing은 3883행 이후, 최종 target_hit의 timing/zone gate는 [3951행](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:3951) 이후 적용된다. 중간 mask를 [v4:68](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:68)의 h에 바로 쓰면 조기/구역 밖 부분 타현에도 지급할 수 있다. 제안: partial strum의 현별 인정 조건과 사건 ID·timestamp를 정의하고 timing/zone-invalid 입력이 h/O/τ 성공으로 들어가지 않는지 검사한다.

4. **할인·지급·PREP·종료 계약은 보상 수식과 함께 확정해야 한다.** [v4:50](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:50)의 Fret 마지막 정산과 [68행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:68)의 중간 hit 지급은 같은 비할인 합계라도 discounted return이 다르다. [PPOConfig:1131](/home/ajou/yigyu/3/tab2body/learning/ppo.py:1131)의 기본 γ=.95는 새 adapter의 확정값이 아니다. 60Hz 가정에서는 현재 행동에 대한 2초 뒤 보상 비중이 약 .00212다. 제안: 초 단위 할인·GAE/critic bootstrap·PREP 제어권·event ledger·정상 timeout·fatal tail을 함께 봉인한다. 고정 시각 −2는 정상 horizon에서 행동과 무관하므로 그 자체를 기다리기 exploit으로 단정하지 않는다. 원본 [Fret:2979](/home/ajou/yigyu/3/tab2body/env/tasks/task_fret.py:2979)는 wrong_press를 물리 실패와 합치고, [Strike:4420](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:4420)는 wrong crossing/recovery timeout으로 done을 만들며 reward도 덮는다. 이유별 새 wrapper 없이 보상식만 교체해서는 v4의 계속 실행/잔여 정산 계약이 구현되지 않는다.

## Warning — 구현·짧은 행동 검증에서 확인

5. **기존 음악 함수와 새 pad/cell 계약은 같지 않다.** [readiness.py:32](/home/ajou/yigyu/3/tab2body/full/readiness.py:32)에 highest occupied fret 함수가 이미 있고 기존 Full 녹화 경로가 사용한다. 그러나 [fret.py:1867](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:1867)의 finger chain 점·[1920행](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:1920)의 원통 반경/ON·OFF hysteresis 및 [1968행](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:1968)의 any-segment raw cell은 [계획의 pad marker·현 중점 영역](/home/ajou/yigyu/3/master_plan/03_fret.md:138)과 다르다. raw cell에는 assigned-finger의 [10–90% position gate](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:2305)도 포함되지 않는다. 제안: 재사용 가능한 음높이 함수와 새 표면/깊이/유효 cell 검증을 분리하고 crossing subframe의 실제 압현/dwell snapshot을 연결한다. 다음 control frame의 상태로 대신하지 않는다.

6. **event/해제/phase의 경로를 명시해야 한다.** [v4:52](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:52)의 L에는 이전 PRESS ID·유효 해제 창·필수 대상 분모·겹친 KEEP·대체 손가락·처음부터 미획득한 경우의 사례표가 필요하다. [standalone matcher:1200](/home/ajou/yigyu/3/tab2body/env/strike_events.py:1200)는 phase/entry 거리를 hit gate에서 의도적으로 제외하지만, [Full readiness:98](/home/ajou/yigyu/3/tab2body/full/readiness.py:98)와 [Synchronizer:470](/home/ajou/yigyu/3/tab2body/full/synchronizer.py:470)는 phase/grip/pre-side/dwell/permission을 요구하고 bounded delay로 완료 deadline도 조정한다. 제안: Fret-only/Strike-only/양손 경로의 승인·release·clock 계약표를 만들고 원본 source 비교 경로를 보존한다.

7. **밀집 신호는 곡 길이와 병목 현에 따라 희석된다.** [v4:79](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:79)와 [97행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:97)의 N_F/N_S·창 길이·β, [99행](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:99)의 T_phys 평균이 신호 크기를 바꾼다. N_F=64/β=.25인 합성 예에서 event별 U 최대는 .000390625, A 최대는 .0001953125다. 온라인 min에서 한 현이 계속 0이면 다른 현 개선의 U 증가도 0이며, 다른 시각에 시작하는 창에서는 지급이 늦어질 수 있다. 제안: 실제 manifest의 창과 초기 실패 분포를 확인하고 한 음→짧은 구절의 항별 advantage/가치 스케일·움직임을 측정한다. 작은 수치만으로 실패를 확정하거나 entropy 계수와 직접 비교하지 않는다.

8. **범위 포함·타현 상대 운동·안전은 별개다.** [v4:85](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:85)의 비용은 순수 위치 이탈 30mm부터 cap=1이므로 그 뒤의 추가 이탈을 구별하지 못한다. [허용범위 계약:22](/home/ajou/yigyu/3/stability_adapter_2/PLAYABLE_ENVELOPE_CONTRACT.md:22)는 actor-root p/q만으로 관통·도달 가능성을 인증하지 않는다. [task_strike.py:3633](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:3633)와 [detector:432](/home/ajou/yigyu/3/tab2body/env/strike_detector.py:432)는 현재 기타 좌표의 상대 운동으로 crossing 속도/방향을 판단한다. 정지한 world pick을 기타가 지나가는 경우도 가능하며 실제 상대 타현일 수 있다. 제안: user 범위 내부 비용0·작은 흔들림 허용을 유지하면서 safe/playable 상태·slip/drop/과압·관통과 실제 pick/guitar 운동 기여를 검증한다. 손 움직임 증가나 초기점 복원 보상을 임의로 추가하지 않는다.

## Suggestion — 추가 진단

[v4:121](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:121)의 fatal tail은 M_cross·최저 잔여 ledger·γ 봉인 전 학습 금지 조건을 유지해야 한다. 남은 모든 bin에 최악 crossing 비용을 넣는 후보는 긴 horizon에서 큰 failure_return_proxy와 critic 분산을 만들 수 있다. detector 실행 주기/중복 귀속의 실제 상한과 종료 회피 방지뿐 아니라 proxy 규모·가치 학습 분산도 함께 확인한다. 현재 source의 [N,S] boolean crossing 출력만으로 새 adapter의 상한이나 PPO 안정성을 인증하지 않는다.

## 수행한 검증과 범위

- root의 [CPU 계산기](/home/ajou/yigyu/3/stability_adapter_2/audit_reward_design_v4_v2.py:1)와 [counterexamples.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/reward_design_audit_v4/counterexamples.json)을 대조했다. 입력 5개 SHA, 할인 3조건·희석 3조건·dropout 2표본·기타 cap 6표본·staggered min이 일치한다. 처음 실패한 [N] 입력 시도와 원본은 attempt_1에 보존되어 있고 성공판은 [N,S] 입력 및 done bool을 사용한다.
- 별도 읽기 전용 CPU 호출로 기존 swept detector에 G 좌표 x=+1mm→−1mm, y=−.32m, z=−2mm, Δt=1/60s를 입력했다. valid/zone_allowed=true, 속도−.12m/s, 깊이2mm, subframe=.5였다. 같은 상대궤적은 world pick 정지와 기타의 G across축 2mm 병진으로도 생성된다. 이 검사는 실제 자유 기타 운동·native 자산 배치·현재 user 회전 범위에서의 행동 재현이 아니다.
- [최종 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/reward_design_audit_v4/README.md)와 [PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/reward_design_audit_v4/audit_signals.png)를 원자료와 육안 대조했다. 동일 U/상이한 tracker 성공, 30mm cap, 가정별 할인 값·log 축·조건부 E·합성60Hz·새 물리/학습0 표기가 일치한다. 반감기 오타와 보고서 예정 상태는 최종본에서 정정됐다.
- main PLAN809/A README1934/D README619/VISUAL_REPORT2389의 추가본문을 감사 보고서와 대조했다. 원본 전체 보존 감사·최종 색인·봉인은 root 담당이다.

동결 v4 SHA-256는 `0d7cff02416874ce98a60697503e1ce79e5fce8be52cdea8d9462617b80e56f1`로 유지된다. 이 담당자는 이 `review.md`만 작성했다. 환경·가중치·v4·이전 산출물을 수정하지 않았으며 Isaac Gym 물리·정책·학습 실행은 0이다. 판단 근거는 source 코드·CPU 합성 입력·산술과 문서 감사이며, 실제 reward hacking 정책을 학습시켜 재현한 결과는 아니다.
