# Guitar Z static preview v1

작성일: 2026-10-06. 이 결과는 `preview.json`의 다섯 초기 Z 오프셋(0, 2, 5, 10, 15 mm)에서 각각 1,404개 human–guitar source-shape pair를 조회한 정적 CPU preview다. 회전, 사람 초기 자세, humanoid root와 기타 목표 회전은 고정했다. 실제 native rollout, PhysX clearance 인증, 전신 자세 변경은 하지 않았다.

## Sol 권고와 해석

| 기타 초기 Z 변화 | 음수 signed-gap pair | R_Hip gap (mm) | R_Elbow gap (mm) | 초기 strap route (m) | route − L_A (mm) |
|---:|---:|---:|---:|---:|---:|
| 0 mm | 1 | −1.33117 | 7.15432 | 1.089185175 | 0.000 |
| +2 mm | 0 | 0.52238 | 5.96396 | 1.086848722 | −2.336 |
| +5 mm | 0 | 3.30269 | 4.20840 | 1.083374161 | −5.811 |
| +10 mm | 0 | 7.93654 | 1.52496 | 1.077665135 | −11.520 |
| +15 mm | 1 | 12.57040 | −0.79598 | 1.072061116 | −17.124 |

공통 절대 rest length는 `L_A = 1.0891851746440693 m`다. Sol은 정적 형상 간격만 기준으로 +5 mm를 다음 후보로 권고했다. +2 mm의 hip 간격은 0.522 mm로 작고, +15 mm에서는 elbow 음수 pair가 다시 나타난다. +5 mm에서는 route가 L_A보다 약 5.811 mm 짧아진다. 이 값은 정적 경로 비교이며 장력이나 안정 동작의 증거가 아니다.

![기타 Z offset별 source signed gap 및 strap 경로 길이 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_preview_v1/images/guitar_z_preview_v1_static.png)

음수 pair 수와 signed gap은 source geometry query 출력이다. gap 음수 크기를 실제 침투 깊이로 보정하지 않았고 PhysX clearance로 해석할 수 없다. +5 mm는 다음 시험의 권고 후보이며 사용자 적용 확인은 대기 중이다. 채택된 환경 설정이나 안정성 성공이 아니다. 실행 중 제어 목표/기타 native 목표는 변경되지 않았다.

## 입력과 재현

- 원자료: `preview.json` (이 디렉터리). 상태 및 설정 hash/불변 검사 기록도 원자료에 포함된다.
- 그림 생성기: `/home/ajou/yigyu/3/stability_adapter_2/plot_guitar_z_preview.py`.
- 재생성: `python /home/ajou/yigyu/3/stability_adapter_2/plot_guitar_z_preview.py --input /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_preview_v1/preview.json --output /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_preview_v1/images/guitar_z_preview_v1_static.png`.
- PNG는 preview JSON의 측정값을 그린 정적 비교 그래프이며 native simulator render가 아니다.
