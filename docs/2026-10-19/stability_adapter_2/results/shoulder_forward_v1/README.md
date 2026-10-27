# 오른 어깨에서 팔을 조금 앞으로 뺀 자세

오른쪽 어깨3개 초기각만조정해 팔꿈치를 기타앞판바깥 수평방향(+worldY)으로 약1cm 뺐습니다. 몸통19°/기타초기p/q/나머지78개초기각은 유지했습니다. root·하체고정·strapOFF·leftgripOFF·기타자유·직접기타힘없음 조건입니다. 실제 초기Elbow+9.893081mm,5초에는이전동시각보다+10.710865mm였습니다. Palm은초기+1.720963mm로팔꿈치1cm와다릅니다.

[그림 설명·자세/접촉 표·영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1/README_V3.md:1)이 정식 결과 안내입니다. 문서V1/V2는 표현 보정 전 보관본입니다.

![이전과 새1cm 후보 실제5초 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/shoulder_forward_v1/baseline_vs_forward10_side_by_side.mp4)

## 실제5초 비교

| 조건 | 종료 바디중심 이동 | 종료 기타 회전 | 후기 상완접촉 | 판단 |
|---|---:|---:|---:|---|
| 이전19° |9.548665mm|2.995398°|120/120|비교기준|
| 팔꿈치앞2cm 목표 |9.402108mm|3.005495°|120/120|3°미만 회전gate 실패·미채택|
| 팔꿈치앞1cm 목표 |9.425103mm|2.887575°|120/120|정지gate 통과·추천 후보|

추천1cm의실행중 최대이동10.455249mm/회전3.343712°는최종값기준과별도입니다. 머리/왼팔손/오른원위팔접촉0,전체상완1173/1200(positive rawlambda1162),오른Hip1194/1200. 실제상완근위35%+기타위볼록영역presence1062/1200(positive237)은이전1117/1113과달라졌습니다. 전체상완접촉과지정영역의힘수반접촉을구분하며rawlambda는N/힘분담으로변환하지않습니다. 겨드랑이해부학적지지·fret/strike연주·새자세팔꿈치운동·장시간·반복성은미검증입니다.

두새시험은각5초/1200physicssteps/300controls/151frames30fps입니다. 기타는초기이후자유롭게이동·회전합니다. 오른12유한EFFORT와다른69POSITION/중력보상·PD·사람상완가상점요청상한10N을기존과같게유지했습니다. 손부착/직접기타힘/state덮어쓰기없음. source기하검사는native cooked형상관통인증이아닙니다.

## 계획·초기값·검증

- [계획V2](/home/ajou/yigyu/3/stability_adapter_2/SHOULDER_FORWARD_PLAN_V2.md:1) · [완료 기록](/home/ajou/yigyu/3/stability_adapter_2/SHOULDER_FORWARD_COMPLETION_V1.md:1)
- [추천초기81각·기타p/q](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/search_v2/shoulder_forward10mm/candidate.json:1) · [환경설정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/search_v2/shoulder_forward10mm/config.json:1)
- [종합실측](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/result_summary_v2.json:1) · [실제접촉분류](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/contact_region_v2.json:1) · [native 독립검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/review_native_v1.md:1)
- [영상6개 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/shoulder_forward_v1/INDEX_V1.md:1) · [변경 파일/줄 번호](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/CHANGED_FILES_v1.md:1)

source1의3D평행이동목표 실패와이전computedmetadata상속오류를보존하고미채택했습니다. source2는전방투영목표와작은직교변위를명시하고현재metadata를재계산했습니다. 새run2는계획2/search2를핀했습니다. 공용자산/기존stability_adapter/소비실험·계획·로그·영상과학습기본값을변경하지않았습니다.
