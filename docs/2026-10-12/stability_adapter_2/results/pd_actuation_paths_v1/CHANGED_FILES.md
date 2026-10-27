# 변경 파일 및 근거 경로

## 이번 산출물

- [정적 경로도 producer](/home/ajou/yigyu/3/stability_adapter_2/plot_pd_paths.py:1) — 저장된 감사 자료와 source/API 경로만 읽는다. [그룹 집계](/home/ajou/yigyu/3/stability_adapter_2/plot_pd_paths.py:42), [입력 SHA·계약 검사 및 출력 manifest](/home/ajou/yigyu/3/stability_adapter_2/plot_pd_paths.py:65).
- [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pd_actuation_paths_v1/README.md:1) — 비교표, 한계, 재생성 명령.
- [그림 62 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:902) — 누적 §47.
- [최종 정적 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pd_actuation_paths_v1/artifacts/pd_actuation_paths.png) 및 [그림 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pd_actuation_paths_v1/artifacts/pd_actuation_paths.manifest.json:1).
- [실제 생성 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pd_actuation_paths_v1/plot_execution_v1.json:1), [실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pd_actuation_paths_v1/plot_run_v1.log:1).

## 읽은 감사 입력

- [순수 감사 구현](/home/ajou/yigyu/3/stability_adapter_2/audit_pd_paths.py:45) — 실제 원본 함수·정책 이름·저장 native200 수치 대조.
- [105축 audit JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pd_actuation_paths_v1/audit.json:1) 및 [정적 audit 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pd_actuation_paths_v1/audit_execution.json:1), [audit 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pd_actuation_paths_v1/audit_run.log:1). 계약 6개와 source 101 SHA 확인; native 초기화와 physics step은 0.
- 원본 경로: [base.py gain/force 제출](/home/ajou/yigyu/3/tab2body/env/base.py:285), [step 제어](/home/ajou/yigyu/3/tab2body/env/base.py:934), [torque cap](/home/ajou/yigyu/3/tab2body/env/safety.py:21), [Fret task](/home/ajou/yigyu/3/tab2body/env/tasks/task_fret.py:75), [Strike task](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:157).
- 현재 경로: [environment drive properties](/home/ajou/yigyu/3/stability_adapter_2/environment.py:162), [position-target 설정](/home/ajou/yigyu/3/stability_adapter_2/environment.py:221). 공식 설치 문서의 [force tensor EFFORT mode 조건](/home/ajou/yigyu/3/isaacgym/docs/programming/tensors.html:384).

## 상위 계획 및 제안 문서

- [계획 §55](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1010) 및 [프로젝트 README 감사 요약](/home/ajou/yigyu/3/stability_adapter_2/README.md:463).
- [읽기 전용 감사 계약](/home/ajou/yigyu/3/stability_adapter_2/PD_ACTUATION_PATH_AUDIT.md:1)과 [미승인·미실행 API 검증 제안](/home/ajou/yigyu/3/stability_adapter_2/TENSOR_EFFORT_API_PROPOSAL.md:1). 제안 단계는 사용자 확인 전이며 본 산출물에는 native 실행이 없다.

## 검수 상태

정적 그림·표·문서의 [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pd_actuation_paths_v1/runtime_review.md:7)를 완료했다. 남은 finding 없음. 기존 실패·초안 자료는 보존되어 있으며 이 인덱스는 최종 산출물 경로만 연결한다.
