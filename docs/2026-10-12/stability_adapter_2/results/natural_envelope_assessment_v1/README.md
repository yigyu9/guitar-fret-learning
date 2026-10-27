# 자연스러운 허용 구역: 저장 자료 평가

![4개 저장 실행의 초기 오차와 rolling 1초 최대 변화를 임시 허용 한계와 비교한 막대 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/natural_envelope_assessment_v1/artifacts/natural_envelope_limits.png)

그림의 막대는 초기 위치 **30 mm**·회전 **5°**, rolling 1초 위치 변화 **5 mm**·회전 변화 **1°** 한계로 나눈 비율이며 막대 끝에는 실제 최대값을 표시했다. rolling 창은 2.000–4.000초에 시작하는 121개이며, 각 창은 241개 240 Hz 표본에서 시작 자세 대비 최대 변화를 계산한다. 기존에 쓰던 2–5초 단일 기준 변위와는 다른 지표다.

| 저장 조건 | 초기 최대 위치 오차 (mm) | 초기 최대 회전 오차 (°) | rolling 1초 최대 위치 변화 (mm) | rolling 1초 최대 회전 변화 (°) |
|---|---:|---:|---:|---:|
| 원래 손목 동작 기준 | 14.132608 | 2.894328 | 0.612804 | 0.113295 |
| 관절18 | 14.084223 | 2.920042 | 0.455912 | 0.084049 |
| 어깨 목표 −0.008 rad | 15.989064 | 2.862553 | 0.700812 | 0.126455 |
| 어깨 목표 +0.008 rad | 11.926351 | 3.169993 | 0.292116 | 0.052998 |

네 저장 기록은 각각 0–5초 1201개 표본을 포함한다. 초기 오차는 네 기록 모두 1201개 표본에서 임시 30 mm/5° 안에 있었고, 후기 창은 각각 121/121개가 임시 5 mm/1° 안이었다. 이는 저장된 이산 표본의 관측 결과이며 자연스러움, 실제 연주 성공, 또는 표본 사이 연속시간을 인증하지 않는다. 네 조건은 모두 작은 한 축 손목 동작 비교이므로 양손 연주 전체로 일반화하지 않는다.

분석은 이미 저장된 자료에 대한 재평가다. 이 그림 생성에서 추가한 native 초기화·물리 단계·actor 추론·학습은 모두 0이다. 현재 비교에 확인된 절대 스트랩 rest length는 **1.1018469719600776 m**이며, 사용자가 지칭한 다른 환경의 기준값은 아직 대조되지 않았다. 공통 길이라고 단정하지 않는다.

아래 native 영상과 프레임은 기존 `joint_only_fixed_strap_v1` 실행의 재사용 자료다. 이번 저장 자료 평가에서 새로 실행하거나 성공 여부를 확인한 결과가 아니다. frame 00150은 마지막 저장 프레임이며 simulation time 5.000초다. 151개 프레임을 30fps로 재생할 때의 영상 표기 길이는 약 5.033초다.

![이전 joint-only fixed-strap native 실행의 손 카메라 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/hands.mp4)

![이전 실행 시작 시 손 프레임, frame 00000](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/frames/hands/00000.png)

![이전 실행 마지막 저장 손 프레임, frame 00150](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/frames/hands/00150.png)

승인된 수치 해석과 다음 시험은 [평가 결정 문서](/home/ajou/yigyu/3/stability_adapter_2/NATURAL_ENVELOPE_ASSESSMENT_DECISION.md:3)에 있다. 상위 기록은 [프로젝트 README](/home/ajou/yigyu/3/stability_adapter_2/README.md:1045), [계획](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1843)에 연결했다. 실행 명령과 환경은 [producer 실행 기록](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/natural_envelope_assessment_v1/artifacts/producer_execution.json>), SHA 목록은 [artifact manifest](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/natural_envelope_assessment_v1/artifacts/artifact_manifest.json>), 복사한 입력은 [source snapshot](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/natural_envelope_assessment_v1/artifacts/source_snapshot.json>)에서 확인할 수 있다.
