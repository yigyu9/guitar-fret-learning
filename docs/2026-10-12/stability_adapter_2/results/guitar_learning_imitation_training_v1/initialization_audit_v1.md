# BC → PPO 실제 초기화 감사

감사 결과: **통과**. 실제 저장된 양손 PPO `initial.pt`와 BC 체크포인트를 CPU에서 읽어 텐서별로 비교했다. 새 시뮬레이터·GPU 실행과 소스 수정은 하지 않았다.

| 항목 | 왼손 | 오른손 |
| --- | --- | --- |
| 활성 Actor의 BC 일치 | 17/17 텐서 완전 일치 | 17/17 텐서 완전 일치 |
| 활성 log_std의 BC 일치 | 33채널 완전 일치 | 6채널 완전 일치 |
| 시작 PPO 업데이트 | 0 | 0 |
| Actor / Value optimizer state | 0 / 0개 | 0 / 0개 |
| 505차원·단계·profile 계약 | BC·캡처·실제 PPO 계약 동일 | BC·캡처·실제 PPO 계약 동일 |

활성 Actor와 표준편차는 실제 BC 값과 완전히 동일하며, PPO counter는 0이고 두 Adam state는 비어 있다. 설정·checkpoint metadata·전달 기록·데이터 및 BC SHA·실행 시 source pin도 서로 일치한다. JSON/native 계약의 tuple/list 표현 차이만 정규화하여 비교했다.

**반대 손·Critic에 대한 근거 범위:** 양손 실행 모두 반대 Actor 17개와 Critic 19개 텐서도 BC와 완전히 동일하다. BC가 이들을 학습하지 않았고 seed7을 공유한다는 설정과 일치하는 결과다. 그러나 실제 전송 직전 모델이 별도로 저장되지 않았으므로, 저장된 두 모델만으로 “복사하지 않았다”를 판별할 수는 없다. 특정 fresh seed 원본과 같다는 직접 검증도 하지 않았다.

실행 입력 pin과 일치하는 [로더](/home/ajou/yigyu/3/guitar_learning/imitation_v2.py:51)는 활성 Encoder/Head와 활성 log_std만 복사한다. [실행기](/home/ajou/yigyu/3/guitar_learning/train_imitation_ppo.py:77)는 그 다음 새 PPO trainer를 구성하고, [PPO 생성자](/home/ajou/yigyu/3/guitar_learning/ppo.py:81)는 새 Adam과 counter0을 만든다. 따라서 비활성/Critic 비복사는 봉인된 구현의 근거로 지지되며, 활성 텐서의 실제 전달·빈 optimizer/counter0은 저장 자료로 직접 확인했다.

상세 텐서별 SHA·차이·계약·입력 목록: [initialization_audit_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_imitation_training_v1/initialization_audit_v1.json)

이 감사는 초기화에 한정하며 이후 PPO 개선·일반화·음악 성공을 판정하지 않는다.
