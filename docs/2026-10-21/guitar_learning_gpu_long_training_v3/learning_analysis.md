# GPU 장기 학습 분석

분석 시점: 2026-10-21T01:03:07.315811+00:00

최종 실행 종료: True / 정상 완료: True

최종 보고서와 분석 스냅샷의 전이·업데이트 일치: True

PPO 반영 업데이트 2000회, 전이 65536000개, 종료 에피소드 34069개입니다.

진행 중인 곡은 완주·실패 분모에 넣지 않습니다. 접촉 수치는 GPU 기하 후보이며 음향 성공이 아닙니다.

| 구간 | 업데이트 | 종료 에피소드 | 전곡 종료 | 물리 실패 | 전곡 과제 성공 | 평균 보상/전이 | 평균 비용/전이 | 손목 도달 | 접촉 후보 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 전체 | 2000 | 34069 | 31524 | 2545 | 0 | 0.00269199 | 0.0159257 | 0.451605 | 0.0323983 |
| 처음 | 100 | 1039 | 1000 | 39 | 0 | 0.0077946 | 0.00803128 | 0.682746 | 0.078017 |
| 마지막 | 100 | 1784 | 1753 | 31 | 0 | -0.00531658 | 0.00783771 | 0.583637 | 0.0430443 |
| 0–99 | 100 | 1039 | 1000 | 39 | 0 | 0.0077946 | 0.00803128 | 0.682746 | 0.078017 |
| 100–199 | 100 | 2055 | 1917 | 138 | 0 | 0.0071502 | 0.013325 | 0.695544 | 0.0644151 |
| 200–299 | 100 | 1241 | 1078 | 163 | 0 | 0.00298465 | 0.0165978 | 0.464058 | 0.0260262 |
| 300–399 | 100 | 2092 | 1858 | 234 | 0 | 0.00409963 | 0.01739 | 0.400995 | 0.027582 |
| 400–499 | 100 | 1927 | 1758 | 169 | 0 | 0.00337361 | 0.0159945 | 0.454097 | 0.0272715 |
| 500–599 | 100 | 1621 | 1180 | 441 | 0 | 0.00256902 | 0.0327152 | 0.349802 | 0.0145939 |
| 600–699 | 100 | 2022 | 1606 | 416 | 0 | 0.0029445 | 0.0319064 | 0.366196 | 0.0182913 |
| 700–799 | 100 | 1841 | 1660 | 181 | 0 | 0.00220201 | 0.0208487 | 0.382174 | 0.0199437 |
| 800–899 | 100 | 1589 | 1410 | 179 | 0 | 0.00294687 | 0.0223181 | 0.363507 | 0.0130844 |
| 900–999 | 100 | 1845 | 1670 | 175 | 0 | 0.0031305 | 0.0212474 | 0.376726 | 0.0135178 |
| 1000–1099 | 100 | 1532 | 1451 | 81 | 0 | 0.00342208 | 0.0174696 | 0.401105 | 0.0133958 |
| 1100–1199 | 100 | 1816 | 1737 | 79 | 0 | 0.00372642 | 0.0171203 | 0.373578 | 0.0125584 |
| 1200–1299 | 100 | 1730 | 1701 | 29 | 0 | 0.00338149 | 0.0144447 | 0.367216 | 0.0214736 |
| 1300–1399 | 100 | 1573 | 1542 | 31 | 0 | 0.00346412 | 0.0126046 | 0.361055 | 0.0352592 |
| 1400–1499 | 100 | 1752 | 1730 | 22 | 0 | 0.00389808 | 0.0108934 | 0.363337 | 0.0421182 |
| 1500–1599 | 100 | 1740 | 1720 | 20 | 0 | 0.00352578 | 0.00864984 | 0.408132 | 0.0459341 |
| 1600–1699 | 100 | 1562 | 1540 | 22 | 0 | 0.00506811 | 0.00931688 | 0.522636 | 0.0512833 |
| 1700–1799 | 100 | 1742 | 1693 | 49 | 0 | -0.000530495 | 0.010124 | 0.61505 | 0.0530785 |
| 1800–1899 | 100 | 1566 | 1520 | 46 | 0 | -0.00599473 | 0.00967858 | 0.575742 | 0.0419454 |
| 1900–1999 | 100 | 1784 | 1753 | 31 | 0 | -0.00531658 | 0.00783771 | 0.583637 | 0.0430443 |

| 구간 | 원래 비용/전이 | 남은 곡 실패 비용/전이 | 총비용/전이 |
|---|---:|---:|---:|
| 전체 | 0.0127289 | 0.00319685 | 0.0159257 |
| 처음 | 0.00743596 | 0.000595322 | 0.00803128 |
| 마지막 | 0.0068778 | 0.000959905 | 0.00783771 |
| 0–99 | 0.00743596 | 0.000595322 | 0.00803128 |
| 100–199 | 0.0112223 | 0.00210269 | 0.013325 |
| 200–299 | 0.0123274 | 0.0042704 | 0.0165978 |
| 300–399 | 0.0109885 | 0.00640152 | 0.01739 |
| 400–499 | 0.0121475 | 0.00384702 | 0.0159945 |
| 500–599 | 0.020435 | 0.0122802 | 0.0327152 |
| 600–699 | 0.0217858 | 0.0101206 | 0.0319064 |
| 700–799 | 0.0165278 | 0.00432086 | 0.0208487 |
| 800–899 | 0.0174355 | 0.00488258 | 0.0223181 |
| 900–999 | 0.0162346 | 0.00501282 | 0.0212474 |
| 1000–1099 | 0.0155274 | 0.00194224 | 0.0174696 |
| 1100–1199 | 0.0153857 | 0.00173459 | 0.0171203 |
| 1200–1299 | 0.0137313 | 0.000713476 | 0.0144447 |
| 1300–1399 | 0.0118033 | 0.000801239 | 0.0126046 |
| 1400–1499 | 0.0103069 | 0.000586522 | 0.0108934 |
| 1500–1599 | 0.00814335 | 0.00050649 | 0.00864984 |
| 1600–1699 | 0.00860399 | 0.000712891 | 0.00931688 |
| 1700–1799 | 0.0089987 | 0.00112531 | 0.010124 |
| 1800–1899 | 0.00865841 | 0.00102018 | 0.00967858 |
| 1900–1999 | 0.0068778 | 0.000959905 | 0.00783771 |

커리큘럼 진행도: 처음 0 → 마지막 1 (최대 1).

물리 실패 원인별 건수: {"guitar_displacement": 1791, "guitar_rotation": 800, "foot_displacement": 8, "joint_speed": 16}.

| 구간 | KL | 보상 critic MSE | 비용 critic MSE | 보상 EV 평균 | 비용 EV 평균 | KL 재시도 |
|---|---:|---:|---:|---:|---:|---:|
| 처음 | 0.00631682 | 0.00629985 | 0.447574 | 0.299682 | 0.90046 | 1 |
| 마지막 | 0.005178 | 0.0214975 | 0.621133 | 0.961651 | 0.990727 | 0 |
| 0–99 | 0.00631682 | 0.00629985 | 0.447574 | 0.299682 | 0.90046 | 1 |
| 100–199 | 0.00758355 | 0.00588848 | 1.62431 | 0.85473 | 0.919484 | 0 |
| 200–299 | 0.00820234 | 0.0128391 | 2.71749 | 0.877642 | 0.939685 | 0 |
| 300–399 | 0.00873223 | 0.0102859 | 4.06954 | 0.879368 | 0.968349 | 0 |
| 400–499 | 0.00600567 | 0.0114634 | 3.6075 | 0.902368 | 0.984039 | 1 |
| 500–599 | 0.00493386 | 0.0165219 | 9.12895 | 0.907993 | 0.980793 | 0 |
| 600–699 | 0.00456467 | 0.017112 | 7.83814 | 0.889437 | 0.983946 | 0 |
| 700–799 | 0.00468097 | 0.0187393 | 3.50447 | 0.949031 | 0.992241 | 0 |
| 800–899 | 0.00472747 | 0.0171553 | 3.44966 | 0.965487 | 0.993145 | 0 |
| 900–999 | 0.0049483 | 0.00843155 | 2.38671 | 0.97024 | 0.996054 | 0 |
| 1000–1099 | 0.0047666 | 0.00542123 | 1.15886 | 0.977925 | 0.998437 | 0 |
| 1100–1199 | 0.00483486 | 0.0123248 | 1.18347 | 0.963964 | 0.998093 | 0 |
| 1200–1299 | 0.005083 | 0.0129953 | 0.752481 | 0.980601 | 0.9969 | 0 |
| 1300–1399 | 0.00484272 | 0.00902073 | 0.601016 | 0.987898 | 0.996949 | 0 |
| 1400–1499 | 0.00469007 | 0.00991947 | 0.370073 | 0.987968 | 0.99609 | 0 |
| 1500–1599 | 0.00509763 | 0.00816651 | 0.404349 | 0.986778 | 0.98257 | 0 |
| 1600–1699 | 0.0052711 | 0.00670232 | 0.439374 | 0.983732 | 0.979456 | 0 |
| 1700–1799 | 0.00563956 | 0.016705 | 1.06892 | 0.954714 | 0.982801 | 0 |
| 1800–1899 | 0.00521873 | 0.0206721 | 0.62526 | 0.958699 | 0.99209 | 0 |
| 1900–1999 | 0.005178 | 0.0214975 | 0.621133 | 0.961651 | 0.990727 | 0 |

기록/반영 집계: `{"sampled": 65536000, "logged": 65536000, "durable": 65536000, "committed": 65536000, "discarded": 0, "sampled_rows": 64000, "logged_rows": 64000, "durable_rows": 64000, "completed_members": 2000, "encoded_bytes": 3985127845, "encode_s": 35.67418583633844, "compress_write_s": 233.40125926944893, "sync_s": 21.128281600773335, "pending_rows": 0, "pending_transitions": 0, "unresolved_sampled": 0, "logged_not_committed": 0, "compressed_bytes": 1290543474, "closed": true, "failed": false, "member_control_ticks": 60, "timing_scope": "encode_s: row JSON/UTF8; compress_write_s: gzip create/write/finish; sync_s: file flush/fsync and initial directory sync; excludes metadata sidecar work; compressed_bytes is produced file bytes, not measured device IO; completed_members are closed and synced"}`

에피소드 로그 대조: `{"logged_episode_rows": 34069, "rows_from_committed_updates": 34069, "committed_update_episode_count": 34069, "noncommitted_failure_reasons": {}}`

진행 중 파일 읽기: `{}`

분모와 해석:

- Reward/cost means are weighted by committed rollout transitions, not episodes.
- mean_remaining_song_failure_cost sums the failure extra charged in that rollout and divides by its committed transitions; mean_original_cost subtracts that extra from total cost and retains the original physical cost and terminal +5.
- Episode cost-component means use ended episodes, whose original cost can span multiple updates; they are not per-transition costs. failure_rate_cost_per_s is the configured rate, not another cost to add.
- Episode fractions use ended episodes in committed updates; ongoing songs are excluded, not failures or successes.
- For this GPU left-hand run, song.stage_success counts full-safe timeline-complete episodes with left_success_count equal to all67 target notes. This is whole-song task success, not a curriculum promotion count or acoustic success; right-hand criteria differ.
- Wrist reach/contact fractions divide achieved notes by all target notes in each episode, including unreached future notes of failed episodes.
- All-ended and full-safe-only note fractions are separate. A PPO horizon boundary is not a song boundary.
- Failure reasons overlap; their counts can exceed failed episodes.
- KL scalar is the last accepted optimizer attempt; minibatch means use actual sample visits. Critic MSE uses full-rollout diagnostics; EV is the arithmetic mean of per-update EV.
- First and last windows overlap before twice the window size; update bins can contain partial windows.
- GPU loaded-body geometric contact candidates and stage success do not establish real string pressure or acoustic success.
- Logged episodes without a committed update snapshot are excluded. The final journal distinguishes sampled/logged/durable/committed/discarded transitions.
