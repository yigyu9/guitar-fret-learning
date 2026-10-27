# Body-center view 파일 색인

## 결과·요약·수치

- [결과 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/README.md:1)
- [세 case 검사·실제 중심·q별 box 요약 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/summary.json:1)
- [세 case의 실제 RFU 중심, 사용자 bounds와 폭 CSV](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/body_center_ranges.csv:1)
- [producer 입력 SHA 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/attempt.json:1)
- [producer 실행 결과 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/producer.log)

## Annotated body-center 그림 6장

- current_control: [정면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/current_control/front.png), [측면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/current_control/side.png)
- reported_reference: [정면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/reported_reference/front.png), [측면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/reported_reference/side.png)
- reported_center: [정면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/reported_center/front.png), [측면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/reported_center/side.png)

## 변환 계획과 구현 줄

- [A body-center 표시 계획의 정의·범위](/home/ajou/yigyu/3/stability_adapter_2/BODY_CENTER_VIEW_PLAN.md:1)
- [A forward body-center 변환](/home/ajou/yigyu/3/stability_adapter_2/body_center_coordinates.py:7)
- [A 역변환과 Pelvis RFU 좌표](/home/ajou/yigyu/3/stability_adapter_2/body_center_coordinates.py:12)
- [A identity/z90·256 random quaternion 왕복 검증](/home/ajou/yigyu/3/stability_adapter_2/build_body_center_view.py:16)
- [A body-center-only 이미지 overlay와 캡션](/home/ajou/yigyu/3/stability_adapter_2/build_body_center_view.py:27)
- [A 저장 frame 입력·q별 좌표 계산·CSV 생성 main](/home/ajou/yigyu/3/stability_adapter_2/build_body_center_view.py:62)
- [A 요약 check와 scope 기록](/home/ajou/yigyu/3/stability_adapter_2/build_body_center_view.py:108)
- [보존 body-center 표시 계획](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/source_final/BODY_CENTER_VIEW_PLAN.md:1)
- [보존 변환 helper](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/source_final/body_center_coordinates.py:1)
- [보존 이미지·CSV producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/source_final/build_body_center_view.py:1)

## main 계획과 누적 기록

- [A main PLAN의 body-center 후처리 단계](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:637)
- [누적 README의 현재 body-center 범위 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:564)
- [누적 VISUAL_REPORT의 세 case 이미지와 수치 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2300)
- [root SHA·native 정합 검증 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/final_verification.json:1)

## 입력 frame 및 보존 기록

이 후처리는 이전 native comparison phase의 저장 raw PNG/depth/camera/geometry를 사용한다. 각 시점의 입력은 `envelope_native_comparison_v1/native/<case>/` 아래에 있다.

- current_control: raw [정면 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/front_raw.png)/[측면 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/side_raw.png), [정면 depth](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/front_depth.npy)/[측면 depth](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/side_depth.npy), [native geometry](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/geometry.json), [camera·SHA report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/report.json).
- reported_reference: raw [정면 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/front_raw.png)/[측면 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/side_raw.png), [정면 depth](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/front_depth.npy)/[측면 depth](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/side_depth.npy), [native geometry](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/geometry.json), [camera·SHA report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/report.json).
- reported_center: raw [정면 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/front_raw.png)/[측면 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/side_raw.png), [정면 depth](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/front_depth.npy)/[측면 depth](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/side_depth.npy), [native geometry](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/geometry.json), [camera·SHA report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/report.json).
- [보호 대상 previous phase 파일 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/protected_before.json:1)
- [기존 inventory/review 시점 불일치에 대한 사전 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/prior_inventory_note.json:1)
- [독립 review 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/review.md:1)
- 최종 SHA inventory 기록 경로: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/artifact_inventory.json`.
