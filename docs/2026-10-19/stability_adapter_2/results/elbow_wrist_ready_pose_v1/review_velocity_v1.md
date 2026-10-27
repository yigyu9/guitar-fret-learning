# V5 목표 속도 항 구현 검수

요약 판정: 문제없음. 기존 감쇠 계수의 목표 속도 항을6개 요청에 추가하고 원 cap으로 clip하는 구현과 기록 scope가 일치한다.

Critical: 0

## 확인 근거

- [V5:51](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v5.py:51): rate 적용 예상 최종6−이전 최종6에60을 곱해 목표 속도를 계산한다. 원 V3의 요청/최종 norm·모델·±1rad·finite/error gate와75 목표를 유지하며 추가 rate 검사도 원 step 전이다. 목표G 경로나 깊이는 바꾸지 않는다.
- [V5:73](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v5.py:73)의 D6=[3,3,3,1,1,1]은 [원 scalar PD:87](/home/ajou/yigyu/3/stability_adapter_2/dual_shoulder_effort_v1.py:87)와 실제 이번 `effort_configuration.json`의 계수에 일치한다. 따라서 기존 −D*qdot에 D*qdot_target을 추가하는 의미다. 새 gain/cap/기타 직접 힘/state setter는 없다.
- [최종 합성:75](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v5.py:75): 원 controller를 한 번 호출한 결과의6만 기존 raw request6+D6*v로 교체·clip하고 나머지75 effort를 bitexact 검사한다. 결과는 원 단일 guarded `apply_actor_dof_efforts` 경로로 전달된다. 원 body/LEFT/상완 task의 명령 owner를 늘리지 않는다.
- 실행 파일이 닫힌 뒤 현재 기록에 한정하여300 control의 target 차분과1200 physics의 속도·D항·clip 수식을 독립 검산했다. 목표 속도 차분 오차0, 최종6 clip 재현 오차0, 나머지75 before→after 차이0, 최대 목표 속도2.785104rad/s였다. 원 상완 고정 task의 superseded distal 성분도 실제1200행에서0이므로 여기서 읽는 raw request6와 원 distal stage의 차이는 없다. V5 AST를 확인했다.
- [encode scope:85](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v5.py:85)는 새 `six_velocity_effort_rows.json`을 실제 최종81로 기록한다. body/tracking 저장 scope는 velocity 추가 전 stage로 바뀌며 현재 파일의 해당 scope도 확인했다. 기존 결과 파일은 수정하지 않는다.

## Warning

- [속도 계산:52](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v5.py:52)은60Hz target 유한 차분을 다음4 physics tick 동안 유지한다. 실제 scalar 속도나 연속 궤적의 정확한 도함수가 아니다. 위치 PD의 목표 속도 항이며 실제 속도·추종·접촉·detector RELEASE 성능은 따로 판정한다.
- [raw 요청 선택:77](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v5.py:77)은 원 controller의 distal raw request를 기준으로 한다. 현재 proximal-only support의 distal 성분0에 의존하며, 후속 task가 distal로 확장되면 velocity 이전 최종 stage의 전체 raw 요청을 기준으로 다시 검수해야 한다. 이번 실제 기록에서는 성분0을 확인했다.
- `actual_submitted_efforts81_Nm`은 최종 actuator 명령이며 측정 drive/contact torque가 아니다. 새 효과가 실제6줄 양방향 성공이나 자유 기타 안정성을 뜻하지 않는다. 완료 원자료의 SHA/초기·첫2초 trace/목표75/실제 접촉·marker·원 detector·영상 전수 검수는 후속 native 검수 범위로 남긴다.

## Suggestion

없음. 이번 구현/명령 수식 범위에서 추가 blocking 오류를 발견하지 못했다.
