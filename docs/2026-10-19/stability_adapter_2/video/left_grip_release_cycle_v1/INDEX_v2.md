# 왼손 그립·해제 사이클 영상

V2를 권장 반복으로 제시한다. V1과 V2는 같은 초기 상태였고 반복 비교 기록상 전체 기타 root trace와 quaternion 성분이 일치했다. V2는 접촉 분류 범위를 수정한 분석을 사용한다. 두 실행 모두 16초 시뮬레이션을 정상 완료했으며 각 native 카메라 영상은 30 fps, 481프레임, 인코딩 길이 16.033초다.

영상은 native Isaac Gym 카메라 장면에 실제 줄 끝점 사이 6개 선분을 깊이 검사해 표시한 캡처다. 선분은 화면용 표시로 물리 형상이나 실제 줄의 굵기·진동을 나타내지 않는다. 저장 영상은 캡처 원본에서 바이트 변경 없이 복사했다.

## V2 · 권장 반복

### 전신

![V2 전신 native 카메라와 비물리적 줄 표시, 전체 16초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/native_v2/whole_body.mp4)

### 손

![V2 손 native 카메라와 비물리적 줄 표시, 전체 16초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/native_v2/hands.mp4)

### 엄지 뒤쪽 시점

![V2 엄지 뒤쪽 native 카메라, 전체 16초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/native_v2/thumb_back.mp4)

## V1 · 최초 실행

V1은 캡처 그대로 보존한다. 실행 전 config hash 누락과 raw LHip 접촉 분류/증거 범위 문제는 V1의 과거 한계이며, V2 수정은 V1을 소급 인증하지 않는다.

### 전신

![V1 전신 native 카메라와 비물리적 줄 표시, 전체 16초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/native_v1/whole_body.mp4)

### 손

![V1 손 native 카메라와 비물리적 줄 표시, 전체 16초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/native_v1/hands.mp4)

### 엄지 뒤쪽 시점

![V1 엄지 뒤쪽 native 카메라, 전체 16초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/native_v1/thumb_back.mp4)

## 관측된 단계

| 시뮬레이션 시각 | 실제 관측 단계 |
|---|---|
| 0–2초 | 준비 |
| 2–3초 | A를 향해 닫기 |
| 3–4.5초 | A 유지, 엄지와 다른 손가락의 양의 접촉 lambda가 360/360 표본에서 관측 |
| 4.5–6초 | A 해제 전이 |
| 6–7초 | A에서 열린 상태, 왼팔·왼손–기타 접촉 없음 240/240 표본 |
| 7–8.5초 | 왼팔·왼손을 연 채 B로 이동, 접촉 없음 360/360 표본 |
| 8.5–10초 | B를 향해 닫기 |
| 10–11.5초 | B 유지, 엄지와 다른 손가락의 양의 접촉 lambda가 360/360 표본에서 관측 |
| 11.5–13초 | B 해제 전이 |
| 13–16초 | B에서 열린 상태, 왼팔·왼손–기타 접촉 없음 720/720 표본 |

측정된 A–B 평균 손목 위치 차이를 현재 G 넥 축에 투영하면 36.727 mm로, 요청한 40 mm보다 짧다. 44.168 mm는 손목의 같은 축 투영 시계열에서 최댓값과 최솟값의 차이다. 2초 준비 종료 상태 기준 기타 BB body centre 최대 편차/SO(3) 회전은 22.264 mm/9.796°였고, 준비를 포함한 초기 상태 기준 값은 41.255 mm/10.455°였다. 휴머노이드 root와 하체는 고정되어 있고, 오른쪽 위팔과 오른쪽 허벅지(R_Hip)의 지지 접촉이 계속 관측됐다. 따라서 이 결과는 무지지/수동 평형이나 force closure를 입증하지 않는다. 상세 수치와 제한은 [한국어 증거 요약](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/README_v2.md), 해시 기록은 [V2 복사 manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/copy_manifest_v2.json) 및 [문서 보완 전 provenance](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/documentation_before_v3.json)에 있다.
