# 왼목 세 면 초기 준비 자세 — native 결과

선택된 삼면 방향에 맞춘 초기 준비 자세를 native Isaac Gym 장면으로 기록했습니다. 기타 방향은 G 기준 하부가 +X, 뒤면이 −Z, 현 앞면이 +Z입니다. 이는 올바른 면과 근처에 손을 배치한 초기 준비 자세입니다. 5초 동안 세 면의 동시 조건과 접촉 기반 grip이 유지된 것은 아닙니다.

## 실행 이력과 범위

Source V1 설정은 실패해 후보 0개였습니다. V2/V3/V4는 각 2개씩, 총 6개가 기각됐고 V5 station20 mm 후보 1개를 수락했습니다. 승인된 native 실행은 `native_off_v1` 한 번뿐이며 5.0초(1200 physics step, 300 control step) 완료했습니다.

기타는 free, strap OFF, root와 하체 고정, self-collision ON이었습니다. 오른쪽 EW6 finite pick 제어는 유지됐으며 checkpoints와 training은 0입니다. Virtual pick detector는 down 6→1과 up 1→6을 통과했습니다. 이는 virtual-pick release 판정이며 학습된 fret 또는 곡 연주의 성공을 뜻하지 않습니다.

## 선택 facet 면 간격

아래 값은 실제 움직이는 기타 좌표계에서 선택된 active collision facet plane과 지정 back/front 기준 사이의 값입니다. 해부학적 pad 위치, 최소 유한 표면 거리, 압력 또는 접촉 인증이 아닙니다.

| 면/부위 | 초기 (mm) | 5초 (mm) | 실제 접촉 steps |
|---|---:|---:|---:|
| palm | 12.833 | 9.192 | 0 |
| thumb | 15.464 | 17.993 | 0 |
| index | 4.835 | 2.517 | 109 |
| middle | 14.188 | 11.180 | 0 |
| ring | 13.763 | 11.341 | 0 |
| pinky | 9.099 | 6.506 | 1183 |

초기에는 여섯 지점 모두 strict three-face gate를 통과했습니다. 감사 시계열에서 모든 여섯 지점 동시 통과 비율은 전체의 0.666%였고, 2초 이후에는 0%였습니다. 즉 후기 엄지 gap은 약 18 mm까지 커졌으며 지속적인 여섯 지점 접촉이나 고정 grip 결과가 아닙니다. 실제 접촉 기록은 index 109 steps, pinky 1183 steps, palm/thumb/middle/ring 각 0입니다.

실행 중 기타 최대 bounding-box 중심 이동은 10.0213 mm, 최대 SO(3) 변화는 3.31719°였습니다. 왼손 접촉 detector 총 1186 steps에는 위의 index/pinky 접촉이 포함됩니다. 오른손·손목 접촉은 0입니다.

## Native 초기 프레임

### Whole-body — 초기 0초

![전신 native 초기 프레임](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/artifacts_v1/native_off_t00_whole_body.png)

### Hands — 초기 0초

![손 native 초기 프레임](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/artifacts_v1/native_off_t00_hands.png)

### Thumb-back — 초기 0초

![엄지 뒤쪽 native 초기 프레임](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/artifacts_v1/native_off_t00_thumb_back.png)

### Thumb-back — 2초

![엄지 뒤쪽 native 2초 프레임](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/artifacts_v1/native_off_t02_thumb_back.png)

### Thumb-back — 5초

![엄지 뒤쪽 native 5초 프레임](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/artifacts_v1/native_off_t05_thumb_back.png)

PNG는 capture 메타데이터의 native 00000/00060/00150 프레임을 선택해 원본 바이트 그대로 복사했습니다. 이미지 재렌더, 합성, 색칠, 자르기 또는 주석은 없습니다.

## Native 영상

### 전신

![전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_three_face_v1/native_off_v1_whole_body.mp4)

### 손

![손 native 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_three_face_v1/native_off_v1_hands.mp4)

### 엄지 뒤쪽

![엄지 뒤쪽 native 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_three_face_v1/native_off_v1_thumb_back.mp4)

## 검증과 링크

- 삼면 선택 분석: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/face_audit_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/face_audit_v1.json)
- 타현 release 분석: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/strike_analysis_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/strike_analysis_v1.json)
- 명령 감사: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/command_audit_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/command_audit_v1.json)
- 실행 전 입력 pin: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/artifacts_v1/preflight_pin_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/artifacts_v1/preflight_pin_v1.json)
- 입력 전후 SHA 및 output SHA/ffprobe: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/artifacts_v1/provenance_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/artifacts_v1/provenance_v1.json)
- 이 담당자가 만든 파일 목록: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/artifacts_v1/FILES_v1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/artifacts_v1/FILES_v1.md)
- 영상 색인: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_three_face_v1/INDEX.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_three_face_v1/INDEX.md)
