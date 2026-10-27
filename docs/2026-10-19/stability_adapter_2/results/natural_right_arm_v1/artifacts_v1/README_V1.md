# Natural right-arm · native 2 front160mm

이 정리는 전완 지지 형태의 실제 native 캡처와 5초 결과를 보존합니다. 앞선 native 11의 교차 팔 자세는 5초 정지 유지 후보였지만 연주 자세로는 자연스럽지 않아 채택하지 않았습니다. 사용자 사진은 정성 참고용이며 정확한 3D 복원 기준이 아닙니다.

![이전 native 11과 새 native 2의 실제 초기 렌더 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/artifacts_v1/initial_pose_pair.png)

![새 native 2 실제 0초·2초·5초 whole_body 캡처](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/artifacts_v1/native_v2_timeline_0_2_5s.png)

## 조건과 관측

새 native 2 `front160mm`는 root와 하체를 고정하고, 스트랩을 끈 상태에서 왼팔·왼손을 기타에서 떼고 왼손 grip 없이 기타를 자유롭게 두었습니다. 오른팔 초기 자세의 shoulder scalar q를 조정하고 손목 목표 조정 제한은 ±0.35 rad로 두었으며, 팔은 전완을 이용하는 지지 형태입니다. 기타를 고정하거나 손에 강제 부착하지 않았고 음악 actor·policy 호출은 0입니다.

| 항목 | 결과 |
|---|---:|
| 물리 실행 | 1,200 physics step / 300 control / 5.000초 |
| 영상 | 151 frame / 30 fps / 5.033333초 재생 |
| 초기 대비 기타 body bounding-box 중심 이동 | 163.447 mm |
| 초기 대비 actor-root 위치 이동 | 287.455 mm |
| 초기 대비 전체 SO(3) 회전 | 62.320° |
| 2→5초 body 중심 이동 / 회전 변화 | 9.884 mm / 3.348° |
| 오른 전완 접촉 표본 | 1077/1200 (240 Hz physics endpoint) |
| 오른상완 접촉 표본 | 8/1200 |
| 왼팔·왼손 / Head 접촉 | 0/1200 / 0/1200 |
| 최소 elbow-outside-shoulder 형상값 | 251.396 mm |
| shoulder scalar q 최대 편차 | 1.40° (`R_Shoulder_x` DOF scalar) |

팔 형상은 이전 교차 팔 자세보다 정성적으로 달라졌지만 기타는 5초 동안 크게 이동하고 회전했습니다. 따라서 이 결과는 자연스러운 팔 모양 후보의 시각·초기 정지 진단이지 기타 유지 성공이 아닙니다. `R_Shoulder_x`의 suffix를 world 회전축으로 해석하지 않습니다. elbow-outside 값은 기록된 형상 field이며 해부학적 적합성 판정이 아닙니다. 접촉 존재 횟수는 접촉력·모멘트 기여를 측정한 값이 아니며, 영상에서 보이는 겹침만으로 실제 PhysX 관통을 보증할 수 없습니다.

새 phase native 1은 point-Jacobian velocity mismatch 검증으로 약0.125초에 중단되어 완전 5초 시험이 아닙니다. native 3은 12 mm 상향 human-target 비교가 진행 중이며 이 문서에서는 결과나 선택을 주장하지 않습니다.

## 실제 영상과 기록

![새 native 2 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/natural_right_arm_v1/front160mm_whole_body.mp4)

![새 native 2 손 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/natural_right_arm_v1/front160mm_hands.mp4)

- [전신 영상 manifest·source/copy SHA](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/natural_right_arm_v1/manifest_v1.json)
- [원래 user reference.jpeg](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/reference.jpeg)
- [analysis verification](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/analysis_v1/verification.json) · [posture/shape trace](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/analysis_v1/posture_shape_trace.json)
- [native 2 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/native_v2/front160mm/report.json) · [initial values](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/native_v2/front160mm/initial_values.json) · [capture metadata](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/native_v2/front160mm/media/capture.json)
- [입력·출력 SHA provenance](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/artifacts_v1/provenance_v1.json)

이 파일과 그림은 완료된 캡처·검증 자료를 정리한 것입니다. 새 native 실행, 물리 변경, 재인코딩은 없었습니다.
