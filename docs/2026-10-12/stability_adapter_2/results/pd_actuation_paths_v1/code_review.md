# 원본 PD 구동 경로 감사 사전 독립 검수

2026-10-07. 새 순수 감사 코드와 계획을 검토했다. 기존 코드·원자료·동결 검수 문서는 변경하지 않았다.

## 요약

문제없음. Critical/Warning/Suggestion 없음. Native 초기화·step 없이 원본 nominal 수치와 저장 properties를 대조하는 범위에 일치한다. 실제 원본 구동 효과나 새 actuator의 성공 판정은 아니다.

## 범위와 코드 확인

`/home/ajou/yigyu/3/stability_adapter_2/audit_pd_paths.py:24`는 원본에서 이름이 유일한 FunctionDef만 AST로 추출한다. 실제 `_compute_gains`와 `dof_torque_limit`은 NumPy·문자열·주어진 값만 사용하는 함수이며 원본 환경 import를 실행하지 않는다. `:36`의 task prefix는 literal_eval로 읽는다. 저장 stiffness200 계약 및 기존 입력 SHA를 확인하고 nominal gain/cap·관절 이름을 비교한 뒤 source SHA를 재확인한다.

`/home/ajou/yigyu/3/stability_adapter_2/PD_ACTUATION_PATH_AUDIT.md:7`의 읽기 전용 범위와 새 구동 변경 전 사용자 확인, 원본 기타 고정·하체 state 재주입 미승계 원칙이 일치한다. Main66은 제어 연결이며 새 학습 action 차원을 확정하지 않는다.

## 독립 검증

실제 CLI와 같은 main을 runpy로 실행해 `/tmp/pd_paths_reviewer_l2jq1c51/audit.json`에6계약/101입력 SHA 통과를 확인했다. 실행 후 sys.modules에서 Gym과 원본 base/safety 환경 모듈이 수입되지 않았음을 확인했다. Native 환경 생성·시뮬레이션·source query는 수행하지 않았다.

105개 gain floor/cap·float32 damping 및 safety cap 산식을 별도로 재계산해 AST 결과와 대조했다. Fret의30개 이름은 원본 FRET_POLICY_ACTION_NAMES literal과 exact였으며 Strike30은 오른팔/손 이름, Main66·Torso9은 기존 제어 연결과 일치했다.

## 해석 한계와 동결

원본 base.py:356/364는 POS drive와 stiffness0, :949는 force tensor 제출이다. 설치된 공식 tensors.html:384는 force tensor 적용 DOF에 EFFORT drive를 요구한다. 이 정적 차이와 원본 solver damping·명시적 kp*(target−q) 경로는 별도 runtime/API 검증 대상이며 실제 무시·버그·토크 포화의 증거로 사용하지 않는다. Nominal cap과 현재 native effort 숫자의 같음도 원본 imported effort나 actuator 동등성을 측정하지 않는다. 사전 검수 완료; 현재 code_review를 동결한다. 실제 감사 산출물과 미디어는 별도 runtime_review로 검수한다.
