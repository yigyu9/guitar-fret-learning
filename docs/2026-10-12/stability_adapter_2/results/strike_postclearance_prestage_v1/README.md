# Strike post-clearance prestage v1

5초 native 진단에서 원본 scheduled recovery와 요구 clearance가 끝난 뒤, 캐시된 다음 target과 현재 musical event의 entry/direction/lane이 다를 때 현재 event의 READY 높이를 adapter 목표로 미리 선택했다. source geometry, phase/clock, 사용자 target box와 hit 기준은 그대로 두었다. Strap은 사용하지 않았고 root lower는 고정했다. 실행은 1,200 physics step, 151 camera frame, 28/28 native checks 통과, native input closure 1,115개 unchanged, analysis SHA 7개 unchanged다. PREPARE 49, PLAY 251, HOLD 0이며 실행은 5초 PLAY에서 끝났다.

## 결과와 범위

| 지표 | 저장 결과 |
|---|---:|
| 적시 target hit / source physical target-hit 판정 / accepted | 4 / 6 / 6 |
| source physical release / miss / wrong crossing | 7 / 6 / 1 |
| scheduled recovery 완료 pulse | 6회 |
| playable region | 전체 controls 245/300, PLAY 199/251 |
| 최대/종료 회전 변화 | 7.095454906° / 3.352545993° |
| 최대/종료 위치 변화 | 46.353645732 mm / 32.792967631 mm |
| PLAY 중 right_noncontact | 251/251 |

Scheduled recovery 완료 시각은 1.516667, 1.800000, 2.650000, 3.250000, 3.966667, 4.666667초로 raw controls에서 확인했다. 첫 prestage는 recovery 이후 3.266667초부터 3.350000초까지 6개 actor command에서 기록됐다. 각 command에는 source waypoint와 adapter waypoint가 따로 저장됐으며, source target을 덮어쓰지 않았다.

3.450000초의 UP 방향 crossing은 source physical target-hit 판정이 있었고 timing은 +25.273561 ms였지만 `target_hit=false`다. 원본 위치 허용 조건 원인은 별도 검토 중이므로 이를 적시 hit 성공으로 추가하지 않았다. 마지막 여섯 번째 source physical hit 판정은 4.283333초로 timing이 −605.015747 ms였다. 따라서 5초 진단의 일부 결과이며 완주 성공이 아니다 (`music_success=false`, 학습 update 0).

표의 physical target-hit/release는 source event geometry의 분류값이며 native rigid-body contact 측정과 같지 않다. Frozen checkpoint는 actor 30개 출력을 낸다. 팔 9개 actor 요청은 기록용이며 실제 R9은 geometry 기반 이전 목표 + 2×IK 보정이 소유한다. 손가락 21개는 policy가 제어하고 free curl 4개에는 +0.2 rad 잔차를 적용한다. 30개 출력을 모두 policy가 실제 구동했다는 뜻은 아니다.

terminal retraction 설정은 켜져 있지만 이번 실행은 HOLD에 들어가지 않았고 PD baseline 복원도 수행되지 않았다. 따라서 terminal 회수 동작은 이 결과로 검증하지 않았다. `postclearance_prestage_audit.json`은 현재 생성되지 않아 독립 offline audit 결과로 인용하지 않는다. Native report/summary의 저장 checks와 input closure만 기록했다.

별도 [staging damping 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_STAGING_DAMPING_PLAN.md)이 준비·사전검토 중이다. 그 단계의 결과는 아직 검증되지 않았고 여기에 포함되지 않는다.

## 원본 실행 자료

- [native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/native/data/report.json), [analysis summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/analysis/summary.json)
- [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/native/data/controls.json), [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/native/data/trace.json)
- [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/native/data/initial_values.json), [checkpoint connection](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/native/data/checkpoint_connection.json), [PD phase properties](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/native/data/PD_phase_properties.json)
- [native input SHA before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/native/inputs_before.json), [native closure after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/native/inputs_after.json)
- [analysis SHA before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/analysis/inputs_before.json), [analysis SHA after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/analysis/inputs_after.json)
- [capture manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/native/data/images/capture.json), [video manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/native/data/images/videos.json), [artifact SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/artifacts/artifact_manifest.json)
- [whole-body MP4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/native/data/images/whole_body.mp4), [hands MP4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/native/data/images/hands.mp4)
- Executed producer: [preserved run entry](/home/ajou/yigyu/3/stability_adapter_2/strike_postclearance_prestage_preserved_run.py); runner: [post-clearance waypoint logic, lines 179–206](/home/ajou/yigyu/3/stability_adapter_2/run_strike_postclearance_prestage.py:179), [separate source/adapter waypoints and saved records, lines 204–250](/home/ajou/yigyu/3/stability_adapter_2/run_strike_postclearance_prestage.py:204), [report metadata, lines 380–384](/home/ajou/yigyu/3/stability_adapter_2/run_strike_postclearance_prestage.py:380); analyzer: [analyze_strike_transfer_trials_v2.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_strike_transfer_trials_v2.py)

![Native whole-body video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/native/data/images/whole_body.mp4)

![Native hands video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/native/data/images/hands.mp4)

## 저장된 native camera frame

각 쌍은 같은 시각의 전신·손 native camera PNG 원본 복사본이다. Producer는 재인코딩 없이 SHA를 대조해 byte-exact 복사했다.

### 0.000초 · step 0

![0초 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/artifacts/whole_body_00000.png)
![0초 손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/artifacts/hands_00000.png)

### 1.333초 · step 320

![1.333초 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/artifacts/whole_body_00040.png)
![1.333초 손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/artifacts/hands_00040.png)

### 3.267초 · step 784, prestage 시작 표본

![3.267초 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/artifacts/whole_body_00098.png)
![3.267초 손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/artifacts/hands_00098.png)

### 5.000초 · step 1200, source PLAY 종료 표본

![5초 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/artifacts/whole_body_00150.png)
![5초 손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_postclearance_prestage_v1/artifacts/hands_00150.png)
