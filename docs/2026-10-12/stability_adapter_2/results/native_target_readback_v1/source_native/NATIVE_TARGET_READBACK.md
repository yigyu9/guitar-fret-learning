# Native 목표각 읽기 대조

2026-10-07. 어깨 PD 비교는 사용자 확인 전이다. 이번에는 기존 PALM_RATE 설정을
유지하고 SDK의 get_actor_dof_position_targets 읽기만 추가한다.
제출 목표와 실제 저장 목표의 차이가 큰 추종 오차 설명에 영향을 주는지 확인한다.

- [ ] 계획·독립 코드 검수: 기존 0.1초 runner를 재사용하는 관측 adapter를 만든다.
- [ ] 같은 초기 조건의 fresh1회:24step/0.1초, 매 step 전후 native 목표를 읽는다.
- [ ] 원래7개 배열의 prefix, 읽기 불변성·형상·단위·목표 차이를 확인하고 그림·설명을 남긴다.

기존 runner는 수정하지 않는다. 별도 adapter에서 환경 factory만 임시 교체하고
원래24step 종료와 finally의 sim 해제를 유지한다. 실패·부분 자료·명령·로그·소스를 보존한다.
Native 목표는 float32 105개를 복사한다. Getter 전후 human/guitar body·DOF state,
Python 목표와 PD properties가 같은지 확인한다. 목표 차이는 관측이며 zero 차이를
성공 gate로 요구하지 않는다. 초기 t0도 실제 getter로 읽으며 합성하지 않는다.
Step n 직전/직후 native 목표와 그 step에 제출한 Python 목표를 각각 기록한다.

초기 q/기타 Z+5mm·초기 회전/LA1.1010801317960974m/PD·effort·solver/root,
PALM_RATE·보정/목표 box·변화율 제한·몸통9·손가락42·C02하체·주요66을 유지한다.
기타 고정·강제 부착·추가 state 쓰기·gain 변경·기타 복원력은 없다.
첫0.1초는 제출/읽기 왕복과 저장 상태 비교 범위이며 후기 추종이나 기타 유지 성공을
증명하지 않는다. 어깨 stiffness 제안의 사용자 답변을 대신하지 않는다.

결과는 docs/2026-10-12/stability_adapter_2/results/native_target_readback_v1에 저장한다.
