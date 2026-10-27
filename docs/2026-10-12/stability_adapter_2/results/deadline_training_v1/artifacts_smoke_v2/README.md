# Deadline smoke v2 산출물

이 문서는 2026-10-12 deadline pilot의 실제 측정 부분집합을 시각화한다. `smoke_v2/report.json`은 256 transitions의 PPO update 1회가 완료됐고, production reward v4 인증은 아니라고 기록한다. 학습은 CUDA, native episode는 CPU PhysX이며, teacher checkpoint는 F035000/S010000이다.

## 실행 요약

| 항목 | 관측값 |
|---|---:|
| profile | `deadline_pilot_v1` |
| 학습 update / transitions | 1 / 256 |
| update 기록 wall time | 15.877 s |
| initial / post-update native episode | 각 1회, 각 3928 physics steps (16.3667 s) |
| joint events / success / accepted crossings | 42 / 0 / 0 |
| teacher checkpoints | F035000 / S010000, 각각 862회 실제 추론 |
| production reward 인증 | 아니오 |

두 native episode는 같은 song horizon까지 완료했다. 이는 작은 deadline pilot 측정이며, full reward v4 certification이나 연주·안정성 성공 판정이 아니다.

## Native Isaac Gym 렌더 프레임

아래는 저장된 native camera capture의 첫 프레임과 마지막 프레임이다. 렌더 이미지이며 데이터 그래프와 구분한다.

### initial 000000

첫 프레임 — [원본 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_v2/evaluations/initial_000000/native/episode_0001/media/frames/whole_body/00000.png)

![initial_000000 첫 native Isaac Gym 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_v2/evaluations/initial_000000/native/episode_0001/media/frames/whole_body/00000.png)

마지막 프레임 — [원본 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_v2/evaluations/initial_000000/native/episode_0001/media/frames/whole_body/00491.png)

![initial_000000 마지막 native Isaac Gym 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_v2/evaluations/initial_000000/native/episode_0001/media/frames/whole_body/00491.png)

### update 000001

첫 프레임 — [원본 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_v2/evaluations/update_000001/native/episode_0001/media/frames/whole_body/00000.png)

![update_000001 첫 native Isaac Gym 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_v2/evaluations/update_000001/native/episode_0001/media/frames/whole_body/00000.png)

마지막 프레임 — [원본 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_v2/evaluations/update_000001/native/episode_0001/media/frames/whole_body/00491.png)

![update_000001 마지막 native Isaac Gym 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_v2/evaluations/update_000001/native/episode_0001/media/frames/whole_body/00491.png)

## 실제 episode 영상

각 환경 녹화는 30 fps, 492 frames, 16.4초 MP4이다. native report의 물리 경과는 16.3667초다.

### initial 000000 — 전신

![initial_000000 whole body](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_v2/evaluations/initial_000000/native/episode_0001/media/whole_body.mp4)

[전신 MP4 원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_v2/evaluations/initial_000000/native/episode_0001/media/whole_body.mp4)

### initial 000000 — 손 확대

![initial_000000 hands](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_v2/evaluations/initial_000000/native/episode_0001/media/hands.mp4)

[손 확대 MP4 원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_v2/evaluations/initial_000000/native/episode_0001/media/hands.mp4)

### update 000001 — 전신

![update_000001 whole body](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_v2/evaluations/update_000001/native/episode_0001/media/whole_body.mp4)

[전신 MP4 원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_v2/evaluations/update_000001/native/episode_0001/media/whole_body.mp4)

### update 000001 — 손 확대

![update_000001 hands](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_v2/evaluations/update_000001/native/episode_0001/media/hands.mp4)

[손 확대 MP4 원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_v2/evaluations/update_000001/native/episode_0001/media/hands.mp4)

## 실제 측정 위치 궤적

이 그림은 Isaac 렌더가 아니라 native `trace.json`의 `position_W_m` 데이터 그래프다. 좌표는 기타 actor-root의 W 프레임 위치(m), 시간은 `physics_step / 240`초다. 파선 상자는 brief의 actor-root 범위 X=[−0.50, −0.15], Y=[−0.15, 0.15], Z=[0.65, 0.883738] m를 표시한다. 검은 별은 기존 nominal reference pW=(−0.230415, 0.086712, 0.700973) m다. Z 상한은 initial human body-state slot 11의 측정 Z=0.8837384 m에 대응한다. 상자는 관측 범위 시각화이며 성공 판정이 아니다.

![두 조건 native actor-root 위치 궤적](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/artifacts_smoke_v2/position_paths_3d.png)

## 요약 비교

| 조건 | physics steps | physics 시간 | return | fixed events | joint success | accepted crossings | 완료 |
|---|---:|---:|---:|---:|---:|---:|---|
| initial 000000 | 3928 | 16.3667 s | -397.140450 | 42 | 0 | 0 | full horizon |
| update 000001 | 3928 | 16.3667 s | -397.744697 | 42 | 0 | 0 | full horizon |

두 조건 모두 42 events에서 성공 0회, accepted crossing 0회다. 이 결과는 보상 인증 또는 음악적 성공으로 해석하지 않는다.

## 원자료

각 condition의 `report.json`, `trace.json`, `controls.json`, `joint_events.json`, `initial_values.json`, `media/capture.json`, `media/videos.json`을 기준으로 표와 그림을 만들었다. 입력 해시 전후 비교는 `input_hashes.json`에 남겼다.
