# Free4 curl의 원래 Strike timing·회복 진단

curl의 첫 correct-string release는 물리 타현으로 인정됐지만 timing hit은 아니다. event0 창 종료 직후 event1로 넘어갔고, 그 다음 READY 명령 중 event1을226.674ms 일찍 통과했다. 이후 geometry5는 이미 원래 clearance 목표였으며, scheduled recovery의 reached latch가 끝까지 성립하지 않았다. 마지막 종료는 wrong crossing count이고 penetration 종료가 아니다.

[전체 수치와 원본 근거 줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/timing_diagnosis.json), [읽기 전 SHA를 기록하는 계산 script](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/timing_diagnosis.py). A·다른 담당 산출물·native raw를 수정하지 않았다. 물리 실행/초기화0이다.

## 시각과 원자료 정의

- 표의 t는 controls의 **명령 전 native 시각**이다. source feedback은4 physics-step=.016667초 뒤다. terminal 명령 t3.383333의 feedback/HOLD 시작 시각은3.4초다. source song_time은 별도이며 원래 그대로 증가한다.
- source303 observation에서 실제 pick G위치와 READY/ENTRY/geometry5 상대벡터를 읽었다. [원래 vector 정의](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:2745), [block ABI](/home/ajou/yigyu/3/tab2body/strike_v2_contract.py:21)를 그대로 사용했다. geometry5를 depth EXIT로 고정 해석하지 않았다.
- 모든 직접 읽은 source/helper/raw18개를 내용 분석 전에 SHA로 기록하고, 다시 읽은 내용 및 종료 SHA와 대조했다. 모두 일치했다. 관절 observation과 actual q도 일치했다. 별도 순수 수학 검산에서 trace와 같은 physics_step의 pick G위치77개(curl)/89개(baseline)는 source observation과 최대.000195/.000208mm 차이다.
- string은 raw의0-based index다. native-body moving-G velocity와 source의60Hz pick G위치 차분 velocity는 별도로 기록했다. native scalar velocity를 q의 시간미분이나 torque 등가성으로 인증하지 않았다.

## event0에서 event1로 넘어간 경계

두 trial 모두 명령 t1.25에는 READY0이고 그 feedback에서 APPROACH1로 전환한다. [원래 READY latch](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:3723)는 actual READY 거리≤10mm, grip 성공,6frame 및 approach_open을 사용한다.

| trial / 명령 t s | event / phase / adapter 목표 | 실제 pick Gz mm | 실제 ENTRY 거리 mm | R9 final goal−actual RMS / max rad |
|---|---|---:|---:|---:|
| curl1.350000 | event0 / open1 / ENTRY | 9.964 | 7.586 | .19457 / .51238 |
| curl1.366667 | event1 / closed1 / READY | 5.122 | 6.066 | .16311 / .46320 |
| baseline1.350000 | event0 / open1 / EXIT | 5.847 | 5.254 | .17082 / .38001 |

curl1.35의 event0 original/effective target song time은.023100s, late tolerance는.050s이다. 다음 song time .073100157이 창 끝.073099999를 넘어 miss=True/index0→1이다. source는 `next_song_time > target_window_end`를 검사한다. [창 종료와 miss 식](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:4005), [event 진행](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:2009).

다음 명령1.366667은 event1 target time=.309600s, song_before=.073100157s라 approach_open=False다. adapter는 READY Gz20.3mm를 명령했지만 실제 pick Gz는5.122mm다. 그 순간 actual native-body velocity_G는 `(+.3978,−.0051,−.3437)m/s`이고, 뒤 feedback의 source 위치차분 velocity_G는 `(+.3535,+.0905,−.1876)m/s`다. source subframe=.589535에서 string2/+direction을 검출했다.

- release song time=.082925740s, native subframe 시각1.376492250초.
- physical_target_hit=True, accepted_release_mask의 string2=True. 검출 depth9.021735mm/across speed+.353748m/s/zone_allowed=True.
- timing_error=**−226.674255ms**, premature_release=True, target_hit=False, miss=True, event1→2, phase1→2.
- adapter entry latch=False, source entry_ready=False였다. raw의 prepared_target_hit=False와 unprepared_target_hit=False도 동시에 기록됐다. [두 flag의 정의](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:4547)는 각각 `target_hit & ready_acquired`와 `target_hit & ~ready_acquired`이며 entry_ready 분류가 아니다. 이 행은 timing target_hit=False이므로 둘 다 false다. 물리 acceptance를 source unprepared_target_hit=True로 부르지 않는다.

baseline은1.35에서 entry latch=True/EXIT를 명령했다. release song=.067584799s, target=.023100s로 **+44.484798ms**이며 physical_target_hit=True와 target_hit=True다.

source는 [release eligibility](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:3648)와 [ordered string/direction acceptance](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:3830)를 먼저 계산한다. approach_open·entry_ready는 physical acceptance의 hard gate가 아니다. phase violation은 [별도 label](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:3939)이며 timing은 [별도 gate](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:3951)다. 따라서 closed APPROACH의 READY 명령 중 early physical acceptance는 원래 source에서도 가능하다.

**가설:** event0의 움직임이 경계 뒤에도 남아 early event1 release에 기여했을 수 있다. 실제 속도와 목표 편차는 이 가설과 부합하지만, command 변경·PD 응답·접촉·정책 및 guitar 운동 중 어느 것이 원인인지 이 저장 자료만으로 분리하지 않았다.

## clean pulse와 scheduled clearance는 다르다

| trial | clean pulse 명령 t s | 최초 lifted feedback의 명령 t s | 최초 reached feedback의 명령 t s | scheduled 완료 명령 t s |
|---|---:|---:|---:|---:|
| curl | 1.566667 | 2.266667 | 없음 | 없음 |
| baseline | 1.550000 | 1.400000 | 2.183333 | 2.366667 |

curl1.566667에는 clean pulse=True, scheduled pulse=False, clearance_required=True/lifted=False/reached=False다. geometry5 목표는 이미 **release_lift** `(.0079699,−.3072093,.0223000)m`이고, actual pick은 `(.0022810,−.3153704,.0308350)m`다. 목표까지13.108mm다. pick 높이가 lift보다 높다는 사실만으로3D 거리 latch를 대신할 수 없다.

[원래 geometry5 선택](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:1440)은 release_lift→next_entry_lift→next_ready를 이미 반환한다. [helper](/home/ajou/yigyu/3/tab2body/env/strike_events.py:728)는 lifted/reached 상태로 목표를 고른다. [clearance 갱신](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:1490)은 실제 목표거리와4mm threshold를 사용한다.

[clean pulse](/home/ajou/yigyu/3/tab2body/env/strike_events.py:679)는 active/rearmed recovery frame의 best count가12frame에 도달하는 조건이다. [scheduled APPROACH 복귀](/home/ajou/yigyu/3/tab2body/env/strike_events.py:963)는 required frames, rearm, clearance_reached, next event timing 조건을 추가한다. curl은 lifted 이후에도 reached=False로 phase2를 유지한 채 event2→3→4→5가 miss로 진행한다. lift 목표가 없었던 결과가 아니다. 명령시점 next_entry_lift 최소거리는4.315mm(t3.35)였으며 feedback 전체에서 reached latch는 false다.

## 실제 wrong crossing과 종료

아래 시간 오차는 검출 subframe과 당시 current event target의 차이를 계산한 보조값이다. accepted=False인 행의 source timing_sample은 false이고 timing_error_ms는0이므로, 이 보조값을 source timing 성적으로 사용하지 않는다.

| curl 명령 t s | 검출 string / 방향 | 당시 target string / 방향 | action phase | raw 분류 | 보조 시간차 ms |
|---|---|---|---:|---|---:|
| 1.050000 | 3 / + | 2 / + | READY0 | unplanned1, phase violation | −250.728 |
| 2.800000 | 2 / − | 2 / + | REC2 | wrong_direction1, phase violation | −21.415 |
| 3.016667 | 2 / + | 3 / + | REC2 | unplanned1, phase violation | −90.348 |
| 3.383333 | 1 / + | 2 / − | REC2 | unplanned1, phase violation | −35.943 |

2.8초와 마지막 crossing은 보조상±50ms 창 안이지만 string/direction acceptance가 실패했다. 마지막 행은 target string 밖이라 raw unplanned=1/wrong_direction=0으로 분류된다. phase violation label 자체를 wrong count에 다시 더하지 않았다. 마지막 feedback에서 누적 physical TP1/FP4/FN4이고 wrong_crossing_count_termination=True다. native3.4초부터 HOLD다.

baseline은 native3.783333초에 같은 count 종료였다. 그 직전3.75초에는 target2에 대해 string4·5 unplanned 두 건,3.766667초에는 target2의 요청−direction에 대해 검출+direction 한 건이었다. source phase는APPROACH1이어서 이때 phase violation은 false다. baseline은 physical TP1/FP4/FN6이다.

curl의 source monitor 최대 depth/swept depth는1.403335mm(t3.033333), baseline은1.281132mm(t.983333)이다. 두 trial 모두 source penetration flag/termination은 false였다. 이 monitor 값, virtual pick string crossing, native collider contact는 서로 다른 기록이다. 작은 body-cross 또는 특정 contact가 wrong crossing이나 early release를 일으켰다고 단정하지 않는다.

## 다음 후보에 대한 범위

이 결과는 source 시간·phase·detector를 바꾸지 않고 READY/closed APPROACH의 실제 몸 움직임을 더 안정시키는 후보를 평가할 근거다. 임시 servo 목표를 사용할 때는 원래 nominal geometry와 source 판정을 그대로 보존하고 별도로 기록해야 한다. root가 진행 중인 다음 controller/native trial은 이 진단에 포함하지 않았다.
