# 조기 종료 유인 위험 분석

업데이트 구간: [400, 499]

종료 에피소드 7225개, 마지막 반영 업데이트 499.

조기 종료는 남은 곡의 비용도 끝냅니다. 아래 총보상·총비용 분포는 이 설계 위험을 조사하는 관측 자료이며, 정책이 의도적으로 실패하도록 학습했다는 증거는 아닙니다.

| 구분 | 종료 수 | 평균 길이(s) | 길이 중앙값(s) | 평균 총보상 | 평균 총비용 | 평균 미할인 R-C 참고값 |
|---|---:|---:|---:|---:|---:|---:|
| all | 7225 | 9.4167 | 2.7000 | -1.3430 | 19.1874 | -20.5304 |
| ended_cycle_007 | 571 | 31.1048 | 32.8167 | -1.4570 | 40.4387 | -41.8957 |
| ended_cycle_008 | 917 | 24.8470 | 28.5167 | -1.1104 | 40.9866 | -42.0970 |
| ended_cycle_009 | 959 | 13.6561 | 11.5000 | -0.6658 | 26.5908 | -27.2566 |
| ended_cycle_010 | 943 | 7.2153 | 4.2000 | -0.8951 | 17.6425 | -18.5377 |
| ended_cycle_011 | 883 | 3.8984 | 2.0000 | -1.2917 | 12.6946 | -13.9863 |
| ended_cycle_012 | 797 | 2.1715 | 1.3167 | -1.5591 | 9.6616 | -11.2207 |
| ended_cycle_013 | 668 | 1.4298 | 0.9500 | -1.7681 | 8.4977 | -10.2658 |
| ended_cycle_014 | 520 | 1.2284 | 0.7833 | -1.8154 | 8.0655 | -9.8809 |
| ended_cycle_015 | 381 | 0.9847 | 0.6500 | -1.8951 | 7.5829 | -9.4780 |
| ended_cycle_016 | 253 | 0.8398 | 0.5333 | -1.9331 | 7.3264 | -9.2596 |
| ended_cycle_017 | 151 | 0.7506 | 0.4500 | -1.9345 | 7.0274 | -8.9619 |
| ended_cycle_018 | 86 | 0.6984 | 0.4417 | -1.9696 | 6.7707 | -8.7403 |
| ended_cycle_019 | 45 | 0.6441 | 0.4500 | -1.9829 | 6.8101 | -8.7930 |
| ended_cycle_020 | 25 | 0.6680 | 0.4500 | -1.9863 | 6.7248 | -8.7111 |
| ended_cycle_021 | 13 | 0.4487 | 0.4000 | -2.0000 | 6.6334 | -8.6334 |
| ended_cycle_022 | 8 | 0.4083 | 0.3917 | -2.0000 | 6.2960 | -8.2960 |
| ended_cycle_023 | 4 | 1.4917 | 1.3750 | -1.5903 | 8.0940 | -9.6843 |
| ended_cycle_024 | 1 | 0.9333 | 0.9333 | -2.0000 | 6.7396 | -8.7396 |
| failure | 6297 | 5.9682 | 1.9667 | -1.4144 | 15.8777 | -17.2921 |
| failure_1_to_5s | 2277 | 2.3607 | 2.0500 | -1.4439 | 10.2220 | -11.6659 |
| failure_over_5s | 1925 | 16.1998 | 15.0667 | -0.7424 | 32.9415 | -33.6839 |
| failure_up_to_1s | 2095 | 0.4876 | 0.4000 | -2.0000 | 6.3454 | -8.3454 |
| full_safe | 928 | 32.8167 | 32.8167 | -0.8579 | 41.6461 | -42.5040 |
| updates_400_424 | 443 | 22.8990 | 26.0667 | -1.2709 | 37.2679 | -38.5388 |
| updates_425_449 | 745 | 25.6142 | 32.8167 | -1.0046 | 36.4280 | -37.4326 |
| updates_450_474 | 696 | 18.6536 | 17.9083 | -0.9542 | 34.4032 | -35.3574 |
| updates_475_499 | 5341 | 4.8354 | 1.5000 | -1.4468 | 13.3001 | -14.7469 |

실패 원인별 건수(중복 가능): {"guitar_rotation": 396, "guitar_displacement": 5962, "joint_speed": 23, "foot_displacement": 4}

| 동일 환경 비교 | 환경 수 | 첫 안전 전곡 길이→실패 길이(s) | 첫 안전 전곡 비용→실패 비용 |
|---|---:|---|---|
| first_failure_in_window | 996 | 32.8167→18.2872 | 17.1427→36.4926 |
| last_failure_in_window | 996 | 32.8167→2.0931 | 17.1427→9.6900 |

비용 밀도 보정용 관측 분포(cost/s): `{"window_full_safe": {"count": 928, "mean": 1.26905341916313, "minimum": 0.35275189509665433, "p25": 0.816157666967265, "median": 1.0606755091491356, "p75": 1.4643715722358668, "p90": 2.133432398961243, "p95": 2.5723118430893686, "p99": 4.519919587344072, "maximum": 7.291987909769394}, "first_full_safe_per_environment": {"count": 1024, "mean": 0.5151679549017876, "minimum": 0.017617949378738673, "p25": 0.23547183323051796, "median": 0.41611817719792277, "p75": 0.6907600046354481, "p90": 0.9866861602023751, "p95": 1.2542094632173442, "p99": 1.8962940593853128, "maximum": 4.187217080817118}, "definition": "Completed full-safe episode total cost / duration_s; units cost per second, not per control tick", "scope": "Observed policy/state cost density; not an estimate of unavoidable or counterfactual remaining cost"}`

원래 첫 안전 전곡과 최근 실패를 비교하면 좋은 완주 정책이 항상 실패보다 불리한 것은 아닙니다. 현재의 고비용 궤적을 일찍 끝내 손실을 줄일 가능성과, 좋은 완주 정책의 가치가 더 높다는 사실은 함께 성립할 수 있습니다.

해석의 한계와 코드 경로:

- Failure terminates the current song; the collector zeros terminal bootstrap and resets that environment. Future song rewards and costs do not occur in that episode.
- Failure adds reward -2 and cost +5 to the failure tick, with positive reward suppressed; accumulated cost before failure remains charged.
- Actual PPO combines reward and cost advantages, using reward gamma .99, cost gamma1 and GAE lambda .95. R-C totals below are descriptive undiscounted proxies, not exact actor advantages or gradients.
- With fixed cost weight1 and episodic undiscounted cost, avoiding future large song cost by ending an episode is a real design risk; repeated resets can simultaneously worsen cost per transition.
- Full-safe and failed records come from different policies/times/visited states. Even same-environment comparisons do not establish a counterfactual continuation cost or prove the cause of a policy gradient.
- A shrinking failed episode duration and smaller total episode cost support the risk hypothesis; they do not identify whether the behavior is learned escape, loss of control, critic error, or another training effect.
- Cycle ordinal counts all ended episodes per environment, including failures. Ongoing episodes are excluded from the completed-episode distributions.
- No native failure claim, new penalty, or implementation change is inferred from increased policy failures.
