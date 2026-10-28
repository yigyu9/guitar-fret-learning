# 실제각 기준 위치 후보와 누적 목표 분리 계획

기존 실패진단 계획의 다음 제어 비교 준비다. **현재는 계획이며 활성 구현/GPU 실행 전이다.** wrist_target_feedback_audit의 독립 검수와 진행 중 wristv2의 다른손가락 회귀 종료·검증 전에는 활성 소스를 바꾸지 않는다.

가설: 위치 미분 Jacobian 교정 뒤에도 실제 손목의 추종 지연 동안 같은 실제 pose오차를 누적 request에 계속 더해, request가 kinematic goal을 지나치거나 더 멀어질 수 있다. 현재 검지 reference는0/4이고 postramp 손목오차 최대72.26mm로 남는다. 기존기록의 가상requested-FK는 기하 검산이며 물리 도달·힘 인과의 증명이 아니다. 새 gain 탐색으로 대체하지 않는다.

검증할 최소 변경은 DLS를 실제각에 대한 위치 후보로 해석하는 것이다.

```
dq = DLS(J_position, current_pose_error)
candidate = actual_arm_q + dq
proposal = teacher_base + stored_correction
delta = clip(candidate - proposal, -existing_step, existing_step)
requested = existing_rate_and_bounds_clip(proposal + delta)
new_correction = requested - teacher_base
```

기존은 dq 자체를 .5도로 clip한 뒤 proposal에 반복 더한다. 새 방식은 실제각에서 계산한 후보와 proposal의 차이를 .5도로 제한한다. feedforward/ramp·correction 상태·기존 request속도/범위·native평활화는 유지한다. .5도는 여전히 feedforward에 더하는 보정 상한이지 전체 요청 변화가항상 .5도이하라는주장이아니다. reset행은 actualq/dq가비유한이어도 delta0으로제외하고 원래 첫reset tick feedforward를 유지한다. 손가락 제어에는 적용하지 않는다.

1. [x] 실제 근거/이전 실행 독립 검수 완료 → verify: 현재source/기존결과 동결 유지, index 분석PASS 및 다른finger 실제종료/검수, request-FK감사 검수.
2. [x] 직전 활성 원문과 새 fixture를 새 archive에 보존 → verify: 모든 원경로/byte/SHA. 과거 source/contract를완화하지않음.
3. [x] wrist.py/runtime.py 및 trace metadata/관련 검사만 최소수정 → verify: qpos-J v2 수학 유지, 새로운 candidate 계약 v3 명시, 실제q 전달·reset 선제제외·본인입력불변. trace requested_delta 의미를 정확히 명시.
4. [x] CPU 회귀와 별도 code review → verify: 요청이이미후보를넘었을때 뒤로수정/동일오차의무한동일방향누적방지의수치예제,0오차·부분reset NaN·범위/속도·동일계약load/이전v2strict거부. 실제native도달개선으로확대하지않음.
5. [x] 새 initial의 검지와중지 각 bootstrap/ref/zero/random4시도 → verify: strict입력·73모델동일성·전체분모/실패·실제음gate·추종오차·힘표본범위·장면종료. 새.5cap/2sramp/3sonset/PD/범위/보상 변경없음.
6. [x] 실제 결과 별도검수 및분기 → verify: oracle압현실패시장기학습을시작하지않고 wrist도달과손가락gate를분리. 성공시기존계획의나머지finger/짧은학습/해제·전환/자유기타/원곡단계로돌아감.

새 알고리즘의 실제 추종/자연스러움/하중 개선은 아직 미검증이다. 기본 raw J33·보상·종료·PD·손가락 전체 가동범위·움직임 비용0은 대상이 아니다. 추가 상태보상이나 범위축소로 성공을 만들지 않는다. 공간정리 중단·진단자료 제외를 유지한다.

직전원문521개(활성Python518+문서2+실제fixture1)를새archive에원경로/byte/SHA로검증보존했다. index/다른finger 실제분석과requested-FK감사독립검수는모두PASS이며현재GPU유휴상태다.

실제 검산용으로 이미계산한candidate_arm_rad를기존env0 trace에 wrist_candidate_arm_rad(12float/끝점)로기록한다. requested_delta_rad 중립필드는유지하며candidate−proposal clip의scope를v3계약과연결한다. reset행candidate는원proposal로마스크된진단값이다. 이필드는관측·보상·물리입력이아니고추가solve도없다. native에서actual+DLS후보와유한요청의정합/후보초과누적억제방향을확인하기위한최소추가다.

active5파일의v3구현/후보trace를동결했고CPU4모듈43검사PASS(작업자보고7.830초),AST/diff검사PASS다. 별도code검수/새index+middle8단계native준비검수를시작한다. 아직실제개선은검증전이다.

별도code review PASS:archive521/지정7변경영역·43CPU·96mixedrows SVD oracle·qpos-J AST불변·oldv1/v2거부/newv3load를독립확인했다. 현재native8단계준비검수를진행하며실제향상은미검증이다.

검지/중지 새GPU8단계실제종료0/199.807초·모든stage후검증완료. ref/zero/random모두0/4이고중지ref audiblewrong100%다. raw예비관찰에서indexref env0음중wrist오차0.205mm/0.041도·postramp최대2.25mm로추종은개선됐지만압현은남았다. 실제analysis및독립검수로재확인하고다음손가락gate/원source자세정합을분리한다. 독립검수전향상인과/모든환경추종으로확대하지않는다.

실제 분석 독립검수 PASS(findings0). 검지 env0 음중 손목오차 중앙값0.205mm/0.041도, 중지2.808mm/2.254도이나 양쪽 reference0/4다. 검지는 방향/위치11끝점 통과·하중0, 중지는 own_wrong_string8/8이다. 이 소계획의 검수는 끝났으며 전체 실패진단/압현 문제는 미완료다. 동일 물리계약과 source/current target 일치에도 실제 자세가 다름을 별도 source audit로 확인했고, 다음은 같은 두 목표에서 손가락4축만 유한 탐색하는 도달가능성 진단이다.
