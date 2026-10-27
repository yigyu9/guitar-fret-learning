# OM 초기 겨드랑이 자세 비교

세 native 평가의 실제 Isaac Gym 전신·손 카메라 이미지와 MP4를 보관한다. 영상의 여섯 현은 프레임별 양 끝점을 투영한 시각 overlay이며 물리 현이 아니다. 그래픽 재실행이나 물리 재실행 없이 완료된 source 영상·캡처만 정리했다.

## 0·2·5초 native 전신 비교

![전신 native 프레임 비교: 행은 0·2·5초, 열은 세 조건](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/artifacts_v1/whole_body_conditions_0_2_5s.png)

![세 조건의 초기 여섯 현 overlay](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/artifacts_v1/initial_strings_conditions.png)

![hold ON 초기 겨드랑이 측면 native camera](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/artifacts_v1/hold_on_initial_axilla_side_captioned.png)

각 조건의 원본 전신·손 영상은 아래에 링크하고, 파일별 원본/복사본 SHA-256, byte 수와 ffprobe 정보는 [manifest](/home/ajou/yigyu/3/docs/2026-10-12/video/om_axilla_initial_pose_v1/manifest_v1.json)에 있다. 영상은 5초 평가로부터 생성된 151-frame MP4이며, 원본 bytes 그대로 복사했다.

| 조건 | 전신 영상 | 손 영상 | 초기→5초 actor-root 위치 변화 | 초기→5초 회전 변화 | 최대 회전 변화 |
|---|---|---|---:|---:|---:|
| clear_reference | [MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_axilla_initial_pose_v1/clear_reference_whole_body.mp4) | [MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_axilla_initial_pose_v1/clear_reference_hands.mp4) | 113.5007455 mm | 4.3950566° | 18.98256° |
| lean18_back30, hold OFF | [MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_axilla_initial_pose_v1/lean18_back30_whole_body.mp4) | [MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_axilla_initial_pose_v1/lean18_back30_hands.mp4) | 114.2593371 mm | 6.5122263° | 9.75153° |
| lean18_back30_hold_pi, hold ON | [MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_axilla_initial_pose_v1/lean18_back30_hold_pi_whole_body.mp4) | [MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_axilla_initial_pose_v1/lean18_back30_hold_pi_hands.mp4) | 65.7176363 mm | 21.4161770° | 21.43427° |

세 실행 모두 R_Shoulder contact query가 300회 중 positive lambda 0회였고, Chest contact query는 순서대로 0, 1, 1회였다. 이 query 횟수는 샘플 결과이며 지속적인 겨드랑이 지지나 연속 비접촉/접촉을 증명하지 않는다. 어느 조건도 안정 성공이나 왼손 자유 연주 성공으로 판정하지 않는다.

hold ON은 PI와 팔 target rate 1→3을 함께 바꿨으므로 결과를 PI 하나의 효과로 분리할 수 없다. 기타를 고정하거나 강제 부착하지 않았다. strap 경로는 켜져 있고 rest length는 1.10184697 m다. 기록된 commanded strap tension 0 N은 계산/명령값이며 실제 측정 힘이 아니다. 본 자세는 adopted stance가 아니다.

## 처리 및 재현

6개 MP4는 세 완료 실행의 원본 `media/whole_body.mp4`와 `media/hands.mp4`를 exact copy했다. 각 복사본의 SHA는 원본과 일치한다. 캡처 선은 밝은 회색 2 px 화면 표시이며 native depth 2 mm 처리에서 가려진 선은 숨겨진다. 선은 물리 현의 굵기·진동·장력·접촉을 나타내지 않는다.

[producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/artifacts_v1/make_archive_v1.py), [생성 입력·출력 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/artifacts_v1/provenance_v1.json), [문서 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/artifacts_v1/docs_provenance_v1.json)를 둔다. 이 정리 작업은 source/native 원본이나 root 문서를 변경하지 않았다.
