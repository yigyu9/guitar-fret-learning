# 사용자 기준 no-left V5 source 검수

요약 판정: 문제없음. LEFT 초기 회전벡터의 pi 경계 여유를 추가하고 V2의 오른팔·몸통·머리·손가락·기타 값을 보존한 변경과 실제 두 source 결과가 일치한다. 현재 실행 중인 native의 안정성은 이 검수 판정에 포함하지 않는다.

Critical: 0

## Critical

- 추가 필수 수정 없음. [search_user_guided_no_left_v5.py:68](/home/ajou/yigyu/3/stability_adapter_2/search_user_guided_no_left_v5.py:68)는 LEFT 네 ball의 norm 150° 초과 soft residual을 추가하고, :72–73은 float32 저장 후 norm을 다시 계산해 모든 값 `<160°`를 수락 gate로 요구한다. 기존 scalar 모델 한계·exact primitive 10mm certificate·source audit·frozen69 gate도 유지된다. XML 네 LEFT ball의 축이 정규직교이며 LEFT 배열 순서가 각 body의 x/y/z이므로 이 norm은 [FK:24](/home/ajou/yigyu/3/stability_adapter_2/upper_arm_static_geometry_v1.py:24)의 회전벡터 축 norm과 일치한다.

## Warning

- 초기 제한의 범위: [PLAN V5:6](/home/ajou/yigyu/3/stability_adapter_2/USER_GUIDED_NO_LEFT_PLAN_V5.md:6)의 160°는 source 초기값 gate이며 이후 동작의 회전 표현 전환을 보장하지 않는다. 실제 qdot/finite/modelcap 안전 guard를 유지한 native 결과로 완료 여부를 판정한다. 이 보완을 실제 안정성 성공으로 선행 해석하지 않는다.
- 실패 로그의 시계: [PLAN V5:3](/home/ajou/yigyu/3/stability_adapter_2/USER_GUIDED_NO_LEFT_PLAN_V5.md:3)의 이전 `native_upper50_v5_static`은 실제 2 physics step/0.008333초, **완료 control 0**이다. `controls.json` 0행, endpoint 2행, body 최종명령 2행과 일치한다. tracking/two-block 3행 중 step2는 중단 전에 생성한 요청이며 세 번째 적용 명령이 아니다. position submission 1행을 완료 control 1로 세거나 `physics=4×completed_control`을 이 부분 기록에 적용하면 안 된다. 0step 호환 실패도 성능 실험과 분리한다.
- 상속된 raw 진단: [source V5:74](/home/ajou/yigyu/3/stability_adapter_2/search_user_guided_no_left_v5.py:74)의 `**prior`는 V2 `left_guitar_pairs_under10mm`를 보존한다. 이 필드는 V5 재측정이 아니다. 현재 V5 certificate와 actual native LEFT 접촉을 구분한다. 이전 V2 내접 캡슐 certificate 제한은 [기존 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/review_source_v2.md:11)에 보존되어 있다.

## Suggestion

- 추가 없음. 원본 및 기존 실패 로그는 보존하고 후속 분석에서 시점·완료 여부를 명시한다.

## 확인 근거

- `search_v5/search.json`의 입력 1002개 SHA가 모두 현재 원본과 일치했다. before pin→contract/FK/형상 구성→종료 전 전수 SHA 순서와 XML/manifest mesh 범위는 이전 검수된 V3와 같다. 계획·source는 새 버전이고 기존 V2/V3/package/helper는 수정되지 않았다.
- 두 후보 모두 source clear, exact LEFT certificate 1780쌍 미보장 0, 모델 한계와 수락 gate 통과. upper50 LEFT ball norm은 `[28.418122,68.673463,69.760074,149.999124]°`, upper65는 `[26.920229,67.084045,70.153344,142.487430]°`다. 저장 로그와 독립 norm 재계산이 exact로 일치했다.
- V2의 나머지 69축 exact 유지. V3와 기타 초기 p/q 및 예측 G39 exact. fresh full upper gap·기존 full/30/45/65 alias가 모두 같은 witness이며, 상완/RHip gap은 upper50 `0.582393/0.398633mm`, upper65 `0.595011/0.395822mm`로 동일하다. 두 config의 candidate SHA도 일치한다. alias 추가는 새 solver가 아니다.
- diff는 출력/계획 버전, palm orientation soft weight 10→1, q regularizer 0.1→2, norm soft/hard gate 및 로그, legacy full-upper alias 추가다. neck gap 17mm/elbow G_Z 80mm soft 목표·source certificate·left gravity/PD·OFF helper·right/body 실제 제어 및 안전 한계를 바꾸지 않았다.
- 과거 실패 native의 초기 L_Wrist norm `186.518954°`, x `−167.477700°`에서 final `+133.156054°`, final x qdot `−100.000366rad/s`를 원자료로 확인했다. 실패 메시지는 `unsafe native joint state before physics`이며 source 수락이나 기타 지지 안정성과 다른 판정이다. 입력 보존 true, forbidden call 0이다.

검수 SHA: source V5 `619408ed91985fa2f240e541114e59d1cf5263ae2238ea41822768ed7b5d39d3`, PLAN V5 `267f5b1af51fc9d2bd47783d219b4c652ba0569409c54055537643e56c2633b2`.

검수자는 이 파일만 생성했다. source·설정·assets·실패/native 원자료 수정 및 물리 재실행은 하지 않았다.
