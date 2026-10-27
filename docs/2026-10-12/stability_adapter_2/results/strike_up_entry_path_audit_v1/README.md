# UP ENTRY 경로 원본 감사

대상은 [incremental approach native 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/controls.json)다. source observation의 READY/ENTRY/geometry5 벡터를 실제 pick_G에 더해 3D 목표를 복원했다. 추가 FK·물리 실행·controller 변경은 없다. **현재 UP의 가로 준비 부족은 관측되지만, 3 mm staging이 성공한 네 DOWN을 전부 보존한다는 예측은 할 수 없다.**

시각은 control의 명령 시각이며 info는 그 뒤 native4 step, 즉 +16.667 ms의 feedback이다. source string index는 0-based다. raw2=G:string3, raw3=G:string4이며 아래 native 이름을 병기한다. direction +1=DOWN, −1=UP이다.

## 3.0–3.633초: 회복 문맥과 scheduler는 별도로 진행

네 timely DOWN은 명령1.316667/1.583333/2.433333/2.816667초, timing +16.4811/−17.5010/−.7144/−3.1532 ms이고 모두 target_hit·prepared_target_hit true다. scheduled REC pulse는1.516667/1.8/2.65/3.25초다. 마지막 pulse 자체는 source phase2→1 전환과 동일하지 않다.

| 명령 시각(s) | source 상태·원래 판정 | 실제 pick_G (mm) | 선택한 source 목표_G (mm) |
|---:|---|---|---|
| 3.000000 | phase2, event4(raw3 DOWN), 회복은 이전 raw2 DOWN 문맥 | 5.425,−313.630,28.075 | geometry5 release_lift: 7.978,−310.503,22.300 |
| 3.083333 | phase2, lifted=true | 6.859,−313.384,24.815 | geometry5 next-entry_lift: −7.975,−308.899,22.300 |
| 3.150000 | phase2, 원래 window timeout miss4→5 | −3.288,−306.240,20.381 | next-entry_lift 유지 |
| 3.250000 | event5(raw2 UP), scheduled_REC=true feedback | −11.866,−307.112,22.104 | next-entry_lift 유지 |
| 3.266667 | phase2, reached=true; 회복 목표는 cached 다음 DOWN READY | −11.116,−307.725,22.358 | geometry5 next_ready: −7.975,−308.899,20.300 |
| 3.350000 | 명령 phase2, feedback phase1 | −9.224,−309.190,21.232 | cached next_ready 유지 |
| 3.366667 | phase1, event5 UP open, ENTRY 미도달 | −9.051,−309.262,21.112 | ENTRY: 6.474,−308.903,10.800 |

3.15의 miss는 clock·판정을 바꾸지 않고 발생했다. musical event는4→5로 진행하지만 회복 next-entry는 처음 저장된 raw3 DOWN 좌표를 보존한다. source [task_strike.py:2009](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:2009)는 event_index를 증가시키면서 preserve_recovery 문맥을 유지할 수 있고, [회복 좌표:1456](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:1456)는 cached next string/direction을 사용한다.

**geometry5는 이미 clearance 목표다.** [task_strike.py:1436](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:1436)와 [strike_events.py:699](/home/ajou/yigyu/3/tab2body/env/strike_events.py:699)가 release_lift→next_entry_lift→next_ready를 반환한다. 3.266667부터 낮아지는 z22.3→20.3 mm도 원래 next_ready 단계다. 새 lift가 없는 경로로 해석하지 않는다.

scheduled completion 후에도 [strike_dual_recovery_to_approach:963](/home/ajou/yigyu/3/tab2body/env/strike_events.py:963)는 회복 frame/rearm/clearance와 함께 time_to_target≤approach_lead 조건을 요구한다. [task 호출:4241](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:4241)은 next_song_time을 사용한다. 그래서3.25 pulse 후 phase2가 유지되다가3.35 feedback에서 phase1, 다음3.366667 명령에서 open ENTRY가 된다.

## 실제 ENTRY 접근과 네 wrong release

event5 UP의 원래 READY는 (+7.974,−308.899,20.300) mm다. cached DOWN next_ready의 x−7.975에서 새 READY x+7.974로 약15.950 mm 반대편 이동이 필요하다. 첫 open3.366667에서 READY xy오차17.030 mm, z오차−.812 mm(실제가 READY보다 높음), ENTRY3D거리18.642 mm다. 원래 window close까지115.801 ms가 남는다. UP의 모든 open 표본에서 ENTRY latch는 false이고 EXIT는 사용되지 않았다.

| 명령(s) | target event / 선택 목표 | READY xy오차(mm) | 실제 pick_G z(mm) / v_G(m/s) | R9 final−actual RMS(rad) | 원래 검출 결과 |
|---:|---|---:|---|---:|---|
| 3.400000 | 5 UP / ENTRY | 8.149 | 19.204 / (.435,−.191,−.080) | .165 | release 없음 |
| 3.416667 | 5 UP / ENTRY | 7.703 | 15.782 / (.511,−.112,−.205) | .167 | release 없음 |
| 3.466667 | 5 UP / ENTRY | 10.184 | −6.456 / (−.164,.452,−.460) | .166 | G:string2 UP: unplanned1, miss5→6 |
| 3.483333 | 6 DOWN / READY closed | 22.532 | −4.869 / (−.308,.360,.095) | .173 | G:string3 UP: unplanned1 |
| 3.500000 | 6 DOWN / READY closed | 19.582 | −.114 / (−.634,.357,.285) | .169 | G:string4 UP: wrong_direction1 |
| 3.550000 | 6 DOWN / ENTRY open | 14.168 | 35.427 / (−.125,−.640,.764) | .138 | release 없음 |
| 3.616667 | 6 DOWN / ENTRY | 38.852 | .031 / (.295,−.086,−1.164) | .172 | G:string3 DOWN: unplanned1, terminal |

네 wrong의 detector release depth는18.1269/14.2750/7.6236/12.4000 mm, crossing lane y는−300.9658/−293.7226/−290.0570/−342.7400 mm다. 모두 physical_target_hit·target_hit false다. 첫 세 번은 open/closed 전환 전후의 움직임과 함께 기록됐지만, 이것만으로 접촉 또는 특정 controller 항의 인과를 확정하지 않는다. 네 번 모두 release_phase_violation=false이며, closed APPROACH가 detector를 꺼 주는 것은 아니다.

3.466667에서 window close delta는15.801 ms이나 다음16.667 ms를 더한 source clock이 끝을 넘어 miss한다([task_strike.py:4005](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:4005)). 다음 event6의 READY가 반대편 x−7.975로 바뀔 때 실제 pick은 z<0이고 음의 x속도다. 3.616667의 count4 termination은 feedback3.633333에 발생하며, terminal TP4/FP4/FN2다. 정확 terminal trace의 pick_G=(6.278,−339.285,−.245) mm, R9 final−actual RMS .171504/max .447620 rad이다.

prepared/unprepared는 [task_strike.py:4547](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:4547)의 `target_hit & ready_acquired`/`target_hit & ~ready_acquired`다. 여기 wrong 네 번은 target_hit 자체가 false여서 두 flag 모두 false다. ENTRY 미도달을 곧바로 unprepared_target_hit로 부르지 않는다.

## 한 요인 후보와 prefix 한계

open phase1·ENTRY 미도달에서 현재 READY xy오차>3 mm이면 adapter 목표만 geometry3 READY로 두는 후보는, 가로 준비 중 z20.3 mm를 유지하고 ENTRY z10.8 mm로 내려가는 동작을 지연한다는 기하적 근거가 있다. 저장된 UP 경로는 가로 접근과 하강이 함께 진행됐고 READY xy오차 최소7.703 mm였다. 다음 event6의 최소도12.939 mm다. source phase·시간·cached recovery·detector를 그대로 두고 추가 latch 없이 매 control 판정하는 경우, 아직 시행되지 않은 기하 후보이며 추종 안정성·wrong 감소·timely hit를 보장하지 않는다. 남은 창을 넘으면 원래 miss를 유지해야 한다.

**첫 open만 비교하면 성공한 네 DOWN은 전부3 mm 이하였지만, open 전체 미도달 표본에서는 event0이 예외다.**

| event | open phase1 & ENTRY未latch 표본 수 | 최대 READY xy오차 | 3 mm gate가 바꿀 원본 시각 |
|---:|---:|---:|---|
| 0 DOWN | 2 | 3.320841 mm | 1.300000 s |
| 1 DOWN | 2 | 1.732275 mm | 없음 |
| 2 DOWN | 2 | .181505 mm | 없음 |
| 3 DOWN | 2 | .859350 mm | 없음 |
| 5 UP | 7 | 17.029628 mm | 7개 전부 |
| 6 DOWN | 5 | 38.852220 mm | 5개 전부 |

event0의1.3초 ENTRY3D거리는7.329521 mm>source6 mm여서 latch=false다. 따라서 이 gate는 원본과1.3초에 처음 분기하며, 네 timely hit 또는 후기까지의 prefix 보존을 예측할 수 없다. event1–3의 해당 저장 표본이 gate를 통과하는 사실도, 앞 event0에서 이미 궤적이 달라질 새 실행을 보장하지 않는다. 현재 frozen policy는 finger21을 맡고 arm9 요청은 사용하지 않는 [실행 계약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_incremental_approach_v1/native/data/checkpoint_connection.json)이므로, open arm을 policy로 돌리는 것은 staging과 별개의 controller 요인이다. 이번 감사에서는 정책 변경이나 post-REC 대기 중 cached next_ready를 새 event READY로 바꾸는 요인을 도입하지 않았다.

## 검증·보존

[analysis.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_up_entry_path_audit_v1/analysis.py)와 [summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_up_entry_path_audit_v1/summary.json)에 원본 경로/SHA·시간 창·모든 후기 표본·wrong/pulse·R9 오차를 기록했다. 직접 입력9개를 내용 decode/parse 전에 SHA256 수집하고 cache 해시·종료 재해시가 모두 같음을 확인했다. 추가 표의 offline 계산도 같은 raw를 SHA 사전 수집 후 읽고 끝에 대조했다.

actor169개에서 source 관측 복원 pick과 adapter 측정의 최대 차이는 .000212438 mm, READY 차이는9.31e−7 mm, 선택 geometry 차이는1.04e−6 mm다. native trace와 정확시각으로 겹치는84개에서 body origin으로 복원한 pick_G와 adapter 측정 차이를1e−10 m 미만으로 확인했다. trace 보간·새 FK·native 실행은 없다. 그림 없는 source 관측 숫자만으로 실제 contact 원인을 판정하지 않는다.
