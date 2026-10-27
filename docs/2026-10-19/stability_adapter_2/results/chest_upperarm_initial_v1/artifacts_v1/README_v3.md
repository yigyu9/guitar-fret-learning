# 가슴·오른쪽 위팔 초기 지지 비교

## 결과

4개 native 실행이 각각 5초(1,200 physics step) 완료됐다. 기타는 자유 동역학이며 strap·강제 부착·인위적 기타 힘은 없고, humanoid root와 하체는 고정했다. self-collision은 켰고 오른쪽 위팔의 유한한 제어 지지는 유지했다. 네 실행의 기타 초기 body BB 중심과 actor root는 모두 동일하다. 다른 75개 관절 목표는 유지했지만 실제 관절 상태까지 고정한 것은 아니다.

| 실행 | 왼팔·손 기타 접촉 | 최대 기타 body BB 중심 변위 | 최대 SO(3) 회전 |
|---|---:|---:|---:|
| Hold, 무타현 | 804/1,200 | 2.759 mm | 0.680° |
| Near, EW6 타현 | 1,090/1,200 | 4.287 mm | 1.219° |
| Clear, 실제 초기 이격 6.02 cm | 326/1,200 | 4.601 mm | 2.486° |
| Far, 목표 이격 10.630 cm | 0/1,200; 오른손목·손도 0/1,200 | 4.915 mm | 2.833° |

Near는 root가 우선 검토안으로 추천한 왼손 넥 준비다. 사용자가 새 자세를 검토하거나 선택했다는 뜻은 아니다. Clear에는 왼팔·손 접촉이 있어 독립 지지 증거가 아니다. Far에서는 왼팔·손과 오른손목·손이 기타에 닿지 않았지만, 왼쪽 허벅지 접촉은 남는다. 따라서 기타를 오른쪽 위팔·허벅지만으로 지지했다고 해석할 수 없다. Hold는 타현하지 않았으며 다른 세 실행만 EW6 가상 피크로 타현했다.

Far의 양의 raw contact lambda 표본은 다음과 같다. 이는 보정된 힘(N)이 아니다.

| 구간 | 표본 | Chest | R_Shoulder (오른쪽 위팔) | R_Hip (오른쪽 허벅지) | L_Hip (왼쪽 허벅지) |
|---|---:|---:|---:|---:|---:|
| 0–2.0 s | 480 | 448 | 474 | 477 | 1 |
| 2.0–3.75 s | 420 | 297 | 420 | 420 | 11 |
| 3.75–5.0 s | 300 | 0 | 300 | 300 | 259 |

V7 phase 기준에서 상승(upstroke)은 **3.75초에 시작해 4.45초에 끝난다**. Chest 접촉은 상승 시작 전까지 끊기며, 상승 구간에는 오른쪽 위팔·오른쪽 허벅지·왼쪽 허벅지 접촉이 남는다. 6줄 하향 6→1 및 상향 1→6 통과는 선별된 원시 시퀀스 분석 결과이며 학습된 곡 연주 성공을 뜻하지 않는다.

## 자세·영상과 한계

오른손 ring/pinky 관절의 −0.21/−0.30/−0.18 rad는 각 1x/2/3 기존 준비각 대비 보정량이지 절대 초기각이 아니다. 네 native 시작 상태의 실제 81개 qpos와 q_ref는 [표](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/initial_joint_angles_81_v1.csv)에 있다. 시각 비교는 [초기 3-view](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/initial_three_view_comparison_v1.png)와 [5초 3-view](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/final_three_view_comparison_v1.png), 움직임은 [그래프](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/guitar_BB_motion_SO3_240Hz_v1.png)와 [240 Hz 원자료](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/motion_samples_v1.csv)에서 확인할 수 있다. [전체 영상](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/chest_upperarm_initial_v1/README_v2.md>)은 native Isaac Gym 카메라 캡처이며 비물리적 6개 string endpoint 선 표시를 포함한다. 비교 시 원본 이미지는 자르거나 덧그리지 않았다.

초기 native_hold_v1은 support_side 카메라 키 충돌(영상 recorder 기대 해상도 1280×720, 상속 카메라 해상도 1280×960)로 0 physics step에서 실패했다. 이는 카메라 키 누락이 아니다. [실패 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/native_hold_v1/report.json)는 완료 실행에 포함하지 않았다. 선호된 근접 source 검사는 [finger_search_v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/finger_search_v2/search.json), [near audit](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/finger_search_v2/near_audit.json), [finger_search_v3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/finger_search_v3/search.json)에서 확인한다. `source_path_v1.json`은 준비 전 오른손 ring/pinky가 61개 표본 중 39개에서 걸린 실패 경로라 선호 결과로 취급하지 않는다. 0.2 mm source clearance와 61개 경로 표본은 정적 proxy 검사이며 PhysX cooked 형상이나 연속 경로를 인증하지 않는다. Native 접촉 분석은 별도 증거이며 force N을 제공하지 않는다. 결과는 passive equilibrium, force closure, 강건성 또는 학습 음악 성공을 입증하지 않는다.

사전 preflight에서 README 경로 수정으로 입력 SHA 변경이 감지되어 `artifact_before_v1.json`의 기존 입력 map을 덮어쓴 기록상 한계가 있다. 실제 산출 전에 현재 입력 pin을 다시 확인했고 산출 후에도 동일성을 검증했다. 물리 원자료는 수정하지 않았다. 복사본 및 산출물의 현재 SHA는 [manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/copy_manifest_v1.json)에 기록돼 있다. 원래 before map을 복원한 것처럼 가장하지 않는다.

[Preferred analysis](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/analysis_v1.json) · [scope correction](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/metadata_scope_correction_v1.json) · [near 사용자 test-space 안내](</home/ajou/yigyu/3/stability_adapter_2/chest_upperarm_pose_test_v1/README_v2.md>)


## 실제 장면

초기 비교의 행은 위에서 hold, near, clear, far, 열은 정면·측면·줄 표시다. 캡션은 형상을 가리지 않도록 이미지 밖에 둔다.

![실제 초기 자세 네 조건 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/initial_three_view_comparison_v1.png)

5초 마지막 프레임은 같은 행 순서이며 열은 전신·손·가슴/위팔 근접이다.

![5초 마지막 실제 장면 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/final_three_view_comparison_v1.png)

![240Hz 기타 바디 중심 이동과 회전](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/guitar_BB_motion_SO3_240Hz_v1.png)

V1/V2 설명은 이력으로 보존한다. 이 V3는 상대 링크를 절대 경로로 바꾸고 카메라 기대/실제 해상도의 순서를 바로잡은 권장 문서다. [기록 정정 범위](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/doc_correction_v1/correction.json).
