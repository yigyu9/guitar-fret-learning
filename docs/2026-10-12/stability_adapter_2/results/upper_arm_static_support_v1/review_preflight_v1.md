# 상완 초기 지지 사전 독립 검수

요약 판정: **수정 권장 — 아래 시간 정규화 오류를 해결하기 전 native 실행은 차단해야 합니다.** 신규 5파일과 직접 사용하는 장면·관측·스트랩·녹화 경로를 읽기 전용으로 검토했습니다. 물리 실행이나 학습을 추가하지 않았습니다.

## Critical

- [search_upper_arm_static_v1.py:30](/home/ajou/yigyu/3/stability_adapter_2/search_upper_arm_static_v1.py:30): 생성 config의 `prep_seconds=5`, `diagnostic_seconds=5`는 [관측 정규화:137](/home/ajou/yigyu/3/stability_adapter_2/environment_contract_v1.py:137)의 분모 `horizon-prep`를 0으로 만듭니다. [runner:31](/home/ajou/yigyu/3/stability_adapter_2/run_upper_arm_static_v1.py:31)의 scene(5.)는 이를 유지하며, 장면 생성 시 observe에서 물리 적분 전에 ZeroDivisionError가 발생합니다. 기존 소비 소스·검색 결과를 보존하고 새 경로에서 prep<horizon인 config를 사용해야 합니다. 기존2초 준비를 유지해도 이 runner는 전5초 동일 q_ref를 제출하므로 연주 목표로 전환되지 않습니다. 정정본은 이 기록의 검토 범위에 아직 포함되지 않습니다.

## Warning

- [search_upper_arm_static_v1.py:26](/home/ajou/yigyu/3/stability_adapter_2/search_upper_arm_static_v1.py:26): 수용 조건은 witness 오차<2mm와 실제 gap≥0이며 요청 간격과 실제 간격의 일치를 강제하지 않습니다. 저장된 [검색 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/search_v1/search.json:1)의 선택된 0° 후보 실제 gap은 2.121294mm이고 3°/5°는 1.503587/1.503499mm입니다. `gap1500`을 실제1.5mm로 설명하지 말고 저장된 signed gap을 보고해야 합니다. source 간격이나 contact offset만으로 실제 지지 여부를 판정할 수 없습니다.

## 확인 결과와 범위

- 몸통9의 Chest 전체 회전 목표, Pelvis forward 기반 world 회전축, 팔24의 기준±0.3rad IK, 왼손 palm world pose 유지 및 head/finger scalar 초기각 보존 경로는 계획과 일치합니다. q 이름의 축 suffix를 world 축으로 해석하지 않습니다.
- calibrated FK는 기준 native 상태를 일치시키며, runner는 새 초기 native 상태와 검색의 예상 pose를 추가 대조합니다. CPU3 통과는 기준 FK·몸통 합성 회전·캡슐 witness 검사이며 변경 후보의 실제 native 초기화나 접촉 유지 인증은 아닙니다.
- runner는 초기 q_ref를 고정 PD 목표로 사용하고 기존 preload 보정·체크포인트·Actor·PI를 호출하지 않습니다. 기존 단일81 목표 제출과 제어당4물리 step, 초기화 이후 state-write guard, 원본 passive strap ON 법칙과 전용 force window를 유지합니다. 300제어/1200물리 step 및 녹화 interval8은 초기 프레임 포함151장/MP4 5.033333초에 해당합니다.
- 접촉은 제어 직전60Hz query이며 raw lambda는 뉴턴 접촉력으로 해석할 수 없습니다. 유효 후보의 실제 contact·전체/후기 이동과 안전 상태는 향후 native 원자료로 판단해야 합니다.
- 검색 JSON의 직접 입력 목록에 geometry helper가 없지만 [source_before_search_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/source_before_search_v1.json:1)이 별도로 해당 소스 SHA를 포함하므로 현재 감사 경로에서 확인 가능합니다.

## 검수 소스 SHA256

| 파일 | SHA256 |
|---|---|
| UPPER_ARM_STATIC_SUPPORT_PLAN_V1.md | e676511b96ab24fd7f8a987445653b4f9703d117fb25cd40ae470e962e310c61 |
| upper_arm_static_geometry_v1.py | ca24cb0e06f1dc5375469352baa482c495f1da889a8c905891ecda3adce29d55 |
| search_upper_arm_static_v1.py | 97c73b88000b09e62567fc490de82f448ba3d70b2d483f25eac8166262dc8219 |
| run_upper_arm_static_v1.py | 85654d393ea80a14d80da67f3cdfb1a791d81f571176e3fa8614503f330a5dcf |
| test_upper_arm_static_geometry_v1.py | 30d59ed74ac48a2d2a31f867badf207720a87a027f70887a7b154ffcc9b49d6c |

검수자는 이 새 문서만 작성했습니다. 신규 정책·물리·학습 실행 및 기존 파일 변경은 없습니다.
