# 손바닥 지지 소실의 관절 유지 관측

## 다음 단계의 근거

±.001rad 결합 보정은 .1초 기타 이동5.341→5.099mm/회전1.006→.973°,
손 추적점9.289→9.113mm로 줄였다. 그러나 종료 source normal gap9.048mm와
step2에만 나타난 양의 palm raw lambda가 남아 유지 지지가 아니다.
보정 폭만 계속 키우기 전에 팔이 지지 자세에서 벗어나는 응답을 관측한다.

저장 raw의 baseline/full 둘 다 R_Hip–G:body 양의 raw lambda는step1–24,
LH:palm–guitar는step2뿐이다. 다른 양의 contact pair는 이 .1초에 없다.
full의 L_Shoulder_x 실제 native pos−전달 target은.338013rad, velocity .63268rad/s다.
이는 native 관절 좌표 한 성분이며 전체 관절의 SO(3) 각도 차이가 아니다.
질량·총 DOF force·drive target 변환 없이 중력 부족/drive 포화/좌표 오류를 단정하지 않는다.
출처는 이번 결과의 hold_observation_seed.json과 그 입력 SHA다.

## 관측 소단계

- [ ] 1. frozen runner와 입력을 보존하고 별도 observer wrapper를 만든다.
  현재 SelfCollisionEnvironment를 상속해 actor 생성 후 DOF force sensor를 활성화하고
  native rigid-body mass/inertia/COM과 DOF type/driveMode/kp/kd/effort를 저장한다.
  기존 run_dof_force_observation.py의 query/상태 보존 검사 방식을 참고하되 수정하지 않는다.
- [ ] 2. 이전 baseline 및 full의 같은 초기 상태·PD 명령·LA로 각24step 관측한다.
  계획2init48steps다. 쿼리 전후 state/target/PD가 같고 이전 states/trace/tasks/
  contacts/controls 5배열과 exact인지 확인한다. sensor readback은 각 완료 step에 맞춘다.
  t0 sensor는 임의로 생성하지 않으며 생성·실행 계약이 다르면 그 사실을 기록한다.
- [ ] 3. 손/관절의 실제 이동·속도와 질량·관절 property·total DOF force를 함께 읽는다.
  total DOF force는 drive-only torque가 아니므로 effort와의 단순 비교로 포화를 선언하지
  않는다. source/native 실제 joint orientation 해석도 구분한다. 결과에 따라 작은 PD 유지
  비교 또는 목표 좌표/feedback 재구성을 다음 계획으로 정한다. 아직 gain은 바꾸지 않는다.
- [ ] 4. 원자료·단위·관측 부작용을 독립 검수하고 Luna가 그림과 설명을 정리한다.

초기 humanoid q·기타 p/q·절대LA1.1018469719600776m·PD·몸통9/다른관절목표,
root/하체 물리고정·self-collision ON·66관절 합성 경로를 유지한다.
기타 free·중력·수동 strap, 고정/강제부착/반복 pose 덮어쓰기 금지는 그대로다.
이번 관측은 유지제어 설계의 근거이며 학습/안정성 성공 기준을 대신하지 않는다.

코드·계획은 stability_adapter_2, 새 결과는
docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1에 둔다.
