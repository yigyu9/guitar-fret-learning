# Strike POSITION geometry PI v1 — 진행 기록

- **상태:** 5초 native diagnostic/analysis 완료; **NOT ADOPTED**.
- **실행:** 1,200 physics steps·151 frames·21 checks, PREPARE/PLAY/HOLD=49/251/0. Native closure 1,085개 changed 0; analyzer 입력 SHA 7개 unchanged. Learning 0, music success false.
- **제어 경계:** native mode POSITION, EFFORT command 없음. Actual-angle geometry PI가 R9 arm 목표를 소유했고 actor의 R9 output은 log-only, RH21 fingers는 policy. Source motor phases는 `[0]`만 관측. phase1 quarter-damping 설정은 실행되지 않았고 `PD_switch_count=0`.
- **결과:** READY/hit/physical hit/accepted/release 0, miss10, wrong0, readiness success0. Minimum policy pick-to-READY distance .024599624m. Guitar rotation max/end45.020741°/43.477582°, position max/end46.353646/36.603237mm. Region control91/300, PLAY policy45/251. No terminal before 5s.
- **비교:** timed-wait rebase는 one timely hit/G rotation max7.095455°였다. 이번 run과 PREPARE49 controls/native trace25/first actor obs-action prefix는 exact지만 이후 PLAY dynamics differ, so no one-factor causal attribution.
- **검증 범위:** prefix comparison is sampled prefix only; numerical goal-owner test 3/3 extracted branch cases true, not physics/full controller certification. Contact/readiness flags are observations, not cause proof.
- **별도 설계:** soft orientation은 [별도 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_SOFT_ORIENTATION_PLAN.md:1)에 연결한다.
- **참조:** [README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/README.md:1), [summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_position_geometry_pi_v1/analysis/summary.json).
