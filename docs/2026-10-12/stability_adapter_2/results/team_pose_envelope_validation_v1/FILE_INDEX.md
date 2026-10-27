# 팀원 자세 적용 진단 파일 색인

## 요약과 결과 그림

- [README: 조건 비교·해석 범위·영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/README.md:1)
- [저장 결과 수치 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/analysis/summary.json:1)
- [실제 native 초기값 readback 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/analysis/native_readback_audit.json:1)
- [phase 실행·보존 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/validation_record.json:1)
- [실제 native t0/5초 카메라 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/analysis/native_comparison.png)
- [151표본 actor-root 위치·회전 변화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/analysis/pose_changes.png)

## 세 조건의 영상

- 현재 수평 배치: [전신 MP4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/native/current_control/images/whole_body.mp4), [손 시점 MP4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/native/current_control/images/hands.mp4)
- 팀원 보고 기준 재구성: [전신 MP4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/native/reported_reference/images/whole_body.mp4), [손 시점 MP4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/native/reported_reference/images/hands.mp4)
- 팀원 보고 중앙 후보 재구성: [전신 MP4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/native/reported_center/images/whole_body.mp4), [손 시점 MP4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/native/reported_center/images/hands.mp4)

## 분석 입력과 native 원자료

- [저장 분석의 입력 전 SHA 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/analysis/inputs_before.json:1)
- [저장 분석의 입력 후 SHA 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/analysis/inputs_after.json:1)
- [기준 freeze runner 입력 보존 자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/analysis/frozen_runner_inputs.json:1)
- 각 native 조건 디렉토리의 `report.json`, `initial_values.json`, `initial_source_intersections.json`, `trace.json`, `contacts.jsonl`, `controls.json`, `attempt.json`, `images/capture.json`, `images/videos.json`에는 실행별 설정·관측·검사·녹화 기록이 저장되어 있다.

## 실행·분석 소스 보존본

- [검증 계획의 재구성 가정과 범위](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/source_final/TEAM_POSE_ENVELOPE_VALIDATION_PLAN.md:1)
- [native 조건 구성과 세 case 선택](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/source_final/validate_team_pose_envelope.py:22)
- [source convex 교집합 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/source_final/validate_team_pose_envelope.py:38)
- [조건별 초기 상태·무스트랩·무policy 설정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/source_final/validate_team_pose_envelope.py:91)
- [1200-step native loop와 접촉 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/source_final/validate_team_pose_envelope.py:128)
- [결과 필드와 학습 update 0 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/source_final/validate_team_pose_envelope.py:160)
- [봉인 실행 wrapper](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/source_final/run_team_pose_envelope_validation.sh:1)
- [실제 native readback 대조·요약 producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/source_final/analyze_team_pose_validation.py:25)

## 변경된 A 문서·소스 및 누적 기록

- [A 검증 계획의 현재 환경 적용 범위](/home/ajou/yigyu/3/stability_adapter_2/TEAM_POSE_ENVELOPE_VALIDATION_PLAN.md:1)
- [A 자세 재구성 함수](/home/ajou/yigyu/3/stability_adapter_2/validate_team_pose_envelope.py:22)
- [A source convex 검사](/home/ajou/yigyu/3/stability_adapter_2/validate_team_pose_envelope.py:38)
- [A native 실행 main과 case 설정](/home/ajou/yigyu/3/stability_adapter_2/validate_team_pose_envelope.py:62)
- [A 실행 wrapper의 runner 호출](/home/ajou/yigyu/3/stability_adapter_2/run_team_pose_envelope_validation.sh:9)
- [A 실제 native readback·summary 분석 main](/home/ajou/yigyu/3/stability_adapter_2/analyze_team_pose_validation.py:25)
- [main PLAN의 이번 검증 소단계](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:618)
- [누적 README의 세 조건 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:554)
- [누적 VISUAL_REPORT의 그림과 해석 범위](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2278)

## 검수·보존 기록

- [독립 검수 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/review.md:1)
- [root 보존 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/final_verification.json:1)
- 최종 SHA inventory 경로: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/artifact_inventory.json`.
