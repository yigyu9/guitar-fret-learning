# 이번 소단계 변경 파일과 실제 줄 번호

아래 링크는 절대 경로와 실제 1-based 줄 번호를 사용한다. 실행된 A 소스와 기존 결과는 고정했으며 장기 학습 중 A를 추가 변경하지 않는다.

## 계획·구현·검사

- [스트랩 비교 계획](/home/ajou/yigyu/3/stability_adapter_2/STRAP_FALLBACK_TRAINING_V1.md:1)
- [스트랩 상수](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v3.py:15), [장력 법칙](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v3.py:42), [물리 force guard](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v3.py:58), [실제 환경·안전 종료](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v3.py:188)
- [기존 정책의 새 상태 공간 확장](/home/ajou/yigyu/3/stability_adapter_2/deadline_warm_start_v1.py:16), [출력 동일성 검사](/home/ajou/yigyu/3/stability_adapter_2/deadline_warm_start_v1.py:85)
- [CUDA 학습·체크포인트·평가 실행기](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v4.py:76), [시간 제한 wrapper](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v4.py:58)
- [native 순수 검사](/home/ajou/yigyu/3/stability_adapter_2/test_deadline_native_v3.py:1), [warm start 검사](/home/ajou/yigyu/3/stability_adapter_2/test_deadline_warm_start_v1.py:1)
- [메인 계획 추가분](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:893), [환경 README 추가분](/home/ajou/yigyu/3/stability_adapter_2/README.md:1992), [산출물 색인 추가분](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:662), [시각 보고 추가분](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2442). 기존 앞부분은 snapshot으로 대조한다.

## 결과·설명·검수

- [결과 설명과 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/README.md:1)
- [초기 비교 수치 계산](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/analyze_initial_comparison_v1.py:1)
- [실제 reset 진단](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/run_reset_probe_v2.py:1)
- [비교 영상·프레임 생성 및 파일 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/CHANGED_FILES.md:1)
- [범례 보완 그래프 및 파일 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v2/CHANGED_FILES.md:1)
- [native 사전 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/review_v1.md:1), [실행 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/review_v2.md:1), [시각화 보완 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/review_v3.md:1)

`deadline_native_v2.py`와 그 검사, 실패한 reset probe v1 및 이전 시각화 버전은 수정 전 기록으로 보존한다. 실제 현재 실행은 native v3와 runner v4다. 동적으로 갱신되는 장기 학습 폴더를 완료된 고정 산출물로 취급하지 않는다.
