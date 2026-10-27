# P 단계 native smoke 결과

## 이전 결과 그림 범례 보완본

이전 분석 그림의 수치·분류·해석과 native 결과·영상 내용은 그대로 두고, 초기/1회 평가 시간 패널의 범례가 막대 위를 가리지 않도록 plot 오른쪽 바깥에 배치한 버전을 추가했습니다. [보완 그림 v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_native_v1/previous_analysis_summary_v2.png)와 [v2 입력·producer SHA-256 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_native_v1/analysis_provenance_v2.json)를 참조하세요. 이전 [그림 v1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_v1/previous_analysis_summary_v1.png) 및 기존 native 결과·영상은 수정하지 않고 보존했습니다.

이 디렉터리는 보정 후보의 `smoke_on_v1` 실제 native 실행만 요약합니다. 이전 저장 결과의 별도 오프라인 분석은 [artifacts_v1 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_v1/README.md)에서 확인할 수 있습니다.

## native 영상 프레임 비교

각 줄은 `initial_000000`(0 update), `update_000001`, `update_000003` checkpoint입니다. 열은 저장된 native 영상에서 0초(0번 프레임), 2초(60번), 물리 episode 종료 시각 16.3667초(491번 프레임)를 보여줍니다. MP4는 30 fps, 492프레임으로 인코딩되어 재생 duration 표시는 16.4초입니다. 정지 화면 비교는 자세의 인과나 성공을 판정하지 않습니다.

![세 checkpoint의 실제 native 전신 프레임을 0초, 2초, 16.3667초에 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_native_v1/native_whole_body_frames_v1.png)

![세 checkpoint의 실제 native 손 프레임을 0초, 2초, 16.3667초에 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_native_v1/native_hands_frames_v1.png)

## 위치 범위 밖 시간 그래프

아래 선은 각 control tick에서 저장한 `position_outside_m` 벡터의 크기를 물리 경과 시간에 따라 표시합니다. 범위 밖 판정 비율과 최대 크기는 runtime v2 검증 값이며, 이 거리는 기타 위치 허용범위에 대한 거리 벡터입니다.

![초기, update 1, update 3 native episode의 위치 범위 밖 거리 시간 그래프](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_native_v1/native_outside_over_time_v1.png)

| Checkpoint | episode 경과 | 종료 안전 위반 | 범위 밖 tick 비율 | 최대 위치 범위 밖 거리 | 공동 음악 성공 |
|---|---:|---|---:|---:|---:|
| initial_000000 | 16.3667초, 492 frames | 없음, full horizon | 85.4379% | 0.4650 m | 0 |
| update_000001 | 16.3667초, 492 frames | 없음, full horizon | 86.0489% | 0.4358 m | 0 |
| update_000003 | 16.3667초, 492 frames | 없음, full horizon | 84.6232% | 0.4708 m | 0 |

세 평가는 모두 예정된 horizon을 마쳤고 안전 종료도 없었지만, 위치 범위 밖 비율은 계속 높고 음악 성공은 0입니다. update 3의 범위 밖 비율이 초기보다 낮아도, 한 번의 짧은 smoke 평가로 안정화 개선이나 음악 성공을 선언할 수 없습니다.

## guarded optimizer step과 KL

| Update | 누적 transition | 승인된 optimizer step 수 | 마지막 해석적 KL | RMS 갱신 |
|---:|---:|---:|---:|---|
| 1 | 256 | 3 | 0.019762799 | 없음 |
| 2 | 512 | 4 | 0.019921599 | 없음 |
| 3 | 768 | 3 | 0.019898698 | 없음 |

runtime 검증 v2는 모든 검사를 통과했습니다. RMS는 초기 상속값과 각 checkpoint 저장값이 정확히 같고, baseline 및 검증 입력도 바뀌지 않았습니다. 세 update는 모두 KL guard에서 승인된 step으로 끝났습니다. v1 runtime 검증은 float32 rate 허용오차가 ULP보다 작아 실패로 보존했고, v2는 2 float32 ULP와 1e-10 허용오차로 raw 결과를 대조했습니다. 이번 결과가 확인하는 것은 정책 갱신 제어와 해당 검증 경로이며 물리 안정성 또는 연주 성공은 아닙니다.

## P 단계 native 동영상

아래 여섯 파일은 모두 `smoke_on_v1`에서 저장된 원본 native 평가 MP4입니다. 각 영상은 16.4초 표시 duration, 492 frames입니다.

### 초기 정책 · initial_000000

전신 영상:

![initial_000000 native 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/smoke_on_v1/evaluations/initial_000000/native/episode_0001/media/whole_body.mp4)

손 영상:

![initial_000000 native 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/smoke_on_v1/evaluations/initial_000000/native/episode_0001/media/hands.mp4)

### Update 1 · update_000001

전신 영상:

![update_000001 native 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/smoke_on_v1/evaluations/update_000001/native/episode_0001/media/whole_body.mp4)

손 영상:

![update_000001 native 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/smoke_on_v1/evaluations/update_000001/native/episode_0001/media/hands.mp4)

### Update 3 · update_000003

전신 영상:

![update_000003 native 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/smoke_on_v1/evaluations/update_000003/native/episode_0001/media/whole_body.mp4)

손 영상:

![update_000003 native 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/smoke_on_v1/evaluations/update_000003/native/episode_0001/media/hands.mp4)

## Nominal 지지 도달성 진단과 다음 판단

[nominal_support_analysis_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/nominal_support_analysis_v2.json)은 teacher arm nominal이 static preload 기준에서 최대 2.71624 rad 벗어나며, PLAY tick의 100%에서 적어도 한 arm joint 요청이 residual ±0.30 rad 범위로 preload 위치에 도달하지 못하는 것으로 분석합니다. 이는 **static preload 대비 target reachability 진단**입니다. 해당 5초 preload는 검증된 참고 상태이지 필수 접촉 조건도, 음악 성공을 보장하는 조건도 아닙니다. 따라서 이 수치만으로 실제 손 위치나 실패의 원인을 단정하지 않습니다.

승인된 다음 검토 방향은 팔 nominal의 preload 편차를 최대 0.15 rad, 왼손 엄지 nominal 편차를 최대 0.10 rad로 제한하는 것입니다. 나머지 보정 상한은 body ±0.03, head ±0.10, arm ±0.30, finger ±0.20 rad를 유지합니다. 다음 단계의 결과가 나오기 전까지 이 P 단계는 **guarded policy update가 작동했다**고만 결론 내립니다. 기타 안정화나 음악 성공은 확인되지 않았습니다.

## 출처와 재현

[build_native_summary_v1.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_native_v1/build_native_summary_v1.py)는 runtime v2, 다음 변경 brief, nominal 분석 v2, training JSONL, 세 native episode의 report·controls·initial values, 여섯 native 영상과 비교에 쓴 실제 프레임 18장을 입력으로 사용합니다. 파일별 SHA-256과 producer SHA-256, 산출물 SHA-256은 [native_provenance_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_native_v1/native_provenance_v1.json)에 기록했습니다. 이 요약 작업은 새 물리 실행이나 학습을 추가하지 않았습니다.
