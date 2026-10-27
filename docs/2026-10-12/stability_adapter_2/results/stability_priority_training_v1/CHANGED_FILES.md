# 기타 안정성 비중 강화: 변경 파일 위치

새 계획·구현은 stability_adapter_2, 결과·로그·영상은 이 결과 폴더에 저장한다. 이전 구현·체크포인트·실험 결과는 보존했다.

- [가중치·초기화·검증 계획](/home/ajou/yigyu/3/stability_adapter_2/STABILITY_PRIORITY_TRAINING_V1.md:1)
- [위치·회전 비용 4배 함수](/home/ajou/yigyu/3/stability_adapter_2/deadline_stability_reward_v1.py:7)
- [원본825 정책 이관 검사와 Actor·RMS 상속](/home/ajou/yigyu/3/stability_adapter_2/deadline_priority_transfer_v1.py:19)
- [새 native 환경](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v4.py:192), [floor·조기 안전 종료 정산](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v4.py:31)
- [실제 CUDA 학습·30분 평가 실행기](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v5.py:76)
- [보상·이관 반례 검사](/home/ajou/yigyu/3/stability_adapter_2/test_deadline_stability_priority_v1.py:1)
- [분리 실행의 실제 종료 코드 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/launch_run_v1.py:1)

메인 문서 추가분: [PLAN](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:900), [환경 README](/home/ajou/yigyu/3/stability_adapter_2/README.md:1999), [결과 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:669), [시각 보고](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2449). 기존 앞부분의 bytes/SHA와 추가 후 prefix 일치를 main_prefix_v1.json 및 before_native_verification_v1.json에 보존했다. 실행 시작 뒤 이 소스 및 main 문서는 동결했다.
