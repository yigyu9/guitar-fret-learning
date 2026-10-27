# 오른쪽 허벅지·waist 배치 native 보관

이 문서는 승인된 세 native 시도의 이미지와 원본 MP4를 정리합니다. 새 물리 실행·학습은 하지 않았으며, 기존 결과를 재인코딩하지 않았습니다. 원본/사본 여섯 영상의 해시와 ffprobe 정보는 [manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_thigh_waist_v1/manifest_v1.json)에 있습니다.

## 초기 위치 비교

![이전과 새 조건의 초기 전신 native 캡처. 전신 카메라 view/projection matrices가 일치함](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/artifacts_v1/initial_whole_comparison_v1.png)

![이전과 새 조건의 초기 측면 native 캡처 비교. 시각 비교이며 측면 카메라 행렬 메타데이터는 제공되지 않음](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/artifacts_v1/initial_side_comparison_v1.png)

새 후보 초기 기타 위치는 이전 기준 대비 world delta `[94.929004, 33.672083, -48.5815375] mm`, local G Y 회전 `-5°`입니다. 넥의 world 방향은 유지됐습니다. 이전/새 전신 캡처의 카메라 행렬은 exact match이며, 측면 이미지는 각 native 원본의 나란한 시각 비교입니다.

## 새 waist 조건의 native 프레임

![새 elbow5 조건의 실제 native 전신 프레임: 0, 3, 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/artifacts_v1/elbow5_whole_0_3_5_v1.png)

![새 elbow5 조건의 실제 native 손 프레임: 0, 3, 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/artifacts_v1/elbow5_hands_0_3_5_v1.png)

각 패널은 native 캡처 프레임을 그대로 배치했고, 캡션은 프레임 밖에 있습니다. wave의 실제 `R_Elbow_y` 이동 범위는 2.5–4.5초에 `10.09574359°`입니다. 실행 길이는 5초이며, wave 분석 구간과 혼동하지 않습니다.

## 기타 프레임의 윤곽과 waist contact 좌표

![기타 G 프레임에서 원본 윤곽과 native contact 좌표 XY 투영](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/artifacts_v1/waist_profile_contacts_v1.png)

윤곽은 [geometry manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/guitar/geometry_v3_manifest.json)의 `half_width_profile_t_m`을 이용해 `G_Y = -0.4 + t × 0.491957431 m`로 배치했습니다. 양의 `G_X`는 기타의 아래쪽 edge 방향입니다. 그림의 core `+5 mm`와 flank `+15 mm` 구간 및 실제 native 접촉좌표는 서로 다른 근거로 표시했습니다. 점은 z를 버린 XY 투영이며, 초기 0–0.5초와 후기 4.5–5초 표본만 색을 달리합니다. 이 도식은 native 렌더 이미지가 아니며, cooked 형상·힘·연속 접촉을 인증하지 않습니다.

## 결과와 범위

| 조건 | 완료 | 물리 step | 물리 시간 | 영상 프레임/재생시간 | 결과 요약 |
|---|---:|---:|---:|---:|---|
| `native_static_v1` | 아니오 | 1148 | 4.783333초 | 145 / 4.833333초 | 부분 실행, abort로 분리 보관 |
| `native_static_v2` | 예 | 1200 | 5초 | 151 / 5.033333초 | 정지 조건 |
| `native_elbow5_v1` | 예 | 1200 | 5초 | 151 / 5.033333초 | elbow 1주기 조건 |

승인 분석에서 새 조건은 waist region presence `1198/1200` step, positive raw lambda `1198/1200` step이며, 마지막 120 step은 각각 `120/120`입니다. 이전 튜닝보다 waist 목표 영역 접촉은 개선됐지만 이는 접촉 표본이지 힘(N)이나 지지력 분담을 뜻하지 않습니다. 오른 허벅지 접촉도 `1198/1200` step으로 오목한 측면(flank)을 받치므로 독립된 허리 지지로 볼 수 없습니다. Thorax는 `72/1200` presence, `33/1200` positive이며 마지막 120 step은 presence `0`입니다. 상완과 왼손 손가락 접촉은 계속 남습니다. 왼손 접촉은 엄지가 아니라 `middle2/fret6`, `index2/fret5/root`, `pinky3/root`입니다.

새 elbow 조건의 초기 대비 기타 body-centre 최종/최대 변위는 `11.66041149/11.72524298 mm`, SO(3) 최종/최대 변화는 `5.2166087°/6.09468586°`입니다. 정지 기준 대비 추가 최대 변화는 `0.1547542294 mm`, `0.148811516°`입니다. body9 scalar 최대 변화는 `2.23482765°`입니다. raw positive lambda는 힘 단위가 아니며, contact presence와 구별합니다.

이 단계는 3 native 시도 중 2회 5초 완료, 1회 부분 중단입니다. CPU 후보 검사는 9개 완료(7 거절, 2 수락)됐습니다. 고정 strap/기타 부착/직접 기타 힘/자세 덮어쓰기/학습 checkpoint 연결은 없었고, root와 하체는 고정, strap은 OFF입니다. full 81개 목표는 body 9개와 arm 24개 effort, head 6개와 finger 42개 position으로 구성되며, body 설정은 K=150, D=1, target=40, cap=10입니다. 두 완료 시험은 초기 상태와 첫 2.5초 trace가 exact match입니다. source1의 입력 목록에는 사전 SHA가 없는 손 STL 35개가 누락된 한계가 있으며, source2 이후에는 human mesh 37개를 pin했습니다. source3/helper1의 shape 검수 prototype은 fitting에 실행하지 않았습니다. 한 번의 정지와 한 번의 단일 elbow 주기이므로 임의 동작, 반복성, 음악 성공을 인증하지 않습니다.

## 원자료와 파일

- [승인 brief](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/artifact_brief_v1.json)
- [canonical analysis](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/analysis_final_v1/analysis.json)
- [이전 기준 native 영상/프레임](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/native_elbow5_close/media/whole_body.mp4)
- [영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_thigh_waist_v1/INDEX_V1.md) · [manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_thigh_waist_v1/manifest_v1.json)
- [생성 입력·출력 SHA provenance](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/artifacts_v1/provenance_v1.json)
- [producer](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/artifacts_v1/build_artifacts_v1.py)
