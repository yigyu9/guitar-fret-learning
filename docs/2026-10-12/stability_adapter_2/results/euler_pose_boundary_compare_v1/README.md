# 기타 위치·회전 범위 경계 이미지

이 자료는 자유 기타의 위치와 방향이 제시된 각 경계에 놓였을 때의 정적 모습을 비교합니다. Isaac Gym native camera로 렌더링했고 물리 step은 0입니다. 접촉·관통·안정성 판정은 하지 않았습니다.

입력값 해석: X `[-0.50, -0.15] m`, Y `[-0.15, 0.15] m`, Z `>=0.65 m`, 월드 기준 extrinsic Euler XYZ 각도 X `[45,90]°`, Y `[50,100]°`, Z `[135,180]°`입니다. X의 역순 표기는 오름차순 구간으로 정리했습니다. Z 상한은 지정되지 않아 상한을 만들지 않았습니다.

각 그림에서 한 축만 움직이고 나머지는 기준값에 둡니다. 기준 위치는 `(-0.325, 0, 0.65) m`, 기준 회전은 `(67.5, 75, 157.5)°`입니다. 위치 그림의 Z 하한과 기준 이미지는 같은 포즈이며, Z 상한 칸은 지정되지 않았음을 표시합니다. 각 축의 경계를 동시에 적용한 모서리 조합은 포함하지 않았습니다.

## 위치 경계

![정면에서 본 위치 경계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v1/images/position_front.png)

![측면에서 본 위치 경계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v1/images/position_side.png)

![손 주변에서 본 위치 경계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v1/images/position_hands.png)

## 회전 경계

![정면에서 본 Euler 회전 경계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v1/images/rotation_front.png)

![측면에서 본 Euler 회전 경계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v1/images/rotation_side.png)

![손 주변에서 본 Euler 회전 경계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v1/images/rotation_hands.png)

## 실제 경계 포즈

| 케이스 | 기타 위치 (m) | Euler XYZ (deg) |
|---|---:|---:|
| `reference` | `-0.325, 0.000, 0.650` | `67.5, 75.0, 157.5` |
| `position_x_min` | `-0.500, 0.000, 0.650` | `67.5, 75.0, 157.5` |
| `position_x_max` | `-0.150, 0.000, 0.650` | `67.5, 75.0, 157.5` |
| `position_y_min` | `-0.325, -0.150, 0.650` | `67.5, 75.0, 157.5` |
| `position_y_max` | `-0.325, 0.150, 0.650` | `67.5, 75.0, 157.5` |
| `position_z_min` | `-0.325, 0.000, 0.650` | `67.5, 75.0, 157.5` |
| `rotation_x_min` | `-0.325, 0.000, 0.650` | `45.0, 75.0, 157.5` |
| `rotation_x_max` | `-0.325, 0.000, 0.650` | `90.0, 75.0, 157.5` |
| `rotation_y_min` | `-0.325, 0.000, 0.650` | `67.5, 50.0, 157.5` |
| `rotation_y_max` | `-0.325, 0.000, 0.650` | `67.5, 100.0, 157.5` |
| `rotation_z_min` | `-0.325, 0.000, 0.650` | `67.5, 75.0, 135.0` |
| `rotation_z_max` | `-0.325, 0.000, 0.650` | `67.5, 75.0, 180.0` |

이미지 원본과 케이스별 pose/state 기록은 `native/` 아래에 보존했습니다. 상세 검사 결과는 `comparison.json`을 참조하세요.
