# 초기 자세 후보 탐색 — 9회 native 결과 (V2 문구 정정본)

 ## 요약

 `margin_only`는 현재 정적/타현 후속 시험용 **임시 후보**다. 전체 왼손 task의 적격 후보는 0개이며, 전역 기본값은 바꾸지 않았다. 네 정적 조건은 5초 관측을 완료했지만 전 구간에서 왼팔·손이 분리된 조건은 아니다. 왼손 task 세 번은 모두 기타/actor-root 안전 한계로 보호 중단됐다. 따라서 현재 자료로 완전한 왼손 운지·양손 연주·수동 평형을 선언할 수 없다.

 총 9회는 네 정적 후보(`margin_only`, `roll_m2`, `roll_p2`, `torso_p2`), 세 왼손 16초 task, 한 EW6 스크립트 타현, 그리고 `margin_only` 정적 exact repeat다. source 검사에서 7개 제안 중 5개가 다음 단계 후보로 적격이었지만, 이는 source analytic 검사이며 cooked 연속 충돌 인증이 아니다. 4개 정적 조건만 실제 native 비교에 포함됐고 `roll_m2_torso_p2`는 이번 9회 native 시험에 없었다.

 ## 9회 결과

 | 조건·모드 | 실제 진행 | 기타 BB 최대 이동 / 회전 | 왼팔·손 무접촉 | 오른손목·손 접촉 | 카메라 끝·영상 |
 |---|---|---|---|---|---|
 | margin_only · static | 완료 · 5.000s | 3.287mm / 0.819° | LH 무접촉 418/1200 | RH 손목·손 0 | 카메라 5.000s · 151f · 5.033333s |
| roll_m2 · static | 완료 · 5.000s | 6.067mm / 2.353° | LH 무접촉 46/1200 | RH 손목·손 0 | 카메라 5.000s · 151f · 5.033333s |
| roll_p2 · static | 완료 · 5.000s | 20.857mm / 4.728° | LH 무접촉 93/1200 | RH 손목·손 0 | 카메라 5.000s · 151f · 5.033333s |
| torso_p2 · static | 완료 · 5.000s | 3.999mm / 1.159° | LH 무접촉 113/1200 | RH 손목·손 0 | 카메라 5.000s · 151f · 5.033333s |
| margin_only · left | 보호 중단 · 9.967s | 112.825mm / 29.122° | LH 무접촉 1315/2392 | RH 손목·손 798 | 카메라 9.933s · 299f · 9.966667s |
| torso_p2 · left | 보호 중단 · 6.433s | 62.826mm / 28.493° | LH 무접촉 468/1544 | RH 손목·손 18 | 카메라 6.400s · 193f · 6.433333s |
| roll_m2 · left | 보호 중단 · 10.017s | 116.170mm / 30.141° | LH 무접촉 1132/2404 | RH 손목·손 916 | 카메라 10.000s · 301f · 10.033333s |
| margin_only · strike | 완료 · 5.000s | 5.116mm / 2.203° | LH 무접촉 337/1200 | RH 손목·손 0 | 카메라 5.000s · 151f · 5.033333s |
| margin_only · static_repeat | 완료 · 5.000s | 3.287mm / 0.819° | LH 무접촉 418/1200 | RH 손목·손 0 | 카메라 5.000s · 151f · 5.033333s |

 완료한 5초 물리 구간은 t=0 초기 프레임을 포함한 0–5초 총 151개 표본이며, 30fps MP4 재생 길이는 5.033333초다. MP4 재생 길이는 추가 물리 경과를 뜻하지 않는다. 세 왼손 실패 영상은 각각 299프레임/9.966667초, 193프레임/6.433333초, 301프레임/10.033333초다. 실제 물리 종료와 카메라 마지막 시각, MP4 재생 길이는 서로 다른 값이므로 각 조건별 표를 함께 본다.

 ### 정적 비교 이미지

 아래 네 이미지는 각각 실제 native annotated 전면·옆면·위 3-up의 5초 snapshot이다. 각 source PNG를 바이트 그대로 복사했다.

 ![margin_only 정적 5초 끝 시점](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/images/static_comparison/margin_only_t5_three_views.png)

![roll_m2 정적 5초 끝 시점](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/images/static_comparison/roll_m2_t5_three_views.png)

![roll_p2 정적 5초 끝 시점](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/images/static_comparison/roll_p2_t5_three_views.png)

![torso_p2 정적 5초 끝 시점](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/images/static_comparison/torso_p2_t5_three_views.png)

 초기 상태 3시점은 `margin_only` 정적 실행의 t=0 front/right/top native annotated frames다: [전면](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/images/initial_views/front.png) · [오른쪽 옆면](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/images/initial_views/right_side.png) · [위](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/images/initial_views/top.png).

 ## 왼손 보호 중단과 접촉 해석

 세 왼손 실행 모두 actor-root 변위가 200 mm 안전 한계를 넘어 보호 중단됐다. 기타 BB 중심 이동은 actor-root 변위와 다른 기준점이다. 회전은 각각 29.122°, 28.493°, 30.141°로 35° 회전 한계보다 낮았다. 오류 로그 문구는 `guitar safety displacement`지만 결과집계의 보호 조건은 actor-root 병진이다.

 - `margin_only` 왼손: 물리 종료 9.966667 s, 마지막 카메라 9.933333 s(차이 0.033333 s), 299프레임·9.966667 s. actor-root 최대 205.923 mm, BB 중심 112.825 mm / 29.122°. A hold 3–4.5 s에서 엄지+다른 손가락 양의 raw lambda가 360/360표본이었다. 6–7 s A open에서는 LH 접촉 없음 240/240이었지만 RH 접촉이 97/240 있었다. 7–8.5 s B로 이동할 때 LH는 360/360 무접촉이었으나 RH:middle3 접촉도 360/360이었다. B hold/release 완료가 아니며 두 손이 동시에 독립 접촉으로 분리된 증거가 아니다.
 - `torso_p2` 왼손: 6.433333 s 보호 중단, 카메라 6.400000 s(0.033333 s 차이), 193프레임·6.433333 s. actor-root 최대 203.210 mm, BB 중심 62.826 mm / 28.493°. A open 단계 6.000–6.433 s에서 104 physics ticks만 실행했고 B에 도달하지 않았다.
 - `roll_m2` 왼손: 10.016667 s 보호 중단, 카메라 10.000000 s(0.016667 s 차이), 301프레임·10.033333 s. actor-root 최대 210.964 mm, BB 중심 116.170 mm / 30.141°. B close에 들어갔지만 holdB와 releaseB는 완료하지 않았다.

 대표 실패의 마지막 카메라 화면은 종료 전 0.033333초의 관측 프레임이며 평형 시점이 아니다.

 ![margin_only 왼손 task 보호 중단 직전 native 3-up](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/images/left_failure/margin_only_left_last_camera.png)

 ## 스크립트 타현

 `margin_only` 타현 trial은 5초 완료했으며 기타 BB 최대 5.116316 mm / 2.203204°, RH 손목·손 접촉 0, LH raw contact query는 863/1200표본이었다. 이 시험은 EW6 팔꿈치·손목 6-DOF IK 스크립트이며 checkpoint 연결은 OFF다. 명령된 가상피크 검출 실제 창은 down 3.20–3.55 s와 up 3.75–4.45 s이며 원본 detector 순서는 하향 6→5→4→3→2→1, 상향 1→2→3→4→5→6이다. legacy 상향 집계의 3.95 s cutoff는 상향 앞부분의 1·2번 줄을 제외해 3·4·5·6번만 집계한다. 원자료는 그대로 보존했다. 이것은 곡 학습/체크포인트 음악 수행 성공이 아니다.

 ![EW6 스크립트 타현 5초 끝 native 3-up](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/images/strike/margin_only_strike_t5.png)

 ## 후보 초기값과 범위

 임시 후보의 기타 BB 중심 world 위치는 `[0.143230, -0.001173, 0.683022] m`, 기타 actor-root world 위치는 `[-0.258574, -0.005746, 0.723792] m`, 기타 쿼터니언 xyzw는 `-0.471704, 0.446243, 0.592982, 0.476167`다. root·하체 fixed, strap enabled=`False`. 주요 몸통 DOF scalar 값은 초기 목표 및 native actual이다. suffix는 native DOF 축 이름이며 world rotation axis가 아니다.

 | DOF | 목표 (rad) | 초기 실제 (rad) |
 |---|---:|---:|
 | Torso_x | 0.145636 | 0.145636 |
| Torso_y | -0.032888 | -0.032888 |
| Torso_z | -0.200075 | -0.200075 |
| Spine_x | 0.323174 | 0.323174 |
| Spine_y | -0.024752 | -0.024752 |
| Spine_z | -0.017793 | -0.017793 |
| Chest_x | -0.034321 | -0.034321 |
| Chest_y | 0.317744 | 0.317744 |
| Chest_z | 0.000279 | 0.000279 |
| Neck_x | -0.036902 | -0.036902 |
| Neck_y | 0.005338 | 0.005338 |
| Neck_z | 0.212275 | 0.212275 |
| Head_x | -0.060227 | -0.060227 |
| Head_y | 0.083957 | 0.083957 |
| Head_z | 0.149916 | 0.149916 |

 전체 [81개 관절각 초기값 JSON](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/comparison_v1/static_candidate_initial_values.json) · [관절각 CSV](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/comparison_v1/static_candidate_joint_angles.csv) · [native initial values](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/native_margin_only_static_v1/initial_values.json).

 source proxy 검사와 native 관측은 구분한다. source report의 analytic capsule/형상 검사는 이산 초기 자세 source 모델 검사이며 PhysX cooked 형상의 연속 clearance나 움직이는 동안의 비관통 인증이 아니다. 아래 PNG/영상과 접촉 수는 native visual report의 실제 annotated frames/MP4 및 native query 집계다.

 ## 공통 조건과 한계

 아홉 실행 모두 자유 기타, strap OFF, root·하체 고정, self-collision ON, 유한한 active human control이다. 기타 고정/부착, 기타 힘, 매 프레임 상태 덮어쓰기는 사용하지 않았다. contact overlay는 고정 반경·X-ray 표시다. 채운 원은 양의 raw lambda, 빈 원은 lambda=0이며 힘(N)·압력·접촉 면적이나 marker 크기 단위가 아니다. 초록/분홍 손 재질은 접촉 색 범례가 아니다. 상체 제어가 남아 있어 관측된 지지는 수동 평형을 뜻하지 않는다.

 완료 정적 조건들의 LH free 표본은 각각 418/1200, 46/1200, 93/1200, 113/1200이고 RH 손목·손 접촉은 0이다. 이 표본 비율은 full-trial independent-support pass가 아니다. 세 LH trial 전체 기준 LH free 1315/2392, 468/1544, 1132/2404이며 RH hand contacts는 각각 798, 18, 916이다. Exact repeat는 initial values, state trace, actual contacts, final efforts, final state 5개 파일 SHA가 정적 실행과 같았다.

 ## 원자료·영상

 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/README_v3.md) · [변경 파일 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/changed_files_v3.md).

[36개 MP4 전체 index](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_search_v1/README_final_v3.md) · [승인된 9시험 brief](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifact_brief_v1.json) · [comparison report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/comparison_v1/report.json) · [native/source proposal report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/search_v2/report.json) · [240 Hz joint audit](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/joint_240hz_audit_v1.json) · [실제 EW6 windows](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/strike_actual_windows_v1.json) · [copy manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/artifact_manifest_v2.json).

 이 문서와 영상 색인은 서로 연결된 동일 버전이다. 복사된 PNG/MP4는 source visual report SHA와 일치하며 재인코딩하지 않았다.
 