# 사전 코드 검수 — 정적 source gap과 순차 초기각 적합

요약 판정: **문제없음.** 추가 Critical 0 / Warning 2 / Suggestion 0. source3/4 계산 방법은 native physics 변경이 아니다. source3 두후보는 미수락이며 source4 계산 결과·native release는 아직 미판정이다.

- [source3:59](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_near_v3.py:59)의 body ID는 `human/` 이름으로 매핑한다. [build_probe:38](/home/ajou/yigyu/3/stability_adapter_2/initial_overlap.py:38)는 각body를 worldbody 직속에 평탄화하므로 FK의 world position/quaternion을 해당 model.body_pos/body_quat에 넣는 [source3:91](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_near_v3.py:91) 수식이 맞다. quaternion은 xyzw→wxyz로 변환한다. mj_kinematics는 forward kinematics이며 mj_step·시간적분·native 상태setter가 없다.
- `mj_geomDistance`의 설치 API 문서는 두geom 최소 signed distance를 반환한다고 명시한다. cutoff .004m는 neck .002m/self .0005m 벌점보다 크므로 먼쌍이 cutoff로 잘려도 벌점0인 범위다. 가까운쌍의 최적화 잔차만 정적source query로 바꾸고 최종float32 q/FK·전체mesh LP source_audit 및 runner2의 actualpose 재감사는 유지한다.
- source3의 station20/60 두후보는 source_clear였으나 facet 점오차42.65~87.88mm로 둘다 accepted false다. 원source1/2의 CPU중단과 source3 완료·거절을 별개로 보존하며 native0 상태다. source_clear만으로 지정면 배치 성공을 선언하지 않은 판정이 맞다.
- [source4:103](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_near_v4.py:103)의 coarse 단계는 collision_weight0으로 점/방향 제안을 찾는다. fine은 기본collision_weight1을 복구하고 최종float32 측정·full LP수락조건도 같다. thumb 선택facet normal 선호6→18 변경은 계획V4에 명시했다. left33/model bounds·frozen48·기타초기값·5/8mm 목표 및 controller/물성·runner2는 변하지 않았다.

Warning 1 — 정적 MuJoCo signed source gap은 실제 PhysX penetration/contact 측정이 아니다. coarse 단계의 중간각은 겹칠 수 있으며 native 이동 경로로 승인하지 않는다. fine/full LP와 actual 초기pose audit를 통과한 최종초기각만 후속native 후보가 될 수 있다. 모델·원형상 source 검사와 cooked 비접촉·해부학적pad·연속시간 contact 인증도 구분한다.

Warning 2 — `max_nfev=100`은 least_squares의 단계별 종료 제한이다. finite-difference Jacobian의 추가잔차 호출을 포함한 전체 함수호출수가100회라는 뜻은 아니다. source4는 coarse/fine 각 단계의 비용이 있으며 반복수·계산중단·후보거절을 native 물리횟수와 혼동하지 않아야 한다. 아직candidate acceptance/global source4 SHA 완결성 및 실제gap/FK/native 결과를 검증하지 않았다.

기존 [preflight1](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/review_preflight_v1.md:1)~[preflight3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/review_preflight_v3.md:1)의 면proxy·실제달성거리·readonly state/native gate 범위도 유지한다. 추가source 탐색/native/정책추론/학습/원본 수정0. 설치 API 문서·코드 diff·완료source3 결과·관련Python AST만 읽기 검토했다.

검수 SHA256:

- source3: `efb5bba260ac5ce9431bc874ab60a6203b8bca22018220d124e4cd827ddc1b34`
- 계획V3: `b7d7a0ac9d43b48459637ec278463af22c45e3230cd945d31efdc7256c3562e9`
- source4: `7e0ddeb11795360ac8150804ac6abebe40bee986cf3705d2f4367e9d8b315cba`
- 계획V4: `da89d38c10709657d758caa419a7427a7907d59e8f4bf43de1024e4bfad5d249`
- 동일native runner2: `1337e4a462be2e49331632198590096a8645f48d200703613f5d45780cae91cb`
