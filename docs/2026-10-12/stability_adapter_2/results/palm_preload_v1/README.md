# PALM_RATE 0/1/2 N 초기 strap-law 비교

2026-10-07. 이 자료는 validated JSON과 저장된 PhysX trace를 그림으로 정리한다. 비교 표에는 6개 측정행(.1초와 .5초 각 0/1/2 N)이 있다. 실행 단계에서는 4개 fresh zero-step 초기 감사와 4개 fresh rollout(총 288 physics steps)이 있었고, 0 N 기준 trace는 기존 run에서 재사용했다. 그림 생성 과정에는 native 실행이 없다.

## 0.5초 trace 그림

![0/1/2 N initial-law .5초 기타 오차와 signed scalar 차이](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_preload_v1/artifacts/palm_preload_hold.png)

위 panel은 각 저장 trace의 실제 absolute guitar position-error norm과 rotation-error scalar다. 아래 panel은 동일 시점에서 1 N 또는 2 N 조건의 scalar error에서 0 N 조건 scalar error를 뺀 값이다. 이 값은 변위 벡터나 제어 보정량이 아니다. 네 panel 모두 trace의 121개 timestamp `0…120/240 s`를 사용하며, 초기값을 0으로 덮거나 작은 차이를 반올림해 없애지 않았다. 0/1/2 N은 strap 초기 법칙 장력 label이지 runtime 장력이 일정하다는 뜻이 아니다. `.5초`의 최대 실제 applied tension은 15.748612/16.465093/17.365715 N으로 run 중 변했다.

## 여섯 측정행

| 구간 | 초기 법칙 장력 label (N) | 절대 rest length (m) | 최대 applied tension (N) | 최대 기타 위치오차 (mm) | 최대 회전오차 (°) | 최대 LH source 이탈 (mm) | LH/RH contact 행 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0.1 s | 0 | 1.101080131796 | 6.757265 | 6.874401 | 1.519676 | 47.473935 | 0 / 0 |
| 0.1 s | 1 | 1.100913465129 | 6.909702 | 6.838543 | 1.518452 | 47.476076 | 0 / 0 |
| 0.1 s | 2 | 1.100746798463 | 7.061181 | 6.821213 | 1.523082 | 47.478217 | 0 / 0 |
| 0.5 s | 0 | 1.101080131796 | 15.748612 | 36.091149 | 4.761921 | 90.540508 | 0 / 135 |
| 0.5 s | 1 | 1.100913465129 | 16.465093 | 36.077130 | 4.757473 | 90.544288 | 0 / 130 |
| 0.5 s | 2 | 1.100746798463 | 17.365715 | 36.087686 | 4.770926 | 90.605066 | 0 / 116 |

0.5초에서 1N−0N의 최대 위치오차 차이는 −0.014019mm, 최대 회전오차 차이는 −0.004448°였다. LH source 이탈은 0.003779mm 늘었다. 이 최대값 간 차이는 아래 그림의 시점별 차이와 구별한다. 작은 관측 tradeoff이며 통계적 유의성이나 안정 후보를 뜻하지 않는다. 모든 조건에 큰 이탈과 LH contact0이 남는다. RH 접촉행 수는 힘·지속 지지·인과·cooked clearance 인증이 아니고, LH source 점은 해부학적 보정이 없는 proxy다. 실제 native scalar 한계위반은 약0.0303°였다.

새 길이를 채택하지 않고 기존0N·PD를 진단 기준으로 유지한다. 1초는 미측정이며 안정·연주 성공은 아니다. 별도 어깨 stiffness 비교는 사용자 확인 대기로 이번에 적용하지 않았다.

## 재생성 및 provenance

```bash
MPLCONFIGDIR=/tmp/palm_preload_plot_mpl python /home/ajou/yigyu/3/stability_adapter_2/plot_palm_preload.py \
  --run /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_preload_v1 \
  --out /tmp/palm_preload_reproduction.png
```

Plotter는 `comparison_validated.json`의 6개 계약/136개 SHA와 세 0.5초 trace의 finite 121행 시간 coverage를 확인한다. 실행 command, 환경, exit code, log 및 SHA는 `plot_execution_v1.json`/`plot_run.log`; source와 image hash는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_preload_v1/artifacts/plot_manifest.json)에 기록했다. 0 N `.1초`와 `.5초` baseline은 각각 이전 저장 run을 재사용한다.

검수 완료: [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_preload_v1/runtime_review.md:7), [변경 파일·실제 줄 번호](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_preload_v1/CHANGED_FILES.md:1). 저장 자료만 다시 분석했을 때 전체 JSON과 PNG byte/RGBA가 일치했다. 최종 동결·보존 검증은 [verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_preload_v1/verification.json)에 기록했다.
