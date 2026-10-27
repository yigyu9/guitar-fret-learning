# 구현·계획 변경 파일

기존 run_recorded_trial/gym_trial_recording/물리자산은 변경하지 않았다.
이번실행은 초기각/LA가같고 왼팔12 kp만변경한 진단이다. 다음은 초기LA변경이다.

| 절대경로·실제줄 | 변경 내용 |
| --- | --- |
| [stability_adapter_2/analyze_palm_stiffness_only.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_stiffness_only.py:20) | 저장된3조건5초 분석·PD/목표/영상 SHA·처음0.1초/전체5초 대조 |
| [stability_adapter_2/make_palm_stiffness_only_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_palm_stiffness_only_artifacts.py:160) | 저장곡선과 실제Gym PNG로 산출물 생성 |
| [stability_adapter_2/trials/palm_stiffness_only_v1/kp_1.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_stiffness_only_v1/kp_1.json:1) | 기준초기값·kp1/kd1 |
| [stability_adapter_2/trials/palm_stiffness_only_v1/kp_1p5.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_stiffness_only_v1/kp_1p5.json:1) | 같은초기값·kp1.5/kd1 |
| [stability_adapter_2/trials/palm_stiffness_only_v1/kp_2.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_stiffness_only_v1/kp_2.json:1) | 같은초기값·kp2/kd1 |
| [stability_adapter_2/STRAP_FIVE_SECOND_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/STRAP_FIVE_SECOND_PLAN.md:1) | 다음 실제초기LA3조건5초 비교;아직미실행 |
| [stability_adapter_2/PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1262) | 메인진행 체크리스트 |
| [stability_adapter_2/README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:657) | 비교결과와다음계획 |
| [docs/2026-10-12/stability_adapter_2/README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:414) | 누적결과 |
| [docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1274) | 그림94/95와실제영상 설명 |
