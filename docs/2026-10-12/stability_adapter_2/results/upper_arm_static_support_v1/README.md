# 연주 없는 초기 자세 유지 시험 — 완료

초기 자세만 바꾼 네 조건의 Isaac Gym 5초 시험을 완료했다. **3° 전경 후보는 2초 이후 가장 조용했지만, 초기에서 약 10.6cm·17.4° 움직였다. 초기 기타 자세 유지와 겨드랑이 지지는 아직 달성하지 못했다.**

## 비교 조건과 실제 결과

기준, 오른상완 접근 0°, 전체 Chest 전경 3°·5°를 비교했다. 전경은 몸통 관절의 초기각으로 나눠 적용했고, 왼손 손바닥의 초기 world 위치·방향은 유지했다. 기타 초기 위치·회전, root·고정 하체, 손가락·머리 초기각, 원본 스트랩 길이·법칙, PD 속성·solver는 같았다. 각 관절의 초기 q_ref를 5초 동안 일정한 PD 목표로 제출했다. 실제 관절은 물리에 따라 움직였으며 기타나 손을 고정하거나 실행 중 pose를 덮어쓰지 않았다.

Fret·Strike, 체크포인트, 안정화 정책, 학습, 초기 노이즈, 기존 preload 보정·PI·실시간 IK는 실행하지 않았다. 설정의 PREP/PLAY 표시는 이번 runner에서 연주 호출을 의미하지 않는다.

| 조건 | 초기→5초 위치 변화 | 초기→5초 회전 | 2→5초 위치 변화 | 2→5초 회전 |
|---|---:|---:|---:|---:|
| 기존 기준 | 11.28cm | 19.63° | 1.175mm | 0.2283° |
| 오른상완 접근·전경 0° | 10.05cm | 15.96° | 0.305mm | 0.1246° |
| 오른상완 접근·전경 3° | 10.59cm | 17.41° | 0.062mm | 0.0168° |
| 오른상완 접근·전경 5° | 10.78cm | 18.34° | 0.466mm | 0.1679° |

위치는 기타 actor-root의 world 이동거리, 회전은 자기 초기 quaternion과의 SO(3) 거리다. 기타 바디 중심의 자연 허용범위를 평가한 수치가 아니다. 후기 열은 2초와 5초의 두 상태 간 변화이며 전체 구간 최대값과 구분한다. 기준도 2초 이후 움직임이 작으므로 조용해진 현상을 새 자세만의 효과로 볼 수 없다. 초기 이탈은 0° 후보가 가장 작고, 후기 변화는 3° 후보가 가장 작았다. 더 기울이면 더 좋아지는 결과는 아니다.

## 실제 지지 부위

60Hz 제어 직전 300개 native 접촉 표본을 대조했다. 오른 전완 capsule인 R_Elbow는 기준/0°/3°/5°에서 282/289/288/287개 시점에 기타와 접촉했다. 오른상완 R_Shoulder는 5°에서만 55개 시점(0.4333–1.3333초)에 일시적으로 접촉했으며 나머지 조건은 0개였다. Chest·Torso·Spine 접촉은 모두 0개였다. 오른 허벅지와 왼손 손바닥 접촉도 관측됐다.

따라서 현재 평형은 주로 **전완·허벅지·왼손 접촉을 동반한 평형**이다. 겨드랑이로 기타를 지속적으로 끼운 상태라고 해석하면 안 된다. raw 접촉 λ는 N 단위 힘이나 압력으로 환산하지 않았다. 상완의 양의 source 예측 간격 또한 PhysX cooked 형상의 최단 간격이나 접촉 인증이 아니다.

## 영상·이미지와 검증

![전경 3° 후보의 실제 Isaac Gym 전신 영상, 0–5초](/home/ajou/yigyu/3/docs/2026-10-12/video/upper_arm_static_support_v1/lean3_gap500_z-10_whole_body.mp4)

![네 조건의 실제 초기·2초·5초 전신 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/artifacts_v1/native_whole_body_frames_v1.png)

![초기 변화와 후기 변화 분리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/artifacts_v1/root_motion_traces_v1.png)

각 시험은 1200 physics step·300 control step을 완료했고, 전신·손 영상은 각각 151프레임/30fps다. 물리 경과는 정확히 5초, t=0 프레임을 포함한 영상 재생 길이는 5.033333초다. 스트랩 경로도 함께 표시했다. 5초까지 물리가 계속 실행됐으므로 후기 정지는 환경 조기 종료 때문이 아니다.

- [전신·손 8개 영상 모음](/home/ajou/yigyu/3/docs/2026-10-12/video/upper_arm_static_support_v1/README.md:1)
- [전체 영상 색인 V11](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V11.md:1)
- [실행·입력·영상 검증 32개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/verification_v2.json:1)
- [동일 조건 검증 8개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/same_conditions_verification_v1.json:1)
- [실제 초기 관절각·PD·기타 상태: 3°](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/native_v2/lean3_gap500_z-10/initial_values.json:1)
- [실행 전 정정 계획](/home/ajou/yigyu/3/stability_adapter_2/UPPER_ARM_STATIC_SUPPORT_PLAN_V2.md:1)

v1 준비 설정의 prep=horizon 오류는 native 실행 전에 검수에서 발견했다. 원본을 보존하고 prep=2초/horizon=5초인 v2 설정으로 네 시험을 실행했다. source 간격 요청값과 예측값을 혼동하지 않았으며, 실제 초기 FK와 소스 예측 pose의 일치는 별도로 검증했다.

## 다음 소단계 제안

연주 없이 초기 지지 위치를 먼저 개선한다. 지금의 3° 후보를 후기 평형 참고로 남기되, 상완 끝점만 가까이 두는 목표를 실제 capsule 접촉 위치·기타 바디 표면 범위에 맞춰 바꾸고 오른팔 두 segment의 위치를 함께 확인한다. 기타가 약 10cm 떨어진 뒤 접촉을 만드는 것이 아니라 시작 때부터 지지가 형성되는지를 우선 비교한다. 왼손 넥 지지와 기타 자연 범위도 함께 확인하며 원본 스트랩 길이는 유지한다. 이 후속 실험은 이번 네 조건에서 검증한 결과가 아니라 다음 계획이며 아직 실행하지 않았다.
