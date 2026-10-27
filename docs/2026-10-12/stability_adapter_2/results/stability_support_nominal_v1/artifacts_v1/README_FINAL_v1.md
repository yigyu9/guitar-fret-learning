# Q nominal support guard · native 결과 비교

## 결과 요약

root 검증에서 Q smoke v2 실행은 exit 0으로 끝났고, CUDA 학습 프로파일에서 1회 update와 256 transitions를 처리했습니다. optimizer 6회 적용 후 KL guard에 따라 update가 끝났으며 최종 KL은 0.01992567256입니다. RMS는 동결 상태를 유지했습니다. 이 검증은 한 번의 update 실행을 확인한 것이며 일반화된 학습 성공이나 안정성 성공을 뜻하지 않습니다.

업데이트 조건은 초기 mean-zero actor, 새 critic Adam, RMS 동결, guarded KL이며 요청 시작 learning rate는 3e-5였습니다. KL guard가 후보 step을 제한했으므로 시작 LR이 모든 optimizer step에 그대로 적용됐다는 뜻은 아닙니다.

가장 눈에 띄는 결과는 **음악 성공이 세 평가 모두 0이고, Q CP1의 최대 위치 범위 밖 거리가 Q 초기보다 커졌다는 점**입니다. Q 초기 0.3382m에서 Q CP1 0.4731m로 0.1349m 악화했습니다. 범위 밖 비율은 55.19%에서 45.82%로 낮아졌지만, 최대 이탈 악화와 음악 성공 0을 함께 보면 개선 성공으로 판정할 수 없습니다. 세 평가 모두 full horizon 16.3667초/492 frames 완료, accepted crossings 0, safety 위반 없음입니다.

| 평가 | 설명 | 범위 밖 비율 | 최대 범위 밖 거리 | 최대 root 이동 | 초기 q 대비 최대 SO(3) 회전 | 음악 성공 / crossing |
|---|---|---:|---:|---:|---:|---:|
| P 초기 | 이전 P 조건, 0 update | 85.44% | 0.4650m | 0.5694m | 94.02° | 0 / 0 |
| Q 초기 | nominal support guard 조건, 0 update | 55.19% | 0.3382m | 0.4488m | 91.24° | 0 / 0 |
| Q CP1 | Q 조건에서 1 update 후 | 45.82% | **0.4731m** | 0.5789m | 95.86° | 0 / 0 |

## 비교 그림

![P 초기, Q 초기, Q CP1의 전신 native frame 비교: 0초, 2초, 종료 직전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/artifacts_v1/qp_final_whole_body_frames_v1.png)

![P 초기, Q 초기, Q CP1의 손 native frame 비교: 0초, 2초, 종료 직전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/artifacts_v1/qp_final_hands_frames_v1.png)

![세 native 평가의 시간별 위치 범위 밖 거리. 범례는 그래프 영역 바깥에 표시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/artifacts_v1/qp_final_outside_over_time_v1.png)

## 영상

P 초기 비교 원본:

![P 초기 평가 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/smoke_on_v1/evaluations/initial_000000/native/episode_0001/media/whole_body.mp4)

![P 초기 평가 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/smoke_on_v1/evaluations/initial_000000/native/episode_0001/media/hands.mp4)

Q v2 초기 평가와 CP1 비교 영상:

![Q 초기 평가 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/smoke_on_v2/evaluations/initial_000000/native/episode_0001/media/whole_body.mp4)

![Q 초기 평가 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/smoke_on_v2/evaluations/initial_000000/native/episode_0001/media/hands.mp4)

![Q CP1 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/smoke_on_v2/evaluations/update_000001/native/episode_0001/media/whole_body.mp4)

![Q CP1 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/smoke_on_v2/evaluations/update_000001/native/episode_0001/media/hands.mp4)

## 조건 효과와 단일 update 효과의 구분

P 초기와 Q 초기의 비교는 이전 P 조건과 nominal support guard 조건의 **초기 평가 차이**입니다. Q는 팔 24개 teacher action을 nominal preload 기준 ±0.15rad, 왼손 엄지 5개를 ±0.10rad 범위로 후처리 제한합니다. 이 과정은 실제 관절 q를 고정하지 않으며 teacher 원본/baseline action을 그대로 재현하지 않습니다. 기존 adapter의 body/head/arm/finger residual cap은 0.03/0.10/0.30/0.20rad입니다. 따라서 P→Q 초기 차이는 이 제한 조건을 포함한 실행 조건 비교이지, 학습 update의 효과가 아닙니다.

Q 초기와 Q CP1의 비교는 **단일 update 전후의 한 번씩의 native 평가**입니다. 범위 밖 비율은 내려갔지만 최대 범위 밖 거리는 0.1349m 증가했고 음악 성공은 여전히 0입니다. 이 한 쌍의 측정만으로 update의 안정화 효과나 일반적 개선을 주장하지 않습니다.

별도 `long_on_v1` 장기 실험은 root가 진행 중이라고 알렸습니다. 아직 결과가 확정되지 않았으므로 이 문서는 그 실험의 완료나 성공을 주장하지 않습니다.

## 근거와 무결성 기록

수치와 native 상태 비교는 [root 비교 JSON v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/comparison_v2.json) 및 [root runtime 검증 v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/runtime_verification_v2.json)에 따릅니다. 그림 생성기는 [최종 비교 producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/artifacts_v1/build_qp_final_comparison_v1.py)이며 그림/원자료 입력 SHA는 [그림 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/artifacts_v1/qp_final_comparison_provenance_v1.json)에 기록했습니다. comparison v2 추가 helper/JSON의 SHA와 이 README/색인의 SHA는 [provenance 추가 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/artifacts_v1/qp_final_comparison_provenance_addendum_v2.json)에 있습니다.
