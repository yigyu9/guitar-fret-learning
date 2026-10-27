# 제한된 관절 목표 PI 코드 검수

판정: **문제없음 — 지정 진단의 제어 경로에서 Critical을 발견하지 않았다.** Critical 0건, Warning 2건, Suggestion 0건. 새 계획·wrapper·config 및 기존 제어 계약을 읽기 전용 검수했다. 실제 ON 결과·지지 성립 판정은 후속 최종 검수 범위이며, 리뷰어는 추가 native·학습이나 원본 수정 없이 이 문서만 작성했다.

[PI 계산:34](/home/ajou/yigyu/3/stability_adapter_2/run_om_axilla_hold_correction_v1.py:34)은 고정 q_goal과 실제 native q의 오차를 사용하고 dt=1/60으로 적분한다. integral/residual은 body9 ±0.05rad, arm24 ±0.3rad에 clamp하며 head6·finger42의 보정은 0이다. native/effective 목표 clip 후 기존 81D codec으로 요청을 만들고 [기존 단일 제출자](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v2.py:105)의 contract.targets·rate 제한·4 physics 경로로 제출한다. 별도 상태 setter·물리 제출·중복 PI 경로는 추가하지 않는다. config 차이는 arm rate1→3rad/s 한 항목이며 초기 후보와 나머지 조건은 유지된다.

[metadata patch:12](/home/ajou/yigyu/3/stability_adapter_2/run_om_axilla_hold_correction_v1.py:12)는 attempt/report를 생성할 때 PI 제어를 명시하며 소비된 결과를 사후 수정하지 않는다. [카메라/기록:28](/home/ajou/yigyu/3/stability_adapter_2/run_om_axilla_hold_correction_v1.py:28)은 side camera 생성과 capture·strap_state 읽기 전후 native_state exact를 검사한다. strap 기록은 현재 계산 명령과 직전 physics 적분에 제출했던 명령을 구분하며 센서 힘으로 설명하지 않는다.

Warning 2건:

- [계획:6](/home/ajou/yigyu/3/stability_adapter_2/OM_AXILLA_HOLD_CORRECTION_PLAN_V1.md:6): ON은 PI와 arm rate 변경을 함께 적용한다. OFF/ON 결과를 PI 단독 효과로 귀속하지 않고 ‘PI+팔 목표 rate’ 조합 비교로 보고한다. 제어 로그 actual/error/requested는 적분 전 단계이며 실제 제출 목표는 trace의 다음 제어 끝점 행과 대응해 검증한다.
- [metadata:14](/home/ajou/yigyu/3/stability_adapter_2/run_om_axilla_hold_correction_v1.py:14): attempt에는 HOLD leaf 경로가 있지만 input_sha256에 해당 md는 포함되지 않는다. 별도 사전 pin이 있으면 최종 보존 감사에 연결하고, 없으면 현재 SHA의 사후 확인을 실행 전 봉인으로 표현하지 않는다. PI 실행 소스는 실제 attempt SHA와 현재 SHA가 일치한다.

제한: bounded target·clamped integral이 실제 q 오차 제거, 안정성, 가슴/상완 동시 지지, 연주 또는 왼손 철수 성공을 보장하지 않는다. 원 strap 법칙·질량·자산을 유지해도 움직임에 따른 경로·명령 힘은 달라질 수 있다. 후속 결과는 실제 초기 exact·최종 제출/rate·속도/금지 API·접촉·자체 초기 pose 변화로 판단한다.

검수 소스 SHA256: `510347b0e192ad00c84896b46239deb38fde058b2c2eca661579d165966d201b`.
