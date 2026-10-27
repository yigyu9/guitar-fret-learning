# 수평 넥 초기 회전 비교

![요청한 −10°, 0°, +10° 넥 각도의 native camera 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/artifacts_v2/horizontal_neck_initial_comparison.png)

세 장면은 물리 실행이 아닌 t=0 정적 배치 촬영이다. CPU PhysX와 Mesa lavapipe ICD를 설정해 실제 Isaac Gym camera PNG를 만들었고 물리 step은 0이다. NVIDIA 장치는 없으며 실제 graphics backend 식별자는 확인하지 않았다. CUDA/visual-geometry 경고가 로그에 있지만 세 후보 이미지와 native camera 검사 결과는 저장됐다. 이는 MuJoCo 그림이나 source geometry 재구성이 아니다.

| 요청 넥 상승각 | 렌더된 넥 상승각 | 앞판 법선 상승각 | 목적 |
|---:|---:|---:|---|
| −10° | −9.9999968° | +0.0000037° | 비교 후보 |
| 0° | 0° | 0° | 수평 넥 우선 후보 |
| +10° | +9.9999968° | −0.0000037° | 비교 후보 |

좌표는 world Z-up이다. 넥 local +Y를 `[-cos(a), 0, sin(a)]`, 앞판 local +Z를 world `[0,1,0]`에 맞췄다. 바디 중심을 고정하는 회전 후보를 계산하고 actor root 위치를 함께 보정해 `[0.16958454, 0.06501235, 0.67597298] m`를 유지한다. 0° 후보의 실제 저장 pose는 [pose.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/native/scene/candidate_001/pose.json)이며 실제 native root 위치 `[-0.2304154634, 0.0867123455, 0.6759729981] m`, quaternion xyzw `[-0.5, 0.5, 0.5, 0.5]`다. pose를 정적 편집기에서 여는 명령:

```bash
bash /home/ajou/yigyu/3/stability_adapter_2/open_guitar_pose_static.sh --candidate /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/native/scene/candidate_001/pose.json
```

권고와 미검증 범위는 [초기 회전 결정 메모](/home/ajou/yigyu/3/stability_adapter_2/HORIZONTAL_NECK_INITIAL_DECISION.md:3), 정적 native 촬영의 exit/step 요약은 [native_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/native_execution.json)에 있다.

0°는 수평 넥과 정면을 향한 앞판에 맞는 우선 초기 회전 후보지만, 기존 왼손이 상대적으로 높아 팔·손 초기각 재배치가 필요하다. 이 단계는 접촉, 관통, 자유 기타 유지, 학습을 검증하지 않았고 기본 시작 pose도 바꾸지 않았다.

비교표는 앞·측면·손 근접의 저장 camera PNG를 요청각 순서로 배열했다. 원본 1280×720 이미지를 비율 유지해 축소했으며 crop이나 overlay는 없다. 첫 표 초안은 음수 기호 글꼴 표시가 깨져 보존했고, 현재 canonical 표에서는 ASCII 하이픈으로 수정했다. 표와 mapping의 입력·출력 SHA는 [v2 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/artifacts_v2/artifact_manifest.json)에 있다. [첫 표 산출물](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/producer_attempt_v1/)과 [최종 producer](/home/ajou/yigyu/3/stability_adapter_2/build_horizontal_guitar_sheet.py)는 보존되어 있다.

검증 입력은 [native comparison](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/native/comparison.json), [계산 pose](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/computed_poses.json), 그리고 각 후보의 저장 pose와 세 camera 이미지다. 정적 회전 계산 및 촬영 범위는 [계획](/home/ajou/yigyu/3/stability_adapter_2/HORIZONTAL_NECK_INITIAL_PLAN.md), [pose helper](/home/ajou/yigyu/3/stability_adapter_2/horizontal_guitar_pose.py), [native renderer](/home/ajou/yigyu/3/stability_adapter_2/render_horizontal_guitar.py)에 설명되어 있다.
