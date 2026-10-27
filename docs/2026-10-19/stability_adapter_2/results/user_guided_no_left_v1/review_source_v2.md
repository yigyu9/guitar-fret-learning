# 사용자 기준 no-left source V2 및 후속 보완 검수

요약 판정: 현재 V3 source·V4 metadata package·OFF helper V2는 문제없음. V2 certificate의 필수 보완은 소비 원본을 유지하고 새 V3에서 해결했다. 이 판정은 CPU source와 코드 사전검수이며, 실제 5초 안정성·LEFT 접촉 0의 판정은 후속 native 원자료로 해야 한다.

Critical: 0 (현재 보완본). V2 단독 certificate에는 아래 역사적 결함이 있었다.

## Critical

- 현재 보완본에서 추가 필수 수정 없음. [search_user_guided_no_left_v3.py:26](/home/ajou/yigyu/3/stability_adapter_2/search_user_guided_no_left_v3.py:26)는 캡슐 끝점과 반경의 정확한 world AABB를 쓰고, :35는 unit guitar face normal에 대한 정확한 최소 support `min(end·n)+d−r`를 쓴다. 양수 s를 얻는 face는 guitar hull의 모든 점에 `n·x+d≤0`을 만족하므로 두 형상 사이 거리가 s 이상이다. AABB의 최소 거리도 실제 형상 거리의 하한이다. mesh/box의 양방향 face-plane 계산도 같은 논리로 유효하다. 미보장 쌍은 제외한다.

## Warning

- 역사적 V2 한계: [search_user_guided_no_left_v2.py:21](/home/ajou/yigyu/3/stability_adapter_2/search_user_guided_no_left_v2.py:21)는 [plot_neck_palm.py:23](/home/ajou/yigyu/3/stability_adapter_2/plot_neck_palm.py:23)의 `count=[8,8]` 캡슐 내접 mesh를 certificate에 사용했다. 이는 원 캡슐의 거리 하한을 보장하지 않는다. 반경 30mm·축 길이 200mm의 수치 반례에서 unit normal 방향 support가 2.979mm 부족하고, polygon gap 11.489mm일 때 정확한 capsule gap은 8.511mm다. V2 두 후보는 다른 미보장 쌍 때문에 모두 제외되었고 native 사용 0이었다. V2를 재인증하지 말고 이 제한과 V3 보완을 함께 보존한다. [PLAN V3:3](/home/ajou/yigyu/3/stability_adapter_2/USER_GUIDED_NO_LEFT_PLAN_V3.md:3)에 같은 범위가 명시되어 있다.
- 상속된 진단의 시점: [search_user_guided_no_left_v3.py:73](/home/ajou/yigyu/3/stability_adapter_2/search_user_guided_no_left_v3.py:73)의 `**prior` 때문에 `left_guitar_pairs_under10mm`는 V2 raw MuJoCo query를 그대로 담는다. V3에서 갱신한 `face_used_left_10mm_certificate`와 혼동하면 안 된다. 현재 V3의 raw MuJoCo 재측정이나 접촉값으로 표현하지 말고 V2 이력으로 표시한다. 이 상속 필드는 수락 gate에 쓰이지 않는다.
- source 범위: face-used guitar hull·원본 primitive에 대한 보장이다. PhysX cooked 형상과 실제 접촉 또는 무제어 평형을 보장하지 않는다. [PLAN V3:6](/home/ajou/yigyu/3/stability_adapter_2/USER_GUIDED_NO_LEFT_PLAN_V3.md:6)의 구분을 유지하고 actual LEFT 접촉 0·OFF task 0·5초 완료 여부를 별도로 검사한다. 0step 호환 실패와 2step 진단 중단도 완료 실험에 합치지 않는다.

## Suggestion

- 추가 없음. 소비된 source/helper/실패 기록을 수정하는 대신 현재 새 버전과 후속 분석에서 위 진단 시점을 명시한다.

## 확인 근거

- V2 996개, V3 998개 입력 SHA가 모두 현재 파일과 일치했다. discovery와 guitar XML discovery도 각 full input map과 일치했다. V2는 guitar discovery를 최종 map 전 assertion에 직접 합치지 않았지만 현재 저장값은 일치하며, [V3:50](/home/ajou/yigyu/3/stability_adapter_2/search_user_guided_no_left_v3.py:50)는 양쪽 discovery를 함께 확인한다. XML mesh 열거와 manifest 입력은 :47–49에서 핀에 포함하고 geometry/contract 구성보다 먼저 저장한다. 종료 전 :78에서 전수 SHA를 다시 확인한다.
- V2 upper50/65는 둘 다 제외: LEFT certificate 미보장 5/6쌍, native 0. 해당 음수 projection 값은 미보장 하한이며 cooked 관통 깊이로 해석하지 않았다.
- V3 upper50/65는 둘 다 수락: source clear, LEFT certificate 1,780쌍 각각 미보장 0. 후보 FK와 guitar 상태로 정적 probe를 새로 구성해 certificate를 재계산한 결과 저장 JSON과 정확히 일치했다. 실제 guitar hull face normal의 unit 오차 최대는 `3.33e−16`이었다. 추가 physics step은 0이다.
- 두 후보 모두 사용자 scalar 15축 주변 body±15°/Thorax±20°/Shoulder±30° 및 native 모델 한계를 만족한다. LEFT12만 새로 fit하고 V2의 나머지 69축을 정확히 유지했으며 finger42도 기준과 exact다. full upper/RHip gap은 각각 upper50 `0.582393/0.398633mm`, upper65 `0.595011/0.395822mm`로 V2와 같다. RH palm 오차는 `5.520964/2.421954mm`, 새 LH palm 오차는 `0.945054/0.611591mm`다.
- [package_user_guided_no_left_v4.py:13](/home/ajou/yigyu/3/stability_adapter_2/package_user_guided_no_left_v4.py:13)는 legacy 30/45/65 이름을 동일 full upper witness로 연결한다. 저장 후보 두 개의 q81, 기타 p/q, 예측 전신 및 G39가 V3와 정확히 같고 candidate config SHA도 일치했다. package 입력 685개 현재 SHA 일치, geometry solver proposals 0이다.
- [left_wrist_tracking_off_v2.py:48](/home/ajou/yigyu/3/stability_adapter_2/left_wrist_tracking_off_v2.py:48)는 OFF를 고정하고 force3=0, :51에서 task81을 Jacobian과 무관한 명시적 0으로 만든다. :52–54의 left gravity/scalar PD/effort clip은 기존과 같다. 사용되지 않는 point-Jacobian 오류만 :46에 기록하고 중단 gate에서 제외했다. 왼 COM gravity Jacobian과 실제 오른팔/몸통 제어의 guard는 유지된다.
- [run_user_guided_no_left_v2.py:11](/home/ajou/yigyu/3/stability_adapter_2/run_user_guided_no_left_v2.py:11)의 helper import 한 줄만 기존 wrapper와 다르다. 명시적 parent 초기화, critical patch 네 개, OFF initializer patch, read-only Chest/trunk 녹화가 유지된다. 인간33 finite/modelcap/ownership guard와 POSITION48 보존 및 관절속도 guard는 [right_block_body_effort_v5.py:22](/home/ajou/yigyu/3/stability_adapter_2/right_block_body_effort_v5.py:22), :57, :89에 그대로 존재한다. 새 세 Python 파일 AST 검사 통과.

검수 SHA: V2 source `f56f1e1b8f4dff418a076133684e3e0b29756902620d6415ca130867b837bffc`, V3 source `5b73a2a5b0a97cc630d1d51a8f5441aaefb2a2a1ceffb77ced71403625289805`, OFF helper V2 `df785cf04763758c1484ee947db6f84d09e1780ff0301e1862bb62d82db0a8f8`, wrapper V2 `323b7f78311e25dd93b73b379f0fd43eaf6b9c05225828e2c5e845702c760693`.

검수자는 이 문서만 생성했으며 source·설정·assets·native 원자료를 수정하거나 물리를 실행하지 않았다.
