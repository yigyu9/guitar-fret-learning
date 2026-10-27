# 구현·결과 파일 안내

## 실험 입력과 기록

- 단일축 입력: [base](</home/ajou/yigyu/3/stability_adapter_2/trials/seed2_guitar_response_v1/base.json>), [Shoulder X](</home/ajou/yigyu/3/stability_adapter_2/trials/seed2_guitar_response_v1/shoulder_x.json>), [Shoulder Y](</home/ajou/yigyu/3/stability_adapter_2/trials/seed2_guitar_response_v1/shoulder_y.json>), [Shoulder Z](</home/ajou/yigyu/3/stability_adapter_2/trials/seed2_guitar_response_v1/shoulder_z.json>), [Wrist X](</home/ajou/yigyu/3/stability_adapter_2/trials/seed2_guitar_response_v1/wrist_x.json>), [Wrist Y](</home/ajou/yigyu/3/stability_adapter_2/trials/seed2_guitar_response_v1/wrist_y.json>), [Wrist Z](</home/ajou/yigyu/3/stability_adapter_2/trials/seed2_guitar_response_v1/wrist_z.json>)
- Heldout 입력: [heldout.json](</home/ajou/yigyu/3/stability_adapter_2/trials/seed2_guitar_response_v1/heldout.json>)
- Native raw와 초기값: [8개 run](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native>)
- 초기 조건/총 run 수: [artifact brief](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/artifact_brief.json>)
- probe 분석: [probe_analysis.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/probe_analysis.json>)
- Heldout 선택·분석: [heldout_selection.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/heldout_selection.json>), [heldout_analysis.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/heldout_analysis.json>)

## 실행 코드와 그림

- 입력 준비: [prepare_seed2_response_trials.py:17](/home/ajou/yigyu/3/stability_adapter_2/prepare_seed2_response_trials.py:17), [prepare_seed2_response_heldout.py:16](/home/ajou/yigyu/3/stability_adapter_2/prepare_seed2_response_heldout.py:16)
- Native 실행: [run_seed2_guitar_response.py:18](/home/ajou/yigyu/3/stability_adapter_2/run_seed2_guitar_response.py:18)
- 분석: [analyze_seed2_guitar_response.py:24](/home/ajou/yigyu/3/stability_adapter_2/analyze_seed2_guitar_response.py:24), [analyze_seed2_response_heldout.py:20](/home/ajou/yigyu/3/stability_adapter_2/analyze_seed2_response_heldout.py:20)
- 그림 생성: [make_seed2_guitar_response_artifacts.py:85](/home/ajou/yigyu/3/stability_adapter_2/make_seed2_guitar_response_artifacts.py:85)
- 출력과 재현 기록: [artifacts](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/artifacts>), [artifact_execution.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/artifact_execution.json>), [artifact_execution.log](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/artifact_execution.log>)

## 계획과 상태

- [작은 응답 방향 계획](</home/ajou/yigyu/3/stability_adapter_2/SEED2_RESPONSE_LOCALITY_PLAN.md>)은 다음 단계 계획이며 이 산출물 작업에서 실행하지 않았다.
- [이번 단계 체크리스트](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1374), [단계 README](/home/ajou/yigyu/3/stability_adapter_2/README.md:732), [날짜별 결과 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:470).
- 독립 검수 기록은 [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/review.md)에 있다.
