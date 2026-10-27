# 변경 파일

- Python 3.8 호환 trace chart producer: [make_fixed_strap_shoulder_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_fixed_strap_shoulder_artifacts.py:1). 실행 전 producer/wrapper/helper/plan 복사본을 만들고 SHA를 확인하며, 저장된 late metric은 `analyze_small_wrist_motion.metrics(rows)` helper로 검산한다.
- 3조건 기타 초기 world pose 오차 trace 2-panel PNG: [fixed_strap_shoulder_response.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/artifacts/fixed_strap_shoulder_response.png).
- pre-run producer/direct-source copies와 SHA 목록: [source_snapshot.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/artifacts/source_snapshot.json:1), [source_snapshot 디렉터리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/artifacts/source_snapshot).
- producer/input before-after 및 PNG output SHA: [artifact_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/artifacts/artifact_manifest.json:1).
- 정확한 실행 command, environment, exit code, SHA: [producer_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/artifacts/producer_execution.json:1), [producer.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/artifacts/producer.log:1).
- 한국어 phase 보고서: [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/README.md:1).
- 물리 결과 결정과 다음 wrist-y 시험 방향: [FIXED_STRAP_SHOULDER_RESPONSE_DECISION.md](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SHOULDER_RESPONSE_DECISION.md:1).
- Root 실행 및 실제 PNG QA: [ROOT_VERIFICATION_NOTES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/ROOT_VERIFICATION_NOTES.md:1).
- 메인 결과 기록: [stability_adapter_2/README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:1013), [stability_adapter_2/PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1811), [누적 시각 보고서 §102](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1877), [영상 색인 v7](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v7.md:1).

## 검증

- `/home/ajou/miniconda3/envs/rl38/bin/python -m py_compile` 통과.
- 생성 전 분석 29 checks/38 input SHA, producer/helper source와 12개 required endpoint frame 확인.
- 실행 1회, exit 0, sealed input count 69. Producer SHA 전후 일치, input SHA before/after 일치.
- PNG SHA-256: `d19d03ba92e80f3a13d3e0405686746421090e250ed84c2cf8aba2f1e93bb234`; figure를 열어 단위, 세 trace, 두 panel, 2–5초 음영 및 범례 겹침이 없는 것을 확인.
- 산출물 생성 중 native initialization/physics, actor inference, training은 모두 0.
