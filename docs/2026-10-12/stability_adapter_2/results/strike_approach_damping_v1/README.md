# 실제 APPROACH 진입 뒤 오른팔 감쇠 비교

timed EXIT 기준의 PREPARE와 실제 source READY까지 기존 native POSITION PD를 유지했다. 실제 source motor phase 1을 처음 관측한 1.266667초에 RShoulder/RElbow/RWrist 9개 관절의 damping만 기존의 0.25배로 낮췄다. POSITION mode를 유지했고 human EFFORT 명령은 없었다. 변경 전후 native PD 전체 배열과 state 보존은 [PD 변경 기록](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/PD_approach_properties.json:1>)에 있다.

전환 직전 동일성도 별도 대조했다. 1.266667초 전 controls 76개와 switch 시점을 포함한 native 전체 상태 trace 39개가 timed EXIT baseline과 정확히 일치했다. 대조 키에는 phase, target, observation, action, source history/time이 포함된다. 이는 전환 전 source READY와 실제 상태가 보존됐음을 뒷받침하지만, 1200 physics step 전체가 baseline과 같다는 뜻은 아니다. 비교에 쓴 6개 입력 SHA도 불변이다. [비교 결과](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/pre_switch_comparison.json:1>)와 [대조 코드](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/compare_before_switch.py:1>)를 참조한다.

## 실제 결과

| 항목 | 결과 |
|---|---:|
| 실행 | 5초, 1200 physics steps, 151 camera frames, 20 contract checks 통과 |
| 입력 closure | 1,051개 입력 변경 없음 |
| PLAY handoff | 0.816667초 |
| 제어 phase 표본 | PREPARE 49 / PLAY 54 / HOLD 197 |
| 감쇠 변경 | 1.266667초, R shoulder/elbow/wrist 9개, scale 0.25 |
| source READY / target hit / physical target hit / accepted release | 1 / 1 / 1 / 1 |
| 인정 타현 | 첫 음표(event index 0), string 2 DOWN, 1.350000초, timing error +44.484798 ms; 타현 후 source event index 1 |
| physical release / miss / wrong crossing | 5 / 1 / 4 |
| source terminal | 1.716667초 |
| 기타 회전 변화 최대 / 종료 | 7.095455° / 5.414131° |
| 기타 위치 변화 최대 / 종료 | 46.353646 / 39.461086 mm |
| 기타 사용자 범위 안 표본 | 전체 292/300, policy 49/54 |
| 마지막 running strike F1 | 0.285714 |

첫 wrong crossing은 1.033333초 string 3에서 기록됐다. RECOVER 첫 adapter 명령은 1.366667초였고, 해당 구간에서 clearance `lifted`/`reached`/scheduled completion은 모두 0이었다. RECOVER 중 wrong crossing은 1.500000초 string 1, 1.683333초 string 1, 1.700000초 string 0에 기록된 뒤 source가 terminal 상태가 됐다.

1.350000초 hit의 실제 adapter key는 `[0, 2, 1]`이고 step 이후 `event_index_after_step`은 1이다. 따라서 hit 대상은 zero-based event index 0인 첫 음표(string 2 DOWN)다. 이전 timed EXIT 결과는 event 3을 2.783333초에 hit했으므로 두 실행은 더 이른 clock hit라는 점만 관찰할 수 있고 같은 scheduled event 비교는 아니다. 이번 실행은 잘못된 crossing 4회 뒤 1.716667초에 종료됐다. 낮춘 감쇠가 RECOVER 중에도 유지됐고 회복 clearance를 얻지 못했다. 마지막 running F1 0.285714는 짧은 PLAY 노출에서 나온 부분 점수라 성능 개선으로 보지 않는다. 이 조건은 채택하지 않으며 full music completion도 아니다. event key와 후속 index는 [해당 시각의 저장 controls](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/controls.json:1>)에서 확인할 수 있다.

## 초기 조건과 원본 native 영상

기준 실행의 initial state와 구동 설정은 [timed EXIT 초기값](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/native/data/initial_values.json:1>), [timed EXIT 설정·결과](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_exit_v1/README.md:1>), [이번 실행 initial audit](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/initial_audit.json:1>), [이번 실행 controls](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/controls.json:1>)에서 확인할 수 있다. 아래 영상과 프레임은 이번 단일 native 진단에서 저장된 Isaac Gym 자료다.

| 시각 | 전신 | 손 근접 |
|---|---|---|
| 0초 | ![전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/images/frames/whole_body/00000.png) | ![손 근접 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/images/frames/hands/00000.png) |
| source terminal 직전 1.7초 | ![전신 1.7초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/images/frames/whole_body/00051.png) | ![손 근접 1.7초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/images/frames/hands/00051.png) |
| 5초 기록 끝 | ![전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/images/frames/whole_body/00150.png) | ![손 근접 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/images/frames/hands/00150.png) |

![전신 native 영상, 151 frames](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/images/whole_body.mp4)

![손 근접 native 영상, 151 frames](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/images/hands.mp4)

## 분석 파일과 한계

- [분석 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/analysis/summary.json:1) · [native report 및 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/report.json:1)
- [초기 native values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/initial_values.json:1) · [checkpoint 연결](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/checkpoint_connection.json:1)
- [native 입력 전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/inputs_before.json:1) · [native 입력 후](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/inputs_after.json:1) · [영상 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_approach_damping_v1/native/data/images/videos.json:1)
- [이번 단계 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_APPROACH_DAMPING_PLAN.md:1) · [runner의 phase 1 damping 전환](/home/ajou/yigyu/3/stability_adapter_2/run_strike_approach_damping.py:133)

요약 분석은 5초 기록 전체가 유지됐어도 source가 1.716667초에 종료되어 뒤의 3.28초는 HOLD 자유 물리/녹화였다. 이 결과는 damping 변경과 회복 실패 사이의 인과를 확정하지 않는다. 다음 비교는 APPROACH에서만 damping을 낮추고 첫 RECOVER command 전에 baseline RECOVER damping을 복구해 확인한다.

다음 단계의 source phase별 R9 damping schedule은 [APPROACH-only 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_APPROACH_ONLY_DAMPING_PLAN.md:1)에 기록돼 있다.
