# Native 정적 범위 비교 파일 색인

## 요약·세 조건 그림

- [결과 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/README.md:1)
- 현재 수평 배치: [정면 annotated](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/front.png), [측면 annotated](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/side.png)
- 팀원 보고 기준: [정면 annotated](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/front.png), [측면 annotated](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/side.png)
- 팀원 중앙 후보: [정면 annotated](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/front.png), [측면 annotated](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/side.png)

## 원본 이미지와 depth

각 조건의 raw native camera color와 depth는 주석 그림과 분리해 보존한다.

- current_control: [정면 raw PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/front_raw.png), [측면 raw PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/side_raw.png), [정면 depth NPY](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/front_depth.npy), [측면 depth NPY](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/side_depth.npy)
- reported_reference: [정면 raw PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/front_raw.png), [측면 raw PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/side_raw.png), [정면 depth NPY](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/front_depth.npy), [측면 depth NPY](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/side_depth.npy)
- reported_center: [정면 raw PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/front_raw.png), [측면 raw PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/side_raw.png), [정면 depth NPY](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/front_depth.npy), [측면 depth NPY](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/side_depth.npy)

## 상태·조건별 기록

- `current_control`: [geometry](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/geometry.json), [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/report.json), [attempt](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/attempt.json).
- `reported_reference`: [geometry](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/geometry.json), [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/report.json), [attempt](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/attempt.json).
- `reported_center`: [geometry](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/geometry.json), [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/report.json), [attempt](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/attempt.json).
- [current_control 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/current_control.log)
- [reported_reference 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/reported_reference.log)
- [reported_center 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/reported_center.log)

## 실행 계획과 구현 위치

- [A 실행 계획의 조건과 해석 한계](/home/ajou/yigyu/3/stability_adapter_2/ENVELOPE_NATIVE_COMPARISON_PLAN.md:1)
- [A 회전범위의 case별 포함 검사](/home/ajou/yigyu/3/stability_adapter_2/render_envelope_native.py:23)
- [A raw native 장면 위 depth-aware 설명 overlay](/home/ajou/yigyu/3/stability_adapter_2/render_envelope_native.py:40)
- [A native 상태 대조·box 변환·정적 렌더 main](/home/ajou/yigyu/3/stability_adapter_2/render_envelope_native.py:71)
- [A 결과에 0 physics/학습과 상태보존 기록](/home/ajou/yigyu/3/stability_adapter_2/render_envelope_native.py:126)
- [A 실행 wrapper](/home/ajou/yigyu/3/stability_adapter_2/run_envelope_native.sh:9)
- [보존 leaf 계획](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/source_final/ENVELOPE_NATIVE_COMPARISON_PLAN.md:1)
- [보존 renderer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/source_final/render_envelope_native.py:1)
- [보존 실행 wrapper](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/source_final/run_envelope_native.sh:1)

## main 계획과 누적 phase 기록

- [main PLAN의 정적 범위 비교 소단계](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:628)
- [누적 README의 세 native 장면 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:559)
- [누적 VISUAL_REPORT의 세 조건 캡처와 표시 범위](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2289)
- [phase 실행·검사 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/validation_record.json:1)

## 검수·root 기록 경로

- [review 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/review.md:1)
- [root 최종 보존 검증 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/final_verification.json:1)
- root 최종 SHA inventory 기록 경로: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/artifact_inventory.json`.
