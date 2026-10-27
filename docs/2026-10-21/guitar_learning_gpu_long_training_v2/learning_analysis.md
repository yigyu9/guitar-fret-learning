# GPU 장기 학습 분석

분석 시점: 2026-10-20T19:12:35.612354+00:00

최종 실행 종료: True / 정상 완료: False

최종 보고서와 분석 스냅샷의 전이·업데이트 일치: True

PPO 반영 업데이트 530회, 전이 17367040개, 종료 에피소드 41756개입니다.

진행 중인 곡은 완주·실패 분모에 넣지 않습니다. 접촉 수치는 GPU 기하 후보이며 음향 성공이 아닙니다.

| 구간 | 업데이트 | 종료 에피소드 | 전곡 종료 | 물리 실패 | 단계 성공 | 평균 보상/전이 | 평균 비용/전이 | 손목 도달 | 접촉 후보 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 전체 | 530 | 41756 | 6534 | 35222 | 0 | -0.000855549 | 0.0283208 | 0.133532 | 0.00814254 |
| 처음 | 100 | 1037 | 1012 | 25 | 0 | 0.00730294 | 0.00720629 | 0.686236 | 0.0760086 |
| 마지막 | 100 | 34483 | 723 | 33760 | 0 | -0.0194758 | 0.0884872 | 0.032172 | 0.00123141 |
| 0–99 | 100 | 1037 | 1012 | 25 | 0 | 0.00730294 | 0.00720629 | 0.686236 | 0.0760086 |
| 100–199 | 100 | 2055 | 1893 | 162 | 0 | 0.00644805 | 0.0136735 | 0.759858 | 0.0709881 |
| 200–299 | 100 | 1308 | 1057 | 251 | 0 | 0.00147173 | 0.0131441 | 0.613138 | 0.0302958 |
| 300–399 | 100 | 2330 | 1636 | 694 | 0 | 0.000208117 | 0.0191237 | 0.507104 | 0.01162 |
| 400–499 | 100 | 7225 | 928 | 6297 | 0 | -0.00335775 | 0.0394874 | 0.168274 | 0.00636058 |
| 500–599 | 30 | 27801 | 8 | 27793 | 0 | -0.0553583 | 0.19155 | 0.00371671 | 9.5025e-05 |

커리큘럼 진행도: 처음 0 → 마지막 0.5 (최대 0.5).

물리 실패 원인별 건수: {"guitar_displacement": 34532, "guitar_rotation": 836, "joint_speed": 66, "foot_displacement": 13}.

| 구간 | KL | 보상 critic MSE | 비용 critic MSE | 보상 EV 평균 | 비용 EV 평균 | KL 재시도 |
|---|---:|---:|---:|---:|---:|---:|
| 처음 | 0.00673531 | 0.00492035 | 0.108496 | 0.139781 | 0.94713 | 1 |
| 마지막 | 0.0085297 | 0.0481318 | 3.2582 | 0.76524 | 0.869702 | 0 |
| 0–99 | 0.00673531 | 0.00492035 | 0.108496 | 0.139781 | 0.94713 | 1 |
| 100–199 | 0.0068399 | 0.0103345 | 0.276132 | 0.789052 | 0.969265 | 0 |
| 200–299 | 0.00790703 | 0.00904109 | 0.438993 | 0.921298 | 0.979537 | 0 |
| 300–399 | 0.00860169 | 0.0132261 | 0.915494 | 0.937804 | 0.979262 | 0 |
| 400–499 | 0.00896194 | 0.0357616 | 3.36991 | 0.847427 | 0.917789 | 0 |
| 500–599 | 0.00744776 | 0.0580189 | 1.24713 | 0.654707 | 0.819868 | 0 |

기록/반영 집계: `{"sampled": 17396736, "logged": 17396736, "durable": 17396736, "committed": 17367040, "discarded": 29696, "sampled_rows": 16989, "logged_rows": 16989, "durable_rows": 16989, "completed_members": 531, "encoded_bytes": 1177169794, "encode_s": 9.993630992481485, "compress_write_s": 62.411919169011526, "sync_s": 5.6219851723872125, "pending_rows": 0, "pending_transitions": 0, "unresolved_sampled": 0, "logged_not_committed": 29696, "compressed_bytes": 341656119, "closed": true, "failed": false, "member_control_ticks": 60, "timing_scope": "encode_s: row JSON/UTF8; compress_write_s: gzip create/write/finish; sync_s: file flush/fsync and initial directory sync; excludes metadata sidecar work; compressed_bytes is produced file bytes, not measured device IO; completed_members are closed and synced"}`

에피소드 로그 대조: `{"logged_episode_rows": 42874, "rows_from_committed_updates": 41756, "rows_without_committed_update_snapshot": 1118, "committed_update_episode_count": 41756, "noncommitted_failure_reasons": {"guitar_displacement": 1117, "guitar_rotation": 1, "foot_displacement": 1}}`

진행 중 파일 읽기: `{}`

분모와 해석:

- Reward/cost means are weighted by committed rollout transitions, not episodes.
- Episode fractions use ended episodes in committed updates; ongoing songs are excluded, not failures or successes.
- Wrist reach/contact fractions divide achieved notes by all target notes in each episode, including unreached future notes of failed episodes.
- All-ended and full-safe-only note fractions are separate. A PPO horizon boundary is not a song boundary.
- Failure reasons overlap; their counts can exceed failed episodes.
- KL scalar is the last accepted optimizer attempt; minibatch means use actual sample visits. Critic MSE uses full-rollout diagnostics; EV is the arithmetic mean of per-update EV.
- First and last windows overlap before twice the window size; update bins can contain partial windows.
- GPU loaded-body geometric contact candidates and stage success do not establish real string pressure or acoustic success.
- Logged episodes without a committed update snapshot are excluded. The final journal distinguishes sampled/logged/durable/committed/discarded transitions.
