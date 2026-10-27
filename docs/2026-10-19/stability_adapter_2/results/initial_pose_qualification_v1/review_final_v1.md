# 초기 자세 적합성 시험: 코드·물리·측정 최종 검수

요약 판정: **문제없음 — 실험 수행과 수정된 측정 범위 기준**. 미해결 Critical 0건, Warning 0건. **정지 초기후보는 유망하지만 양손 연주용 기본값 확정은 보류**하는 결론이 증거와 맞다. 왼손 시험은 실패했으며 검수 통과를 안정화 성공으로 해석하지 않는다. 산출물 복사·최종 문서/영상 색인 검수는 별도다.

## 주요 결과 독립 대조

|조건|물리 경과·완료|최대 BB 이동 mm|최대 SO3 °|왼팔·손 raw 접촉 없는240Hz 표본|
|---|---|---:|---:|---:|
|원래 near 정지|10s·완료|2.810968562|0.692878869|145/2400|
|새 cold 정지 V3|10s·완료|2.718870860|0.826450615|2400/2400|
|새 cold EW6 타현|5s·완료|6.145018627|4.236779277|1159/1200|
|새 cold 왼손 cycle|7.283333s·보호 중단|115.508460350|30.527374500|1084/1748|
|새 cold G world Z+3mm|10s·완료|5.181435723|0.957880006|2400/2400|

- 모든 조건의 초기0초와 매240Hz 기타 상태에서 BB local centre `[0,-0.4,-0.055937985]m`를 정규화 쿼터니언으로 world 변환해 전체 이동·SO3 최대를 독립 재계산했다. [qualification_summary_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/qualification_summary_v1.json:1)과 일치한다. 위치/회전 최대의 발생 시각이 같다는 주장은 없다.
- 완료4조건의 오른손목·손 접촉은0이다. 타현 중 왼팔/손 접촉41step은 실제로 존재하며, 전체1159/1200 무접촉을 항상 무접촉이라고 바꾸면 안 된다. 원래 near 정지는 대부분 왼손 접촉이 있어 왼손 독립 지지의 대조군이라고 할 수 없다.
- 새 정지 마지막2초의 구간 기준 최대 변화는0.015909777mm/0.006184922°, Z+3mm는0.024140485mm/0.009668302°로 원자료와 맞다. 이는 초기 대비 최대 변화와 다른 값이다.

## 왼손 중단·접촉·비교 범위

- [runner V2](/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_qualification_v2.py:75)의 actor-root20cm/회전35° guard 중 실제 원인은 이동이다. 매240Hz 원자료에서 actor-root가7.279167초에 처음20cm를 넘고,60Hz sample이7.283333초에203.188648mm로 중단한다. SO3 최대30.527375°는35° 미만이다. BB115.508460mm와 actor-root203.188648mm는 다른 위치 지표다.
- A 유지3–4.5초는 실제 **LH:thumb3와 LH:index3**의 동시 양의 접촉이360/360step이다. 모든 손가락의 지지를 뜻하지 않는다. openA6–7초는 왼팔/손 raw접촉 없는240/240step이지만 Chest 양의 접촉0, R_Shoulder91/240, R_Hip240/240이다. 원시 행은 force N이나 인과적 지지 분담이 아니다.
- 실패 중 오른 RH:thumb3/RH:middle3 접촉은6.345833–7.095833초181step이며 각 step에 양의 lambda가 있다. 이때의 오른손 접촉은 별도 완료 타현 조건의0접촉과 구분한다.
- 실제로는 move_B 초기에 끝나 B잡기·B유지·마지막놓기에 도달하지 않았다. 부분 분석기는 [analyze_initial_pose_qualification_v2.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_initial_pose_qualification_v2.py:39)에서 completed=false를 보존하고 나머지 측정 불변식만 검사한다. 성공한16초 시험으로 소급하지 않는다.
- [station 대조](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/left_station_comparison_v1.json:1)를 양쪽 실제 target 로그로 재계산했다. 새A−이전A는 G좌표[-1.170453,+42.047834,−0.034344]mm다. 새 초기14초는 이전B분리 위치였으므로 A/B 명칭과 body/q/G/제어 참조가 함께 바뀌었다. 초기 몸통 하나의 인과 비교가 아니다.

## 제어·입력·재현

- 5조건 native before map 현재 SHA를 모두 대조했다. baseline1,300개, 나머지 각각1,303개가 일치한다. 실제 humanoid/G XML과 compiler.meshdir의 모든 mesh 선언 union106개를 각 map에서 확인했다. 직접 config/candidate/native reference와 실제 사용 소스·자산이 보존된다.
- 실제 contacts의 step이1..N 연속이고 최종81 effort의 매240Hz coverage·finite·cap, 목표각 model limit·rate, 소유하지 않은 목표 exact를 독립 확인했다. EW6는다른75목표, left cycle은다른48목표, 정지는전체 목표를 유지한다. 이것은 실제 관절 상태를 고정한다는 뜻이 아니다. 초기·최종 Pelvis/하체 native 상태 동일성을 확인했으며 runner는 매60Hz에도 이를 검사한다.
- 기타는 자유·strap OFF이며 새로운 지속 pose 덮어쓰기·부착·기타 force 경로는 없다. 기존 body9+arms24 유한 human 제어와 POSITION 나머지48을 구별한다. 최종81 effort 파일은 실제 제출 EFFORT 벡터이며 접촉력·모든 drive의 측정 토크가 아니다.
- 초기 source_v4는14초의 실제 q/G를 속도0·새 solver 상태로 재구성하고 L_Wrist_y 약0.0000438094rad 및 기타[+1.846939,+0.415309,−1.359105]mm 보정을 기록했다. 모델한계/native FK/초기속도0/source proxy gate가5조건 모두 true다. 초기 L_Wrist_y 여유0°, R_Thorax_y0.000046104°, L_Thorax_z0.001200406°로 매우 작다. 이는 native scalar 한계이지 해부학적 world축 인증이 아니다.
- source_v4의 새 right_block witness가 유한 task에 사용된다. inherited face/finger/path·body_side_lean 메타는 과거 호환 기록이며 새 자세/연속경로 접촉 인증이 아니다. 실제 판정은 새 proposal와 native 관측에 근거한다. source discrete IK·capsule clearance도 cooked 연속 비관통 인증과 구분한다.
- static_v2의 completed/inputs_unchanged=false는 보존한다. renderer helper pin 변경1개를 native-before SHA와 같은 재구성 사본으로 검증한 범위와, 원래 before 사본 보존을 구별했다. 새static_v3는 full guard true이며 초기값·전체60Hz trace·240Hz contacts·최종 상태·최종efforts5개가 V2와 바이트 동일함을 독립 확인했다. batch V1은 사용 중단 상태이고0-step 카메라 실패와 source import 실패도 보존한다.
- Z+3mm는 reset 시 support motor local 참조도 다시 계산하므로 고정 앵커 외란 복원력이나 일반 강건성 인증이 아니다. 학습 checkpoint/곡 수행/수동평형 검증도 아니다.

## 관절 측정 scope Warning 해결

초기 측정의 maximum actual joint overshoot는60Hz81각 표본이었다. 이를 전체240Hz 실제 최대처럼 설명한 부분은 경고했으며, 원래 분석/summary/README는 보존하고 새 [권장 README V2:36](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/README_v2.md:36)와 [보충 brief V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/approved_artifact_addendum_v2.md:1)에서 해결했다.

[새240Hz audit](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/joint_240hz_audit_v1.json:1)의32개 입력 SHA와 소스를 확인하고 별도 재계산했다. pre0..N−1+finalN의 active33 위치 overshoot는 baseline0.0200193°, static0.00160168°, strike0.00780008°, leftcycle0.22019847°(L_Wrist_y,5.541667초), Z+3mm0.00277135°다. 원래60Hz81의 실패0.19815°와 다르다. 나머지48위치의240Hz 최대는 기록 범위 밖이다. 전체81속도240Hz 최대는각각0.499782/0.375186/3.203110/2.556389/0.399174rad/s로 독립 계산과 맞고 모두50미만이다. 실제 속도와 목표 변화율 한계를 구분한다.

## 타현·부분 후처리

- 원본 RELEASE를 direction/global-zone/lane과 실제 V7 command window로 집계했다. down3.2–3.55초는6→1(3.245153–3.506191초), up3.75–4.45초는1→6(3.833421–4.363378초)이다. legacy3.95초 up cutoff가 처음2줄을 누락한다는 정정이 맞으며 원본 detector/과거 집계를 수정하지 않았다. 가상피크 왕복 검출은 checkpoint/곡 수행 성공이 아니다.
- [부분 renderer V2](/home/ajou/yigyu/3/stability_adapter_2/render_initial_pose_qualification_v2.py:13)는 완료 또는 명시된 safety displacement 부분 실패만 받아 native_completed=false를 보존한다. floor(N/8)+1개와 실제 camera/physics 끝 간격을 확인한다. 직접 helper를 포함한 모든5후처리 input map은 현재 일치한다.
- 5조건 총25,028개 G측 world feature를 초기 rigid G-link offset과 해당240Hz root pose로 독립 재구성했다. 저장 world point와 최대 차이2.98e−7m 미만(링크 pose float 오차 범위)이며 모든3,819개 annotated view frame은 in-frame다. 채움/빈원·색·X-ray·고정 크기 의미는 유지한다.
- 실패 마지막 실제 PNG를 직접 열었다. 7.267초와 ‘보호 중단 직전·16초 목표 미완료’가 명시된다. 마지막camera1744step=7.266667초, 물리1748step=7.283333초,219frame/30fps=7.3초를 구분한다. B단계 snapshot을 만들어내거나 끝을 정지 평형이라고 표시하지 않는다.

검수자는 이 보고서만 작성했다. 물리를 재실행하거나 원래 소스·결과·과거 검수 문서를 수정하지 않았다.

## 검수 시점 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_qualification_v2.py`: `8726cfed0af3c2d1d2e41954f58ecd5672038c0274ff072221b7a7485e64814c`
- `/home/ajou/yigyu/3/stability_adapter_2/prepare_initial_pose_qualification_v4.py`: `54bce2810e771d4f361daf501844f418b084d2e247baf2f5b57dbd5469cb21cb`
- `/home/ajou/yigyu/3/stability_adapter_2/analyze_initial_pose_qualification_v2.py`: `73de81f362a34fc0023b860da7518797c21fac7d11ffb1ba2127f53297674966`
- `/home/ajou/yigyu/3/stability_adapter_2/render_initial_pose_qualification_v2.py`: `d075cc712a5c50697d6de0e0ca9797686d03a7a712e64a5275bae7b92b75e929`
- `/home/ajou/yigyu/3/stability_adapter_2/audit_initial_pose_qualification_240hz_v1.py`: `09461c4127b48d68cb62498752ed8fadfd27a831b867c2f1088362335891e685`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/qualification_summary_v1.json`: `25f8941d1d54bb9d4f777adfc4aeff963b4464d126d04d138c48383f0d37a04f`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/joint_240hz_audit_v1.json`: `1a2baf54aeee1ae8e37d84a44f22ac6e031b89f239281f95112758854d595e0e`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/README_v2.md`: `44327b6947a385d0822b19a88b34f9e9d22ebfafda5358de0ffae056f3fe9b42`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/approved_artifact_addendum_v2.md`: `57641fa8983c5f8868b363552e186e50e9d4d88858e06d587b3a7f1343b562d6`
