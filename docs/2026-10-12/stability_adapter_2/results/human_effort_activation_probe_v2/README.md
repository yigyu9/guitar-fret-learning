# 사람 관절 EFFORT 활성화 진단 v2

## 결과

같은 초기 사람 상태, 초기 위치 PD 목표, EFFORT 모드 속성, 기타 상태를 사용해 OFF와 ON을 각각 새로 실행했다. 두 실행은 각각 1,200 physics step(5초), 151개의 Isaac Gym 카메라 프레임으로 완료됐고, 각 실행의 9개 계약 검사는 모두 통과했다. 이 비교는 재생 영상이 아니라 저장된 native PhysX 결과이며, root와 하체는 고정했고 상태 덮어쓰기나 기타 body-force 제출은 없었다. 음악 정책·Strike/Fret·학습은 실행하지 않았다.

오른팔의 12개 관절(R_Thorax/R_Shoulder/R_Elbow/R_Wrist)을 처음 네 physics step 동안만 EFFORT 모드로 바꾸고 stiffness와 damping을 0으로 설정했다. OFF도 같은 관절 토크 텐서 API에 0 벡터를 제출했고, ON은 같은 API로 계산된 제한 토크 벡터를 제출했다. 두 조건 모두 같은 `R_Shoulder_z` +0.05 rad 목표를 사용했다. ON의 첫 벡터는 `R_Shoulder_z`에 10.000001907 Nm였고 첫 네 physics step에 제출된 뒤 0 벡터로 바뀌었다. 이는 요청된 명령값이지 관절에서 측정한 토크가 아니다. 네 step 뒤 원래 POSITION PD 속성을 복원했고 이후 명령은 0이었다. 나머지 69개 관절은 기존 속성을 유지했다.

| 저장 시점 | ON−OFF 최대 관절좌표 차이 | ON−OFF 최대 관절속도 차이 | R_Shoulder_z 좌표·속도 차이 |
|---|---:|---:|---:|
| 초기, step 0 (0초) | 0 rad | 0 rad/s | 0 rad / 0 rad/s |
| 네 step 뒤, step 4 (0.016667초) | 0.039242268 rad | 3.846986488 rad/s | +0.039242268 rad / +3.846986488 rad/s |
| 전체 저장 비교에서 최대 | 0.042840123 rad | — | — |

초기 전체 native 상태, POSITION PD 목표와 원래 PD 속성은 두 실행에서 일치했다. 네 step 뒤 상태는 더 이상 같지 않아 이 짧은 시험에서 EFFORT 텐서 제출에 대한 native 응답이 관측됐다. 이 결과만으로 전체 GPU 경로의 동등성, 지속 제어 효과 또는 연주 성공을 입증하지 않는다. 이전 POSITION(강성 0) 진단에서는 같은 actuation API로 OFF 0 Nm와 ON 10 Nm를 제출했지만 저장 상태가 일치했다. 이 결과는 별도로 보존하며, POSITION 구동 모드와 토크 명령 OFF/ON을 구분해 이번 EFFORT 모드 결과와 혼합하지 않는다.

초기 질량행렬은 읽기 전용으로 `(1, 81, 81)` 모양에서 저장했고 최대 비대칭은 `4.47034836e-8`이었다. 질량행렬은 토크 계산에 사용하지 않았다. 물리 계약은 각 실행의 [OFF report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/report.json)와 [ON report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/report.json)에 기록되어 있다.

## 저장된 영상과 대표 프레임

각 영상은 해당 실행의 실제 Isaac Gym 카메라 저장본이다. 두 실행 모두 151프레임, 30 fps이며 ffprobe stream duration은 5.033333초다.

### OFF

![OFF 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/images/whole_body.mp4)

![OFF 손 근접 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/images/hands.mp4)

대표 프레임: [전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/images/frames/whole_body/00000.png) · [손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/images/frames/hands/00000.png) · [전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/images/frames/whole_body/00060.png) · [손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/images/frames/hands/00060.png) · [전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/images/frames/whole_body/00150.png) · [손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/images/frames/hands/00150.png)

### ON

![ON 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/images/whole_body.mp4)

![ON 손 근접 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/images/hands.mp4)

대표 프레임: [전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/images/frames/whole_body/00000.png) · [손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/images/frames/hands/00000.png) · [전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/images/frames/whole_body/00060.png) · [손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/images/frames/hands/00060.png) · [전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/images/frames/whole_body/00150.png) · [손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/images/frames/hands/00150.png)

## 기록과 한계

- [분석 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/analysis/summary.json)은 저장된 native 상태 152개를 비교한다. 입력 보존 상태는 [분석 전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/analysis/inputs_before.json)과 [분석 후](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/analysis/inputs_after.json)에 기록되어 있다.
- 각 실행의 초기값, 81개 DOF의 EFFORT 속성 readback, 토크 요청, 저장 상태, 질량행렬은 [OFF 데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/initial_values.json), [OFF 명령](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/commands.json), [OFF 상태](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off/data/states.json), [ON 데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/initial_values.json), [ON 명령](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/commands.json), [ON 상태](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on/data/states.json)에서 확인할 수 있다. [OFF 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/off.log)와 [ON 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_effort_activation_probe_v2/on.log)도 보존했다.
- 실행 규약은 [계획](/home/ajou/yigyu/3/stability_adapter_2/HUMAN_EFFORT_ACTIVATION_PROBE_V2_PLAN.md:1), [runner](/home/ajou/yigyu/3/stability_adapter_2/run_human_effort_activation_probe_v2.py:15), [preservation wrapper](/home/ajou/yigyu/3/stability_adapter_2/human_effort_probe_v2_preserved_run.py:12), [저장자료 analyzer](/home/ajou/yigyu/3/stability_adapter_2/analyze_human_effort_probe.py:13)에 있다.

후속 검토 방향은 오른팔 9축의 POSITION damping만 낮춘 비교를 고려하는 것이다. 이번 EFFORT 진단만으로 해당 변경을 채택하거나 원인을 특정하지 않는다.
