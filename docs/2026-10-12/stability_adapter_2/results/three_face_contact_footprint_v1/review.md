# 독립 검수 — contact footprint source 검색과 직전 feature-map v2

**요약 판정: 수정 권장.** 현재 source 후보 2개를 모두 거절한 판정은 타당하다. 승인 후보 0개이며 새 native 초기화·물리 실행은 0이다. 향후 후보 승인에 사용하려면 아래 footprint 검사를 보완해야 한다. 코드·원자료·직전 frozen phase는 수정하지 않았다.

## Critical

없음. 현재 교차 후보를 통과시키거나 실제 시험 대상으로 만든 오류는 확인하지 않았다.

## Warning

- [search_contact_footprint.py:228](/home/ajou/yigyu/3/stability_adapter_2/search_contact_footprint.py:228) — `if max(anchor_error.values()) > 3:`만으로 대표점의 목표 근접성을 검사하고, [계획:29](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_CONTACT_FOOTPRINT_PLAN.md:29)의 대표점·인접 source facet 투영 내부 여부, 엄지/손바닥 경계 여유 ≥2/3mm, source 간격 0.3–1.0mm를 직접 검사하지 않는다. 목표 오차 ≤3mm는 이 조건들을 보장하지 않는다. 실제 선택 palm triangle의 Gz 범위는 0.3mm 후보 −7.441…11.999mm, 0.7mm 후보 −7.463…11.976mm로 요청 side patch 상단 9.3mm 밖까지 뻗는다. 후속 새 버전에 대표점·인접 triangle의 유한 patch 투영/최소 경계 여유와 실제 source 간격 metric·gate를 추가하고, 소비된 v1 입력·출력은 보존할 것을 권장한다.

## Suggestion

없음.

## 현재 source 검색의 확인 범위

- 실행 source SHA `feffb62ae1a6473a6704c10bfe8f3795e0b94ca36d9e9352805a24ba7c5ef781`가 전후 동일하고 exit 0이다. `proposal.json`의 봉인 입력 SHA를 현재 파일과 대조해 불일치 0개를 확인했다.
- 양의 raw lambda를 가진 저장 native contact의 body-local feature에서 선택한 active source hull 최근접 triangle을 독립 재계산했다. thumb3 triangle 786/거리 0.163660669mm, palm triangle 547/거리 0.039014632mm가 일치한다. 해부학적 pad 또는 cooked surface 인증이 아니다. thumb_pad는 probe 제외 상태다.
- 17개 축 모두 ±0.0001rad 중앙차분 G좌표 Jacobian을 재계산해 기록과 일치했다. 엄지 5축의 palm 미분은 0이며, 임의 관절 부호 대신 실제 FK 변화량이 기록돼 있다.
- 팔 12축 현재각 ±0.05rad, 엄지 5축 ±0.10rad와 native/C02 ±0.3rad/Aug19/기존 절대 목표 ±0.3rad의 교집합을 독립 계산했다. 저장 bounds는 모두 해당 교집합 안의 representable float32 값이다. 최종 초기각을 한계로 clipping하지 않는다.
- 각 후보의 실제 초기각 변화는 정확히 이 17개이며 나머지 64개는 기준과 동일하다. 전신 81개 절대 목표가 기준과 동일하고 최대 목표–초기각 차이는 각각 0.262814641/0.265541434rad다. 기타 전체 body state와 root/왼팔 체인 외 상태는 유지된다. LA·gain·물리 고정 설정은 기준 trial을 복사하는 경로다. 실제 fresh native 설정/FK 대조는 승인 후보가 없어 수행하지 않았다.
- human–guitar, 양손, graph-distance >2의 비인접 왼손 source hull 교차를 검사한다. 0.3mm 후보의 palm/thumb3 공통 내접반경은 0.214141/1.370114mm, 0.7mm 후보는 0.031669/1.336307mm다. 두 후보 모두 `source_human_guitar_intersection`으로 거절됐다. 양손/비인접 왼손 교차 기록은 없다. 이 반경은 source convex intersection proxy이며 물리 관통 깊이가 아니다.
- 소스 계산에만 scoped되어 있고 안정화 성공·면/힘 지지·cooked clearance를 주장하지 않는다. 현재 후보는 실제 5초 시험 대상으로 사용하면 안 된다.

## 직전 feature-map v2 최종 독립 검수

검수 대상은 [analyze_three_face_native_features_v2.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_three_face_native_features_v2.py), frozen phase의 `analysis_v2.json`, `feature_map.png`, `patch_distance.png`, `native_hands.png`, `README.md`다. 이전 phase 파일을 편집하지 않고 이번 검수 기록으로 범위를 보완한다. **이 범위는 문제없음.**

- 세 저장 실행의 15,511행(기준 4,346 / half 5,556 / zero 5,609)을 원본 contact/pose와 전수 대조했다. 기타 root G좌표 feature와 SDK 문서 부호 normal의 재계산 차이는 0이다. body/lambda/행 대응도 일치한다.
- 네 유한 polygon의 투영 내부 여부, signed-plane/경계/finite distance, SDK 부호와 반대 부호 dot를 독립 계산했다. 15,511×4 metric의 최대 수치 차이는 7.11e−15 수준이다. 기타/neck/fret/nut source geometry 25개를 active source와 초기 저장 pose에서 재구성해 vertex와 face가 일치했다.
- 양λ palm 요청 side-patch 내부 표본은 세 조건 모두 0이며 거리 21.105–22.783 / 24.390–29.806 / 25.996–28.382mm가 원자료와 일치한다. thumb3 rear 내부 표본 41/10/2행은 경계 분류이고 interior 지지 표본은 없다. index3/middle3 양λ는 주로 fret4/fret5이며 ring3/pinky3 contact 행은 없다.
- PNG 3개를 직접 확인했다. XY/YZ 축·mm 단위, body 색과 요청 patch/source 형상의 구분, front skin 9.3mm와 outer 11.230006mm의 구분, 양λ 거리 산점도와 무보간 설명이 코드·수치와 일치한다. 범례와 제목이 표본을 가리지 않는다.
- native montage의 3조건×0/0.5/5초 총 9개 원본 capture SHA와 리사이즈 후 내부 pixel을 각각 대조해 모두 일치했다. 저장 Isaac Gym frame의 재배열이며 새 render가 아니다.
- 로컬 SDK `struct_py.html:888`의 body0→body1 normal 문구와 v2의 기타측 부호 변환이 일치한다. 전면/옆면 outward와 반대인 관찰 dot를 geometry classification gate로 사용하지 않고 반대 부호도 별도로 기록한다. post-step pair 재구성 잔차는 수치적 관찰이며 COM/body-frame의 native 인증이 아니다.
- `configured_substeps=1`은 source 설정 근거이고 native SimParams readback은 `false`다. native COM query, cooked/해부학적 접촉면 인증, raw lambda의 N 변환, 연속 지지·안정화 성공은 수행하거나 주장하지 않는다. README에 이 한계가 명시돼 있다.

검수는 read-only 재계산과 이미지·SHA 대조로 수행했다. Isaac Gym 모듈을 import한 source probe 재계산은 native scene 생성이나 physics step을 호출하지 않았다.
