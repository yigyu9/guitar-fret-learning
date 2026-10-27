# Palm-side strap rest length 및 초기 preload 비교

저장된 네 개의 0.1초 실행을 비교했다. 초기 자세, PD/controller, palm tracking 조건은 같고 strap rest length 및 연결된 초기 tension-law 조건이 다르다. 네 조건의 첫 step·0.1초 비교와 10N camera 재현을 포함한 총 실행 집계는 9 native initialization / 124 physics steps다.

| 조건 | 절대 rest length (m) | 초기 law (N) | 기타 최대 p/q 오차 (mm / °) | 첫 step 기타 p/q 오차 (mm / °) | trace tension 최대 / 종료 (N) | palm 접촉 행 |
|---|---:|---:|---:|---:|---:|---|
| Current | 1.101846972 | 0 | 5.107730 / 0.969008 | 0.016300 / 0.003208 | 0 / 0 | 7, steps 1–2 |
| Taut | 1.080474113 | 0 | 3.719666 / 0.551110 | 0.016300 / 0.003208 | 2.590060 / 1.772229 | 7, steps 1–2 |
| Initial 5 N | 1.079640780 | 5 | 3.354576 / 0.461241 | 0.028153 / 0.011105 | 5.000000 / 1.996061 | 11, steps 1–3 |
| Initial 10 N | 1.078807446 | 10 | 2.536296 / 0.356604 | 0.066217 / 0.023984 | 10.000000 / 0 | 15, steps 1–4 |

10 N 조건의 0.1초 최대 기타 오차는 이 네 조건 중 가장 작았지만 첫 step p/q 오차는 Current보다 컸다. Current·Taut·5N의 palm 접촉 행은 모두 raw `lambda=0`이다. 10 N의 양의 raw 값은 step 1 한 행뿐이다 (`0.6697399`, 단위 인증 없음). 접촉행 수나 이 값은 접촉 하중·지속 지지의 증거가 아니다. 기타 오차가 짧은 구간에서 작아진 것을 지지 성공으로 보지 않는다.

Rest length는 각 실행에서 고정됐지만 strap tension은 시간에 따라 달랐다. 그래프의 tension은 저장 `last_applied_tension_n` PRESTEP 필드다. trace 시각 `t_k`의 값은 physics step `k` 직전(`t_(k-1)`)에 적용된 장력이며, `t=0`의 0 N은 아직 첫 step에서 적용된 장력이 없다는 뜻이다. 10 N 초기-law 조건도 종료 tension은 0 N이지만 종료 linear/angular speed는 0.071236 m/s / 0.181603 rad/s로 움직임이 남아 있다. 이는 안정 상태를 뜻하지 않는다.

![네 strap 조건의 기타 오차·저장 tension·palm 추적점 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/artifacts/palm_side_strap_curves.png)

아래 2×2 camera panel은 10 N 초기 조건의 physics step 0/24 front/side frame이다. 이는 이번 단계에서 실제 촬영한 Isaac Gym native capture이며 MuJoCo source replay가 아니다. 청록색은 각 시점의 target polygon, 주황색 점은 같은 시점의 native palm 자세로 바꾼 source facet 추적점이다. 표시점은 cooked contact location이나 압력 중심이 아니다.

![10 N 조건의 저장 native camera 초기 및 종료 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/artifacts/palm_side_strap_camera.png)

모든 조건에서 기타 초기 p/q와 주요 제어 설정은 유지했다. Source normal/gap과 palm-up proxy는 cooked collision clearance, anatomy 또는 물리 지지의 증명이 아니다. 네 값 중 10 N을 최종 strap으로 채택하지 않는다. 다음 판단 전 더 긴 비교를 확인하며 forced attachment나 기타를 목표로 당기는 조건은 적용하지 않았다.

실행에서 사용하는 원자료·helper·producer·그림 SHA는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/artifacts/plot_manifest.json), 실제 plot 명령·환경·종료 코드는 [실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/artifacts/plot_execution.json), 전체 경로는 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/CHANGED_FILES.md)에 있다. [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/review.md:7)는 완료됐고 남은 지적은 없다.
