# 가슴·오른쪽 위팔 초기 지지 비교

## 결과 범위

4개 실제 native 실행이 각 5초(1,200 physics step) 정상 완료됐다. 기타는 자유 동역학이며 strap·강제 부착·인위적 기타 힘은 없고 humanoid root/하체는 고정, self-collision은 켰다. 오른쪽 위팔의 유한한 제어 지지는 유지했다. 공통 초기 기타 body BB 중심은 W=[0.143238, −0.001125, 0.683019] m이며 actor-root 값은 실행별로 다를 수 있다. 다른 75개 관절 목표는 유지했지만 실제 관절 상태까지 고정한 것은 아니다.

| run | 조건 | LH arm/hand 기타 접촉 | 최대 기타 BB 변위 | 최대 SO(3) |
|---|---|---:|---:|---:|
| `native_hold_v2` | 지지 유지, 무타현 | 804 / 1,200 | 2.759 mm | 0.680° |
| `native_strike_near_v1` | 왼손 근접 준비, EW6 타현 | 1,090 / 1,200 | 4.287 mm | 1.219° |
| `native_strike_left_clear_v1` | 실제 초기 이격 6.02 cm, EW6 | 326 / 1,200 | 4.601 mm | 2.486° |
| `native_strike_left_far_v1` | 목표 이격 G=[0.070, 0.080, 0] m, norm 10.630 cm, EW6 | 0 / 1,200; RH hand 0 / 1,200 | 4.915 mm | 2.833° |

Near는 왼손 넥 준비를 기본으로 보는 사용자 선택안이다. Clear의 왼팔/손 접촉 326회 때문에 독립 지지 증거가 아니다. Far만 5초 동안 LH arm/hand와 RH wrist/hand 모두 기타에 닿지 않았지만 L_Hip 접촉이 있었으므로 전신의 왼쪽 접촉이 전혀 없었다고 말하지 않는다. 홀드 실행은 타현을 하지 않았고 EW6 가상 피크 타현은 나머지 세 실행에서만 동작했다. 6줄 하향 6→1 및 상향 1→6 통과는 선별된 원시 시퀀스 분석 결과이지 학습된 곡 연주 성공이 아니다.

Far의 양의 raw contact lambda 표본 수는 다음과 같다. lambda는 보정된 힘(N)이 아니다.

| 실제 구간 (physics step 기준) | 표본 | Chest | R_Shoulder (오른쪽 위팔) | R_Hip (오른쪽 허벅지) | L_Hip (왼쪽 허벅지) |
|---|---:|---:|---:|---:|---:|
| 0–2.0 s | 480 | 448 | 474 | 477 | 1 |
| 2.0–3.75 s | 420 | 297 | 420 | 420 | 11 |
| 3.75–5.0 s | 300 | 0 | 300 | 300 | 259 |

따라서 상승 타현 3.75–5초에는 Chest 접촉이 끊기지만 오른쪽 위팔·허벅지와 왼쪽 허벅지 접촉은 남는다. 상태 변화는 기타 body BB 중심 변위와 SO(3) 회전으로 [240 Hz 전체 시계열 표](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/motion_samples_v1.csv>) 및 [그래프](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/guitar_BB_motion_SO3_240Hz_v1.png>)에 표시했다.

## 초기 자세와 이미지 비교

오른손 ring/pinky 세 관절의 −0.21/−0.30/−0.18 rad 값은 각각 1x/2/3의 **기존 준비각 대비 보정량**이며 절대 초기각이 아니다. 네 native 시작 상태의 실제 81개 qpos와 q_ref는 [전체 표](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/initial_joint_angles_81_v1.csv>)에 run별로 기록했다. 실제 자세 시점마다 원본 카메라 이미지를 사용했으며, 비교 시트에는 글자나 캡션을 넣지 않았다.

초기 시트는 행 순서가 hold, near, clear, far이고 열은 native overview, support side, string view다. 아래 이미지는 native 카메라 원본을 축소·배치한 비교 시트다.

![4실행의 실제 초기 native 카메라 3-view 비교; 행/열 안내는 본문](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/initial_three_view_comparison_v1.png)

최종 시트도 같은 행 순서이며 열은 5초 시점 whole body, hands, chest/arm close다. 캡션은 이미지 밖에 두었다.

![4실행의 5초 실제 native 카메라 3-view 비교; 행/열 안내는 본문](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/final_three_view_comparison_v1.png)

모든 이미지·영상은 Isaac Gym native camera의 실제 캡처이며 줄 endpoint 사이 비물리적 6개 선 표시를 포함한다. 합성 시 원본 이미지는 잘라내거나 덧그리지 않았다. 캡처 원본과 바이트 보존 복사 SHA는 [manifest](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/copy_manifest_v1.json>)에 있다.

## 초기 각도 보정 및 한계

| 오른손 관절 그룹 | 기존 준비각 대비 변경량 |
|---|---:|
| `RH:ring1_x`, `RH:pinky1_x` | 각 −0.21 rad |
| `RH:ring2`, `RH:pinky2` | 각 −0.30 rad |
| `RH:ring3`, `RH:pinky3` | 각 −0.18 rad |

− 값은 flexion 증가가 아니라 기존 준비에서 덜 말리도록 하는 변경이다. source geometry query는 초기 자세와 61개 정적 경로 표본에 대한 proxy이며 0.2 mm 초기 clearance는 PhysX cooked 형상/연속경로 인증이 아니다. Native 실제 접촉 자료는 별도 증거로 집계했고 force N을 제공하지 않는다.

초기 native_hold_v1은 support_side camera key 누락으로 0 physics step에서 실패했으며 완료 실행에 포함하지 않았다 ([원본 report](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/native_hold_v1/report.json>)). V7 phase detector가 반영된 [preferred analysis](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/analysis_v1.json>)의 down/up 6줄 집계를 사용한다. 오래된 detector 판정은 V7의 실제 상승 종료 3.75 s에 적용하지 않는다. Near가 선호 사용자 준비 영상, Far가 LH arm/hand 접촉 분리 영상이다. 두 경우 모두 passive equilibrium, force closure, 강건성, 학습 음악 성공을 입증하지 않는다.

[scope correction](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/metadata_scope_correction_v1.json>) · [61-sample source path proxy](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/source_path_v1.json>) · [근접 자세 source audit](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/finger_search_v2/left_clear_head_audit.json>) · [preferred test-space 안내(V2)](/home/ajou/yigyu/3/stability_adapter_2/chest_upperarm_pose_test_v1/README_v2.md)

[전체 영상 index](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/chest_upperarm_initial_v1/README.md) · [작성 전 input pin](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/artifact_before_v1.json>)
