# Goal angle-loss CPU 준비

원 goal1000 NN의 음악126/128·A 해제73/128과 비교할 단일 loss 변경이다. 원 fresh73/1416행/1000×192/6구간/env0..2·heldout3/seed7/Adam3e−4/clip.5를 유지하고, 손실만 기존 decode 뒤의 각도 rad² MSE로 바꾼다. 추가1000회나 기존70e40d 모델에서 시작하지 않는다. 기존 GoalPolicy/관측/codec/105/.25Nm/90쌍/손목/guard/9항·기준은 그대로다.

원 reference128의 독립PASS를 재사용한다. 새 reference 수집·PPO·GPU 실행은 이 CPU 준비에서 하지 않는다. root가 독립 준비PASS 뒤 `cpu_inputs/commands.json`의 fit→evaluate 두 명령만 순서대로 실행한다. 출력은 `runs/fit`, `runs/evaluate`이며 기존 출력과 symlink는 입력·native import 전에 거부한다.

새 metadata schema/procedure는 `diagnostic.index_prefix_goal_angle_loss_initialization.v1`이다. 환경·GoalPolicy의 output identity는 원 goal과 같지만 초기화 절차/loss 출처는 새 선언으로 구분한다. full trainer.load를 그대로 쓰고 원 raw-loss 모델을 이 실험의 저장본으로 받아들이지 않는다. raw 목표·각도 오차를 함께 기록하고 새 빈 PPO/update0 저장본 하나만 만든다.

상태 분포/피드백과 해제 미달의 단독 원인을 확정하지 않는다. 표준편차의 수치 동일성은 물리 탐색 동일성이 아니다. 음악·해제·AND 원90% 기준이 모두 필요하며 미달 시 예산/학습률/계수를 자동 탐색하지 않는다. 원 fit 종료1·회복 수용/평가·분석/모델은 보존한다. 영상126모델과 새 결과도 구분한다.
