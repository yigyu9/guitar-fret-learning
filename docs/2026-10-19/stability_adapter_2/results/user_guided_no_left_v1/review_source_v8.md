# 사용자 기준 no-left V6/V7 제외 및 V8 source 검수

요약 판정: 현재 V8 upper50 수락값은 문제없음. source 보완과 원자료 보존을 확인했으며 현재 실행 중인 native의 완료·안정성·actual LEFT 0은 별도 후속 검수 대상이다.

Critical: 0

## Critical

- 현재 수락 후보의 추가 필수 수정 없음. [search_user_guided_no_left_v8.py:37](/home/ajou/yigyu/3/stability_adapter_2/search_user_guided_no_left_v8.py:37)은 정확 AABB/unit face support가 10mm를 증명하지 못한 **capsule/sphere만** segment–convex distance−radius로 추가 검사한다. mesh/box의 미보장 쌍은 계속 제외하고 여유 기준은 10mm로 유지한다. 구는 동일 끝점 두 개로 환원하므로 식이 같은 점–convex 거리다. 현재 asset의 human geom은 capsule/box/mesh이며 sphere 실행 사례는 없다.

## Warning

- 수치 projection과 엄밀 하한의 구분: [V8:39](/home/ajou/yigyu/3/stability_adapter_2/search_user_guided_no_left_v8.py:39)가 호출하는 [segment_convex:16](/home/ajou/yigyu/3/stability_adapter_2/om_axilla_source_geometry_v3.py:16)은 SLSQP 수치 최적화다. 성공·hull feasibility는 검사하지만 임의 입력에서 최적 거리의 엄밀한 하한 증명까지 검사하는 것은 아니다. 현재 upper50의 fallback 9쌍은 검수자가 반환 최근접 방향의 **별도 exact support 분리 하한**을 계산해 모두 10mm 이상, 최솟값 18.756890mm임을 확인했다. distance 값과 그 하한 차이 최대 4.083nm라 현재 수락값은 충분한 여유를 가진다. 일반적 무오차 certificate로 확대해 표현하지 않는다.
- 상속 값의 수락 조건: [V8:76](/home/ajou/yigyu/3/stability_adapter_2/search_user_guided_no_left_v8.py:76)은 LEFT 및 전체 clear/model/frozen69를 확인하지만 V7의 `RH_target_error_m<.025`, T/U/H 근접 상한은 직접 다시 gate하지 않는다. 현재 upper50은 각각 RH오차 21.204mm, T/U/H 2.400/.199/.509mm로 모두 기존 기준을 만족한다. upper65는 LH오차 38.193mm로 현재 제외되며 RH오차도 27.016mm로 기존 RIGHT 기준 미달이다. 다음 source 버전에는 동결한 RIGHT/body 기준도 명시적으로 재확인하고 최종 제외 사유에 이 RH 미달을 함께 표시한다. 현재 소비 파일은 수정하지 않는다.
- source와 native 범위: [PLAN V8:6](/home/ajou/yigyu/3/stability_adapter_2/USER_GUIDED_NO_LEFT_PLAN_V8.md:6)의 face-used 원본 hull/primitive 간격은 cooked 접촉과 구분한다. 초기 LEFT 10mm와 ball norm<160°도 동작 중 LEFT 0·안정성을 보장하지 않는다. 기존 OFF task0/active left gravity·PD와 사용 right/body finite/velocity/Jacobian guard를 유지한 원물리 결과로 판정한다.

## Suggestion

- 다음 버전에서 fallback 결과를 저장할 때 최근접 방향 support 하한도 기록·gate하면 numerical 거리와 certificate 의미가 명확해진다. 현재 consumed V8는 보존한다.

## 확인 근거

- V6/V7/V8 diff는 계획된 초기 배치·목표/residual/여유 판정 변경이며 실제 controller/helper를 바꾸지 않는다. V6는 사용자 선호 주변 G centre 범위와 Thorax 근접을 조정했고, V7은 상완 gap 양수 penalty·오른 distal 범위/선호·LEFT 목표를 조정했다. V8은 V7 LEFT12만 새로 fit한다.
- V6 두 후보는 source 전체 audit clear여도 analytic upper gap `−0.277978/−0.861340mm`이고 RH오차 `33.120/34.076mm`, LH오차 `74.283/26.561mm`로 제외됐다. proxy audit clear를 analytic primitive 통과로 해석하지 않았다.
- V7 두 후보 모두 제외. T/U/H gap은 upper50 `2.400182/0.199079/0.509272mm`, upper65 `1.249441/0.505293/0.406488mm`이며 source clear지만 LH오차 `100.635/126.500mm`, face-axis 미보장 각각 8쌍이었다. 미보장 자체를 실제 겹침으로 단정하지 않았다. native 사용 0이다.
- V8은 2후보 중 upper50만 수락: LH오차 `0.508001mm`, certificate 1780쌍 미보장 0. upper65는 certificate는 통과하지만 LH오차 `38.192848mm`로 제외됐다. 두 후보 모두 model bounds/frozen69 exact이며 LEFT ball norm은 upper50 `[36.400463,74.126430,59.934274,84.451254]°`, upper65 `[36.400463,66.400478,29.880487,105.483206]°`다. 손가락42·오른팔·body/head 69축 및 기타 초기 회전/배치를 V7에서 유지한다. full upper 30/45/65 alias와 fresh upper witness exact도 확인했다.
- 두 V8 후보의 FK/G 배치를 정적 probe로 재구성해 certificate를 독립 재계산한 결과 저장 JSON과 정확히 일치했다. upper50 fallback 9쌍의 추가 support 하한 검사는 위 Warning에 수치를 기록했다. 추가 physics step 0.
- 실제 geometry source는 V1 3후보, V2/V3/V5/V6/V7/V8 각 2후보로 **15후보/5수락/10제외**다. 초기 진단 1개는 별도이며 V4 package는 geometry solver 0이다. V6 1002핀/V7 1003핀/V8 1005핀과 이전 source 전체 input map을 현재 파일 SHA와 비교해 불일치 0을 확인했다. V6/V7/V8 source AST 검사 통과. V8 discovery·guitar discovery/full map 저장 후 contract/FK/형상을 구축하고 종료 전 전수 SHA를 확인한다.
- V8 :77의 `raw_MuJoCo_proximity_scope` 및 [PLAN V8:9](/home/ajou/yigyu/3/stability_adapter_2/USER_GUIDED_NO_LEFT_PLAN_V8.md:9)는 상속 raw query가 V7의 옛 LEFT 진단임을 명시한다. 현재 certificate와 혼동하지 않는다.

검수 source V8 SHA: `c73f206a6fc00639a52c1db91f8b12149a7437fda79b76b164e44f2bd8119255`.

검수자는 이 문서만 생성했으며 source·설정·assets·native 원자료를 수정하거나 물리를 실행하지 않았다.
