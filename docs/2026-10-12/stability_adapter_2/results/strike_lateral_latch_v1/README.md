# Strike lateral latch v1

5초 native 진단에서 열린 접근 phase 동안 READY 평면 거리가 4 mm 이내로 한 번 들어오면 latch를 유지해 ENTRY 목표를 계속 선택하도록 했다. 원본 기타 geometry, source phase/clock, hit/miss 기준과 ±50 ms timing window는 바꾸지 않았다. 실행은 physics 1,200 step, camera 151 frame, 27/27 native checks 통과, native input closure 1,112개 unchanged, analysis SHA 7개 unchanged다. 저장 trace는 152행이며 camera의 8-step 표본 151행 외에 terminal 시각 3.816667초(physics step 916)의 off-grid HOLD 표본이 하나 더 있다. PREPARE 49, PLAY 180, HOLD 71; HOLD는 5초까지 이어졌고 baseline PD readback 복원은 확인됐다.

## 결과

| 지표 | 저장 결과 |
|---|---:|
| 적시 타현 / source 물리 타현 판정 / accepted | 4 / 4 / 4 |
| source physical release / miss / wrong crossing | 8 / 4 / 4 |
| terminal source 시각 | 3.816667초 |
| playable region | 전체 controls 191/300, PLAY 115/180 |
| 최대/종료 회전 변화 | 9.3660562215° / 5.8358449122° |
| 최대/종료 위치 변화 | 46.353645732 mm / 45.3526033003 mm |

앞선 네 적시 타현은 유지됐지만 이후 source wrong crossing 4회로 PLAY가 3.816667초에 terminal 됐다. 완주 성공은 아니며 `music_success=false`, 학습 update는 0이다. 이전 staging run은 5초까지 PLAY에서 wrong crossing 2회였으므로 이번 latch 결과는 채택하지 않는다. 두 실행은 latch 발동 전 controls 206개와 native trace 104개까지 exact prefix를 공유하며, 이 비교는 전체 실행이 동일하다는 뜻이 아니다.

저장 trajectory에서 latch는 3.416667초, 측정 READY xy 거리 3.996863 mm일 때 잡혔다. 이후 3.433333초 READY xy 거리가 6.045976 mm로 다시 커져도 ENTRY geometry 선택이 유지됐다. 당시 source ENTRY까지 남은 거리는 12.316802 mm였고, 이후 최소도 8.135464 mm로 source ENTRY 판정 거리 6 mm에 도달하지 못했다. 3.466667초 source miss도 기록됐다. 이는 시간 순서와 저장된 상태의 관찰이며 latch가 miss를 일으켰다고 입증하지 않는다.

표의 “source 물리 타현 판정”은 source geometry/event 판정이다. 이를 native rigid-body contact 측정으로 해석하면 안 된다. 요청된 30개 actor 출력 중 팔 9개는 기록 전용이며, 팔 목표는 geometry 기반 이전 목표 + 2×IK 증분이 소유했다. 손가락 21개는 policy가 제어하고 free curl 4개에 +0.2 rad 잔차를 적용했다. actor 30개 전체의 실제 policy 구동이나 policy-source actuator 동등성을 뜻하지 않는다.

이 실행은 terminal retraction을 실제로 수행했다. HOLD 71 control rows에서 source clock/history와 다른 72개 관절 목표를 유지하며 R9을 회수했고, terminal baseline PD 설정은 native readback으로 복원됐다. 이는 5초 진단의 terminal 처리 확인이며 완성 연주 성공은 아니다.

후속 [post-clearance prestage 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_POSTCLEARANCE_PRESTAGE_PLAN.md)은 별도 단계다. 음악 준비상태를 읽는 source-coordinate 경로의 효과는 아직 확인되지 않았고 이 결과에 포함되지 않는다.

## 원본 실행 자료

- [native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/native/data/report.json), [analysis summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/analysis/summary.json)
- [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/native/data/controls.json), [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/native/data/trace.json)
- [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/native/data/initial_values.json), [checkpoint connection](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/native/data/checkpoint_connection.json), [PD phase properties](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/native/data/PD_phase_properties.json)
- [native input SHA before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/native/inputs_before.json), [native closure after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/native/inputs_after.json)
- [analysis SHA before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/analysis/inputs_before.json), [analysis SHA after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/analysis/inputs_after.json), [lateral latch audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/lateral_latch_audit.json)
- [whole-body MP4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/native/data/images/whole_body.mp4), [hands MP4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/native/data/images/hands.mp4)
- [capture manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/native/data/images/capture.json), [video manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/native/data/images/videos.json), [artifact SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/artifacts/artifact_manifest.json)

![Native whole-body video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/native/data/images/whole_body.mp4)

![Native hands video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/native/data/images/hands.mp4)

Source implementation: [READY latch acquisition and waypoint selection, lines 158–179](/home/ajou/yigyu/3/stability_adapter_2/run_strike_lateral_latch.py:158), [saved target/latch fields, lines 203–223](/home/ajou/yigyu/3/stability_adapter_2/run_strike_lateral_latch.py:203), [terminal PD restore and HOLD target update, lines 292–336](/home/ajou/yigyu/3/stability_adapter_2/run_strike_lateral_latch.py:292), [report fields, lines 353–357](/home/ajou/yigyu/3/stability_adapter_2/run_strike_lateral_latch.py:353).

## 저장된 native camera frame

각 쌍은 같은 시간의 native 전신·손 카메라 PNG 복사본이다. 파일은 [artifact producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/make_artifacts.py)가 원본 SHA를 전후 확인해 byte-exact 복사했다.

### 0.000초 · step 0

![0초 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/artifacts/whole_body_00000.png)
![0초 손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/artifacts/hands_00000.png)

### 1.333초 · step 320

![1.333초 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/artifacts/whole_body_00040.png)
![1.333초 손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/artifacts/hands_00040.png)

### 3.433초 · step 824, latch 유지 후 재이탈 표본

![3.433초 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/artifacts/whole_body_00103.png)
![3.433초 손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/artifacts/hands_00103.png)

### 5.000초 · step 1200, terminal 이후 HOLD

![5초 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/artifacts/whole_body_00150.png)
![5초 손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_latch_v1/artifacts/hands_00150.png)
