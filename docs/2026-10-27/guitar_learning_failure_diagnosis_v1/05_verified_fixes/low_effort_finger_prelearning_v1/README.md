# 낮은 상한에서 학습 전 네 손가락 대조

CPU 준비 뒤 root만 `cpu_inputs/jobs.json`의 열 가지 명령을 순서대로 실행한다. 각 장면은 같은 seed7의 네 환경에서 환경별 첫 종료 시도 하나(실패 포함)이며 총 40시도다. 검지112/중지114 reference 네 시도씩은 독립 검수된 원자료를 재사용한다. 약지16/소지23 reference는 원래 목표각 그대로다. 네 환경은 네 seed가 아니다.

`probe.py --prepare`는 원 `make_settings/read_reference`, cap의 private16 effort 사본·105속성 검사, 평가 입력과 독립 검수 자료를 고정한다. 새 프로세스 `--gate-check`가 실제 선행 actual 검수와 자체 입력 봉인을 모두 검사하며 Torch/NumPy/IsaacGym을 import하지 않음을 확인한다. `--execute --finger F --control C`는 독립 준비 검수 PASS와 전체 SHA 확인 뒤 IsaacGym을 먼저 import한다. 기존 출력/상위 symlink를 거부하고 장면·loader 복원·전후 입력 검사를 기록한다. 준비 봉인 이후 PLAN을 포함한 입력은 변경하지 않는다.

원 `runner._evaluate`에 비신경망 행동 공급자만 전달한다. zero는 선택4 행동0, random은 선택4 독립 mean0/std0.1711710544767014 Gaussian을 tanh한 seed7 명령이다. reference는 기존 evaluator의 2초 ramp/trajectory다. 비선택 B/엄지035/손목v3/물리240Hz/제어60Hz/범위·4rad/s/PD/90충돌은 그대로이며, private 비엄지16축 effort만 기존 cap 조건0.25Nm다. 다른89축/엄지5축은 원본이다. NN·기존 checkpoint·학습·그래픽은 없다. 설정의 updates1은 원 make_settings 문서 호환 필드이며 실행되는 학습 업데이트는0이다.

원 `evaluation.json`의 네 시도 원장·각도 통계와 `trace_env0_episode0.npz`(env0 첫 시도60Hz, 실패 끝점 포함)를 저장한다. trace의 legacy `policy_action` 필드는 이 비신경망 명령을 뜻하며 기존 untrained NN과 exact라는 뜻이 아니다. force는 몸체 합력이고 실제 접촉쌍 압력이나240Hz 최대값이 아니다. 고정 기타·팔 안내 조건의 명령 대조이며 팔 이동만으로 달성해도 손가락 학습 성과로 세지 않는다. 자유 기타·전곡·자연스러움은 미검증이다.
