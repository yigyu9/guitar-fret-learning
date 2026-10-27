# 실제 quiet 검지 목표 응답

기존 quiet 기준을 보존한 채 LH:index3 PD 목표에만 ±0.005 rad를 더해 비교했다. 보정은 2.0초부터 2.5초까지 선형 ramp하고 5초까지 유지했다. 시작 81관절각, 고정 LA 1.1018469719600776 m, 몸통9 PD 설정, root/하체, 기타 목표와 기존 손목 파형은 유지했다. plus/minus 각각 다른 80관절 목표는 1200명령 모두 기준과 exact였고, 공통 20개 초기 필드도 exact였다. 0~2초 native state/trace와 첫 484개 전체 목표명령도 exact이며 step485에서 처음 달라졌다.

첫 minus 초기화는 −11(SIGSEGV)로 관측 step152에서 끝났다. 그 원인을 확정하지 않았으며 이 신호를 음수 보정의 물리 실패로 해석하지 않는다. Python report와 5초 영상은 생성되지 않았다. 원 출력 86개 파일은 SHA·크기와 함께 보존했다. Capture에 저장된 frame 19개(t=0..0.6초)로 만든 두 partial MP4의 재생시간은 19/30초(0.633333초)다. 마지막 저장 화면시각 0.6초와 native step152에서 관측된 시뮬레이션 시각 0.633333초를 구분한다. 동일 입력 재시도는 새 `native/minus_retry_v2` 경로에서 완료되어 실패 기록과 섞지 않았다.

| 완료조건 | 최대 초기 world 위치/회전 오차 | 5초 종료 위치/회전 오차 | 후기 완전 1초 창 최대 위치/회전 변화 |
|---|---:|---:|---:|
| 저장 baseline | 14.608483 mm / 2.918412° | 13.819696 mm / 2.918277° | 0.648625 mm / 0.115306° |
| plus | 14.608483 mm / 2.921661° | 13.750278 mm / 2.921428° | 0.685555 mm / 0.124373° |
| minus 재시도 | 14.608483 mm / 2.916999° | 13.887982 mm / 2.916812° | 0.604995 mm / 0.106007° |

끝점에서는 plus의 위치오차가 0.069418 mm 낮아졌지만 회전오차는 0.003151° 높아졌다. minus는 위치오차가 0.068286 mm 높아지고 회전오차가 0.001465° 낮아졌다. 이 두 endpoint 응답은 위치와 회전을 함께 낮추지 않는다. 후기 1초 창은 plus가 두 변화량 모두 기준보다 컸고 minus는 둘 다 작았다. 이 작은 단일축 응답은 큰 보정각이나 안정화 성공으로 외삽하지 않는다.

![저장 baseline과 완료된 plus/minus 실제 5초 응답: 기타 초기오차, index3 목표/실제각, baseline 대비 world 위치 차이](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/artifacts/v2/quiet_index_support_response.png)

위 그림의 실제 index3 각도는 t=k/240초의 1201개 state이고, PD 목표는 step 1..1200의 post-step 기록을 같은 물리시각에 놓았다. 제어명령은 60 Hz로 갱신되어 중간 물리 step에서 유지된다. 하단 오른쪽은 saved baseline 대비 world 위치 차이다. 최초 그림과 producer는 그대로 보존했고, 최초 그림의 범례가 plus plateau를 가리던 표시만 별도 v2 그림에서 오른쪽 아래로 옮겼다. v2는 동일 series·계산·축을 사용하며 새 물리나 분석은 실행하지 않았다.

명목 ±0.005 rad 차이의 t5 중앙차분은 특정 자세와 해당 접촉분기에서 측정한 유한응답이다. 아래 6×1의 앞 세 행은 world 위치 m/rad, 뒤 세 행은 world 회전 log rad/rad다.

| 응답 행 | 값 | 단위 |
|---|---:|---|
| world 위치 X | −0.008817017078 | m/rad |
| world 위치 Y | −0.008571147919 | m/rad |
| world 위치 Z | −0.007355213165 | m/rad |
| world 회전 log X | −0.013808164676 | rad/rad |
| world 회전 log Y | −0.020449243808 | rad/rad |
| world 회전 log Z | 0.040464169087 | rad/rad |

이 응답은 전역 Jacobian이나 feedback gain 인증이 아니며 큰 손가락 각도로 외삽할 수 없다. baseline/plus/minus는 LH:index3 양의 raw λ가 각각 1156 step으로 같고, thumb3는 587/521/615 step이었다. palm 양의 접촉은 없었다. raw λ는 뉴턴 단위의 힘·force closure·동적 지지 증명이 아니다. 세 완료 기록의 최대 실제 native 관절한계 초과는 동일한 0.000099949539 rad였으며, 목표값 한계 통과와 실제 state의 한계 완전 준수는 구분한다. 새 actor inference·training은 0이다. 자연스러움·연주 성공·정책 호환성을 검증하지 않았다.

47개 저장 분석 검사가 모두 통과했다. 분석 wrapper는 2054 입력의 전/후/current SHA와 2053 사본 및 log SHA를 확인했고 analyzer 직접 입력은 2045개였다. 분석은 baseline과 두 완료 조건만 1200 step씩 비교한다. 실패 시도의 152 observed step은 별도 회계하며 완료된 두 5초 trial을 이어붙이지 않는다. [분석 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/analysis.json:1), [시계열 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/series.json:1), [분석 실행기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/analysis_execution.json:1), [root 확인기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/ROOT_VERIFICATION_NOTES.md:1)을 확인할 수 있다.

초기값 기록은 [저장 baseline](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/initial_values.json:1), [실제 plus](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/native/plus/initial_values.json:1), [완료 minus 재시도](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/native/minus_retry_v2/initial_values.json:1)에서 비교할 수 있다.

### 실제 Isaac Gym 저장 프레임

아래는 추가 overlay 편집 없이 저장한 실제 strap-on Gym 카메라 프레임이다. `00150.png`의 simulation time은 5.000초다. 각 조건의 전신 원본 t0/t5도 링크했다.

| 완료 trial | t0 hands | t5 hands | 전신 t0 / t5 |
|---|---|---|---|
| plus | ![plus Gym hands t0](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/native/plus/frames/hands/00000.png) | ![plus Gym hands t5](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/native/plus/frames/hands/00150.png) | [t0](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/native/plus/frames/whole_body/00000.png), [t5](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/native/plus/frames/whole_body/00150.png) |
| minus 재시도 | ![minus retry Gym hands t0](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/native/minus_retry_v2/frames/hands/00000.png) | ![minus retry Gym hands t5](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/native/minus_retry_v2/frames/hands/00150.png) | [t0](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/native/minus_retry_v2/frames/whole_body/00000.png), [t5](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/native/minus_retry_v2/frames/whole_body/00150.png) |

두 완료 trial의 실제 영상은 각각 151 frame/30 fps로 저장했으며 MP4 길이는 5.033333초, simulation 종료는 5.0초다.

**Plus 전신**

![완료 plus 실제 Isaac Gym 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/native/plus/whole_body.mp4)

**Plus hands**

![완료 plus 실제 Isaac Gym hands 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/native/plus/hands.mp4)

**Minus 재시도 전신**

![완료 minus 재시도 실제 Isaac Gym 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/native/minus_retry_v2/whole_body.mp4)

**Minus 재시도 hands**

![완료 minus 재시도 실제 Isaac Gym hands 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/native/minus_retry_v2/hands.mp4)

### 보존한 첫 minus partial 영상

첫 minus의 부분 MP4는 완성 trial과 분리해 기록한다. 각 파일은 19 frame, 재생 0.633333초이며 마지막 저장 frame은 시뮬레이션 t=0.6초다. 이는 완료된 5초 trial이 아니다.

![첫 minus crash partial 전신 영상, 19 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/partial_videos/minus_crash__whole_body.mp4)

![첫 minus crash partial hands 영상, 19 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/partial_videos/minus_crash__hands.mp4)

기존 영상 152개를 보존하고 완료 영상 4개와 partial 2개를 더한 [영상 모음 v14 — 158개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v14.md:1) 및 [복사 SHA 갱신 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/video_collection_update_v13.json:1)에 원본 경로, 복사 SHA, 스트림 정보를 기록했다.

### 실행 경로와 후속 계획

원래 minus의 terminal 기록은 [minus 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/minus_execution.json:1), [native crash inventory](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/minus_native_crash.json:1), [partial 영상 metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/partial_videos/videos.json:1)에 남겼다. 같은 조건의 별도 재시도는 [재시도 실행기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/minus_retry_v2_execution.json:1)에 기록했다.

후처리 소스에서 실행되지 않은 a52 변형을 발견해 별도 [source-drift 사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/source_drift/run_quiet_index_postprocess_unexecuted_collection_edit.py:1)과 [SHA 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/source_drift/record.json:1)에 보존했다. 분석에 소비된 ea42 canonical은 byte-exact 복구했고, a52 변형은 analysis·collection에서 사용하지 않았다. root는 복구본으로 collection을 실행했다. 상세는 [root 검증 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/ROOT_VERIFICATION_NOTES.md:1)에 있다.

다음 [L_Wrist_y ±0.005 rad 측정 계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_SUPPORT_AUTHORITY_PLAN.md:1)은 초기 quiet 자세와 fixed strap을 유지하는 두 실제 응답을 계획한다. 아직 실행하지 않았다. 이번 scalar 검지 보정이나 계획된 손목 측정은 자연스러운 연주, checkpoint 호환성, 전체 feedback 제어를 인증하지 않는다.
