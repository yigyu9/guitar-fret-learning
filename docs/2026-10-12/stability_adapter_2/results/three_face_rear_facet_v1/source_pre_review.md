# Rear thumb facet source 검색 실행 전 독립 검수

검수일: 2026-10-08. **요약 판정: 문제없음.** 최종 미소비 source와 실행 계약의 사전 검수를 완료했다. Critical/Warning/Suggestion 없음. 이 기록은 실제 후보 검색 결과나 native admission 통과를 대신하지 않는다.

검수한 [search_rear_thumb_facet.py](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet.py:1)의 SHA256은 `3f26ff1fa49ed1a3e7c4ee666043a735e7b0160f8230807172d9913cc4443dc1`이다. [실행 계약](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_REAR_FACET_EXECUTION.md:1)의 SHA256은 `b9b0fa54a059ce978e25b81ab63a63c5756b5ec9cf2708feec56f0aaa7784fca`다. 이 SHA 이후 source가 바뀌면 해당 변경은 이 검수의 완료 범위에 포함되지 않는다.

## Critical

없음.

## Warning

없음.

## Suggestion

없음.

## 확인 결과

- [phase/trial 경로:11](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet.py:11), [소비 보호:29](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet.py:29) — 새 result/trial 경로를 사용한다. 기존 검수·복사본을 담은 result 디렉터리의 존재는 허용하되 attempt/proposal이 있거나 새 trial 디렉터리가 존재하면 재소비를 막는다. 검수 종료 시 attempt/proposal 및 새 trial 디렉터리는 없었다.
- [입력 봉인:33](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet.py:33), [이전 source 보존](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v1/previous_search_source_preservation.json) — 직전 v2 proposal의 검수된 입력 mapping을 이어받아 대조하고, 직접 읽는 직전 proposal·이전 producer 복사본/보존 기록·새 producer·계획·inventory를 추가한다. 직전 producer의 실행 전후 SHA `16f58c3ba4382d159c9be13e065925f867d57bc9e95db2b92cf203cff64d94b6`가 원 파일·새 phase의 exact 복사본·보존 기록과 일치한다. 기존 v2 source를 수정하는 구현이 아니다.
- [bounds:73](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet.py:73) — 팔12±0.05rad, 엄지5±0.10/0.20rad를 native/Aug19/팔 C02±0.3rad/기존 절대 목표 offset±0.3rad와 교차하며 float32 representable 내부 경계로 좁힌다. 저장 입력으로 bounds 함수만 독립 실행하여 첫 단계 lower/upper가 직전 v2 sensitivity와 exact 같은 것을 확인했다. 두 번째 단계의 팔 경계는 그대로고 엄지만 넓어지며 실제 제한 때문에 일부 엄지 축은 비대칭이다. 17개 좌표·시작점 포함·빈 교집합 거절을 확인했다.
- [facet 선택:133](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet.py:133) — 초기 thumb3 활성 source face normal을 G-root로 회전하고 +GZ dot>0.75인 triangle 중 면적 최대를 선택해 중심을 anchor로 삼는다. 기존 native 관측 feature와 nearest source anchor는 별도 진단 기록에 유지한다. 선택 anchor의 scope는 새 source centroid이며 해부학적 pad/cooked 인증으로 설명하지 않는다.
- [확장 단계:248](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet.py:248) — 첫 ±0.10rad 두 clearance 후보 중 통과가 있으면 ±0.20rad 단계를 생략한다. 둘 다 실패했으면 확장 단계의 첫 성공 뒤에도 두 번째 clearance를 검사한다. 최종 condition을 AST로 분리해 첫 단계 통과/모두 실패/확장 첫 통과 경우를 검증했다. 이 흐름은 최대 통과 후보 2개를 유지한다.
- [거리 구간:215](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet.py:215), [간격 gate:346](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet.py:346) — 중심화 mm 좌표에서 convex hull 내부 witness와 finite quad의 convex-combination witness를 최적화한다. Witness 거리 상한과 동일 방향의 전체 vertex support-plane 하한을 기록한다. Solver 성공만으로 gate를 통과시키지 않고 하한≥0.3mm 및 상한≤1mm를 기존 0.1µm 수치 tolerance와 함께 확인한다. 함수만 분리해 world offset이 있는 synthetic box/finite patch의 알려진 0.25/0.30/0.70/1.00/1.10mm 거리 다섯 경우를 검사했다. 각 실제 거리가 계산 구간에 수치 오차 범위 내 포함됐으며 거리 오차는 `1e-10m` 미만, 최대 상·하한 차이는 `1.70e-17m`였다. 이는 helper 검사이며 실제 후보의 거리 구간은 실행 후 별도로 확인해야 한다.
- [rear witness:349](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet.py:349) — hull witness→rear patch 방향의 +GZ dot>0.75와 hull witness의 rear plane 바깥 배치를 함께 검사한다. Zero-distance witness는 통과하지 않는다. 대표점 patch 내부 여유2/3mm와 전체 source 교차·양손/비인접 왼손 교차·상향 palm proxy 검사도 유지한다. Facet normal의 목표 방향은 계속 soft term이다.
- [다른 앞손가락:245](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet.py:245), [float32 후보 구성:288](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet.py:288) — 기존 index/middle/ring/pinky16 초기 관절각은 17개 변경 축에 포함되지 않는다. 저장 q0가 이미 float32 exact이며 native initial DOF 위치와 exact 같음을 대조해 `q0.astype(float32)`가 나머지64를 바꾸지 않는 것을 확인했다. 앞손가락 source 높이 residual은 기존 부드러운 선호로 유지한다. Arm 변경으로 앞손가락 world pose가 달라지는 것은 허용된 FK 결과이며 앞손가락 pose 고정으로 설명하지 않는다.
- [trial/row:357](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet.py:357), [절대 목표 확인:379](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet.py:379) — 이전 input trial을 복사해 왼손33 초기 설정과 offset만 갱신한다. 기타 translation/initial Z·절대 strap rest length `1.1018469719600776m`·left-arm kp/kd scale1은 원 trial에서 유지한다. 저장 81개 절대 목표는 compose 후 float32 exact 검사를 거친다. 시작점과 확장 lower/upper 극점 두 경우의 compose를 독립 계산해 전체81 target exact를 확인했다. 몸통9·오른팔손 초기각과 target, 자유기타/하체 고정/제어 구성은 재사용 경로를 따른다.
- [fresh runner 입력:56](/home/ajou/yigyu/3/stability_adapter_2/run_three_face_shape_readback.py:56), [fresh row LA 검사:127](/home/ajou/yigyu/3/stability_adapter_2/run_three_face_shape_readback.py:127) — 새 proposal의 rows에는 label·alpha·clearance·accepted·trial path/SHA·예상81 초기각/target·source state와 `absolute_strap_rest_length_m`가 있다. Trial의 다섯 top-level 필드·왼손33 offset schema·기존 LA/gain을 저장 기준으로 확인했다. Proposal facets는 기존 앞손가락을 유지하면서 thumb/palm을 이번 anchor로 바꾸므로 fresh source audit의 point/normal field와 맞는다. Fresh runner는 명시한 새 `--proposal`과 accepted row를 받아 초기각/target/LA/FK 및 실제 readback을 별도로 검사해야 한다.

## 방법과 범위

직전 exact source와 새 source의 diff, 실행 계획, 저장 기준 입력 및 기존 fresh runner의 소비 필드를 읽었다. UTF-8 decode와 Python3.8 `compile`을 통과했다. Main은 호출하지 않았고 nested bounds/거리 helper 및 확장 condition만 AST로 분리해 메모리에서 확인했다. Native scene 생성·물리 step·실제 source 후보 검색·trial 파일 생성은 수행하지 않았다. 본 담당자는 이 검수 파일과 직전 후처리 검수 파일 외에 다른 파일을 변경하지 않았다.

남은 검증은 실제 source 검색이 남긴 bounds·facet 선택·거리구간·모든 거절/통과 이유·입력 SHA 전후 대조이며, source통과 후보가 있다면 fresh native admission과 실제5초 영상/원자료 검사다. 이번 사전 검수는 source 접촉·cooked clearance·지속 지지·안정성의 성공 판정이 아니다.
