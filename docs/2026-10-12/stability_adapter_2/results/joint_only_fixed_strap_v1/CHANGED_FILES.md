# 변경 파일

- 새 Python 3.8 호환 읽기 전용 차트 producer: [make_joint_only_fixed_strap_artifacts_v2.py](/home/ajou/yigyu/3/stability_adapter_2/make_joint_only_fixed_strap_artifacts_v2.py:1). 보존된 `analyze_small_wrist_motion.py`의 metrics helper를 호출하며 native/physics/actor/training 호출은 없다.
- baseline과 후보의 저장 trace에서 만든 위치·회전 2패널 그림: [joint_only_fixed_strap_timeseries.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/artifacts/v2/joint_only_fixed_strap_timeseries.png).
- producer와 입력 전후 SHA, 출력 SHA 및 실행 범위 기록: [artifact_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/artifacts/v2/artifact_manifest.json:1), [producer_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/artifacts/v2/producer_execution.json:1), [producer.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/artifacts/v2/producer.log:1).
- 실행 전 producer/source/input SHA 기록과 복사본: [source_snapshot.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/artifacts/v2/source_snapshot.json:1), [source_snapshot 디렉터리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/artifacts/v2/source_snapshot).
- 그림 생성 전 종료한 최초 시도의 보존본: [producer_source.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/artifacts/v1_failed_attempt/producer_source.py:1), [producer.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/artifacts/v1_failed_attempt/producer.log:1), [producer_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/artifacts/v1_failed_attempt/producer_execution.json:1). 실패 원인은 scalar initial-error 차이로 late-change를 검사한 것이며, 최초 시도의 입력 전후 SHA map은 저장되지 않았다.
- 한국어 결과 보고서: [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/README.md:1).
- 실제 native 비교 결정: [JOINT_ONLY_FIXED_STRAP_DECISION.md](/home/ajou/yigyu/3/stability_adapter_2/JOINT_ONLY_FIXED_STRAP_DECISION.md:1).

## 검증

- 새 producer Python 3.8 `py_compile` 통과.
- 실행 전 snapshot에서 producer와 141개 source/input 복사본의 SHA 확인 통과.
- producer는 `/home/ajou/miniconda3/envs/rl38/bin/python`에서 1회 실행, exit code 0. 정확한 명령·로그·SHA metadata는 `artifacts/v2/`에 보존.
- PNG를 열어 두 패널, 단위, 제목, 2–5초 음영, 범례가 겹치지 않는 것을 확인.
- 저장 파일만 읽음: native initialization 0, physics step 0, actor inference 0, training update 0.
