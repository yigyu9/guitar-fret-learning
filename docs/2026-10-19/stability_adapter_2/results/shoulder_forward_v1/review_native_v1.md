# Native 검수 — 작은 어깨 전방 이동

요약 판정: **문제없음.** Critical 0 / Warning 2 / Suggestion 0. 10mm 후보의5초 정지 비교 gate 통과를 한정 확인하며20mm는 미채택이다. 추가 native/학습/소스 수정0.

- 두 조건 모두5초1200 physics/300 control을 완료했다. 2400행 상완 인간점·COM 점속도·cap10N·child Elbow/Wrist J열·posture·Jᵀ 합산/모델 clip을 원자료로 재계산했고 최대 합산 요청 오차8.88e−16Nm다. 600 control의 POSITION69/readback/state 보존, forearm force0, human right12만 단일 effort 제출·다른69 POSITION·root/하체 고정·strap OFF·자유 기타·금지 API0 계약이 유지된다. 관측 latch를 실제 토크 중단으로 해석하지 않는다.
- [실제 비교 producer:15](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/summarize_results_v2.py:15)의 고정78 scalar·기타 초기 전체state·Chest/Torso/Spine 초기state와 원19° baseline을 직접 대조했다. PD/mass도 exact다. 전체어깨 frame 원점의 약 .000067mm 차이는 float roundtrip 범위이며 어깨 원점의 의도적 평행이동이 아니다.
- [변위 비교:17](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/summarize_results_v2.py:17)를 native body pose로 재계산했다. 추천10mm의 실제 초기 R_Elbow 전방+9.893081mm,5초 동일시각 기존19° 대비+10.710865mm다. RH:palm은 초기+1.720963mm/5초+2.570061mm로 다른 양이다. 20mm는 Elbow 초기+19.749402mm/5초+20.512162mm, Palm 초기+2.998498mm다. Shoulder scalar 회전·팔 원호와 전방 projection을3D 평행이동으로 설명하지 않는다.
- 20mm는 최종BB9.402108mm/SO3 3.005495°로 기존<3° gate 실패다. 10mm는 최종BB9.425103mm/SO3 2.887575°,후기상완120/120·Head/왼팔손/오른원위접촉0으로 [정지 비교 gate:18](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/summarize_results_v2.py:18)를 통과했다. 10mm의2→2.5초 .074953mm/.045982°,2→5초 .338869mm/.193547°도 기록과 맞다. source1 두 거절·source2의 새 projection 정의/출력을 보존한다.
- native local feature+offset을 human/G world로 변환하고 캡슐 축 fraction≤.35 및 G상부영역을 raw로 재분류했다. [접촉 분류2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/contact_region_v2.json:1)의10mm presence1062/1200·positive237/1200,20mm1102/122가 일치한다. 최대 pair오차1.26e−7m/반경차 .433842mm로 quality 범위 안이다. 전체10mm 상완presence1173/positive1162 및 Hip1194와 지정영역 count는 다르다. Head/왼쪽/오른원위·전완·RThorax0을 확인했다.

Warning 1 — [결과2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/result_summary_v2.json:1)의 gate는 최종값이다. 추천10mm 실행중 최대BB10.455249mm/SO3 3.343712°는 최종10mm/3° 기준을 넘는다. 전시간 이내 유지·반복 강건성 또는 새팔 자세의 동작 인증으로 확대하지 않아야 한다. 이전19°의 팔꿈치 동작 결과는 이번 shoulder 초기값의 동작 시험이 아니다.

Warning 2 — 지정35% 상부영역의 양의 raw lambda는 기존19°1113/1200에서 새10mm237/1200으로 감소했다. presence1062와 이를 동일시하거나 전체상완positive1162를 ROI값으로 쓰면 안 된다. raw lambda는 N단위 지지력/힘·모멘트 분담·해부학적 겨드랑이 인증이 아니고, endpoint 표본은 연속시간 contact 인증도 아니다. 정지 gate 통과와 이 접촉 분포 tradeoff를 함께 설명해야 한다.

검수 시 입력904개 SHA 및 현재 summary 입력을 대조했다. 새 source2·관련 분석/명령 및 실제 변위·접촉 핵심 범위만 검사했으며, 최종 문서·PNG·영상 사본/provenance·main prefix와 이전 전체 보존 봉인은 후속 범위다. 이전 result1/contact1/producer1은 소비본으로 그대로 둔다.

주요 SHA256:

- 결과 summary2: `15d06f009d8a0dad774add1fe18caf1a90447bce3067479b31d6ba4dfbfd77b0`
- 접촉 분류2: `6cd8ad6a1cda08f10264c8a276f17d7f44dca9b8164ac7bc13d18967dcbefdcf`
- 비교 producer2: `bb953673bb898b75a196f8444484264ae2176519cadb3ee9a5f415077ebb0886`
- 20mm verification: `b97430bb08d102b4e592e684e9450caf70ce95bf8e8d7964ef0ac616606771a9`
- 10mm verification: `0758d78037a8dc4b9fbb98879802df93af9bbd31b761cc1359690647b915f2b9`
