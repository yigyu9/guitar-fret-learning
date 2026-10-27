# 오른쪽 어깨·팔의 전방 배치 비교

오른쪽 어깨를 조금 앞으로 옮기려는 요청에 대해, baseline과 shoulder target 20 mm / 10 mm 조건을 실제 native 5초 진단으로 비교했습니다. 10 mm 조건을 현재 후보로 권합니다. 이 비교는 자연스러운 연주자세나 반복·장기 안정성을 인증하지 않습니다.

## 실제 native 캡처

![기준 자세와 10 mm 후보의 실제 native whole-body 초기/5초 프레임](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1/baseline_vs_forward10_wholebody_timeline.png)

![같은 whole-body 원본 이미지에서 자른 어깨·팔 확대 crop. 새 카메라 시점이 아님](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1/baseline_vs_forward10_shoulder_crop.png)

어깨·팔 그림은 실제 native whole-body frame을 같은 좌표 범위로 잘라 확대한 2D crop입니다. 겹침·가림을 물리 관통 판정으로 해석하지 않습니다.

## 초기 target과 실제 위치는 다릅니다

두 조건 모두 초기 기타 81개 q, G position/quaternion, Chest/Torso/Spine 전체 초기 상태를 baseline과 정확히 같게 유지하고 오른쪽 Shoulder의 초기 3 scalar 각도만 바꿨습니다. gain, 중력, 10 N upper-effort cap, strap OFF, left grip OFF, root/lower 고정, 기타 자유·기타 직접힘 없음 조건은 같았습니다. Source 전방 방향은 수평 world +Y이며, target displacement는 관절 scalar 각도나 실제 runtime 이동량과 동일하지 않습니다.

| 조건 | 초기 elbow: baseline 대비 | 5초 elbow: baseline 대비 동시 시각 | 초기 palm: baseline 대비 | 최종 body bbox 중심 / 전체 회전 | 최대 body 중심 / 전체 회전 |
|---|---:|---:|---:|---:|---:|
| shoulder target 20 mm | +19.749402 mm | +20.512162 mm | +2.998498 mm | 9.402108 mm / 3.005495° | 10.232100 mm / 3.246177° |
| shoulder target 10 mm (추천) | +9.893081 mm; world Δ[−3.984809,+9.893082,+0.374317] mm | +10.710865 mm | +1.720963 mm (최종 +2.570061 mm) | 9.425103 mm / 2.887575° | 10.455249 mm / 3.343712° |

20 mm 조건은 최종 전체회전 3° 기준을 넘어 선택하지 않았습니다. 10 mm 결과는 최종 전체회전 2.887575°였고 최대는 3.343712°입니다. 최대 변화와 최종값은 별도 값입니다. elbow 이동과 palm 이동을 구분합니다.

## 접촉과 범위

두 조건은 각각 5초/1200 physics step/300 control step, 영상 151 frames/30 fps/5.033333초로 완료했습니다. 10 mm의 late upper contact는 120/120, total upper 1173/1200, R_Hip1194/1200; head/left/right distal은0입니다. strict 35%+upper-rim contact는1062/1200입니다. 20 mm의 late upper 120/120, total upper1178/1200, R_Hip1195/1200; head/left/distal0, strict region1102/1200입니다. 접촉 표본·raw lambda는 힘 크기나 해부학적 지지의 인증이 아닙니다. 이는 움직임이 없는 5초 native 진단이며 별도 elbow motion, 학습, 음악 평가는 하지 않았습니다.

![기준 whole-body 영상과 10 mm whole-body 영상의 side-by-side 파생 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/shoulder_forward_v1/baseline_vs_forward10_side_by_side.mp4)

개별 원본 전신·손 영상은 [색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/shoulder_forward_v1/INDEX_V1.md)에서 확인할 수 있습니다. 자세/조건 숫자는 [검증 요약](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/result_summary_v2.json), [20 mm verification](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/analysis_v1/shoulder_forward20mm/verification.json), [10 mm verification](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/analysis_v2/shoulder_forward10mm/verification.json), [contact region 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/contact_region_v2.json)에 연결했습니다. Source geometry 겹침 검사는 PhysX cooked clearance 인증이 아닙니다.
