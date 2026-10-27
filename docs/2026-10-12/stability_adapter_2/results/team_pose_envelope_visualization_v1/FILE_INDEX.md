# 파일 색인

원자료, 최종 `analysis_v2` 그림과 입력 보존 자료를 기준으로 정리했다. 코드와 계획 링크는 실제 관련 줄을 가리킨다. 앞선 `analysis/` 그림은 초안 보존본이며 본문에는 최종 v2 그림만 사용했다.

## 산출물

- [한국어 결과 설명과 최종 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/README.md:1)
- [최종 위치·회전 후보 개념도](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/analysis_v2/pose_candidates.png)
- [최종 96행 판정 표본 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/analysis_v2/judgment_samples.png)

## 입력 및 전후 기록

- [팀원 판정 원본 CSV, 96행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/inputs/guitar_pose_judgments_20261010.csv)
- [첨부 자세 허용범위 이미지 원본 사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/inputs/guitar_pose_tolerance_20261010.png)
- [v2 분석 facts](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/analysis_v2/facts.json:1)
- [v2 분석 입력 SHA 전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/analysis_v2/inputs_before.json:1)
- [v2 분석 입력 SHA 후](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/analysis_v2/inputs_after.json:1)
- [보존 자료 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/protected_before.json:1)

## 생성 코드와 계획

- [첫 producer의 입력 봉인·CSV 읽기](/home/ajou/yigyu/3/stability_adapter_2/visualize_team_pose_envelope.py:35)
- [첫 producer의 도형과 원자료 표본 표시](/home/ajou/yigyu/3/stability_adapter_2/visualize_team_pose_envelope.py:49)
- [최종 v2 producer의 입력 SHA 기록](/home/ajou/yigyu/3/stability_adapter_2/visualize_team_pose_envelope_v2.py:35)
- [v2 위치 후보·기준 좌표](/home/ajou/yigyu/3/stability_adapter_2/visualize_team_pose_envelope_v2.py:49)
- [v2 방위·roll 후보 표기](/home/ajou/yigyu/3/stability_adapter_2/visualize_team_pose_envelope_v2.py:77)
- [v2 96행 표본·범례·검사](/home/ajou/yigyu/3/stability_adapter_2/visualize_team_pose_envelope_v2.py:104)
- [v2 facts와 입력 SHA 전후 대조](/home/ajou/yigyu/3/stability_adapter_2/visualize_team_pose_envelope_v2.py:137)
- [시각화 leaf 계획과 해석 한계](/home/ajou/yigyu/3/stability_adapter_2/TEAM_POSE_ENVELOPE_VISUALIZATION_PLAN.md:3)
- [표본 수·후보 수치·범위](/home/ajou/yigyu/3/stability_adapter_2/TEAM_POSE_ENVELOPE_VISUALIZATION_PLAN.md:5)
- [기록 차이·미확인 물리량](/home/ajou/yigyu/3/stability_adapter_2/TEAM_POSE_ENVELOPE_VISUALIZATION_PLAN.md:7)
- [초기 producer 보존 사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/before/visualize_team_pose_envelope.py:1)
- [보존 최종 v2 producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/source_final/visualize_team_pose_envelope_v2.py:1)
- [보존 leaf 계획](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/source_final/TEAM_POSE_ENVELOPE_VISUALIZATION_PLAN.md:1)

## 상위 문서 진행 위치

- [main PLAN 시각화 소단계](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:612)
- [main PLAN의 현재 설정 보존 항목](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:614)
- [main PLAN의 개념도·96표본 작업 항목](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:615)
- [누적 결과 README의 시각화 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:550)
- [누적 시각 보고서의 두 최종 그림과 해석 한계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2268)

## 검수 및 root 보존 감사

- [독립 검수 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/review.md:1)
- [root 보존 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/final_verification.json:1)

최종 SHA 기록 경로: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/artifact_inventory.json`.
