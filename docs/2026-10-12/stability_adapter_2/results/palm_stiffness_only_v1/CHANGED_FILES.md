# 변경 파일 및 근거

| 파일 | 실제 위치/줄 | 용도 |
|---|---|---|
| 저장 결과 시각화 producer | [make_palm_stiffness_only_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_palm_stiffness_only_artifacts.py:1), [입력 봉인·검사](/home/ajou/yigyu/3/stability_adapter_2/make_palm_stiffness_only_artifacts.py:20), [곡선 생성](/home/ajou/yigyu/3/stability_adapter_2/make_palm_stiffness_only_artifacts.py:102), [카메라 프레임 합성](/home/ajou/yigyu/3/stability_adapter_2/make_palm_stiffness_only_artifacts.py:134), [CLI·manifest 작성](/home/ajou/yigyu/3/stability_adapter_2/make_palm_stiffness_only_artifacts.py:160) | 저장된 분석 곡선과 카메라 프레임만 사용 |
| 결과 설명 | [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/README.md:1) | 조건, 비교표, 그림, 한계, 재생성 방법 |
| 분석 결과 | [analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/analysis.json:1) | 7개 검사와 3조건 요약·곡선 |
| 곡선 그림 | [palm_stiffness_only_curves.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/artifacts/palm_stiffness_only_curves.png) | 저장 수치의 5초 비교 |
| 카메라 그림 | [palm_stiffness_only_camera.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/artifacts/palm_stiffness_only_camera.png) | 세 조건의 실제 Gym t=0 전신 및 t=5초 손 프레임 |
| SHA 및 실행 정보 | [artifact_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/artifacts/artifact_manifest.json:1), [artifact_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/artifact_execution.json:1), [artifact_execution.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/artifact_execution.log:1) | 읽은 입력·producer·출력 해시와 후처리 실행 정보 |
| 이전 산출물 보존본 | [producer_attempt_v1.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/producer_attempt_v1.py), [artifacts_attempt_v1/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/artifacts_attempt_v1/) | 표시하지 않은 프레임까지 manifest에 기록했던 이전 producer와 그림/manifest 보존 |
| 기존 분석·trial 도구 | [analyze_palm_stiffness_only.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_stiffness_only.py:20), [run_recorded_trial.py](/home/ajou/yigyu/3/stability_adapter_2/run_recorded_trial.py:18), [단계 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_STIFFNESS_ONLY_PLAN.md:1) | 이번 산출물에서 참조한 도구 및 조건 |

이번 후처리 단계에서는 producer와 산출물만 추가·갱신했습니다. 기존 native 원자료와 물리 설정은 수정하지 않았고, 실제 native trial은 상위 단계에서 이미 완료되었습니다.
