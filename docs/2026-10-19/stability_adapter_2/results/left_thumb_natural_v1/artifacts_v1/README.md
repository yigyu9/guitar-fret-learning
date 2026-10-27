# 왼엄지 자연 완화 — native 결과와 캡처

Isaac Gym native 실행 `native_v1`은 물리 관측 5.0초(1200 physics step, 300 control step)를 완료했습니다. 영상은 세 카메라 모두 30 fps, 151프레임, 1280×720이며 인코딩 길이는 5.033333초입니다. PNG와 MP4는 캡처 메타데이터 및 report SHA를 확인한 바이트 그대로의 사본입니다. 재렌더·자르기·표시용 편집·재인코딩은 하지 않았습니다.

사용자 요청에 맞춰 palm과 나머지 손가락의 초기 배치는 보존하고 왼엄지 관절 초기값만 바꾼 조건입니다. 감사 결과 other76 joint 초기각과 guitar 초기 raw state, PD 속성은 정확히 일치했습니다. non-thumb 초기 body pose의 최대 위치 차는 0 m, 최대 회전 차는 1.3947×10⁻¹⁶ rad입니다.

## 엄지 관절 초기값

| DOF | 기준 자세 (deg) | 새 초기값 (deg) |
|---|---:|---:|
| `LH:thumb1_x` | 0.04959 | 30.30269 |
| `LH:thumb1_y` | -76.19976 | -75.00000 |
| `LH:thumb1_z` | 0.00006 | 34.07980 |
| `LH:thumb2` | 84.82585 | 65.00000 |
| `LH:thumb3` | 81.27211 | 0.46734 |

엄지 5개 목표값은 300개 control step 동안 유지됐습니다. 초기 조건 비교용 값이며 자연스러운 해부학적 기준을 인증하지 않습니다. 실제 실행에서 엄지-기타 접촉 기록은 0입니다.

## 이미지

기준 실행은 EW pick-feedback의 native front hand 카메라 0초 캡처입니다. 오른쪽은 이번 실행의 native front hand 0초 캡처입니다. 양쪽 이미지 모두 원본 native 프레임입니다.

![기준 실행의 왼손 전면 0초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/artifacts_v1/baseline_elbow_wrist_pick_feedback_t00_hands.png)

![새 실행의 왼손 전면 0초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/artifacts_v1/current_t00_hands.png)

새 실행 전체 자세 0초:

![새 실행 전신 0초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/artifacts_v1/current_t00_whole_body.png)

새 실행 전체 자세 5초:

![새 실행 전신 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/artifacts_v1/current_t05_whole_body.png)

엄지 뒤쪽 카메라의 native 시계열은 아래 프레임이며, 각 프레임은 해당 카메라의 원본 해상도와 픽셀을 유지합니다.

### 엄지 뒤쪽 카메라 — 0초

![새 실행 엄지 뒤쪽 0초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/artifacts_v1/current_t00_thumb_back.png)

### 엄지 뒤쪽 카메라 — 2초

![새 실행 엄지 뒤쪽 2초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/artifacts_v1/current_t02_thumb_back.png)

### 엄지 뒤쪽 카메라 — 5초

![새 실행 엄지 뒤쪽 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/artifacts_v1/current_t05_thumb_back.png)

## 실행 결과와 해석 경계

보고된 분석은 down 6→1 및 up 1→6 순서를 모두 통과했습니다. 왼손 접촉 0 step, 오른손/손·손목 접촉 0 step, 엄지-기타 접촉 0건입니다. 기타 최대 bounding-box 중심 이동은 11.4028705 mm, 최대 SO(3) 변화는 3.8715877°이며 마지막 값은 각각 9.853485 mm와 3.304837°입니다. 기타는 free였고 strap은 OFF, root/lower body는 고정, self-collision은 ON이었습니다. Human PD/gravity와 current-G upper-point 제어는 활성 상태였습니다. Guitar에 힘을 가하거나 붙이지 않았고, runtime pose write·checkpoint·training은 없었습니다.

엄지 뒷면 감사의 선택 facet-to-back-plane gap은 초기 39.424 mm, 최종 62.576 mm입니다. 이는 선택된 collision facet과 back-plane 기준의 기하값이며 실제 접촉거리나 해부학적 pad 인증이 아닙니다. 명목 back 24 mm 라벨도 실측 gap 24 mm를 뜻하지 않습니다. Aug 19 참고자료 시계열 ABI/해부학 정체성은 인증되지 않았고 source V1 모델 끝 후보는 실행하지 않았습니다.

## 영상

### 전신

![왼엄지 완화 native 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_thumb_natural_v1/whole_body.mp4)

### 손 전면

![왼엄지 완화 native 손 전면 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_thumb_natural_v1/hands.mp4)

### 엄지 뒤쪽

![왼엄지 완화 native 엄지 뒤쪽 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_thumb_natural_v1/thumb_back.mp4)

## 추적 자료

- 분석 수치: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/strike_analysis_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/strike_analysis_v1.json)
- 엄지·비엄지 자세 감사: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/thumb_audit_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/thumb_audit_v1.json)
- 사전 입력 SHA pin: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/artifacts_v1/preflight_pin_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/artifacts_v1/preflight_pin_v1.json)
- 입력 전후 SHA, 복사 결과와 ffprobe: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/artifacts_v1/provenance_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/artifacts_v1/provenance_v1.json)
- 영상 색인: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_thumb_natural_v1/INDEX_v1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_thumb_natural_v1/INDEX_v1.md)
