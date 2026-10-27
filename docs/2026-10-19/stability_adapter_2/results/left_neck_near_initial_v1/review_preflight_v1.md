# 사전 코드 검수 — 왼손 넥 주변 비접촉 초기 배치

요약 판정: **문제없음.** 현재 코드 Critical 0 / Warning 2 / Suggestion 0. source 계산 중이므로 후보의 수락·실제 native 초기 및 동역학 성공은 아직 승인하지 않는다. 수락된 float32 후보와 native 초기 gate를 통과하는 범위에서만 다음 단계가 가능하다.

- [helper:17](/home/ajou/yigyu/3/stability_adapter_2/left_neck_near_geometry_v1.py:17)의 taper 폭은 실제 guitar_neck1 OBJ 양끝 폭/길이와 맞고, [helper:32](/home/ajou/yigyu/3/stability_adapter_2/left_neck_near_geometry_v1.py:32)의 아래면+X/뒤−Z/앞+Z normal 부호도 맞다. palm 옆면의 slope normal, back−.008m/front 기본+.0093m는 source neck 규약이다. 기타-local 방향을 world 수직이나 joint suffix 축으로 바꾸지 않는다. hand selected facet의 world→G 점/normal 변환과 hull 평면의 회전·평행이동 수식도 맞다.
- [source:41](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_near_v1.py:41)의 소유권은 L_Thorax부터finger까지33이며 frozen48이다. 모델 bounds 교집합에서 적합하고 최종float32각으로 FK/측정을 다시 계산한 뒤 [source:101](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_near_v1.py:101)의 전체source audit와 fixed48 조건을 검사한다. source_audit는 인간–기타·양손 및 tree거리>2 비인접 인간 교차를 검사한다. 손–넥/손가락 간 hull separation residual도 있다. 최종 candidate는 genuine predicted_human_poses를 새로 저장한다. 기타p/q와 오른지지 제어를 바꾸는 경로가 없다.
- [runner:76](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_near_v1.py:76)은 actual 초기48 DOF·nonleft body 전체·기타 전체state exact와81 q_ref를 검사하고, actual pose vs candidate FK 및 facet 면 관측을 기록한다. rejected 초기도 첫capture 뒤 중단하므로 물리 진행과 초기 진단을 구분할 수 있다. 기존constructor/OM물성·right12 EFFORT/69POSITION·단일81/240Hz owner·기타 자유/strap OFF/root하체 고정 및 source first-done 연결 경로는 같다.
- 실행 전 두 지적을 해결했다. [runner:53](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_near_v1.py:53)은 native_faces가 실제로 읽는 외부 FACETS JSON을 attempt SHA closure에 포함한다. [runner:96](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_near_v1.py:96)의 PD/mass exact 비교를 기록만 하지 않고 [runner:118](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_near_v1.py:118)의 gate에 포함했다. source inputs_before에는 이runner가 없고 현재 기존source 입력 SHA 불일치0이다. native 미소비 수정이 source 소비원본에 영향을 주지 않음을 확인했다.

Warning 1 — [helper:42](/home/ajou/yigyu/3/stability_adapter_2/left_neck_near_geometry_v1.py:42)의 signed plane gap은 선택collision facet 점과 정의된 면 proxy 사이 값이다. patch·target오차와 normal alignment도 함께 보지만, 유한면 전체 최소거리·실제 cooked collider·연속시간 비접촉·해부학적 손바닥/지문 pad 인증이 아니다. source convex/capsule 근사의 교차 검사와 actual pose 기반 같은proxy 관측도 이러한 인증으로 확대하지 않아야 한다. 실제초기/진행중 contact와 동역학은 따로 기록해야 한다.

Warning 2 — source5~8mm는 목표이며 current gate의 목표오차 허용범위와 달성 gap은 별개다. 후보의 실제 gap·patch오차·finger 분산·모델/frozen48 및 G초기값을 수락 결과에서 재대조하고 native 초기/5초 및 첫done을 분리해야 한다. 손을 넥 근처에 둔 것만으로 fret 준비·원checkpoint source profile 적합이나 양손 연주 성공을 보장하지 않는다. 상속된 이전 right-support metadata는 오른쪽/역사적 문맥이고 새left33는 `left_neck_near`와 top-level81/FK가 권위다.

검수는 계획/helper/source/runner의 read-only 코드·source OBJ 규약·입력 경계·Python3개 AST에 한정한다. 추가 native/학습/정책추론·기존소스 수정0. 아직global search 결과가 없어 후보별 숫자·genuine FK·모델/입력SHA 완결성 및 native release는 후속 확인 사항이다.

검수 SHA256:

- 계획: `697652a4c0f99cceb653ce3f85658568003ae3a826ec7ac2cc47114d1c25899b`
- geometry helper: `c71e2251b36136384137e478f47c81e0e0b88b9e43cb1b88a69661720ac4cad8`
- source search: `ed88558733fec8421a9d3fb91d569c18e22d29e4243dc69137f838af715345ef`
- 수정runner: `20706636076b71bd44cb6a792e9e8e268695f5380ff698565a31b4ded2a63a7d`
