# trunk 추가 검사 변경 사전 검수 V3

요약 판정: **문제없음**. **Critical: 0 / Warning: 0 / Suggestion: 0**. 추가된 미실행 diff만 검수했으며 Source V2 CPU 탐색으로 진행 가능하다. 이전 V2 검수 기록과 consumed V1은 보존했다.

- [search_right_arm_wrap_upright_v2.py:103](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v2.py:103): final capsule map에 Torso/Spine을 추가하고118행에서 각각≥20mm를 요구한다. 실제 fixed-lower XML에서 두 body의 첫 geom은 `capsule`이고 `fromto`/radius가 존재해 `CapsuleBodyDistance` 키 생성과 일치한다. Chest30mm 및 나머지 수락 조건은 유지된다. body 고정 뒤의 상수 잔차를 다시 추가한 변경은 없다.
- [run_right_arm_wrap_upright_v2.py:26](/home/ajou/yigyu/3/stability_adapter_2/run_right_arm_wrap_upright_v2.py:26): V1 대비 변경은 Torso/Spine/Chest↔any guitar의 `trunk_guitar_contacts` 추가뿐이다. 기존 Chest field와 native state 전후 exact 검사를 유지하며 이전 callback을 먼저 실행해 같은 endpoint row에 읽기 전용으로 붙인다. 초기화4개 patch·기존 제어·힘·gain에는 차이가 없다.
- [analyze_right_arm_wrap_upright_v2.py:89](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_upright_v2.py:89): 기존1200행 검증 뒤 trunk 필드를 필수로 요구하고 endpoint presence를 집계한다. 누락 필드를 접촉0으로 대체하지 않는다. uniform G39 translation residual/rotation·Chest presence/positive와 실제 자세 비교 방식은 그대로다.
- leaf V2의 추가 문단은 source Torso/Spine20mm 및 native trunk raw 진단을 명시하며 source clearance를 cooked 비관통 인증으로 설명하지 않는다. Source before pin의 leaf/asset 및 `A.glob('*.py')`가 현재 수정 source·분석기와 새 runner V2를 포함하고 종료 재대조한다.

새 source/runner/분석기 AST 통과. V1 wrapper/source SHA가 이전 검수와 exact하다. 실제 형상 수락과 native trunk 접촉은 아직 실행하지 않은 후속 검증이며 이 변경이 수락 또는 접촉0을 보장한다는 뜻은 아니다.

현재 검수 SHA256:

- Plan V2: `660fce8f67af16ef89642bea911697175a1a3f755f367d8bb9c0be2d735f3a9b`
- Source V2: `4dd4f3f2e3116979663d600c25336948756c8b37d76f1fb3d4529692889f4b29`
- runner V2: `773f7f982c5f8dc5075839bfe373b75ae184210ddfa9cd45fec920696a504ee1`
- 분석기 V2: `6af68da6ecdb2a1b3ed44b9608a4bdd1b80abc709d0c7ae9e52b506ad53a3d46`

지정된 이 검수 기록만 생성했다. Source/native/producer를 실행하지 않았고 다른 담당자 파일을 수정하거나 되돌리지 않았다.
