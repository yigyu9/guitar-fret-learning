# 초기 기타 pose noise bank 검증

## 검증된 bank 범위와 단위

원자료 분석은 12/12 check, 두 eval 검증은 18/18 check 통과를 보고합니다. Eval1·eval4 모두 input closure unchanged 및 exit code 0입니다. 32개 제안 중 27개가 absolute-rotation envelope 검사에서 reject됐고, bank에는 원점 한 개와 noise pose 네 개가 남았습니다. 원점 외 translation envelope는 world x/y 각 ±5 mm, z 0–5 mm이고 rotation은 world rotation-vector의 각 성분 ±1°입니다. Rotation-vector 성분은 Euler angle이 아닙니다.

표는 저장된 bank 행의 실제 world translation (mm), world rotation-vector (deg), native SO(3) jitter, 최대 팔 q 변화, native palm 위치 오차입니다. 모든 행에서 fixed body/head/finger q는 정확히 유지되고 source-hull audit은 clear였습니다. 최대 SO(3) jitter는 1.0718°, 팔 24 joints의 최대 q 변화는 1.2436°, 최대 native palm 위치 오차는 0.0001717366 mm입니다. Source-hull clear는 source geometry 검사이며 native cooked geometry의 clearance 인증이 아닙니다.

| bank index | Δposition W (mm) | rotation-vector W (deg, x/y/z) | SO(3) jitter (deg) | max arm Δq (deg) | max native palm position error (mm) |
|---:|---|---|---:|---:|---:|
| 0 | 0, 0, 0 | 0, 0, 0 | 0.0000 | 0.0000 | 0.000000000 |
| 1 | −0.299, −3.674, 1.019 | −0.179, −0.642, 0.144 | 0.6824 | 1.1383 | 0.000106907 |
| 2 | 2.339, 4.584, 4.877 | 0.311, 0.547, −0.868 | 1.0718 | 0.6551 | 0.000112906 |
| 3 | −1.857, 2.555, 0.585 | 0.044, 0.427, −0.701 | 0.8218 | 0.5837 | 0.000171737 |
| 4 | −0.322, −0.579, 3.608 | −0.105, −0.868, 0.214 | 0.9003 | 1.2436 | 0.000112813 |

![저장된 bank 수치와 CP320 원본 대비 noisy 초기 native frame 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/artifacts_v1/initial_noise_bank_and_native_reference_v1.png)

## 실제 선택과 재생

Training/reset은 검증된 discrete bank에서 with-replacement 선택을 사용합니다. 이것은 continuous uniform noise 분포가 아닙니다. 아래 두 개별 비디오 평가는 `--eval-index 1`과 `--eval-index 4`의 고정 index 선택이며, 그 평가 안에서 무작위로 bank를 뽑지 않았습니다.

| 평가 | 선택한 bank 행 | Δposition W (mm) | world rotation-vector (deg) | validated max arm Δq (deg) | actual native palm position error max (mm) |
|---|---:|---|---|---:|---:|
| noise eval 1 | 1 (trial 17) | −0.299, −3.674, 1.019 | −0.179, −0.642, 0.144 | 1.1383 | 0.000106907 |
| noise eval 4 | 4 (trial 31) | −0.322, −0.579, 3.608 | −0.105, −0.868, 0.214 | 1.2436 | 0.000112813 |

각 평가는 동일한 새 smoke checkpoint를 model/RMS exact warm-start로 사용하지만 Adam과 counters는 fresh입니다. 검증에서는 두 평가의 checkpoint 동일성과 renderer가 state를 보존하는 점도 확인했습니다. 즉 CP320 원본 physical frame과의 그림 비교는 noise만 바꾼 통제 성능 비교가 아닙니다. 두 평가 모두 앞 2초 PREP에서는 hand-position reset IK만 적용하고, 이후는 기존 PD와 policy를 사용했습니다.

![noise eval 1과 eval 4의 전신·손 0초, 5초, 마지막 native frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/artifacts_v1/noise_eval1_eval4_native_frames_v1.png)

두 평가는 각각 전체 16.366667 physics seconds(3,928 physics steps, 982 controls, 492 frames; MP4 재생 16.4초)를 완료했습니다. 각 평가에서 music success는 0/42, strap 호출은 51,064회(13×3,928), 금지 API는 0회이며 safety violation은 없었습니다. 이는 initial response tool의 구동·진단 결과이지 음악 수행 성공이 아닙니다.

초기 hand-matching 검사는 통과했지만, 후반 기타의 큰 drift는 해결되지 않았습니다. 아래 수치는 각각 자기 초기 상태를 기준으로 한 actor-root world box 및 SO(3) 진단입니다. 두 평가의 결과는 pose noise만의 효과를 분리하지 않으며 안정화 성공을 뜻하지 않습니다.

| 평가 | actor-root box 밖 시간 | 최대 이탈 (m) | 평균 이탈 (m) | 자기 초기 orientation 대비 max SO(3) |
|---|---:|---:|---:|---:|
| noise eval 1 | 55.8045% | 0.457416 | 0.094066 | 94.0134° |
| noise eval 4 | 51.3238% | 0.404862 | 0.079887 | 89.7177° |

Actor-root box 값은 body-center 자연범위가 아니며, 자기 초기 SO(3)는 허용 orientation distance 인증이 아닙니다.

![noise eval 1 전신](/home/ajou/yigyu/3/docs/2026-10-12/video/initial_pose_noise_v1/noise1_whole_body.mp4)

![noise eval 1 손](/home/ajou/yigyu/3/docs/2026-10-12/video/initial_pose_noise_v1/noise1_hands.mp4)

![noise eval 4 전신](/home/ajou/yigyu/3/docs/2026-10-12/video/initial_pose_noise_v1/noise4_whole_body.mp4)

![noise eval 4 손](/home/ajou/yigyu/3/docs/2026-10-12/video/initial_pose_noise_v1/noise4_hands.mp4)

## 별도 reset probe와 업데이트

2-worker reset probe는 3회 native reset에서 index `[[2, 3], [1, 4], [0, 1]]`을 사용했고, native state와 ABI가 정확히 일치했습니다. 네 worker smoke update는 CUDA에서 실제 256 transition, optimizer 4회, final analytic KL 0.0196185를 기록했으며 RMS는 갱신되지 않았습니다. Reset probe, 단일 갱신 smoke 및 결정론 평가의 범위는 각각 다릅니다.

## 근거와 provenance

- [bank/native 수치 분석(12개 check)](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/analysis_v1.json)
- [noise eval 1 report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/eval_noise_1_v1/report.json)
- [noise eval 1 input 봉인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/eval_noise_1_v1/inputs_verified.json)
- [noise eval 4 report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/eval_noise_4_v1/report.json)
- [noise eval 4 input 봉인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/eval_noise_4_v1/inputs_verified.json)
- [두 eval 및 수치·native video SHA 검증(18개 check)](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/verification_v1.json)
- [네 영상 manifest](/home/ajou/yigyu/3/docs/2026-10-12/video/initial_pose_noise_v1/manifest.json)
- [산출물 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/artifacts_v1/provenance_v1.json)
