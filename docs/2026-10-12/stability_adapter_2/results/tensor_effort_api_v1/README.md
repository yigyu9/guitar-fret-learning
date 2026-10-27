# 1축 CPU force-tensor API 진단 그림

2026-10-07, 승인된 별도 L_Shoulder_x single-hinge fixture의 저장 결과 6개(각 24 physics steps, 총 144)를 그렸다. 이 단계는 전신 humanoid·기타·원본 GPU 실행의 구동 동등성이나 기타 안정화 성공을 판정하지 않는다.

## 저장 trace 비교

![POS/EFFORT 0 및 ±1 Nm trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/artifacts_final_v2/tensor_effort_api.png)

그림은 native hinge 좌표를 degree로 환산한 q와 angular velocity (rad/s)를 표시한다. 각 조건은 초기값과 24개 완료 상태의 25점을 가진다. POS의 0/±1 Nm 선은 q=0 및 velocity=0에서 정확히 겹쳐 있어 인위적인 offset을 주지 않았다. EFFORT ±1 Nm에서는 반대 방향의 양방향 응답이 관측됐다.

| Drive | Submitted torque | 종료 q (rad) | 종료 velocity (rad/s) | 같은 drive의 0 Nm 대비 |
|---|---:|---:|---:|---|
| EFFORT | 0 Nm | 0 | 0 | 기준 |
| EFFORT | +1 Nm | +0.001976419706 | +0.000237588421 | q, velocity 변화 관측 |
| EFFORT | −1 Nm | −0.001976419473 | −0.000237583067 | 반대 방향 변화 관측 |
| POS | 0 Nm | 0 | 0 | 기준 |
| POS | +1 Nm | 0 | 0 | 25 상태 모두 exact 일치 |
| POS | −1 Nm | 0 | 0 | 25 상태 모두 exact 일치 |

6개 run에서 각 9개 계약 검사가 통과했고 API 제출은 모두 accepted였다. 각 완료 단계의 contact 목록은 비어 있다. 비교 JSON의 계약상 5개 입력 SHA와 각 rollout JSON의 SHA를 manifest에 기록했다. 로그에는 각 fixture 시작 시 CUDA device 탐색 오류가 한 번씩 남아 있으나, CPU PhysX로 여섯 실행이 완료됐으며 runner return code는 0이다. 이 CPU fixture에서 POS force 제출의 움직임은 관측되지 않았고, EFFORT 양방향 반응은 확인됐다. 이 결과를 모든 API·backend·모델의 동작으로 일반화하거나 원본 연주 구동의 실패로 확대하지 않는다.

## 조건과 한계

Fixture는 하나의 L_Shoulder_x hinge이며 stiffness 0, damping 50, effort 150, gravity 0, CPU PhysX 240 Hz/1 substep을 사용했다. Source XML의 authored range는 ±90°지만 native property readback은 `hasLimits=false`였고 lower/upper는 모두 0이다. `initial_within_limits`는 native readback의 lower/upper 숫자에 대한 비교다. Source XML authored ±90° 범위와 초기·저장 q의 포함 여부는 별도 [analysis 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/analysis_validated_v2.json:1)에서 대조했으며, 비활성 native limit이나 안전성을 인증하지 않는다. 이 그림은 저장된 PhysX trace 그래프이지 PhysX renderer 이미지가 아니다. 0.1초 관측이며 전신·기타·접촉 안정성, 원본 GPU 구동 및 실제 연주 성능은 검증하지 않았다. Main scene의 gain, drive mode, controller는 이 산출 과정에서 변경하지 않았다.

## 재생성 및 provenance

```bash
MPLCONFIGDIR=/tmp/tensor_effort_api_reproduction MPLBACKEND=Agg \
python /home/ajou/yigyu/3/stability_adapter_2/plot_tensor_effort_api.py \
  --run /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/rollouts \
  --out /tmp/tensor_effort_api_reproduction.png
```

실행 기록은 [plot_execution_v4.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/plot_execution_v4.json)과 [plot_run_v4.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/plot_run_v4.log)에 있다. 최신 그림·입력·producer SHA는 [validated manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/artifacts_final_v2/tensor_effort_api.manifest.json)에 기록했다. 최초 그림과 중간 수정본은 `artifacts/`, `artifacts_validated/`, `artifacts_final/`, `source_artifacts_attempt_v1/`, `source_artifacts_v2/`, `source_artifacts_v3/`에 보존했고, 대응 producer 사본은 `source_plot_attempt_v1/`, `source_plot_v2/`, `source_plot_v3/`에 두었다. canonical 경로는 `artifacts_final_v2/`이다. [독립 검수](runtime_review.md:7)를 완료했다.

## 완료-step 속도와 구간 평균의 구분

EFFORT +1Nm 마지막 구간의 Δq/Δt는 0.01976547763rad/s, SDK 완료-step velocity는
0.0002375884214rad/s였다. 두 값은 구간 평균과 완료시점 측정으로 서로 다르며, 차이의
원인·단위 오류를 단정하지 않는다. 이후 torque-PD 감쇠·velocity feedback 검증에 반영한다.
계산값과 두 ±1Nm의 전체24구간은 [analysis_validated_v3.json](analysis_validated_v3.json)에 있다.
