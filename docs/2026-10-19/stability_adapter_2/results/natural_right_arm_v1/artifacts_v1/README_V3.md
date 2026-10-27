# Natural right-arm · native 2/3 비교

> V3 정정: native 3의 +12 mm 조건은 상완 목표가 아니라 전완의 초기 world 기준점을 올린 조건입니다. 나머지 비교 내용은 V2와 같습니다. V2 원문은 보존했습니다.

이 문서는 실제로 완료된 두 5초 조건을 함께 정리합니다. 사용자 사진은 정성 참고일 뿐 정확한 3D 재구성 기준이 아닙니다. 이전 native 11의 교차 팔 자세는 정지 유지 후보였으나 연주 자세로 자연스럽지 않아 채택하지 않았습니다. [초기 장면 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/artifacts_v1/initial_pose_pair.png)와 native 2 원래 프레임은 [v1 문서](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/artifacts_v1/README_V1.md)에서 볼 수 있습니다.

![native 2와 native 3의 실제 0·2·5초 whole_body 프레임 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/artifacts_v1/native2_native3_timeline_comparison.png)

## 결과 비교

두 실행 모두 root/하체 고정, 스트랩 OFF, 왼팔·왼손을 기타에서 떼고 왼손 grip 없이 기타를 자유롭게 둔 5초 정지 진단입니다. 음악 actor/policy는 0입니다. native 3은 전완의 초기 world 기준점을 +12 mm 올린 front160mm_lift12mm 비교 조건입니다.

| 관측값 | native 2 · front160mm | native 3 · front160mm_lift12mm |
|---|---:|---:|
| body bounding-box 중심 초기 대비 이동 | 163.447 mm | 194.398 mm |
| actor-root 초기 대비 이동 | 287.455 mm | 264.687 mm |
| 초기 대비 전체 SO(3) 회전 | 62.320° | 76.809° |
| 2→5초 body 중심 이동 / 회전 변화 | 9.884 mm / 3.348° | 1.690 mm / 0.646° |
| 오른 전완 접촉 표본 | 1077/1200 | 179/1200 |
| 오른상완 / 왼팔·왼손 접촉 표본 | 8/1200 / 0/1200 | 0/1200 / 0/1200 |
| Head 접촉 표본 | 0/1200 | 812/1200 |

표의 접촉 count는 240 Hz physics endpoint 1,200개 기준이며 접촉력·모멘트 기여를 나타내지 않습니다. native 3의 Head raw lambda count는 N 단위 힘이 아니므로 힘처럼 표시하지 않습니다. native 3은 2→5초 변화가 작아졌지만 그 전에 크게 이탈·회전한 자세에 머문 것이며, Head 접촉 812/1200과 전체 회전 76.809°로 거절된 조건입니다. native 2는 Head 접촉이 없고 전완 접촉이 더 자주 관측됐지만 기타 중심 이동 163.447 mm·회전 62.320°로 유지에 실패했습니다. 따라서 natural-arm shape reference는 native 2이며, 어느 조건도 기타 유지 성공으로 보지 않습니다.

이미지의 각 칸은 저장된 actual native frame을 사용합니다. 화면상 겹침으로 실제 PhysX cooked 관통/여유를 보증하지 않습니다. 새 학습이나 물리 실행은 이 문서 작업에서 추가하지 않았습니다. native 진단은 5초 완료 2회와 Jacobian gate에서 약0.125초에 중단된 native 1회입니다.

## 영상과 원자료

![native 2 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/natural_right_arm_v1/front160mm_whole_body.mp4)
![native 2 손 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/natural_right_arm_v1/front160mm_hands.mp4)
![native 3 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/natural_right_arm_v1/front160mm_lift12mm_whole_body.mp4)
![native 3 손 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/natural_right_arm_v1/front160mm_lift12mm_hands.mp4)

- [네 영상 source/copy SHA manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/natural_right_arm_v1/manifest_v2.json) · [video README v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/natural_right_arm_v1/README_v2.md)
- [native 2 verification](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/analysis_v1/verification.json) · [native 2 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/native_v2/front160mm/report.json)
- [native 3 verification](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/analysis_v2/verification.json) · [native 3 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/native_v3/front160mm_lift12mm/report.json)
- [사용자 reference.jpeg](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/reference.jpeg)
- [입력·출력 provenance v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/artifacts_v1/provenance_v2.json)
