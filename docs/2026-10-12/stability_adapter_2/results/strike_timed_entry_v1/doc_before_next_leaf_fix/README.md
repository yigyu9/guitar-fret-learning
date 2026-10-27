# Timed ENTRY 대기 waypoint 진단

이 결과는 source APPROACH가 아직 열리지 않았을 때 adapter waypoint를 원본 READY geometry 3으로 두고, `originalapproach_open`이 열린 뒤 기존 ENTRY geometry 4 및 ENTRY/EXIT 처리를 따르는 진단이다. 원본 helper의 phase, clock, detector, READY·clearance 판단은 변경하지 않았고, phase 1의 R9 damping은 0.25배, 다른 phase는 baseline으로 native 적용했다. phase 1이 닫힌 동안 geometry 3을 사용한 command는 16회였으나, 1.350000초 첫 음표 타현은 그대로 발생했다. [진단 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_ENTRY_PLAN.md:1), [실행 코드: waypoint 선택](/home/ajou/yigyu/3/stability_adapter_2/run_strike_timed_entry.py:155), [phase별 native property 기록](/home/ajou/yigyu/3/stability_adapter_2/run_strike_timed_entry.py:288).

완료된 재실행은 `native_retry_v1`이며, summary 분석은 `analysis_retry_v1`에 저장됐다. 5초·1,200 physics step·151 camera frame·21/21 checks가 완료됐다. Native 실행 closure는 1,059개 입력이며 변경이 없고, 분석기 입력은 별도 7개 파일로 before/after SHA가 동일하다. PREPARE/PLAY/HOLD는 49/172/79 control sample이다. source는 wrong-crossing count로 3.683333초에 종료됐으며, 이후 HOLD에서 physics와 기록을 계속했다. [분석 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/analysis_retry_v1/summary.json), [native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/report.json).

첫 타현은 1.350000초, 첫 음표(event index 0) string 2 DOWN, timing +44.484798 ms로 timely `target_hit` 1건이었다. 2.750000초 event index 3의 string 2 DOWN은 physical/geometry accepted hit였지만 premature였고 timing −63.5116 ms라 추가 timely hit로 집계되지 않았다. 합계는 READY 1, timely `target_hit` 1, physical target hit 2, geometry-accepted mask 2, physical release 6, miss 6, wrong crossing 4다. Partial F1=0.307692319는 이 172 PLAY sample 노출의 부분 결과이지, 전체 연주 완료나 다른 길이의 실행과의 성능 우위를 뜻하지 않는다.

첫 clearance는 lifted 1.400000초, reached 2.183333초, scheduled completion 2.366667초였고 회복이 실제 완료됐다. 그러나 READY의 최초 wrong crossing은 1.033333초 string 3이며, 이후 wrong crossing 4회로 source가 종료됐다. 기타 최대/종료 회전 변화는 7.095455°/3.690350°, 위치 변화는 46.353646/28.895391 mm였다. playable-region sample은 제어 241/300, policy 162/172다. 원본 sensor의 geometry crossing/acceptance를 기록한 것이며 실제 줄의 음향 또는 측정된 현력 검증은 아니다. `music_success=false`, learning updates 0이다.

동일 실행기의 최초 시도는 94 whole-body/hands frame 뒤 process exit 143으로 중단됐고 wrapper `finally`·최종 report·controls/trace 출력 없이 종료됐다. 해당 부분 파일은 보존했지만 5초 성공 근거나 결과 영상으로 사용하지 않았다. 최초 시도 뒤 원본 1,059개 native input SHA는 현재와 같았고, retry는 같은 실행 코드 hash로 별도 output 경로에서 완료됐다. [중단 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/interrupted_run.json), [부분 실행 산출물](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native/data/images/capture.json), [retry input SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/inputs_before.json).

다음 계획은 source APPROACH에서 R9 damping을 소유하는 phase를 기다리는 우선순위를 분리해 검토한다. [다음 단계 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TIMED_ENTRY_PLAN.md:1). 해당 후속 단계나 전체 곡 성공을 이 결과가 입증하지 않는다.

## 저장된 retry native 영상

아래 이미지는 모두 완료된 `native_retry_v1`의 실제 Gym native 카메라 프레임이며, 최초 중단 run의 부분 영상은 사용하지 않았다. retry 영상은 151 frames, 30 fps, stream duration 5.033333초다.

| 시점 | 전신 | 손 |
|---|---|---|
| 0초 | ![retry 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/images/frames/whole_body/00000.png) | ![retry 손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/images/frames/hands/00000.png) |
| 2초 | ![retry 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/images/frames/whole_body/00060.png) | ![retry 손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/images/frames/hands/00060.png) |
| 5초 | ![retry 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/images/frames/whole_body/00150.png) | ![retry 손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/images/frames/hands/00150.png) |

### Retry 영상

![완료된 retry 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/images/whole_body.mp4)

![완료된 retry 손 근접 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/images/hands.mp4)

## 관련 기록

[Retry native 입력 closure](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/inputs_before.json), [분석 입력 SHA before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/analysis_retry_v1/inputs_before.json), [분석 입력 SHA after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/analysis_retry_v1/inputs_after.json), [native phase property 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/PD_phase_properties.json), [Retry frame capture manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/images/capture.json), [Retry video manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/images/videos.json).

## Saved native trajectory의 R9 goal authority 분석

별도 authority 분석기는 retry 실행에서 저장한 8개 native sample만 읽었다. 6개 분석 입력 SHA는 before/after 대조에서 변경되지 않았고 새 physics나 control을 실행하지 않았다. source READY reference waypoint는 guitar-local z=20.3 mm로 유지되지만, 같은 구간에서 R9 최종 goal을 FK로 예측한 pick z는 −103.658297…−74.598310 mm, R9 goal과 actual의 최대 관절 오차는 0.417103…0.710770 rad다. 이 값은 저장된 실제 상태에서 측정한 줄 위치와 R9 목표 기반 추정 위치가 크게 다를 수 있음을 보이는 권한/목표 경로 진단이다.

![저장 native sample에서 측정 pick, READY reference waypoint, R9 final-goal FK prediction 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/authority_analysis_v2/goal_authority.png)

그림의 파랑은 저장 native sample의 실제 pick 위치, 주황은 요청한 READY reference waypoint, 초록은 최종 R9 goal을 FK로 계산한 예측이다. 초록 예측은 현재 actual finger 값을 고정하고 actual anchor 및 ChestDelta를 적용한 값이며, 미래 actual pose의 측정값이 아니다. 이 그림은 unobserved derivative/방향 Jacobian을 인증하지 않고, 실제 줄의 음향·접촉력 측정이나 연주 성능을 나타내지 않는다.

분석 원자료는 [8개 sample rows](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/authority_analysis_v2/rows.json), [요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/authority_analysis_v2/summary.json), [입력 SHA before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/authority_analysis_v2/inputs_before.json), [입력 SHA after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/authority_analysis_v2/inputs_after.json), [저장 데이터 분석기](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/goal_authority_diagnosis_v2.py)에서 확인할 수 있다. 최초 v1 분석기 실행은 project root를 PYTHONPATH에 넣지 못해 import 단계에서 실패했다. 그 실패 기록은 [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/authority_analysis/failed_run.json)에 남아 있으며, 성공 결과는 별도 `authority_analysis_v2` 출력 경로에 생성됐다.
