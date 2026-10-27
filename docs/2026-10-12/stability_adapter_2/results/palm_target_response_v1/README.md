# 저장된 팔 목표와 실제 4-step 응답 대조

2026-10-07. 새 native 실행이나 설정 변경 없이 `response.json`의 PI, RATE_PI, PALM_RATE 세 조건을 요약했다. 각 조건은 30개 창을 가지며 창은 step `k`에서 전달된 목표와 `k+4` 실제 상태를 비교한다. 전체 분석은 6개 contract check와 154개 입력 SHA를 통과했다.

## 그림

![저장된 목표 gap과 실제 4-step 이동 projection](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_target_response_v1/artifacts_final/palm_target_response.png)

위 panel은 각 창 시작점의 왼팔 12개 scalar 좌표에서 `target − actual`의 최대 절대값(`left_max_pre_gap_deg`)이다. 도 단위 좌표 차이이며 실제 상대 회전각이나 토크가 아니다. 아래 panel은 4 physics steps 후 측정한 LH source-hull center 이동을 창 시작 시점의 목표 복귀 방향에 투영한 부호 있는 값(`observed_return_direction_projection_mm`)이다. 첫 창은 초기 오차가 0이어서 원자료 `null`로 남고 그림에서 생략했다. 부호를 강제하거나 값을 0으로 바꾸지 않았다.

## 0.5초 저장 표본

| 조건 | 최대 LH 전달 목표–실제 좌표 차이 (°) | 해당 관절 | 최대 RH 차이 (°) | 해당 관절 | 복귀 방향 투영 음수 / 정의되지 않음 |
|---|---:|---|---:|---|---:|
| PI | 21.038724 | L_Shoulder_x | 17.213643 | R_Shoulder_z | 29 / 1 |
| RATE_PI | 21.062126 | L_Shoulder_x | 17.228633 | R_Shoulder_z | 29 / 1 |
| PALM_RATE | 21.462316 | L_Shoulder_x | 17.236607 | R_Shoulder_z | 29 / 1 |

29개 유효 창 모두 실제 네-step 이동에는 창 시작 시점의 목표 복귀 방향과 반대인 성분이 관측됐고, 초기 창 하나는 투영을 정의할 수 없다. 이것은 실제 이동의 구간별 방향 관측이지 연속시간의 거리 단조 증가를 증명하거나 원인을 특정하지 않는다. 위치점은 LH source-hull center이며 해부학적 palm 점, 접촉점, COM, cooked 접촉/힘을 뜻하지 않는다.

## 마지막 PALM_RATE 창의 구분

| 비교량 | 값 |
|---|---:|
| pre-step 116의 정적 `A × (delivered target − actual)` 이동 크기 | 177.530793 mm |
| step 116→120 동안 측정된 실제 source-center 이동 크기 | 0.745714 mm |
| 실제 이동의 목표 복귀 방향 투영 | −0.613600 mm |

정적 선형 계산에는 응답 시간이 없으므로 177.531 mm를 4-step 예상 이동이나 PD 부족의 증거로 해석하지 않는다. 실제 네-step 이동에는 몸통을 포함한 전체 humanoid 움직임이 들어간다. 실제 이동과 팔 좌표변화만으로 계산한 선형 이동의 차이는 몸통·비선형성 등 여러 영향을 포함하며 원인을 분리하지 않았다. 이는 목표 유지/기타 안정성/물리 지지를 인증하지 않으며, PD·gain·제어권 변경도 적용하지 않았다.

세 조건은 공통 초기 자세와 초기 기타 세계 목표를 유지했다. 고정 LA는 `1.1010801317960974 m`, 기타 목표 p/q는 기존 `+5 mm` 초기 상태이며, 손 위치 task 목표는 LH source 중심의 초기 world 위치다. 주요 66관절 연결, 24개 팔 목표 보정, Torso9·finger42·C02 하체 PD 목표, root 고정, 나머지 PD와 물리는 그대로다. 목표 보정 후 실제 자세는 고정되지 않는다.

## 재생성 및 provenance

```bash
MPLCONFIGDIR=/tmp/palm_target_response_mpl python /home/ajou/yigyu/3/stability_adapter_2/plot_palm_target_response.py \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_target_response_v1 \
  --out-dir /tmp/palm_target_response_reproduction
```

기존 산출물을 덮어쓰지 않도록 출력 경로는 비어 있어야 한다. 실행 명령·종료 상태와 image hash는 `plot_execution_v3.json`, response 및 154개 입력 SHA와 producer/output hash는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_target_response_v1/artifacts_final/plot_manifest.json)에 기록했다. 별도 native 실행은 하지 않았다.

최초 draft의 추가 null 거절을 검수에서 수정했다. 초기 null 조건은 유지하고 후기 null과
관측 부호는 허용한다. Draft producer/이미지/실행은 보존했으며 최종 그림은
`artifacts_final`에 둔다.
