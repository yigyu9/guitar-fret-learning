# 오른쪽 몸통 접근 거리 비교

이 문서는 기존 오른 허벅지·waist 초기 배치에 기타를 몸통 쪽으로 3, 6, 10, 20, 30 mm 이동한 실제 native 비교를 정리한다. `inset`은 humanoid의 고정된 수평 전방축 반대 방향, 즉 몸쪽으로 이동한 거리이며 world-Y 단독 이동이 아니다. 20/30 mm 조건은 완료 실행이 아니다. 이 접근만으로 후기 Thorax 접촉은 회복되지 않았고, 이전 waist 기준 자세를 유지한다. 새 elbow wave, 학습 또는 checkpoint 연결은 없다.

## 초기 배치 비교

![여섯 조건의 실제 초기 전신 프레임. 카메라 행렬 일치 확인 후 나란히 배치](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/artifacts_v1/initial_six_whole_body.png)

![같은 픽셀 좌표로 자른 오른쪽 기타·몸통 주변 프레임](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/artifacts_v1/initial_six_right_blocks_crop.png)

각 패널의 각도 표기는 baseline `q_ref`와 해당 후보의 초기 81개 scalar 관절각을 비교한 최대 절대 차이다. 이는 여러 관절의 초기 보정 중 가장 큰 단일 관절 차이이며 전체 자세의 회전각을 뜻하지 않는다. 여섯 native capture의 whole-body view/projection 행렬은 모두 정확히 일치했다. 프레임은 실제 Isaac Gym native 캡처다.

## 비교용 조건: inset 6 mm

![6 mm 조건 실제 전신 native frame 0, 60, 150 (0, 2, 5초)](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/artifacts_v1/inset6_whole_body_timeline.png)

![6 mm 조건 실제 hands native frame 0, 60, 150 (0, 2, 5초)](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/artifacts_v1/inset6_hands_timeline.png)

6 mm는 비교를 위한 물리 실행이며 새 기본값으로 채택한 조건이 아니다. 물리 실행은 5.0초(1200 physics steps) 완료됐다. actor-root 이동과 기타 body bounding-box 중심 이동은 다른 기준이다. 이 완료 조건의 root 최대 이동은 승인 brief에 실리지 않아 여기서는 제시하지 않는다. 최대 body bounding-box 중심 이동은 12.180 mm였다. 종료 중심 이동은 11.879 mm, 종료 전체 SO(3) 회전은 5.880°였다. 2→5초 동안 중심은 추가 0.824 mm, 회전은 0.273° 변했다.

끝 120 physics samples에서 Thorax 접촉은 0/120, 상완 접촉은 120/120이었다. 전체 1200 samples에서 waist-region/R_Hip 접촉은 1198/1200, 왼팔·손과 기타 접촉은 1189/1200이었다. 이는 접촉 관측 횟수이지 힘(N)이나 힘 분담이 아니다. source 형상 검사는 PhysX cooked 간격을 보증하지 않으며, 왼손 손가락 접촉이 남아 있어 손을 떼고 유지하는 지지 증명도 아니다. 접근만으로 두 블록/Thorax 지지가 회복됐다고 볼 수 없다.

## 완료·부분 중단 결과

| 조건 | 상태·물리 경과 | actor-root 최대 이동 | body bounding-box 중심 최대 이동 | 최대 회전 | 끝 0.5초 Thorax 접촉 | 끝 0.5초 상완 접촉 |
|---|---:|---:|---:|---:|---:|---:|
| 이전 waist 기준 | 5.0초 완료 | brief 미수록 | 11.831 mm | 6.095° | 0/120 | 120/120 |
| inset 3 mm | 5.0초 완료 | 미기재 | 12.621 mm | 6.718° | 0/120 | 120/120 |
| inset 6 mm | 5.0초 완료 | 미기재 | 12.180 mm | 6.671° | 0/120 | 120/120 |
| inset 10 mm | 5.0초 완료 | 미기재 | 17.550 mm | 8.231° | 0/120 | 120/120 |
| inset 20 mm | 1.116667초에서 보호 중단, 268 physics / 67 control steps | 200.071 mm | 75.384 mm | 30.638° | 해당 없음 | 해당 없음 |
| inset 30 mm | 0.850000초에서 보호 중단, 204 physics / 51 control steps | 208.281 mm | 101.805 mm | 34.355° | 해당 없음 | 해당 없음 |

20/30 mm는 기타 actor-root 이동이 200 mm 안전 한계를 넘어 중단됐다. 두 조건 모두 회전 35° 한계는 넘지 않았다. 이들은 5초 결과가 아니며 종료 자세/접촉을 완료 실행과 직접 비교하지 않는다. partial 접촉 요약은 전체 body contact 분류이며 근위 상완 범위 인증이 아니다. 20 mm에서 중단 전 전체 Thorax/상완/R_Hip/왼팔-손 contact presence는 각각 30/102/266/112 samples, 30 mm는 0/14/202/122 samples였다. Raw lambda 양성 표본도 물리적 힘 N을 뜻하지 않는다.

부분 실행 영상의 재생 길이와 물리 경과도 다르다. 20 mm 영상은 35 frame·30 fps·1.166667초, 물리는 1.116667초다. 30 mm 영상은 27 frame·30 fps·0.900000초, 물리는 0.850000초다. 완료 영상은 각각 151 frame·30 fps·5.033333초 재생이며 물리 구간은 5.0초다.

## 원본 영상

![완료된 inset 6 mm 실제 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_body_approach_v1/native_inset6_static/whole_body.mp4)

![보호 중단된 inset 20 mm 실제 전신 영상 — 부분 실행](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_body_approach_v1/native_inset20_static/whole_body.mp4)

새 실행 다섯 조건의 전신·손 영상 10개만 복사했다. 기준 조건은 초기 이미지 비교에만 사용했으며 영상 복사에는 포함하지 않았다. 원본–사본 해시와 ffprobe 메타데이터는 [영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_body_approach_v1/INDEX_V1.md:1) 및 [manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_body_approach_v1/manifest_v1.json:1)에서 확인할 수 있다. 그림·영상 복사·문서 생성 단계에서 물리/학습 실행은 없었다. 직접 읽은 입력과 출력의 SHA-256은 [provenance](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/artifacts_v1/provenance_v1.json:1)에 기록했다.
