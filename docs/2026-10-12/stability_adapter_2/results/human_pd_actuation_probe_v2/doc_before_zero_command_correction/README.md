# 오른팔 관절 토크 명령 응답 진단

동일한 초기 native 상태와 위치 PD 목표에서 `R_Shoulder_z` 목표를 0.05 rad 바꾸고, 오른팔 12축에 관절 토크 텐서 명령을 보내지 않은 조건(OFF)과 보낸 조건(ON)을 비교했다. strap은 두 조건 모두 꺼져 있고, 60 Hz 제어 명령을 240 Hz 물리 스텝에 유지했다. 두 실행은 각각 1200 physics steps와 151 프레임을 완료했으며, 각 실행의 7개 계약 검사와 입력 closure 검사가 통과했다.

## 관측

| 항목 | OFF | ON |
|---|---:|---:|
| 첫 `R_Shoulder_z` 관절 토크 명령 | 0 Nm | 10.000001907 Nm |
| 저장 상태 수 | 152 | 152 |
| ON/OFF DOF 위치·속도 및 모든 body 상태 차이 | 0 | 0 |
| 상태 비교 최대 관절각 차이 | 0 rad | 0 rad |

명령값은 측정된 관절 힘이 아니다. 위치 drive는 두 조건에서 모두 POS 모드였고, `R_Shoulder_z` 위치 drive stiffness는 0으로 기록됐다. 이 비교에서는 ON/OFF 전 구간의 저장 native 상태가 같았다. 따라서 이 CPU/POS 설정에서 tensor stiffness 토크가 상태에 영향을 준다는 증거가 없으며, 이를 근거로 hybrid 구동을 채택하지 않았다. 이는 다른 simulator 구성이나 source 정책의 결과를 검증한 것이 아니고, 타현 또는 연주 성공 평가도 아니다.

v1 OFF 시도는 중첩된 `GraphicsGym → NoStrapGym → native Gym` wrapper를 한 겹만 처리해 guard에 막혀 physics 0에서 끝났다. [v1 실패 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v1/off.log)와 [실패 report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v1/off/data/report.json:1)은 보존되어 있다. v2는 wrapper 두 종류를 명시적으로 확인한 뒤 정상 human joint tensor API로 오른팔만 명령하고, 기타/root 외력과 상태 덮어쓰기를 금지하는 검사를 유지했다. 이번 비교는 해당 CPU 환경의 API 경로 점검도 포함한다.

## 실제 native 카메라 자료

각 실행은 5초/1200 physics steps였고, 각 전신 및 손 카메라 영상은 151 frames, 30 fps, ffprobe stream duration 5.033333초다. 아래는 원본 native 프레임이다.

### OFF

| 시점 | 전신 | 손 근접 |
|---|---|---|
| 0초 | ![OFF 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/off/data/images/frames/whole_body/00000.png) | ![OFF 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/off/data/images/frames/hands/00000.png) |
| 2초 | ![OFF 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/off/data/images/frames/whole_body/00060.png) | ![OFF 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/off/data/images/frames/hands/00060.png) |
| 5초 | ![OFF 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/off/data/images/frames/whole_body/00150.png) | ![OFF 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/off/data/images/frames/hands/00150.png) |

![OFF 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/off/data/images/whole_body.mp4)

![OFF 손 근접 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/off/data/images/hands.mp4)

### ON

| 시점 | 전신 | 손 근접 |
|---|---|---|
| 0초 | ![ON 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/on/data/images/frames/whole_body/00000.png) | ![ON 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/on/data/images/frames/hands/00000.png) |
| 2초 | ![ON 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/on/data/images/frames/whole_body/00060.png) | ![ON 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/on/data/images/frames/hands/00060.png) |
| 5초 | ![ON 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/on/data/images/frames/whole_body/00150.png) | ![ON 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/on/data/images/frames/hands/00150.png) |

![ON 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/on/data/images/whole_body.mp4)

![ON 손 근접 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/on/data/images/hands.mp4)

## 원자료 및 구현 색인

- [분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/analysis/summary.json:1) · [분석 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/analysis.log)
- OFF: [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/off/data/report.json:1) · [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/off/data/initial_values.json:1) · [commands](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/off/data/commands.json:1) · [states](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/off/data/states.json:1)
- ON: [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/on/data/report.json:1) · [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/on/data/initial_values.json:1) · [commands](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/on/data/commands.json:1) · [states](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/on/data/states.json:1)
- [v2 계획](/home/ajou/yigyu/3/stability_adapter_2/HUMAN_PD_ACTUATION_PROBE_V2_PLAN.md:1) · [실행 runner](/home/ajou/yigyu/3/stability_adapter_2/run_human_pd_actuation_probe_v2.py:15) · [보존 실행 wrapper](/home/ajou/yigyu/3/stability_adapter_2/human_pd_probe_preserved_run_v2.py:12) · [저장 자료 비교기](/home/ajou/yigyu/3/stability_adapter_2/analyze_human_pd_probe.py:13)
- [메인 PLAN 기록](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:251) · [메인 README 기록](/home/ajou/yigyu/3/stability_adapter_2/README.md:1556)
