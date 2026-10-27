# 왼손을 기타에서 뗀 초기 자세: 중단된 native 관측

선택 native run은 `native_back100_static`이다. 왼손을 t=0부터 기타에서 떨어뜨린 초기화 결과이며, 잡고 있다 놓는 연속 release 전이를 시험한 것이 아니다. 왼손 추종·가상력·task 요청은 실행 구간에서 0이었지만 중력/PD와 오른쪽 몸통의 현재 기타 G점 제어는 유지됐다. 스트랩은 없고 기타는 자유 상태였다. 이 결과를 수동 평형이나 왼손 없이 지속 지지 성공으로 해석하지 않는다.

## 실제 native 시작과 종료 프레임

![시작 0.000초와 실제 마지막 0.933초의 native 전신 프레임](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/artifacts_v1/whole_body_start_end_v2.png)

![시작 0.000초와 실제 마지막 0.933초의 native 손·기타 근접 프레임](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/artifacts_v1/hands_start_end_v2.png)

각 패널의 장면은 원본 native PNG 픽셀 크기 1280×720을 유지한다. 제목과 시간 표지만 원본 프레임 바깥에 추가했다. 마지막 프레임은 physics step 224, 0.933333초이며 그 뒤 시점의 프레임이나 영상을 보간·연장하지 않았다.

## 결과와 범위

- 실행은 224 physics step / 56 control step에서 guitar safety displacement로 중단됐다. 완료된 5초 결과가 아니다.
- 왼손 기타 접촉 presence는 0/224 step, 왼손 추종 활성 0 step, 왼손 가상력·task 요청은 정확히 0이었다.
- 종료 시 기타 바디 중심 이동은 77.452 mm, 초기 대비 SO(3) 회전은 35.625°였다. 따라서 이 짧은 구간은 기타 자세 유지 성공이 아니다.
- 지속 release transition, 수동 안정성, 연주 성공, 접촉력 기여는 검증하지 않았다. 접촉 관측 횟수를 힘으로 해석하지 않는다.

## native 영상 사본과 검증 자료

[전신·손 native 영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_hand_off_current_v1/INDEX.md)에서 두 사본을 볼 수 있다. 사본은 원본과 byte-exact이며, 각 1280×720, 30fps, 29 frames, 파일 재생시간 0.966667초다. 물리 시뮬레이션 경과 0.933333초와 30fps 영상 길이는 별도 값이다.

[입력·생성 결과·복사 영상 SHA 및 ffprobe 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/artifacts_v1/provenance_v2.json) · [실행 전 디스크 pin](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/artifacts_v1/preflight_pin_v2.json) · [생성기](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/artifacts_v1/build_artifacts_v2.py)

레이아웃이 겹친 초기 표시본은 이력으로 보존했고, 이 문서에서는 수정된 V2 이미지와 V2 영상 사본을 사용한다. 물리 실행이나 영상 재인코딩은 추가하지 않았다.
