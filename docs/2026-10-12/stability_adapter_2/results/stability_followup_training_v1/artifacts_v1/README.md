# CP1과 CP86 native follow-up 비교

## 핵심 결과

root 분석은 CP1 이후 85회 추가 update를 검증했습니다. 이 checkpoint snapshot은 총 86 updates, 22,016 transitions, 학습 중 완주 episode 22개를 포함합니다. 체크포인트 전후 actor와 critic은 실제로 변경됐고 RMS는 고정됐습니다. 이 보고서는 CP1과 CP86 한 쌍을 비교합니다. 별도 `long_on_v1` 학습은 계속 진행 중이며 여기서 이후 완료나 성공을 주장하지 않습니다.

두 checkpoint 평가는 같은 native 초기 상태·PD 설정·ABI·고정 RMS를 사용했고, 각각 16.3667초, 982 control steps, 3,928 physics steps, 492 frames를 완주했습니다. 두 평가 모두 safety termination 0, 음악/joint success 0, accepted crossings 0입니다. 실제 crossing event는 양쪽 3회였으며 모두 `wrong_string`으로 분류되어 accepted crossing이 아니었습니다.

| 항목 | CP1 · update 1 | CP86 · update 86 | 관측 |
|---|---:|---:|---|
| actor-root world-box 범위 밖 비율 | 45.82485% | 49.89817% | 악화 |
| 최대 범위 밖 거리 | 47.3142cm | 41.9738cm | 감소 |
| 평균 범위 밖 거리 | 9.40894cm | 8.31205cm | 감소 |
| 범위 밖 10cm 초과 최초 시각 | 13.2167초 | 13.2667초 | 0.05초 차이 |
| 초기 기타 root quaternion 대비 최대 SO(3) 회전 | 95.8645° | 88.9132° | 감소 |
| PLAY 중 진단 press-cell 표시 frame | 427 / 3448 | 466 / 3448 | 진단 표시만 증가 |
| 음악 성공 / accepted crossing / safety | 0 / 0 / 0 | 0 / 0 / 0 | 성공 미확인 |

최대·평균 이탈 거리는 줄었지만, 전체 범위 밖 비율은 4.07%p 나빠졌고 10cm 초과 시작 시각 차이는 0.05초뿐입니다. 진단 press-cell은 기타 현을 정확히 누른 사실의 확인값이 아닙니다. 이 한 쌍에서 안정성·음악 성공 또는 일반화 개선을 판정하지 않습니다.

## Native 프레임과 시간 곡선

![CP1과 CP86 전신 native frame 비교: 0초·2초·13초·종료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/artifacts_v1/cp1_cp86_whole_body_frames_v1.png)

![CP1과 CP86 손 native frame 비교: 0초·2초·13초·종료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/artifacts_v1/cp1_cp86_hands_frames_v1.png)

![CP1과 CP86 기타 actor-root world-box 위치 이탈 거리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/artifacts_v1/cp1_cp86_outside_distance_v1.png)

![CP1과 CP86 초기 기타 root quaternion 대비 SO(3) orientation 회전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/artifacts_v1/cp1_cp86_guitar_orientation_v1.png)

actor-root world-box는 기타 actor의 world 좌표 위치 허용 상자입니다. 이는 body-center 기준 자연스러움 범위가 아닙니다. SO(3) 회전은 기타 root quaternion을 초기 quaternion과 비교한 orientation 변화이며 scalar 관절 q 변화와 다른 양입니다.

## 훈련 중 stochastic episode return

![학습 중 정책이 바뀌는 stochastic rollout episode별 return: 완주한 22개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/artifacts_v1/stochastic_episode_returns_v1.png)

이 값들은 학습 도중 정책이 계속 갱신되는 stochastic rollout의 완주 episode return입니다. 아래 CP1/CP86 표에 적은 deterministic native 평가의 저장 ledger return과 다른 자료이며, 개별 값이나 평균을 음악 성공으로 해석하지 않습니다.

## Deterministic 평가 return 구성

root 저장 reward ledger를 합산한 평가 episode return은 CP1 −41.04112, CP86 −35.68874이며 저장된 보고 값과 재구성 합의 오차는 0입니다. 아래 각 성분은 학습 reward의 scaled ledger 합입니다.

| scaled reward 성분 | CP1 | CP86 |
|---|---:|---:|
| 위치 | −31.70159 | −27.43965 |
| 회전 상한 proxy | −7.29025 | −6.20116 |
| body | −0.000589 | −0.000568 |
| target rate | −0.001496 | −0.001511 |
| sounding | 0.00000 | +0.00100 |
| fret approach | +0.02997 | +0.02731 |
| pick approach | +0.09783 | +0.10084 |
| actual crossings | −0.07500 | −0.07500 |
| fixed event deadlines | −2.10000 | −2.10000 |
| floor/safety settlement adjustment | 0.00000 | 0.00000 |
| **합계** | **−41.04112** | **−35.68874** |

## 원본 및 archive 영상

아래 native MP4는 분석 원본을 그대로 연결합니다. 오른쪽 archive 링크들은 기존 복사본이며 manifest 및 SHA 대조를 통과했습니다.

| 평가·시점 | 원본 전신 | 원본 손 | archive 사본 |
|---|---|---|---|
| CP1 · update 000001 | ![CP1 전신 native 원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/smoke_on_v2/evaluations/update_000001/native/episode_0001/media/whole_body.mp4) | ![CP1 손 native 원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/smoke_on_v2/evaluations/update_000001/native/episode_0001/media/hands.mp4) | [archive_v2 전신](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v2/stability_adapter_2/results/stability_support_nominal_v1/smoke_on_v2/evaluations/update_000001/native/episode_0001/media/whole_body.mp4) · [손](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v2/stability_adapter_2/results/stability_support_nominal_v1/smoke_on_v2/evaluations/update_000001/native/episode_0001/media/hands.mp4) |
| CP86 · update 000086 | ![CP86 전신 native 원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/long_on_v1/evaluations/update_000086/native/episode_0001/media/whole_body.mp4) | ![CP86 손 native 원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/long_on_v1/evaluations/update_000086/native/episode_0001/media/hands.mp4) | [archive_v3 전신](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v3/update_000086_whole_body.mp4) · [손](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v3/update_000086_hands.mp4) |

## 무결성·범위

수치는 root [analysis_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/analysis_v1.json) 및 저장 ledger 분해 [reward_analysis_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/reward_analysis_v1.json)을 기준으로 했습니다. producer 및 입력 전후 SHA, 원본·archive 영상 hash, 출력 SHA는 [provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/artifacts_v1/followup_comparison_provenance_v1.json)에 있습니다. 실제 변경 파일과 본문 줄은 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_followup_training_v1/artifacts_v1/CHANGED_FILES.md)에 기록합니다.
