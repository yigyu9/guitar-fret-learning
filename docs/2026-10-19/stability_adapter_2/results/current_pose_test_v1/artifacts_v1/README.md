# 현재 자세 viewer용 native 초기 카메라 프리뷰

아래 세 장은 V2 headless 점검 trial_000에서 저장한 native Isaac Gym 카메라의 0초 프레임입니다. 데스크톱 viewer 화면을 캡처한 이미지가 아닙니다. 각 PNG는 원본 native 프레임의 바이트 그대로 복사했으며 잘라내기·합성·색상 편집·주석을 하지 않았습니다.

## 초기 프리뷰

### 전신 카메라 — native 0초 프레임

![전신 native 0초 프리뷰](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/artifacts_v1/native_preview_t00_whole_body.png)

### 손 전면 카메라 — native 0초 프레임

![손 전면 native 0초 프리뷰](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/artifacts_v1/native_preview_t00_hands.png)

### 엄지 뒤 카메라 — native 0초 프레임

![엄지 뒤 native 0초 프리뷰](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/artifacts_v1/native_preview_t00_thumb_back.png)

## 검증된 범위

저장된 headless trial은 0.2초 동안 48 physics step, 12 control step을 완료했습니다. report에는 입력 전후 동일, 금지 호출 0, 기존 reference 대비 초기값 exact가 기록되어 있습니다. 승인된 비교 결과에서는 첫 48 physics/12 control prefix가 기존 삼면 자세 native run과 일치합니다. 이는 짧은 headless 데이터 재현 점검입니다.

viewer 조작 흐름은 별도 공간의 실행 안내에 적힌 설정입니다. 시작하면 정지된 상태에서 Space로 진행, N으로 한 tick, R로 새 시뮬레이션 시작, C로 3개 카메라 순환, G로 형상 표시 전환, Esc로 종료합니다. 5초에 도달하면 일시정지되며 2초부터 오른 EW6 가상 피크 시험이 설정되어 있습니다.

**실제 GUI 통합은 검증되지 않았습니다.** 현재 환경에 DISPLAY가 없어서 viewer 창의 키·마우스 입력을 시험하지 못했습니다. 이 문서의 PNG는 native 카메라 프리뷰이며 desktop viewer의 작동 스크린샷이 아닙니다.

이 패키지는 `trial_000`의 초기 프리뷰만 제공합니다. 세션의 0.2초 점검 영상은 원래 위치에 보존되어 있으며 여기로 복사하지 않았습니다. 별도 진행 중인 recreation check의 결과는 이 패키지 범위에 포함하지 않았습니다.

## 실행 안내와 원자료

- Viewer 실행 및 키 안내: [/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/README.md:1](/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/README.md:1)
- 현재 실행 스크립트: [/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/open_v2.sh:1](/home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/open_v2.sh:1)
- 테스트 공간 결과 문서: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/README.md:1](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/README.md:1)
- Headless trial report: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/sessions/20261014_215819_009632/trial_000/report.json:1](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/sessions/20261014_215819_009632/trial_000/report.json:1)
- Native capture metadata: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/sessions/20261014_215819_009632/trial_000/media/capture.json:1](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/sessions/20261014_215819_009632/trial_000/media/capture.json:1)
- SHA pin 및 copy provenance: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/artifacts_v1/preflight_pin_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/artifacts_v1/preflight_pin_v1.json), [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/artifacts_v1/provenance_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/artifacts_v1/provenance_v1.json)
- 이 소유 범위 파일 색인: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/artifacts_v1/FILES_v1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/current_pose_test_v1/artifacts_v1/FILES_v1.md:1)
