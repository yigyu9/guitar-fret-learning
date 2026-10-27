# 무스트랩·오른손 비접촉 기타 초기 배치

이번 조건은 수평 넥·줄 면 정면 기타, 스트랩 힘과 표시 OFF, 오른손 비접촉이다. 왼손은 손바닥이 넥 아래면, 엄지가 뒷면, 나머지 네 손가락이 전면을 향하도록 정의했다. 기록된 초기 run은 `native_refine10000`이며 초기 native 감사 9개 검사를 통과했고 물리 step은 0이다. 이 단계는 새 손 관절각을 만들지 않았고 source 간격만으로 실제 접촉이나 지지를 인증하지 않는다.

## 저장된 초기 장면

아래 contact sheet는 기존 Isaac Gym native 카메라의 step-0 전신·손 정면·손 뒤쪽 이미지를 crop이나 overlay 없이 균일 축소해 배치했다.

![수평 넥 초기 장면: 기존 native 카메라의 전신·손 정면·손 뒤쪽](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/figures/initial_views_v1/initial_native_views.png)

원본: [전신 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/native_refine10000/images/frames/whole_body/00000.png), [손 정면 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/native_refine10000/images/frames/hands/00000.png), [손 뒤쪽 이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/native_refine10000/rear_hand.png), [캡처 metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/native_refine10000/images/capture.json).

## 초기값과 source 감사

refinement 선택은 [candidate_w10000.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/refine/candidate_w10000.json)이다. 기타 목표는 `p=[-0.2304154634, 0.0867123455, 0.7009729981] m`, `q_xyzw=[-0.5, 0.5, 0.5, 0.5]`이고 기준 배치보다 Z를 25 mm 올렸다. native 초기 기타 위치는 float32 표현으로 Z 약 `0.7009729743 m`다. [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/native_refine10000/initial_values.json), [initial audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/native_refine10000/initial_audit.json), [native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/native_refine10000/report.json).

Source 감사에서는 기타–인체 및 인체 자기 겹침 쌍이 0, 오른손 보수적 간격 하한이 52 mm, 손바닥 위쪽 proxy가 0.9903이었다. 설명용 영역과 palm/thumb/index/middle/ring/pinky source 간격은 각각 0.326/0.024/0.361/0.404/0.789/0 mm였다. 이는 cooked PhysX clearance, 해부학적 pad 정렬, native contact 또는 접촉력을 인증하지 않는다.

## 저장된 5초 비교

| run | 최대 기타 이동 / 회전 | 종료 이동 / 회전 | Z 하한 관측 | 구분 |
|---|---:|---:|---|---|
| `physics_off` | 133.434 mm / 28.547° | 133.434 mm / 28.542° | 최저 0.599025 m; 151개 저장 시점 중 144개가 0.65 m 미만 | 무스트랩·고정목표 기준 |
| `physics_follow` | 261.399 mm / 70.404° | 261.387 mm / 70.392° | 최저 0.580679 m; 145/151 시점이 0.65 m 미만; 300 update 중 267개 cap 기록 | 기준보다 악화 |
| `physics_hold_v5` | 62.438 mm / 15.540° | 34.364 mm / 4.620° | 최저 0.649339 m; 하한보다 최대 0.661 mm 낮은 3/151 시점; 종료 0.667007 m | 종료 위치는 범위 안; 일부 저장 시점은 하한을 소폭 벗어났고 세 면 접촉 유지는 미완료 |

v5는 300 update 중 127회 cap에 닿았고 마지막 L_Shoulder_x의 실제각−초기각 좌표 오차는 `1.73075°`였다(무스트랩 기준 `16.58°`). 이는 해당 관절의 좌표 오차이며 native 절대각이나 팔 전체 방향 각도가 아니다. v5에서 기타 이동은 초기에 최대 62.438 mm까지 갔다가 종료 때 34.364 mm였고, 2–5초 구간의 추가 변동은 최대 1.8522 mm / 0.2984°였다. 종료점이 범위 안이라는 사실은 5초 전체 범위 통과를 뜻하지 않는다.

![저장 PhysX 기타 상태 5초 비교: 위치 변화, 회전 변화, 월드 Z](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/figures/hold_compare_v5/hold_comparison_v5.png)

곡선은 저장된 native state 151개(0–5초)를 사용하며 장면 렌더가 아니다. 점선은 Z 하한 0.65 m다. `physics_hold_v5`의 접촉 자료는 8 physics-step 간격의 150개 표본과 별도 전체 step pair-count를 구분한다. 이 표본에서는 thumb가 149개 시점, pinky가 150개 시점에 기타와 접촉 행을 가졌고 양의 raw lambda는 각각 149/148개 시점에서 관측됐다. ring은 12개 시점에 접촉, 그중 11개에서 양의 raw lambda였다. palm은 이 간격 표본에서 없었지만 별도 전체 step pair-count에는 2 step이 있다. index와 middle 접촉은 기록되지 않았고 오른손 접촉도 없었다. 이 값들은 sample/census 기준의 접촉 관측이며 연속 접촉·지지력·힘(N) 판정은 아니다. 따라서 초기 source 근접은 달성했지만 palm/index/middle의 유지 접촉은 달성하지 못했고, 안정 또는 연주 성공으로 보지 않는다.

`physics_hold/`는 v5와 같은 설정으로 수행한 v4 중간 run이다. 추가 guard 검사에서 `set_dof_actuation_force_tensor` 우회 가능성이 발견됐지만 그 호출은 v4 물리 run에서 사용되지 않았다. 이를 보완한 v5가 완료됐고 v4/v5의 trace와 controls는 exact 일치한다. v5 guard 검사는 통과했다. 저장된 151개 시점 중 3개는 Z 하한보다 최대 0.661 mm 낮았으므로 5초 전체가 상자 안에 머물지는 않았다.

## 저장 자료와 재현 파일

[연속된 5초 native 영상: v5 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/physics_hold_v5/images/whole_body.mp4)

![v5 native 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/physics_hold_v5/images/whole_body.mp4)

[연속된 5초 native 영상: v5 손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/physics_hold_v5/images/hands.mp4)

![v5 native 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/physics_hold_v5/images/hands.mp4)

각 영상은 151 frame, 30 fps, ffprobe stream duration 5.033333초다. 같은 형식의 [무스트랩 전신/손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/physics_off/images/whole_body.mp4)과 [손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/physics_off/images/hands.mp4), [follow 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/physics_follow/images/whole_body.mp4)과 [follow 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/physics_follow/images/hands.mp4)도 저장돼 있다.

비교 그림은 [plot_hold_comparison.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/figures/plot_hold_comparison.py:1)가 저장 trace만 읽어 생성했다. [입력·출력 SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/figures/hold_compare_v5/manifest.json), [실행 metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/figures/hold_compare_v5/artifact_execution.json), [실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/figures/hold_compare_v5/artifact_execution.log)을 확인한다. 이 그림 생성은 native 실행이나 물리 step을 추가하지 않았다. 전체 파일 색인은 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/CHANGED_FILES.md:1)에 있다.
