# 고정 스트랩 · 중지3 유지 목표 완화

![중지3 실제 각도와 보유 목표, 두 조건의 후기 1초 최대 변화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/artifacts/middle_relax_native_summary.png)

같은 초기81관절/Guitar 위치·자세/절대 스트랩 길이 **1.1018469719600776 m**/body9 목표/손목 파형을 두고 LH:middle3의 유지 목표만 **−0.05 rad** 낮춘 actual 비교다. 초기 중지3 실제각은 양쪽 모두 **60.145874°**였고, 기준 목표 **60.684346°**에서 완화 목표 **57.819559°**로 이동했다. 그 외80개 목표와 1200개 시계가 정확히 유지됐다.

| 지표 | 기존 관절18 기준 | 중지3 목표 −0.05 rad |
|---|---:|---:|
| 중지3 유지 목표 (°) | 60.684346 | 57.819559 |
| 중지3 5초 실제각 (°) | 60.684291 | 57.820850 |
| 초기 기타 최대 위치 오차 (mm) | 14.084223 | 14.036110 |
| 초기 기타 최대 회전 오차 (°) | 2.920042 | 2.918102 |
| 후기 rolling 1초 최대 위치 변화 (mm) | 0.455912 | 0.437298 |
| 후기 rolling 1초 최대 회전 변화 (°) | 0.084049 | 0.081147 |
| 2초 시작 자세 기준 2–5초 최대 위치 변화 (mm) | 0.257786 | 0.298139 |
| 같은 2초 기준 최대 회전 변화 (°) | 0.051003 | 0.058458 |

그림 왼쪽의 실선은 0–5초 중지3 실제 각도, 점선은 각 실행의 고정 유지 목표다. 오른쪽 막대는 시작 자세 기준 완전한 1초 창의 최대 변화를 5 mm와 1° 한계로 나눈 값이며, 점선 x=1이 잠정 한계다. 창은 2.000–4.000초에 60 Hz로 시작하는 121개이고 각 창은 241개 표본을 사용한다. 두 조건 모두 초기30 mm/5° 밖 표본 0/1201, 잠정 1초 범위 안 창 121/121이었다. 이산 관측이며 연속시간 보증이나 자연스러움·연주 성공 인증은 아니다. 후기 1초 값은 조금 줄었지만 앞선 2초 시작 기준 2–5초 변화는 커져 모든 지표가 나아졌다고 해석하지 않는다.

이 trial은 actual 1회 초기화·1200 물리 단계와 손/전신 151-frame recording을 완료했다. 영상 마지막 프레임은 simulation time 5.000초이며 151 frames at 30 fps의 컨테이너 재생 길이는 **5.033333초**다. 아래는 이번 조건의 native 자료이며, 캡처 상단의 주황 스트랩 경로 표시는 실행 시 저장된 표시다. 이번 문서/그림에서 프레임을 수정하거나 새 overlay를 더하지 않았다.

![중지3 완화 trial 손 카메라 영상, 151 frames·30 fps](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/native/hands.mp4)

![중지3 완화 trial 전신 카메라 영상, 151 frames·30 fps](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/native/whole_body.mp4)

![trial 시작 손 frame 00000, simulation time 0.000초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/native/frames/hands/00000.png)

![trial 마지막 손 frame 00150, simulation time 5.000초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/native/frames/hands/00150.png)

중지3의 마지막 실제각은 약 **57.82°**로, 8월19일 관측 p99 **46.1°**보다 크다. 그 분포는 soft 자세 선호이지 hard limit이 아니다. 중지2 목표는 그대로이고 손 전체의 자연스러움이나 실제 fret/strike 기능은 확인되지 않았다. 따라서 이번 결과는 중지 목표 응답 비교일 뿐 자연성이나 연주 성공으로 확대하지 않는다. 다음 total−0.15 rad는 **미실행 제안**이다. 다른 환경의 스트랩 길이 출처도 확인 전이며, 현 비교 길이를 모든 환경의 공통값이라고 단정하지 않는다.

그림 생성 자체에서는 추가 native 초기화·physics step·actor inference·training update가 모두 0이다. 저장 분석은 [analysis.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/analysis.json>), 시계열은 [joint_series.jsonl](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/joint_series.jsonl>), 후기 창은 [windows.jsonl](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/windows.jsonl>)에 있다. [root의 승인 결정](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_MIDDLE_RELAX_DECISION.md:1)과 [프로젝트 README](/home/ajou/yigyu/3/stability_adapter_2/README.md:1055), [계획](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1853)을 함께 참조한다. 산출물 실행 기록, SHA manifest, 입력 보존 목록은 각각 [producer_execution.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/artifacts/producer_execution.json>), [artifact_manifest.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/artifacts/artifact_manifest.json>), [source_snapshot.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/artifacts/source_snapshot.json>)에 기록했다.
