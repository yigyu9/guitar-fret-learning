# waist 척추 굽힘 완화·오른팔 접근 사전 검수 V2

요약 판정: **문제없음**. Critical / Warning / Suggestion 없음. V1 사전 검수의 Warning 2건이 보완됐다. 이는 Source/native 실행 전 소스 검수 판정이며 물리 유지 성공 판정이 아니다.

## 변경 범위

새 `search_waist_upright_right_arm_v2.py`와 `WAIST_UPRIGHT_RIGHT_ARM_PLAN_V2.md`의 V1 대비 변경 부분을 검수했다. 원본 검색·계획 V1은 미실행 상태로 보존됐고 SHA도 이전 검수 기록과 정확히 같다. 검수자는 원본을 수정하지 않고 이 기록만 생성했다.

## 보완 확인

- [search_waist_upright_right_arm_v2.py:26](/home/ajou/yigyu/3/stability_adapter_2/search_waist_upright_right_arm_v2.py:26): anchor SHA를 먼저 저장하고 metadata를 읽는다. guitar XML도 29행에서 SHA를 저장한 뒤 읽고, 발견용 파일 재대조 후 37행에서 전체 `inputs_before`를 저장한다. EnvironmentContract/FK/CapsuleBodyDistance/clearance 구축은 그 이후다. 계약 입력 SHA를 봉인 목록과 대조하고 종료 시 전체 입력 SHA를 다시 검사한다. V1의 형상 소비 후 before 기록 문제가 해소됐다.
- [search_waist_upright_right_arm_v2.py:109](/home/ajou/yigyu/3/stability_adapter_2/search_waist_upright_right_arm_v2.py:109): 팔꿈치 origin의 bbox 중심 거리 전/후/감소량을 계산한다. 114행은 축 투영 및 실제 거리 감소를 모두 요청 접근량의 25% 초과로 요구하고 115행에 3D 목표 오차도 기록한다. 양의 축 투영만으로 거리 증가 후보를 수락하던 문제가 해소됐다.
- [search_waist_upright_right_arm_v2.py:59](/home/ajou/yigyu/3/stability_adapter_2/search_waist_upright_right_arm_v2.py:59): 후보가 Chest 방향 완화4°/팔8mm, 8°/12mm, 2°/5mm로 변경됐다. 계획 V2의 실행 전 보완 섹션과 일치한다. world 오른축 회전 부호·누적 .25/.625/1 분산·body fit 후 고정하여 right fit하는 순서는 V1에서 확인한 대로 유지된다.
- 기존 body±.15/양팔±.4/head±.35rad와 모델 한계의 교집합, elbow ±5° 여유, 고정 기타 p/q·하체·finger42·왼손목 상대 p/q·머리 방향, waist 및 전체 source 비겹침 수락 조건은 변경되지 않았다. 8° 목표가 실제로 가능한지는 검색 결과로 확인하고, 맞추지 못하면 body error/tilt gate가 거절한다.

## 검증과 한계

Python AST 문법 검사 통과. 새 소스와 같은 경로 수집 규칙을 실행 없이 재구성했을 때 **고유 입력749개가 모두 존재**했고 human37개·guitar XML69개·XML/manifest union70개가 포함됐다. `search_v1`/`search_v2` 출력 폴더는 검수 시점에 없었다.

전체 Source fitting/겹침 audit와 native 초기 실제 상태·접촉·5초 유지 성능은 아직 실행하지 않아 미검증이다. 기존 `run_right_body_approach_v1.py` 및 controller는 이번 변경에 포함되지 않는다. 재사용 runner의 초기 검증 및 새 결과 입력/출력 보존 검사는 실제 실행 단계에서 확인한다.

## 검수 입력 SHA256

- `search_waist_upright_right_arm_v2.py`: `b1b8f4ffc1fa80062e4aa26eeb93810a5ca107e308ef5ecbe40a300a95cb963b`
- `WAIST_UPRIGHT_RIGHT_ARM_PLAN_V2.md`: `1be961bc74a6c8c05b132bc648a92fcd299124f57a2c1981f2083b1fb475ea5a`
- 보존 V1 source: `762297cc887eae100b6c21790df2ad8e960525995e98727b64deace28951f84a`
- 보존 V1 plan: `c353d7d1397c8fca83c93de62a445612729463d6f4887eca33aed59487515c6f`
