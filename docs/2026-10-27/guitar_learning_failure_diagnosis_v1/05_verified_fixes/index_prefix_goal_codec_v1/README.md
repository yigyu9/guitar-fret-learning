# 선택4 목표각 출력 진단 — CPU 준비

원1000회 incremental warmstart와 비교하는 새 목표각 출력 조건이다. 추가1000회 실패 모델에서 시작하지 않는다. 원 fresh73개 tensor 값과 같은 가중치 구조를 새 고유 goal policy/control identity로 생성한다. 원 모델의 strict identity를 우회하거나 metadata를 위장하지 않는다.

선택4 raw NN tanh 출력→035 준비각 기준 부호별 full-native affine 목표각→원 trajectory_actions 역 codec의 물리 증분 요청→원 incremental controller/current-goal DIP guard 순서다. 실제 q·목표를 직접 대입하지 않으며 다른104열·4rad/s·범위·PD·cap.25/105readback·90충돌쌍·손목v3·비선택B/엄지035·9보상/종료를 유지한다. 원 source settings는 incremental 환경의 출처다. 새 policy_output_adapter는 policy 생성 전에 contract의 action/task 두 곳과 architecture에 저장된다.

원 관측1416행을 재사용하며 label은 원 일정의 planned desired(t+1/60)에서 계산한다. 포화된 증분 요청으로 역추정하지 않는다. 원 reference 요청 재생은 bitexact를 요구하고, 별도 float32 affine 왕복은 최대각/요청 잔차를 그대로 기록한다. NN과 reference는 같은 decode/정밀도 경로를 쓴다.

읽기전용 관측 확인: q_offset·target_error는 scale1(rad), q_velocity는÷10이며 공통clip±10이다. 비포화행의 oldtarget=reference+q_offset+target_error이고 선택4 local20에도 직접 제공된다. music.elapsed_s와 remaining이 시계를 제공한다. 원 reference 요청은 일정·시계·oldtarget 함수여서 숨은 phase/호출이력 누락 근거는 찾지 못했다. 학습 성공이나 일반적 관측 충분성 증명과는 구분한다.

CLI는 probe.py --execute reference|fit|evaluate이고 outputs는 runs/reference, runs/fit, runs/evaluate다. 준비 검수 후 root만 reference128을 실행한다. 음악/해제/stage_ready 원기준 및 reference_analysis/results_v1/review.json PASS/hash 연결 전에는 fit을 거부한다. 이후 같은1000회/192(6구간32)/seed7/Adam3e-4/clip.5/env0..2·heldoutenv3로 한 번만 fit하고 NN-only128을 평가한다. NN 실행 reference/N 호출은 금지한다. 원collect exit1의 단일 보고결함 별도회복 이력은 원문 그대로 보존한다.

원 evaluation.json/trace는 변환된 physical request를 기록한다. observations4.npz와 goal_codec_env0.npz의 raw_goal_normalized/decoded_goal_rad, requested_reference_action 또는 requested_NN_action(둘 다 physical request), guard 후 final_target_rad를 구분한다. source settings 원초기화 문구를 실제 goal 초기화로 해석하지 않는다.

표준편차 값이 같아도 목표각의 물리적 탐색과 증분 탐색은 다르다. 이번은 deterministic 고정기타/F4/finite wrist·같은 장면/seed 진단이며 PPO/자유기타J33/자연스러움·압력·일반화 성공을 주장하지 않는다. GPU/native/fit/실제 새reference128은 CPU 준비에서 실행하지 않는다.

CPU 확인: 원1416행 source reference 요청은 bitexact이며 이 자료의 float32 정규화 왕복 최대각/요청잔차도0이다. 별도 양끝·035·중간각 검사 최대잔차는7.450580596923828e−9rad로 일반 float32 bitexact는 주장하지 않는다. 원fresh73값 동일·새same strict load·원incremental/잘못된tag 거부, 원부호/속도/범위·부분reset·입력 및 다른35 action열 보존·예외복원을 확인했다. 관측부족설을 지지할 누락은 코드읽기에서 찾지 못했으나 학습·native도달 충분성을 보증하지 않는다.
