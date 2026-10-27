# 기타를 몸 쪽으로 붙인5조건 비교

3/6/10mm는5초를 완료했지만 후기Thorax 접촉은0이었다.20/30mm는기타actor-root 이동20cm로보호중단됐다. 기존waist 배치를 유지한다. **몸 쪽 접근만으로 두 블록 받침은 회복되지 않았다.**

| 몸 쪽 접근 | 실제 물리 경과 | 초기 대비 최대 바디 중심 변화 | 최대 SO3 변화 | 후기 Thorax | 결과 |
|---|---:|---:|---:|---:|---|
| 기준0mm |5초|11.831mm|6.095°|0/120|기존 기준 유지|
|3mm|5.000000초|12.621mm|6.718°|0/120|5초 완료, 두 블록 회복 안 됨|
|6mm|5.000000초|12.180mm|6.671°|0/120|5초 완료, 두 블록 회복 안 됨|
|10mm|5.000000초|17.550mm|8.231°|0/120|5초 완료, 두 블록 회복 안 됨|
|20mm|1.116667초|75.384mm|30.638°|중단|기타 actor-root 이동20cm 보호 중단|
|30mm|0.850000초|101.805mm|34.355°|중단|기타 actor-root 이동20cm 보호 중단|

비교용6mm 실제 영상이다. 현재기타를따르는 기존 관절 보정도 사용하며상완/허벅지/왼손손가락접촉이남아있다.

![6mm 접근 실제5초 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/native_inset6_static/media/whole_body.mp4)

[구현·초기값·한계·후속 계획](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_BODY_APPROACH_COMPLETION_V1.md:3) · [완료 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/analysis_static_v2/analysis.json:1) · [부분 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/partial_analysis_v2.json:1).

원본source/native/후처리실패·부분영상은보존한다. Source5수락/native3완료+2부분/4072physics/1018control/checkpoint0/학습0/새팔꿈치운동0이다. 부분통계는완료5초검증과다르다.
