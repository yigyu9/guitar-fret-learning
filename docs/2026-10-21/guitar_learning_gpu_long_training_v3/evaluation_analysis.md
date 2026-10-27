# 초기·최종 고정 정책 첫 곡 평가

검증을 통과한 실제 평가만 집계한다. 전체 첫 곡은 각1024개이며 안전 완주는 별도 분모다.

| 정책/집단 | 곡 수 | 손목 도달 | 접촉 후보 | 달성 음/67 | 전곡 과제 성공 | 원비용 | 남은곡 실패비용 |
|---|---:|---:|---:|---:|---:|---:|---:|
| initial/all_first | 1024 | 0.72984 | 0.06743 | 3.96875 | 0 | 6.12916 | 0.00000 |
| initial/full_safe_first | 1024 | 0.72984 | 0.06743 | 3.96875 | 0 | 6.12916 | 0.00000 |
| initial/physical_failure_first | 0 | — | — | — | 0 | — | — |

initial: curriculum=0.0, 시간축 완주=1024, 물리 실패=0, 성공 없는 음 수={'all_first': 59, 'full_safe_first': 59}.

| 정책/집단 | 곡 수 | 손목 도달 | 접촉 후보 | 달성 음/67 | 전곡 과제 성공 | 원비용 | 남은곡 실패비용 |
|---|---:|---:|---:|---:|---:|---:|---:|
| final/all_first | 1024 | 0.70842 | 0.06731 | 4.23242 | 0 | 5.52277 | 0.09619 |
| final/full_safe_first | 1023 | 0.70876 | 0.06738 | 4.23656 | 0 | 5.51101 | 0.00000 |
| final/physical_failure_first | 1 | 0.35821 | 0.00000 | 0.00000 | 0 | 17.55462 | 98.50000 |

final: curriculum=1.0, 시간축 완주=1023, 물리 실패=1, 성공 없는 음 수={'all_first': 52, 'full_safe_first': 52}.

## all_first 음별 변화

| 방향 | 실제 음 ID | 현(1=high-e) | 프렛 | 초기 성공률 | 최종 성공률 | 증감 |
|---|---|---:|---:|---:|---:|---:|
| top5_increases | event-000051/string-3/note-52 | 3 | 6 | 0.20996 | 0.78223 | +0.57227 |
| top5_increases | event-000041/string-3/note-41 | 3 | 6 | 0.28711 | 0.78613 | +0.49902 |
| top5_increases | event-000061/string-3/note-62 | 3 | 6 | 0.32812 | 0.79199 | +0.46387 |
| top5_increases | event-000062/string-3/note-63 | 3 | 6 | 0.34668 | 0.77148 | +0.42480 |
| top5_increases | event-000063/string-3/note-64 | 3 | 6 | 0.34082 | 0.76172 | +0.42090 |
| top5_decreases | event-000001/string-2/note-1 | 2 | 5 | 0.82422 | 0.03320 | -0.79102 |
| top5_decreases | event-000007/string-2/note-7 | 2 | 5 | 0.82324 | 0.05859 | -0.76465 |
| top5_decreases | event-000008/string-2/note-8 | 2 | 5 | 0.80859 | 0.05762 | -0.75098 |

## full_safe_first 음별 변화

| 방향 | 실제 음 ID | 현(1=high-e) | 프렛 | 초기 성공률 | 최종 성공률 | 증감 |
|---|---|---:|---:|---:|---:|---:|
| top5_increases | event-000051/string-3/note-52 | 3 | 6 | 0.20996 | 0.78299 | +0.57303 |
| top5_increases | event-000041/string-3/note-41 | 3 | 6 | 0.28711 | 0.78690 | +0.49979 |
| top5_increases | event-000061/string-3/note-62 | 3 | 6 | 0.32812 | 0.79277 | +0.46464 |
| top5_increases | event-000062/string-3/note-63 | 3 | 6 | 0.34668 | 0.77224 | +0.42556 |
| top5_increases | event-000063/string-3/note-64 | 3 | 6 | 0.34082 | 0.76246 | +0.42164 |
| top5_decreases | event-000001/string-2/note-1 | 2 | 5 | 0.82422 | 0.03324 | -0.79098 |
| top5_decreases | event-000007/string-2/note-7 | 2 | 5 | 0.82324 | 0.05865 | -0.76459 |
| top5_decreases | event-000008/string-2/note-8 | 2 | 5 | 0.80859 | 0.05767 | -0.75092 |

전체67음 비교와 비용·보상·길이·종료 원인 집계는 evaluation_analysis.json에 있다.

해석 범위:

- All-first denominator1024 includes failed/unreached future notes; full-safe-first uses each checkpoint's own safe whole first-song cohort, whose membership can differ.
- Same song and prepared pose; each checkpoint restores its own curriculum and corresponding observations/weights. Reward is not a common fixed-weight metric.
- Not independent seeds, held-out generalization, calibrated string pressure, or acoustic success. Zero-success notes refer only to these evaluation cohorts.
- New evaluation ledgers do not reconstruct missing per-note TRAIN history.
- No-PPO evidence is limited to static evaluation-source inspection plus unchanged pinned checkpoint files; no independent runtime optimizer trace is available.
