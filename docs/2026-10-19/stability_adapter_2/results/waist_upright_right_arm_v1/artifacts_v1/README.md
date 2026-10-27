# 허리 굽힘 완화·오른팔 접근: native 이미지와 영상

비교 기준은 [오른 허벅지 waist 배치의 정지 run](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/native_static_v2/report.json)이다. 이번 4° 완화 정지 run은 선택 결과이며, 2° 정지 run은 함께 확인할 비교 조건이다. 모든 프레임은 저장된 실제 Isaac Gym 캡처에서 가져왔다. 이번 산출물 준비 중 새 물리 실행은 없었다.

## 초기 전신과 확대 비교

![기준 native_static_v2와 4도 완화 native_relief4_static의 t=0 전신 프레임. 실제 캡처의 view/projection 행렬 일치](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/artifacts_v1/initial_whole_comparison_v1.png)

![동일 전신 카메라의 원본 프레임에서 몸통·팔꿈치·기타·허리 주변을 같은 픽셀 범위로 자른 확대 비교. 양쪽 모두 t=0](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/artifacts_v1/initial_closeup_comparison_v1.png)

확대 비교는 각 run의 별도 손 카메라 영상이 아니라, 두 초기 전신 프레임에서 동일한 `(x=365..875, y=190..590)` 영역을 잘라 만든 것이다. 저장된 카메라 메타데이터에서 전신 view/projection 행렬은 일치한다. 손 카메라의 view 행렬은 두 run에서 일치하지 않아 카메라가 같다고 표시하지 않았다.

초기 Chest local-Z의 world 전방 기울기 proxy는 기준 65.412312°, 4° 후보 61.412311°다. 이 값은 임상적 척추각이나 body9 scalar 합이 아니다. 4° 후보의 실제 초기 오른 팔꿈치 관절 중심에서 기타 bounding-box 중심까지 거리는 기준 0.400908m에서 0.397789m로 줄었다. 거리 감소는 3.119324mm이며, 탐색 요청 8mm를 실제 이동량으로 표현하지 않는다.

## 4° 후보 팔꿈치 목표 주기: native 0·2·5초 프레임

![4도 후보 native elbow5 전신 원프레임 0초, 2초, 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/artifacts_v1/elbow5_whole_body_0_2_5_v1.png)

![4도 후보 native elbow5 손·기타 카메라 원프레임 0초, 2초, 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/artifacts_v1/elbow5_hands_0_2_5_v1.png)

장면은 원본 `frames/`의 frame 0, 60, 150이며 30fps에서 각각 0, 2, 5초다. 두 갤러리의 패널은 캡처 원프레임을 축소 배치했고, 캡션만 프레임 바깥에 추가했다. 5초 장면은 팔꿈치 목표 주기(2.5–4.5초) 뒤의 종료 장면이다.

## 실제 native 영상

아래 여섯 MP4는 [영상 폴더](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/waist_upright_right_arm_v1/INDEX.md)에 정리했다. 각 run의 전신·손 영상을 원본 그대로 복사했다. 모든 영상은 30fps, 151프레임, 5.033333초 재생 길이이며 물리 경과시간은 5.000초다.

![4도 완화 정지 조건의 실제 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/waist_upright_right_arm_v1/native_relief4_static_whole_body.mp4)

![4도 완화 정지 조건의 실제 손·기타 확대 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/waist_upright_right_arm_v1/native_relief4_static_hands.mp4)

![2도 완화 정지 조건의 실제 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/waist_upright_right_arm_v1/native_relief2_static_whole_body.mp4)

![2도 완화 정지 조건의 실제 손·기타 확대 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/waist_upright_right_arm_v1/native_relief2_static_hands.mp4)

![4도 완화 및 팔꿈치 목표 ±5도 조건의 실제 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/waist_upright_right_arm_v1/native_relief4_elbow5_whole_body.mp4)

![4도 완화 및 팔꿈치 목표 ±5도 조건의 실제 손·기타 확대 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/waist_upright_right_arm_v1/native_relief4_elbow5_hands.mp4)

## 결과와 해석 범위

세 run은 각각 1200 physics step, 300 control tick, 물리 5초를 완료했다. 4° 정지 조건에서 기타 bounding-box 중심 최대 이동은 14.545447mm, 최대 SO(3) 회전은 8.012684°였다. 2° 정지 조건은 각각 17.004627mm와 8.473343°다. 4° 정지와 elbow 목표 ±5° 조건을 같은 시각으로 비교한 추가 최대 기타 변화는 0.180525mm와 0.083762°이며, 실제 elbow scalar 범위는 2.5–5초에 10.078053°다.

4° 조건 후기 마지막 120 step의 Thorax 접촉은 0/120이고, 근위 상완과 waist 접촉은 각각 120/120이다. 따라서 이 결과를 두 블록의 지속 지지, 왼손 없는 수동 안정, 반복 강건성 또는 연주 성공으로 해석하지 않는다. 허벅지·상완 접촉과 왼손 손가락 접촉이 남는다. raw lambda는 힘 단위 N이 아니다.

## 원자료와 provenance

- [확정 산출물 brief](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/artifact_brief_v1.md)
- [명령·접촉 분석 JSON](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/analysis_final_v1/analysis.json)
- [세 native 실행 독립 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/review_native_v1.md)
- [영상 SHA·크기·ffprobe 및 원본 대조 manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/waist_upright_right_arm_v1/manifest_v1.json)
- [직접 입력 및 producer SHA provenance](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/artifacts_v1/provenance_v1.json)
- [이미지·provenance 생성 스크립트](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/artifacts_v1/build_artifacts_v1.py)
