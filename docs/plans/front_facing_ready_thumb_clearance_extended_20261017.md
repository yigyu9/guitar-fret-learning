# LH thumb3 범위 확장 — 네 표본 조건부 source 진단 V3

2026-10-17. 소유권은 `diagnose_left_thumb_clearance_v1/`의 새 V3/CPU/version 문서와 본 leaf뿐이다. 다른 작업자가 공존하며 기존 source/결과/문서를 고치거나 되돌리지 않는다. 독립 검수·Root ACK 전 actual main/IK/새 실제 sourcepair/native/PPO0이다.

## 근거와 이번 단일 변경

원 V2 actual `result_v1/result.json` SHA `eb487a8d68d03ece9b781a8f345aa2f69d9d5a889652b369ea706c28086b0a46`는 완결/inputs_unchanged=True/selected=None다. 기존 δ0,−.01,−.02,−.03 모두 후기 thumb–G source를 실패했고28초의 g는−1.2034644mm에서−1.13276984mm로 약70.69µm 개선에 그쳤다. 다른1513 source/명령/self36 및 before-self36 통과가 실패를 성공으로 바꾸지 않는다. 원 main·review·Root before14670/after/ACK/log를 그대로 핀한다.

새 `diagnose_v3.py`는 원 수학을 복제하고 δ=(0,−.04,−.06,−.08,−.10)rad로 확장한다. 약1.72°에서 최대5.73°로 넓히는 조건부 정적 가설이다. 실제 spec의 closed/open thumb55 값을 먼저 SHA로 확인해 전체 open 증분(약−.18rad) 안임을 요구한다. 이 범위 안이라는 사실은 압현·파지·동적 추종의 성공 근거가 아니다. 검지/다른 finger/RHfinger/arm의 바탕과 PD K20/D5/cap4Nm는 그대로다.

네 시각3840/5532/6644/6720×두 precision×다섯 δ의40행을 전부 계산한다.16초는 δ0/held exact이고 δ0은 원 V4 및 직전 thumb V2의 control 재현이다. global source1mm/엄지89쌍 .9mm 설계 여유/self36 before-and-after/원 strict IK fit10µm·.01°/fixed wrist 목표1mm·.5°/명령13 bounds/qref±.8/principal160/F32/other92·zero8 보존/조건부 local hinge/고정 child/제한 fallback을 유지한다. 선정은 전체 AND한 최소 |δ| 하나이며 없으면 None이다. source 문턱에 epsilon을 더하지 않는다.

## actual bounds 요약의 새 범위

원 V2에는 전체 predicted q와 원 zero8 exact False만 저장한 Warning이 있었다. V3에서 다음을 별도 진단 row에 추가한다. native scalarq를 world Euler로 재해석하지 않는다.

- 원 actual105와 predicted105의 finite/strict EPS0 native limit 초과 축·값·초과량·최대값. 원 zero-ROM8의 qref 잔차/최대와 exact bool은 별도다.
- 실제 `arm12` indices와 thumb55를 결합한 **수정13개**의 전후 strict bounds를 별도로 집계한다. predicted modified13의 finite/bounds를 후보 AND gate로 추가한다.
- 전체105의 strictEPS0 False는 기존 zero8 등 원 잔차를 숨기지 않고 그대로 남긴다. 이를 모든 기하 후보의 자동탈락 조건으로 바꾸지 않는다. command bounds, actual13 bounds, actual105 건강과 숫자 예산은 서로 다른 판정이다. solver cause/final adoption은 여전히False다.

## 사전 핀과 최소 CPU

이전 V2 source/freeze150/원 leaf·보완문서/actual result·inputs_before·Root proof expectedSHA를 확인한다. 실제 spec는 native cfg의 ready_spec_sha256와 직전 Root before의 같은 SHA를 대조해 새 입력에 명시 핀한다. 원 model108/소비 helper/native8/source14FAIL/core30은 기존 selected pin 경로를 재사용하며 새 A glob/전체 조상 재분석/대량 raw 사본을 만들지 않는다.

- [ ] 원 actual metadata와 spec의 closed/open delta 및 기존 result32행/선정None/실패를 확인한다.
- [ ] 새 source·before를 고정한 작은 CPU: clone의 불변 함수 AST, 새δ5값과 full-open 범위, 실제40 command-response/경계·δ0, actual13 bounds와 전105 EPS0/zero8 분리 및 초과 반례, 실제 main gate·선정 반례, argc/closure·입력 종료SHA를 검사한다. 원48 전체 중 이번 변경에 관계없는 compiled placement/self/hinge/G projection은 불변 AST/동결 근거를 연결하고 재실행하지 않는다.
- [ ] 새 code/CPU/docs/freeze를 불변 SHA로 닫고 독립 검수·Root ACK를 기다린다.
- [ ] Root만 새 `result_v2` output으로 actual main을 한 번 실행한다. 여기서 통과해도 ramp interior/전행/실제 finite PD 추종·하체/지지/압현/건강 성공은 미검증이다.

이번 구현·CPU 단계의 `main_executed=False`, 새 actual sourcepair0/native0/IK0/PPO0을 지킨다. 원 실패 자료는 사후 재작성하지 않는다.
