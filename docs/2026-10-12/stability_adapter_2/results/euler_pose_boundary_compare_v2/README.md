# 기타 위치·회전 범위 경계 이미지

제시한 각 위치·회전 경계에서 기타가 어떻게 보이는지 정적 장면으로 비교한 자료입니다. 캡처는 Isaac Gym native camera로 만들었고 물리 step은 0입니다. 이미지는 배치의 시각적 검토용이며 접촉·관통·안정성 판정을 뜻하지 않습니다.

범위 해석: X `[-0.50, -0.15] m`, Y `[-0.15, 0.15] m`, Z `>=0.65 m`, 월드 기준 extrinsic Euler XYZ X `[45,90]°`, Y `[50,100]°`, Z `[135,180]°`입니다. 입력의 X 역순은 오름차순 구간으로 정리했습니다. Z에는 상한이 없어 하한만 표시했습니다.

각 비교는 한 좌표만 바꾸고 나머지는 기준값에 둡니다. 기준 위치는 `(-0.325, 0, 0.65) m`, 기준 회전은 `(67.5, 75, 157.5)°`입니다. 위치 시트의 Z 하한과 기준은 같은 위치 포즈이며, 상한 칸은 지정되지 않은 상태를 나타냅니다. 모든 축을 함께 경계에 놓는 조합은 이번 이미지에 포함하지 않았습니다.

## 위치 경계

![정면 시점 위치 경계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v2/images/position_front.png)

![측면 시점 위치 경계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v2/images/position_side.png)

![손 시점 위치 경계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v2/images/position_hands.png)

## 회전 경계

![정면 시점 회전 경계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v2/images/rotation_front.png)

![측면 시점 회전 경계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v2/images/rotation_side.png)

![손 시점 회전 경계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v2/images/rotation_hands.png)

## 경계 포즈 값

| 케이스 | 위치 X,Y,Z (m) | Euler X,Y,Z (deg) |
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

원본 12개 native 장면과 포즈·상태 기록: [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v1/native](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/euler_pose_boundary_compare_v1/native).
시트의 한글은 나눔고딕으로 렌더링했으며, 원본 카메라 프레임은 잘라내거나 기하를 보정하지 않고 축소해 배치했습니다.
