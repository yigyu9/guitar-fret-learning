# 독립 검수 — contact footprint source 검색 v2

**요약 판정: 문제없음.** 현재 2개 후보의 거절 판정은 타당하다. 승인 후보 0개, 신규 native 초기화·물리 실행 0이다. 소비된 v1/직전 feature-map phase는 수정하지 않았다. 직전 feature-map v2·PNG 3개의 최종 독립 검수는 [v1 검수 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v1/review.md)에 완료 범위를 남겼다.

## Critical

없음.

## Warning

없음. 현재 후보의 명시적 거절을 뒤집는 버그는 확인하지 않았다.

## Suggestion

- [search_contact_footprint_v2.py:284](/home/ajou/yigyu/3/stability_adapter_2/search_contact_footprint_v2.py:284) — 간격 gate의 수치 epsilon은 `1e-7m`(0.1µm)이지만 사용한 [closest_polygon:57](/home/ajou/yigyu/3/stability_adapter_2/audit_palm_side_target.py:57)의 성공/feasibility 검사는 최적성 오차를 보장하지 않는다. 독립 support-plane 거리 하한과 witness 거리 상한의 차이가 이번 계산에서 최대 0.954µm였다. 현 후보들은 다른 명확한 거절 사유가 있어 판정에 영향이 없다. 향후 0.3/1.0mm 경계에 가까운 후보는 primal–dual 거리 구간 또는 정밀 재계산으로 gate를 확인할 것을 권장한다.

## 확인 결과

- [v2 source](/home/ajou/yigyu/3/stability_adapter_2/search_contact_footprint_v2.py)의 실행 SHA `16f58c3ba4382d159c9be13e065925f867d57bc9e95db2b92cf203cff64d94b6`가 전후 동일하고 exit 0이다. `proposal.json`의 봉인 입력 SHA 불일치는 0개이며 추가된 closest-polygon source도 봉인 입력에 포함돼 있다.
- v2의 anchor·17개 축명·중앙차분 Jacobian·representable float32 bounds는 검수된 v1 `sensitivity.json`과 정확히 같다. 실제 두 후보 모두 이 17개 초기각만 변하고 다른 64개는 동일하다. native/Aug19/C02/current/기존 절대 목표의 bounds 교집합과 목표–초기각 ±0.3rad 조건을 만족한다. 초기각 clipping은 없다.
- 기존 절대 81개 목표 배열과 기타 전체 body state가 기준과 동일하다. 초기 trial 복사는 LA·gain·root/하체 물리 고정·기타 p/q·기존 제어 설정을 유지하는 경로다. 승인 후보가 없어 fresh native 설정/FK 대조와 실제 목표 제출은 이번 범위에 없다.
- [source 검색 soft term:207](/home/ajou/yigyu/3/stability_adapter_2/search_contact_footprint_v2.py:207)은 thumb3/palm 전체 source hull의 neck face-plane 분리와 관측 facet 법선의 면 방향 선호를 추가한다. 이는 source 설계용 선호이고 실제 cooked 접촉면/해부학적 pad/힘 방향 인증이 아니다. 대표점 목표·상향 palm proxy와 나머지 손가락 초기각 유지 조건이 유지된다.
- [대표점·facet 기록과 gap gate:271](/home/ajou/yigyu/3/stability_adapter_2/search_contact_footprint_v2.py:271)에 유한 patch 투영/경계 여유와 source hull–finite patch 간격이 추가됐다. 대표점과 triangle 3개 vertex의 projection/경계/signed-plane metric을 독립 재계산해 일치했다. **triangle extent는 관찰하고 overhang은 허용하는 scope**다. triangle 전체가 ≥2/3mm 내부 여유를 가진다고 주장하지 않는다.
- 두 후보의 저장 source state로 전체 human–guitar convex intersection을 다시 계산해 교차 0을 확인했다. 코드의 양손/비인접 왼손 교차 gate도 유지되고 해당 기록은 모두 0이다. 대표점이 가까운 것만으로 통과시키지 않는다.
- 0.3mm 후보: thumb 목표 오차 3.200398mm, rear patch 밖 경계 여유 −0.200727mm, hull–finite patch 거리 0.232736mm로 거절됐다. palm 대표점 여유 4.721738mm, hull 간격 0.305334mm다.
- 0.7mm 후보: thumb 목표 오차 3.412930mm, rear patch 밖 경계 여유 −0.395092mm로 거절됐다. thumb hull 간격 0.421864mm, palm 대표점 여유 4.960842mm/palm hull 간격 0.493368mm다.
- 저장 QP witness 두 점 사이 거리가 기록과 일치한다. 독립 분리평면 하한/거리 상한(mm)은 0.3mm 조건 thumb `0.231782…0.232736`, palm `0.305325…0.305334`; 0.7mm 조건 thumb `0.420968…0.421864`, palm `0.492631…0.493368`다. 이 구간들이 현재 간격 거절/통과 판정을 바꾸지는 않는다.
- 현재 두 후보는 실제 5초 시험 대상으로 쓰면 안 된다. source clear는 cooked clearance 인증이 아니며 실제 엄지 후면/손바닥 옆면 지지·연속 접촉·안정화 성공은 아직 없다.

검수는 변경 diff, SHA 대조, read-only source geometry·bounds·projection·거리 witness 재계산으로 수행했다. native scene 생성·physics step은 호출하지 않았다. 원본 v1 wrapper 시작 실패는 성공한 v2 검색 결과와 별도이며 이번 코드/결과 검수의 근거는 exit 0 v2 실행이다.
