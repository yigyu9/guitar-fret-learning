# 같은 시작 자세의 스트랩 힘 켬/끔 실제 5초 비교

사용자 요청에 따라 기존 `initial_middle3_alignment_v1` 시작 자세와 81×1200 목표 명령을 그대로 두고, 별도 실행에서 스트랩 cable force와 주황 경로 overlay를 끈 실제 5초 영상을 기록했다. Root와 하체 고정, 몸통 9관절 PD hold, 자유 기타, 중력·실제 접촉·관절 PD, 손목 ±0.005 rad·1 Hz 명령은 유지했다. 비교한 20개 공통 초기 필드와 모든 1200×81 명령은 exact다. 분석 검사 이름 `all21_initial_fields_exact`는 legacy 이름으로 보존되어 있지만 실제 `compared_initial_fields` 목록은 20개다.

| 측정값 | 기존 스트랩 힘 켬 | 이번 스트랩 힘 끔 |
|---|---:|---:|
| 초기 자세 기준 최대 기타 위치오차 | 14.608483 mm | 20.584004 mm |
| 초기 자세 기준 최대 기타 회전오차 | 2.918412° | 12.152977° |
| 5초 위치오차 / 회전오차 | 13.819696 mm / 2.918277° | 20.525764 mm / 12.145216° |
| 후기 완전 1초 창 최대 위치변화 / 회전변화 | 0.648625 mm / 0.115306° | 0.335897 mm / 0.064720° |
| 임시 초기 30 mm / 5° 구역 밖 표본 | 0/1201 | 1145/1201 (회전 5° 초과) |
| 임시 후기 1초 창 5 mm / 1° 이내 | 121/121 | 121/121 |

스트랩 힘을 끈 조건에서 후반 창의 변동은 더 작았지만, 기타는 처음 위치·자세에서 크게 벗어난 새 자세로 움직였다. 후기 1초 창 통과만으로 초기 자세 유지 성공이라고 볼 수 없다. 반면 같은 초기 자세에서 strap-on 기준의 초기 최대 회전오차는 2.918412°였고 strap-off에서는 12.152977°였다. 이번 별도 비교에서는 스트랩 힘이 초기 회전 억제에 도움을 줬다. 본선의 고정 LA 기준은 바꾸지 않는다.

스트랩 힘 OFF 상태에서도 nominal LA `1.1018469719600776 m`와 route 길이 `1.0857446870679612 m`는 비활성 진단값으로 기록돼 있다. `strap_enabled=false`, `strap_rendered=false`, explicit force API 호출 0회, 1201개 표본의 applied tension 0이다. 따라서 남아 있는 nominal route/LA 숫자를 실제 스트랩 사용으로 해석하지 않는다. 손·기타 강제 부착이나 시작 후 pose 덮어쓰기도 없었다.

## 실제 Gym 프레임

아래 네 장은 이번 CPU PhysX native 실행에서 저장한 원본 카메라 이미지다. 전체 raw native PNG 302개의 SHA를 대조해 보존했다. t=0과 step 1200의 시뮬레이션 시간은 각각 0.000초와 5.000초다. 151프레임을 30 fps로 만든 MP4 파일 재생시간은 5.033333초다. 프레임에 경로 overlay는 없으며 이미지를 편집하지 않았다.

![손 카메라 실제 native 프레임, t=0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/frames/hands/00000.png)

![손 카메라 실제 native 프레임, t=5.000초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/frames/hands/00150.png)

![전신 카메라 실제 native 프레임, t=0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/frames/whole_body/00000.png)

![전신 카메라 실제 native 프레임, t=5.000초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/frames/whole_body/00150.png)

![스트랩 힘과 경로 표시를 끈 실제 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/hands.mp4)

![스트랩 힘과 경로 표시를 끈 실제 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/whole_body.mp4)

분석은 fresh source 검사 14/1188 clear, native 1초기화·1200 physics step, 각 151프레임 영상 2개를 확인했다. 이 source 검사 통과는 PhysX cooked 형상의 동적 침투가 없다는 증명이 아니다. 임시 초기·후기 기준은 자연스러움, 완전한 접촉, checkpoint 호환성 또는 실제 연주 성공을 인증하지 않는다. 이번에 새 actor 추론·학습은 없었다.

기준 strap-on 측정은 [앞선 초기 middle3 정렬 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/README.md:1)에 있다. 이번 run의 [초기 상태](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/initial_values.json:1), [no-strap mode 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/no_strap_mode.json:1), [분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/analysis.json:1), [native 영상 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/videos.json:1)을 보존했다. 영상 모음은 기존 140개를 보존한 뒤 2개를 추가해 총 142개다.
