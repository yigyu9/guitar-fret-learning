# 실행 자원 분석 준비

- 담당 범위: `analyze_runtime.py`와 이 진행 기록만 작성했다. 실행 중인 학습의 소스·설정·원자료와 기존 결과는 수정하지 않았다.
- `analyze_runtime.py`는 학습 종료 후 root가 실행한다. 아직 실행하지 않았으며 결과 수치를 생성하지 않았다.
- 동일한 8개 worker PID의 RSS/PSS 완전 표본만 합산한다. 시작 60초 이후 첫 표본과 마지막 완전 표본, 60초 이후·후반 절반·마지막 10분 OLS와 R²를 기록한다. 소표본/짧은 구간과 자기상관의 한계를 명시한다.
- parent 현재 메모리·peak 및 worker 개별 peak의 합을 분리한다. 시스템 전체 MemAvailable 최솟값, reset/step/PPO timer 범위, 종료·정리 근거와 worker별 생성/종료 횟수·시작 episode 수를 함께 분석한다.
- 분석 소스·신구 report/resources/status/settings·새 core/audit/lifecycle 파일의 SHA를 파싱 전에 기록한다. 출력 세 파일은 exclusive 생성하며 이전 출력을 덮어쓰지 않는다. 실제 실패·중단은 그대로 남기고 분석 무결성과 학습 완료 여부를 분리한다.
- 구식 약 1시간 실행과 정책 25회 업데이트에서 재개한 새 실행의 기간·정책·동시 부하 차이를 비교 한계로 남긴다.

종료 후 실행 예정:

```bash
python /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_training_v1/analyze_runtime.py
```

예정 출력: `runtime_inputs_before.json`, `runtime_analysis.json`, `runtime_verification.json`. 이 파일들은 아직 만들지 않았다.
