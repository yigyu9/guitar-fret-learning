# 사전 검수 — 명시적 왼팔 PD 계수 변경

요약 판정: **문제없음. Critical 0 / Warning 2 / Suggestion 0.** 기존 양팔24 EFFORT/57 POSITION과 동일 초기 설정을 유지하는 제한된 5초 진단을 막는 추가 코드 오류는 발견하지 않았다. 아직 새 조건의 실제 유지·안전 결과를 인증하지 않는다.

- [helper2:41](/home/ajou/yigyu/3/stability_adapter_2/left_near_arm_effort_v2.py:41)는 mode 변경 전 원 native K/D를 별도 보존하고 왼 외부 PD만 Thorax30/1·Shoulder60/3·Elbow60/3·Wrist20/1로 설정한다. 단위는 K=Nm/rad, D=Nms/rad다. 오른 제어·중력 계산·target 소비·토크 clip·단일81 제출·owner window는 helper1과 같다. scene2는 지원 helper import만 변경했다.
- [runner4:108](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_near_v4.py:108)는 원 native K/D 기록값을 직전 reference와 비교하며, 실제 external gain과 원 native gain을 혼동하지 않는다. 초기 PD 선언·mass/FK/전체 source LP·고정48/G 검사와 POSITION57/state guard는 유지된다. 실행 설정 SHA는 preflight6의 config/reference와 같다. Python 3파일 AST도 통과했다.
- [hold2 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/native_hold_v2/report.json:1)는 completed false, 440 physics/110 control/1.833333s, unsafe native joint state, 입력 불변/금지 API0으로 기록되어 있다. 완주로 해석하지 않는다. [안전 검사:214](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_near_v4.py:214)는 기존 finite/속도50rad/s 조건 그대로이며 제어 step 끝 저장 sample에서 검사한다.

Warning 1 — '낮은 PD'는 모든 계수를 낮췄다는 뜻이 아니다. 예를 들어 원 L_Elbow_y,z K60은 새 K60과 같고 D15는3으로 바뀐다. 실제 계수 표를 권위로 삼아야 한다. 오른 제어에서 사용한 수치 재사용만으로 왼팔 안정성을 인증할 수 없으며, implicit POSITION과 외부 PD+gravity는 동일 동역학이 아니다.

Warning 2 — 앞선 preflight6의 Jacobian frame·gravity 모델 인증 한계는 유지된다. 기존 속도 안전 검사는 4 physics step마다의 sample 검사이며 모든 solver 내부 시각의 최대 속도를 보장하지 않는다. hold2 실패 원인의 단독 인과 분리 및 새 조건의 근접 유지 여부는 실제 결과 확인이 필요하다.

검수 범위는 계획V8·이전 helper/scene/runner와의 diff·hold2 report·설정 SHA·AST다. 추가 native/정책추론/학습과 다른 담당 파일 수정은 하지 않았다.

검수 SHA256:

- 계획V8: `b40570224d278cc75e94816a36ed531d9b9d5fc2578617bdb35dc375dfd985d9`
- helper2: `9ee0c361033cd074e0126da7bf598f6ce70c7afbd8237afefa5fe90bac886922`
- scene2: `225092d3b815d047577e9e6b1f4d2a75464544dd95bcd91bdd3260ece1b9bc2b`
- runner4: `bead51b87a4cd6d0bc9a8de711e939ca5475485d6c8453c7d3d6f540c37b0cc7`
- config: `d84373d7a56800987de903bd57a43b0d2428d80c0de01f3e8b6702ddf0ca72b3`
