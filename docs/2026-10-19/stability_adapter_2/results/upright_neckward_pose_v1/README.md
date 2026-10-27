# 덜 숙이고 넥 쪽으로 회전한 초기 자세

추천 후보는 기존 추가앞굽힘+2°/넥쪽yaw12°에서 −6°/19°로 조정한 자세입니다. 실제5초 종료에서 앞으로8.50°덜 기울고 넥 방향으로5.79°더 돌아갔습니다. 기타초기회전은같게설정하고오른팔과허벅지의받침을맞췄습니다. 스트랩과왼손지지없음·root/하체고정·기타자유·직접기타힘없음입니다.

자세/영상의 정식 안내는 [README_V2.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/artifacts_v1/README_V2.md:1) 입니다. V1은 표현 보정 전 보관본입니다.

![이전12°와새19° 실제5초 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upright_neckward_pose_v1/static12_vs_static19_whole_body_side_by_side.mp4)

![팔꿈치±5° 실제5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upright_neckward_pose_v1/native_v7/whole_body.mp4)

## 실제 결과

| 조건 | 종료 바디중심 mm | 종료 회전 ° | 후기상완 /120 | 판단 |
|---|---:|---:|---:|---|
| static_neckyaw30 | 6.377229 | 2.818339 | 0 | gate 실패·미채택 |
| static_neckyaw26 | 8.345834 | 2.743838 | 0 | gate 실패·미채택 |
| follow_neckyaw26 | 6.207858 | 2.282108 | 0 | gate 실패·미채택 |
| follow20_neckyaw26 | 8.104589 | 2.721095 | 0 | gate 실패·미채택 |
| static_neckyaw20 | 9.722709 | 3.001326 | 120 | gate 실패·미채택 |
| static_neckyaw19 | 9.548665 | 2.995398 | 120 | 추천 진단 후보 |
| elbow_neckyaw19 | 9.574004 | 2.990860 | 120 | 추천 진단 후보 |

19° 정지의 실행중 최대는 중심10.380810mm/회전3.313974°입니다. 최종 회전3°미만 gate 여유는0.004602°로 작습니다. 실제 팔꿈치±5°(약10.1°왕복)의 영향은 같은시각 정지 대비 최대.077660mm/.042115°였습니다. 정지/동작의 native초기전체와2.5초전trace는같습니다. 실제상완근위35%+기타위볼록영역접촉1117/1200,후기상완120/120. 머리/왼팔손/오른원위팔접촉0.

목표19°와실제Chest heading27.986843°를구분하며실제전경은39.846996°입니다. 해부학적겨드랑이/지지력분담,반복강건성,장시간 및 fret/strike연주는아직검증하지않았습니다. 신규5초7회영상14개와이전기준2개는보존했습니다.

## 계획·초기값·검증

- [UPRIGHT_NECKWARD_POSE_PLAN_V5.md](/home/ajou/yigyu/3/stability_adapter_2/UPRIGHT_NECKWARD_POSE_PLAN_V5.md:1) · [UPRIGHT_NECKWARD_POSE_COMPLETION_V1.md](/home/ajou/yigyu/3/stability_adapter_2/UPRIGHT_NECKWARD_POSE_COMPLETION_V1.md:1)
- [candidate.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/search_v2/bend-6_neckyaw19/candidate.json:1) · [config.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/search_v2/bend-6_neckyaw19/config.json:1)
- [result_summary_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/result_summary_v1.json:1) · [elbow_comparison_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/elbow_comparison_v1.json:1) · [contact_region_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/contact_region_v1.json:1)
- [INDEX_V2.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upright_neckward_pose_v1/INDEX_V2.md:1) · [CHANGED_FILES_v1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/CHANGED_FILES_v1.md:1)

run1 attempt는원PLAN_V1 SHA를핀하며20°의추가실행맥락은계획V4,19°/동작은V5에기록했습니다. 소비소스/원계획/실패/공용자산/이전실험은보존했습니다. 네트워크/보상/학습기본값변경없음.
