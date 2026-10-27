# Strike lateral staging v1

5초 native 실행에서 source 조건은 유지한 채, open phase 1에서 실제 `RH:pick`의 기타 좌표계 READY 평면 거리를 보고 ENTRY로 가기 전 최대 4 mm까지 측면 staging을 추가했다. 실행은 1,200 physics step, 151 camera frame, 27/27 checks 통과, native closure 1,109개 unchanged, analysis input 7개 unchanged다. trace는 151행이며 마지막은 5.0초 PLAY다. PREPARE 49, PLAY 251, HOLD 0; 실행은 5초까지 PLAY로 진행했고 terminal stop은 없었다.

## 결과와 범위

| 지표 | 저장 결과 |
|---|---:|
| 적시 target hit / 물리 target hit / accepted | 4 / 5 / 5 |
| 물리 release / miss / wrong crossing | 7 / 6 / 2 |
| playable region | controls 223/300, PLAY 177/251 |
| 최대/종료 회전 변화 | 7.095454906° / 4.355243945° |
| 최대/종료 위치 변화 | 46.353645732 mm / 33.298227031 mm |

앞선 네 적시 hit은 유지됐다. 첫 staging은 3.366667초에 시작했다. READY 평면 거리는 17.029628 mm에서 12.864843 mm, 6.737893 mm, 3.996863 mm로 줄어 ENTRY 경로를 선택했고, 다음 표본에서는 6.045976 mm가 되어 READY 경로가 다시 선택됐다. 이는 저장 trajectory에서 관찰된 전환이며, staging이 원인이라고 입증하지 않는다.

4.266667초 crossing은 string 2 DOWN 물리 접촉이 기록됐지만 timing은 −612.092712 ms였고 `target_hit=false`다. 이를 적시 hit으로 세지 않는다. source 사용자 조건과 ±50 ms 허용창은 바꾸지 않았다. 완주 성공은 아니며 `music_success=false`, 학습 update 0이다.

제어는 frozen checkpoint를 사용했다. R9 actor 요청은 기록만 하고 실제 팔 목표는 현재 기타 좌표계 geometry에 대한 이전 목표 + 2×증분 IK 보정이 소유했다. 손가락 21개는 policy가 제어하고 free curl 4개에 +0.2 rad 잔차를 적용했다. R9 출력 30개 전체를 policy가 실제 구동했다고 해석하면 안 된다.

terminal retraction 설정은 켜져 있었지만 실행은 HOLD에 들어가지 않았고 (`HOLD=0`), baseline PD 복원도 일어나지 않았다. 따라서 이번 결과는 terminal/HOLD 동작 시험이 아니다. 후속 latch 단계는 별도 계획에서 준비·사전검토 중이며 효과는 아직 확인되지 않았다: [STRIKE_LATERAL_LATCH_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_LATERAL_LATCH_PLAN.md).

## 원본 실행 자료

- [native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/native/data/report.json), [analysis summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/analysis/summary.json)
- [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/native/data/controls.json), [native trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/native/data/trace.json)
- [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/native/data/initial_values.json), [checkpoint connection](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/native/data/checkpoint_connection.json)
- [native SHA before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/native/inputs_before.json), [native SHA after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/native/inputs_after.json)
- [analysis SHA before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/analysis/inputs_before.json), [analysis SHA after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/analysis/inputs_after.json), [lateral staging audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/lateral_staging_audit.json)
- [whole-body MP4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/native/data/images/whole_body.mp4), [hands MP4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/native/data/images/hands.mp4)

### 원본 native 영상

![native whole-body 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/native/data/images/whole_body.mp4)

![native hands 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/native/data/images/hands.mp4)
- [capture manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/native/data/images/capture.json), [video manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/native/data/images/videos.json), [artifact SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/artifacts/artifact_manifest.json)
- [producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/make_artifacts.py), [offline audit helper](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/audit_lateral_staging.py)

Producer copied the selected PNGs byte-for-byte from the saved native capture and verified source SHA before/after; it did not initialize native or run physics. Source logic: [staging gate and geometry selection, lines 152–183](/home/ajou/yigyu/3/stability_adapter_2/run_strike_lateral_staging.py:152), [incremental IK target and saved staging fields, lines 193–221](/home/ajou/yigyu/3/stability_adapter_2/run_strike_lateral_staging.py:193), [terminal HOLD branch, lines 300–334](/home/ajou/yigyu/3/stability_adapter_2/run_strike_lateral_staging.py:300).

## Native frames

각 그림은 저장된 native camera frame의 원본 PNG 복사본이다. `whole_body`와 `hands`는 같은 시각의 서로 다른 카메라다.

### 0.000초 · physics step 0

![0초 전신 native frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/artifacts/whole_body_00000.png)
![0초 손 native frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/artifacts/hands_00000.png)

### 1.333초 · step 320, 첫 적시 hit 직후 구간

![1.333초 전신 native frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/artifacts/whole_body_00040.png)
![1.333초 손 native frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/artifacts/hands_00040.png)

### 3.400초 · step 816, READY 거리 6.737893 mm로 기록된 표본

![3.4초 전신 native frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/artifacts/whole_body_00102.png)
![3.4초 손 native frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/artifacts/hands_00102.png)

### 5.000초 · step 1200, 종료 표본 (source PLAY)

![5초 전신 native frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/artifacts/whole_body_00150.png)
![5초 손 native frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_lateral_staging_v1/artifacts/hands_00150.png)
