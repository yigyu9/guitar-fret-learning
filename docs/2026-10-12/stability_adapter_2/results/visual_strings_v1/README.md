# 물리 없는 기타 6현 영상 표시

결과 영상을 쉽게 확인하도록 기존 6개 현의 실제 native 양 끝점을 밝은 회색 선으로 표시했다. 화면 표시만 추가했으며 기존 기타 자산·현 목표·충돌 형상·질량·제어는 유지했다. 기타가 이동하거나 회전하면 현재 끝점에 따라 선도 움직인다. 손 등에 가려진 부분은 native 카메라 깊이 정보로 숨긴다.

![줄이 보이는 실제 Isaac Gym 초기 화면과 현 오버레이](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/native_v1/media/initial_strings.png)

2px 선은 영상에서 식별하도록 정한 표시 굵기다. 실제 현의 굵기·진동을 재현하지 않는다. 2mm 깊이 여유를 사용하는 표본 가림 처리이며 완벽한 픽셀 단위 가림 인증은 아니다. 위 그림과 영상은 실제 Isaac Gym 렌더 위에 선을 합성한 결과다. 카메라 원본과 스트랩만 표시한 중간 프레임은 각각 따로 보존했다. 3D 현 geometry나 새로운 현 접촉을 추가하지 않았다.

## 실제 검증

같은 OM 초기 자세와 물리 조건으로 5초/1,200 physics step/300 control을 실행했다. 전신·손 근접 각각 151frame/30fps/5.033초 영상이다. 원본·스트랩·줄 포함 PNG는 총906개를 보존·SHA검사했다. 초기값·전체 관절/기타 궤적·접촉 기록·native 물성·shape·캐시는 직전 OM 실행과 동일했다. 모든 녹화에서 읽기 전후 시뮬레이터 상태가 동일했고, 실제 6현 끝점과 기타 root pose 기반 예상 끝점의 최대 차이는 약0.000202mm였다.

이번 실행도 처음→5초 기타 위치113.200mm/회전4.858° 변화 후 정착했다. 줄 표시 기능을 확인한 시험이며 초기 자세 유지나 연주 성공을 의미하지 않는다.

![6현·실제 스트랩 경로를 함께 표시한 손 근접 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/native_v1/media/hands.mp4)

[전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/native_v1/media/whole_body.mp4). 영상 모음은 `/home/ajou/yigyu/3/docs/2026-10-12/video/visual_strings_v1/`에 보관한다.

## 구현과 이후 사용

[StringTrialRecording](/home/ajou/yigyu/3/stability_adapter_2/string_trial_recording_v1.py:30)은 기존 StrapTrialRecording을 보존해 호출하는 새 녹화 wrapper다. [선택 실행 진입점](/home/ajou/yigyu/3/stability_adapter_2/run_visual_strings_trial_v1.py:8)은 기존 OM runner에서 녹화 종류만 선택한다. 기존 runner와 과거 영상은 변경하지 않았다. 이후 새 실험에서 이 wrapper를 선택하면 같은 줄 표시를 적용할 수 있다. 모든 기존 영상·runner에 자동 적용된 것은 아니다.

[계획](/home/ajou/yigyu/3/stability_adapter_2/VISUAL_STRINGS_PLAN_V1.md:1) · [정량 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/verification_v1.json:1)
