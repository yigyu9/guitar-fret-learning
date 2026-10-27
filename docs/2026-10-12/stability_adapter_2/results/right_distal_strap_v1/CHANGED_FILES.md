# 이번 변경 파일과 실제 줄 번호

초기 입력·계획·구현은 stability_adapter_2, 검증 원자료·로그·산출물은 docs에 저장한다.

- [RIGHT_DISTAL_STRAP_COMPARE.md](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_DISTAL_STRAP_COMPARE.md:1) — 소단계 계획과 선정·진단·판정.
- [compare_fixed_strap.py](/home/ajou/yigyu/3/stability_adapter_2/compare_fixed_strap.py:14) — 12개 선언 실행·8개 short 조건·물리/보정/고정LA 검증.
- [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:660) — 메인 진행 기록.
- [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:49) — 현재 결과.

기존 pose_strap_inputs/run_joint_hold/JointHoldResidual은 수정하지 않고 재사용했다.

- [legacy.json](/home/ajou/yigyu/3/stability_adapter_2/trials/right_distal_strap_v1/legacy.json:1) — 초기 절대LA 입력; legacy는0N과 동일하여 중복 native 실행하지 않았다.
- [load_00n.json](/home/ajou/yigyu/3/stability_adapter_2/trials/right_distal_strap_v1/load_00n.json:1) — 초기 절대LA 입력; legacy는0N과 동일하여 중복 native 실행하지 않았다.
- [load_05n.json](/home/ajou/yigyu/3/stability_adapter_2/trials/right_distal_strap_v1/load_05n.json:1) — 초기 절대LA 입력; legacy는0N과 동일하여 중복 native 실행하지 않았다.
- [load_10n.json](/home/ajou/yigyu/3/stability_adapter_2/trials/right_distal_strap_v1/load_10n.json:1) — 초기 절대LA 입력; legacy는0N과 동일하여 중복 native 실행하지 않았다.
- [load_20n.json](/home/ajou/yigyu/3/stability_adapter_2/trials/right_distal_strap_v1/load_20n.json:1) — 초기 절대LA 입력; legacy는0N과 동일하여 중복 native 실행하지 않았다.
- [comparison_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_strap_v1/comparison_v2.json:1) — 현재 비교와 coverage 검사.
- [coverage_regression_validation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_strap_v1/coverage_regression_validation.json:1) — 10N ON 누락을 거부한 읽기전용 회귀 fixture.
- [plot_fixed_strap.py](/home/ajou/yigyu/3/stability_adapter_2/plot_fixed_strap.py:77) — 저장 trace의0.1/0.5초 비교 그림.
- [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_strap_v1/README.md:1) — 길이·실측값·판정·이미지·재현 명령.
- [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:616) — 누적 그래프와 설명.
- [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_strap_v1/review.md:1) — 독립 검수.
