# 현재 목 지지 자세 — 검증된 baseline archive

이 폴더는 현재 받아들인 `left_neck_three_face_v1/native_off_v1` baseline과 해당 viewer 설정의 바이트 보존 사본입니다. 재현 가능한 독립 모델 번들이 아닙니다. 보관한 config와 candidate에는 원래 절대경로가 그대로 있으며, Isaac Gym model·mesh 등 공용 자산은 기존 위치를 참조합니다. 원본 파일은 이동하거나 수정하지 않았습니다. 새 후보나 진행 중인 실험도 이 archive에 포함하지 않았습니다.

## 보관 범위

보관된 `initial_values.json`에는 81개 joint 각도와 전체 native body 상태가 있습니다. 함께 둔 `native_properties.json`에는 초기 PD/물성 정보가 있고, accepted source `config.json`·`candidate.json`, native report·초기 검증·삼면 측정 JSON, face/strike/command 감사 JSON 및 V2 viewer `config.json`·`initial.json`·실행 안내를 원본 바이트 그대로 복사했습니다.

실제 native run은 5.0초(1200 physics step, 300 control step)입니다. viewer의 GUI 동작 확인과 구별하기 위해 보관 영상은 native 카메라 기록으로 표기합니다.

## 초기 native 카메라 프레임

이 이미지는 원본 native run의 실제 0초 캡처입니다. 데스크톱 viewer 화면 캡처가 아니며 편집하지 않았습니다.

![Native 전신 0초](/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/archive/native_off_v1/media/frames/whole_body/00000.png)

![Native 손 0초]({AR}/native_off_v1/media/frames/hands/00000.png)

![Native 엄지 뒤 0초]({AR}/native_off_v1/media/frames/thumb_back/00000.png)

## Native 5초 영상

### 전신

![native_off_v1 전신](/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/archive/native_off_v1/media/whole_body.mp4)

### 손

![native_off_v1 손](/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/archive/native_off_v1/media/hands.mp4)

### 엄지 뒤

![native_off_v1 엄지 뒤](/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/archive/native_off_v1/media/thumb_back.mp4)

## baseline 상태와 측정 경계

초기 배치는 손바닥을 넥 아래, 엄지를 뒤, 네 손가락을 줄 면 가까이에 둡니다. 기타는 자유 상태, strap OFF, root·하체 고정, self-collision ON이며 오른쪽 EW6 finite-control이 유지됩니다. virtual-pick detector는 6→1 down과 1→6 up 한 번씩 통과했습니다. 이는 학습 checkpoint 기반 연주 성공을 뜻하지 않으며 checkpoint·training은 0입니다.

검증된 실행에서 기타 최대 body-center 이동은 10.02 mm, 최대 SO(3) 변화는 3.317°입니다. 5초 종료 시 palm/thumb 접촉은 0입니다. 선택 facet 측정에서 엄지 뒤 gap은 약 15.46 mm에서 17.99 mm로 증가했고, 2초 이후 six-face strict gate의 동시 통과는 0입니다. 따라서 이 baseline은 초기 면 방향과 손 위치를 보존하지만 지속적인 full-contact grip은 아닙니다. 선택 facet gap은 해부학적 pad 거리나 접촉 인증값이 아닙니다.

## Viewer 실행

현재 viewer 사용법과 조작키는 [/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/README.md:1](/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/README.md:1)에 있습니다. 그래픽 데스크톱의 터미널에서 아래 실행 파일을 사용합니다.

`bash /home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/open_v2.sh`

실제 DISPLAY가 없는 환경에서는 데스크톱 viewer 조작 통합을 검증할 수 없습니다. 이 archive의 native 이미지와 영상은 viewer screenshot 또는 GUI 검증 기록이 아닙니다.

## 보존 기록

- 보관 파일 색인: [/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/artifacts_v1/FILES_v1.md](/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/artifacts_v1/FILES_v1.md:1)
- 사전 SHA pin: [/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/artifacts_v1/preflight_pin_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/artifacts_v1/preflight_pin_v1.json:1)
- 원본/사본 SHA 및 영상 probe: [/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/artifacts_v1/provenance_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/artifacts_v1/provenance_v1.json:1)
- 원본 accepted result: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/README.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/README.md:1)
- 원본 viewer 안내: [/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/README.md](/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/README.md:1)

이 archive는 검증된 baseline 보관용입니다. 원본 소스·결과·viewer 파일을 수정하지 않았습니다.
