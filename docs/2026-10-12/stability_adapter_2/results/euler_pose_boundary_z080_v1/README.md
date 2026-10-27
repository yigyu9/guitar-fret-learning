# Z=0.80m로 다시 렌더링한 기타 위치·회전 경계

사용자 요청대로 새 기준 기타 높이를 Z=0.80m로 두고 X/Y 및 Euler XYZ 경계를 다시 촬영했습니다. Z 행에는 이전 하한 0.65m와 새 기준 0.80m를 함께 표시합니다. Z 상한은 지정되지 않아 비워 두었습니다.

위치는 월드 기준 기타 actor root 위치입니다. 회전은 월드 기준 extrinsic Euler XYZ입니다. 새 기준 위치 `(-0.325, 0, 0.80) m`, 기준 회전 `(67.5, 75, 157.5)°`입니다. X/Y 위치 및 회전 경계 이미지는 모두 Z=0.80m입니다. 각 비교는 한 축씩 바꾸며, strap은 보이지 않게 했습니다.

모든 이미지는 Isaac Gym native 카메라에서 물리 step 0으로 생성했습니다. 이는 정적 시각 검토이며 실제 접촉·관통·안정성 인증은 아닙니다.

## 위치 경계

![위치 경계 정면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_z080_v1/images/position_front.png)

![위치 경계 측면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_z080_v1/images/position_side.png)

![위치 경계 손 시점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_z080_v1/images/position_hands.png)

## 회전 경계

![회전 경계 정면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_z080_v1/images/rotation_front.png)

![회전 경계 측면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_z080_v1/images/rotation_side.png)

![회전 경계 손 시점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_z080_v1/images/rotation_hands.png)

## 포즈 값

| 케이스 | 위치 X,Y,Z (m) | Euler XYZ (deg) |
|---|---:|---:|
| `reference_z080` | `-0.325, 0.000, 0.800` | `67.5, 75.0, 157.5` |
| `position_x_min` | `-0.500, 0.000, 0.800` | `67.5, 75.0, 157.5` |
| `position_x_max` | `-0.150, 0.000, 0.800` | `67.5, 75.0, 157.5` |
| `position_y_min` | `-0.325, -0.150, 0.800` | `67.5, 75.0, 157.5` |
| `position_y_max` | `-0.325, 0.150, 0.800` | `67.5, 75.0, 157.5` |
| `position_z_previous_065` | `-0.325, 0.000, 0.650` | `67.5, 75.0, 157.5` |
| `rotation_x_min` | `-0.325, 0.000, 0.800` | `45.0, 75.0, 157.5` |
| `rotation_x_max` | `-0.325, 0.000, 0.800` | `90.0, 75.0, 157.5` |
| `rotation_y_min` | `-0.325, 0.000, 0.800` | `67.5, 50.0, 157.5` |
| `rotation_y_max` | `-0.325, 0.000, 0.800` | `67.5, 100.0, 157.5` |
| `rotation_z_min` | `-0.325, 0.000, 0.800` | `67.5, 75.0, 135.0` |
| `rotation_z_max` | `-0.325, 0.000, 0.800` | `67.5, 75.0, 180.0` |
