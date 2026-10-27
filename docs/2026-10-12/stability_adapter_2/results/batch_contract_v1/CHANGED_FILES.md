# 이번 단위 변경 파일·검토 위치

2026-10-06. 실제 파일의 1-based 줄 번호로 연결한다. 신규 파일과 기존 파일의 이번 변경을 함께 표시했다. 기존 stability_adapter 및 과거 자료는 변경하지 않았다.

| 절대 경로·실제 줄 | 내용 |
|---|---|
| [/home/ajou/yigyu/3/stability_adapter_2/environment.py:37](/home/ajou/yigyu/3/stability_adapter_2/environment.py:37) | 초기 입력의 1회 적용·절대 길이 유지 |
| [/home/ajou/yigyu/3/stability_adapter_2/trial_settings.py:10](/home/ajou/yigyu/3/stability_adapter_2/trial_settings.py:10) | 관절 rad·절대 m 검증과 source hash |
| [/home/ajou/yigyu/3/stability_adapter_2/run_trial.py:13](/home/ajou/yigyu/3/stability_adapter_2/run_trial.py:13) | 정적 query·초기 상태·실제 trace 기록 |
| [/home/ajou/yigyu/3/stability_adapter_2/run_batch.py:49](/home/ajou/yigyu/3/stability_adapter_2/run_batch.py:49) | 순차 실행·checkpoint·완료 재사용·잠금 |
| [/home/ajou/yigyu/3/stability_adapter_2/trials/input_contract_batch.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/input_contract_batch.json:1) | 세 기능 진단 입력 |
| [/home/ajou/yigyu/3/stability_adapter_2/tests/test_trial_settings.py:7](/home/ajou/yigyu/3/stability_adapter_2/tests/test_trial_settings.py:7) | 입력·제어권·다른 목표 보존 검사 |
| [/home/ajou/yigyu/3/stability_adapter_2/tests/test_batch.py:17](/home/ajou/yigyu/3/stability_adapter_2/tests/test_batch.py:17) | 부분 재개·변조 거부·partial 보존 검사 |
| [/home/ajou/yigyu/3/stability_adapter_2/tests/test_native_contract.py:10](/home/ajou/yigyu/3/stability_adapter_2/tests/test_native_contract.py:10) | native 초기각·절대 길이 검사 추가 |
| [/home/ajou/yigyu/3/stability_adapter_2/plot_batch_contract.py:36](/home/ajou/yigyu/3/stability_adapter_2/plot_batch_contract.py:36) | 원시 trace 기반 비교 그림 |
| [/home/ajou/yigyu/3/stability_adapter_2/BATCH_EXPERIMENTS.md:9](/home/ajou/yigyu/3/stability_adapter_2/BATCH_EXPERIMENTS.md:9) | 이번 계획·조건·체크리스트 |
| [/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:530](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:530) | 메인 계획의 이번 구현 단위 |
| [/home/ajou/yigyu/3/stability_adapter_2/README.md:228](/home/ajou/yigyu/3/stability_adapter_2/README.md:228) | 현재 구현 상태와 검사 수 |
| [/home/ajou/yigyu/3/stability_adapter_2/EXPERIMENT_WORKFLOW.md:55](/home/ajou/yigyu/3/stability_adapter_2/EXPERIMENT_WORKFLOW.md:55) | 반복 역할·구현 현황 갱신 |
| [/home/ajou/yigyu/3/stability_adapter_2/INITIAL_STATE_DIAGNOSTICS.md:56](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_STATE_DIAGNOSTICS.md:56) | 진단 입력 연결의 현재 상태 |
| [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:384](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:384) | 이미지·조건·수치·한계 누적 |
| [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/batch_contract_v1/README.md:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/batch_contract_v1/README.md:1) | 이번 결과·재현 명령·원자료 안내 |

원자료 report·trace·settings·checkpoint, 실행 로그, 검증 JSON, 당시 source 사본과 그림은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/batch_contract_v1/README.md:1)에 정리했다. PNG에는 줄 번호가 없으며 결과 문서에 포함했다.
