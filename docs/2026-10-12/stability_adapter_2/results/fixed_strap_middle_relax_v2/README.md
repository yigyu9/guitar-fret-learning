# 고정 스트랩 · 중지3 총 −0.15 rad 응답 비교

![세 조건의 중지3 실제 각도·보유 목표와 후기 1초 최대 변화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/artifacts/middle_relax_v2_native_summary.png)

기존 관절18 기준, 직전 중지3 목표 −0.05 rad, 이번 총 −0.15 rad를 비교했다. 세 조건에서 초기81관절·기타 초기 위치/자세·절대 LA **1.1018469719600776 m**·body9 목표·나머지80개 목표를 유지했고, middle3 보유 목표만 단계적으로 바꿨다. 세 실행 모두 초기 middle3 실제각은 **60.145874°**였다.

| 조건 | middle3 유지 목표 (°) | 초기 실제각 (°) | 5초 실제각 (°) |
|---|---:|---:|---:|
| 관절18 기준 | 60.684346 | 60.145874 | 60.684291 |
| 목표 −0.05 rad | 57.819559 | 60.145874 | 57.820850 |
| 목표 총 −0.15 rad | 52.089980 | 60.145874 | 52.090865 |

| 조건 | 초기 최대 기타 위치 오차 (mm) | 초기 최대 기타 회전 오차 (°) | rolling 1초 최대 위치 변화 (mm) | rolling 1초 최대 회전 변화 (°) | 2초 시작 기준 2–5초 위치 변화 (mm) | 같은 2초 기준 회전 변화 (°) |
|---|---:|---:|---:|---:|---:|---:|
| 관절18 기준 | 14.084223 | 2.920042 | 0.455912 | 0.084049 | 0.257786 | 0.051003 |
| 목표 −0.05 rad | 14.036110 | 2.918102 | 0.437298 | 0.081147 | 0.298139 | 0.058458 |
| 목표 총 −0.15 rad | 14.077232 | 2.922581 | 0.437387 | 0.080289 | 0.246108 | 0.047665 |

그림 왼쪽 실선은 실제 middle3 scalar 각도, 색이 같은 점선은 고정 보유 목표다. 오른쪽은 각 조건의 rolling 1초 최대 위치 변화(5 mm 한계)와 회전 변화(1° 한계)를 각각 한계로 나눈 막대이며, 점선은 fraction 1의 잠정 경계다. 창은 2.000–4.000초에 60 Hz로 시작하는 121개이고, 각 창은 241개 표본에서 시작 자세 대비 최대 변화를 측정했다.

세 조건 모두 임시 초기 30 mm/5° 범위 밖 표본이 0/1201이고, 1초 창은 각각 121/121개가 임시 5 mm/1° 안이었다. −0.15의 1초 최대 위치 변화는 −0.05보다 **0.000089 mm 커졌고** 회전 변화는 조금 줄었다. 따라서 전 지표가 단조 개선된 것은 아니다. 이전 2초 기준 2–5초 변화는 창의 시작 자세와 최대값 정의가 다른 별도 측정이다. 어느 기준도 자연스러움이나 실제 fret/strike 연주 성공을 인증하지 않는다.

이번 native 비교는 초기화 1회·1200 physics step·두 카메라의 151개 프레임을 완료했다. simulation time은 5.000초까지 기록했으며, 151프레임을 30 fps로 인코딩한 영상 길이는 **5.033333초**다. 실행 로그에는 CPU PhysX, CUDA 장치 부재와 visual-geometry 경고가 남아 있으며 종료코드 0과 기록 완료를 확인했다. 아래의 손/전신 영상과 손 프레임은 이번 trial에서 저장한 native 자료다. 이번 산출물 생성에서는 native 프레임에 새 overlay를 더하지 않았다. 주황 경로는 실행 때 저장된 실제 strap route overlay이며 천 geometry가 아니다.

![총 −0.15 rad trial 손 카메라 영상, 151 frames·30 fps](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/native/hands.mp4)

![총 −0.15 rad trial 전신 카메라 영상, 151 frames·30 fps](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/native/whole_body.mp4)

![trial 시작 손 frame 00000, simulation time 0.000초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/native/frames/hands/00000.png)

![trial 종료 손 frame 00150, simulation time 5.000초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/native/frames/hands/00150.png)

새 중지3 양의 raw λ는 50 step(30–80, 0.125–0.333초)에만 있었고 2초 이후에는 0이다. 약지3도 19 step(37–55)에만 나타났다. Raw λ는 N 단위의 힘이나 지속 지지 인증이 아니다. 중지2 목표 64.343141°는 유지되었고, 이 값은 8월19일 중지2 soft 관측범위 22.7–80.2° 안에 있어 크기만으로 부자연스럽다고 판정하지 않는다. 중지3 52.09°도 자연스러움이나 손 전체 자세를 단독으로 설명하지 않는다. 분포는 hard limit이 아니다.

현재 스트랩 길이는 고정 비교값이고 사용자가 지칭한 다른 환경의 출처는 아직 pending이다. 다음에 제안된 것은 초기 middle3 각을 현재 held goal **52.089980°**에 맞추되 같은 최종 절대 목표를 제출하는 한 시험이며 아직 실행되지 않았다. 다른80개 초기각/목표를 유지하고, 더 큰 −0.26 rad 또는 middle2 동시 변경은 포함하지 않는다.

저장 분석은 [analysis.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/analysis.json>), 실제 각도/목표 시계열은 [joint_series.jsonl](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/joint_series.jsonl>), 창별 최대는 [windows.jsonl](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/windows.jsonl>)에 있다. 판정은 [root 결정 문서](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_MIDDLE_RELAX_V2_DECISION.md:1), [프로젝트 README](/home/ajou/yigyu/3/stability_adapter_2/README.md:1065), [계획](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1863)을 참조한다. 그림 산출물의 명령/환경, SHA 목록, 입력 보존은 [producer_execution.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/artifacts/producer_execution.json>), [artifact_manifest.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/artifacts/artifact_manifest.json>), [source_snapshot.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/artifacts/source_snapshot.json>)에서 확인할 수 있다.
