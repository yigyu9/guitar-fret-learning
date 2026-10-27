# 단음 국소 동작 구현 검수 v1

요약 판정: **문제없음**. 현재 동결한 코드의 연결·판정·기록을 검수한 결과이며, 실제 해제/회복이나 학습 정책의 음악 성공을 인증한 판정은 아니다. 검수자는 생산 코드·기존 자료·실행 중인 프로세스를 변경하지 않았고 native 실험을 실행하지 않았다.

- Critical: 없음.
- Warning: 없음.
- Suggestion: 없음.

## 확인한 근거

- `guitar_learning/local_skills/controls.py:87`: 실제 정책 시작부터 매 60Hz tick을 관측하고, 왼손은 음 종료 뒤에만, 오른손은 이전 실제 측정의 첫 accepted crossing 뒤에만 후보로 전환한다. 39행동 범위·반대손 0을 검사한다. 적용 target hold는 기존 비대칭 codec의 역변환으로 구성하고 마지막 명령 유지와 구분한다.
- `guitar_learning/local_skills/probe.py:108`: `env.step(action)` 전의 관측과 실제 그 step에 사용한 행동을 함께 캡처한다. 원 563 관측·39행동·7초/420tick 품질 및 240Hz 안전 판정을 그대로 사용하며 원 모델 전체 가중치를 정확히 불러온다. 한 번에 native 환경 하나, 시작 여유 8GiB/진행 중 6GiB, case 600초 보호를 적용한다. CLI에서 Isaac Gym을 NumPy/Torch보다 먼저 import한다.
- `guitar_learning/local_skills/probe.py:170`: cleanup 이후 최종 case/result를 한 번만 생성하고, 원 실패·cleanup 실패·입력 변경을 보존한다. cleanup 실패는 성공을 취소한다. 교사 suffix 성공을 학습 정책 성공으로 표현하지 않는다.
- `guitar_learning/local_skills/learning.py:75`: 정상 종료한 parent search와 일치하는 성공 case만 받는다. 원 checkpoint/전체 계약/SHA·완전한 420행 배열·실제 원 정책의 관측별 결정적 행동을 확인한다. 실패·진행 중 캡처를 BC로 넘기지 않는다.
- `guitar_learning/local_skills/learning.py:175`: 국소 교사 행동과 비개입 구간의 원 정책 행동에 각각 MSE를 부여한다. 선택 손의 actor만 최적화하고 critic·반대손·std·buffer·전역 Torch RNG 보존을 검사한다. prefix 오차를 보고하며 원 동작 보존을 무조건 보장한다고 설명하지 않는다.
- `guitar_learning/local_skills/evaluate.py:20`: 교사 없는 정책 평가에 시작 8GiB/매 60tick 6GiB, case 600초/전체 3000초 보호를 적용한다. 직렬화 후에도 전체 예산을 확인한다. 실패 및 cleanup 원인을 남기며 실패한 평가로 새 gate를 발급하지 않는다.
- `guitar_learning/local_skills/train.py:14`: 동일 BC·원 checkpoint·dataset·전체 native 계약을 나타내는 SHA와 실제 평가 자료를 검증하고, 원 품질/안전 전체 실행 4/4를 통과해야 새 PPO를 허용한다. actor 초기화와 새 critic/Adam/counter를 분리하며 strict resume에는 actor를 다시 주입하지 않는다. 기존 실행기를 process-local patch로 연결하고 종료/실패 시 binding을 복원한다.

## 검증 범위

- controls/probe CPU 8개 PASS: 이 디렉토리의 `probe_cpu_v2.log`를 직접 확인했다. 실제 native dynamics를 사용하는 검사는 아니다.
- learning/dispatch CPU 11개 PASS(25.975초), 담당자 실행 결과. 최종 동결한 5파일 SHA를 검수자가 다시 확인했다. malformed/실패/진행 중 캡처 거부, actor 외 상태 보존, 엄격한 계약, gate 자료 변경, 초기화 순서, strict resume, 자원 보호 및 실패 시 binding/cleanup 경로를 검사한다.
- 기존 169개 및 curriculum 15개 소스 SHA 변경 0은 담당자의 확인 결과다. 이 검수에서 기존 구현을 광범위하게 재검수하거나 실험을 반복하지 않았다.
- 실제 중단된 `left_native_probe_v1/result.json`도 확인했다. 247tick에서 KeyboardInterrupt가 보존됐고, completed/success는 false이며 successful_candidates는 비어 있었다. cleanup_error는 null, 입력 SHA는 유지됐다.
- 최신 `left_native_probe_v2`는 이 기록 작성 시 실행 중이다. 그 실행의 성공 여부, 성공 교사를 사용한 실제 BC, 정책 단독 native 평가 및 후속 PPO 성과는 이 판정에 포함하지 않는다.

## 검수 중 해결한 사항

초안 cleanup 보완 과정에서 `recording.write`의 exclusive 생성 방식으로 같은 case/result를 두 번 쓰는 오류를 발견했다. case의 중간 기록을 `partial_result.json`으로 분리하고 close 이후 `result.json`을 한 번 생성하도록 수정한 것을 확인했다. 정상 종료 및 cleanup 실패 회귀를 포함한 CPU 검사가 통과했다. 정상 native 실행 전 초안을 보존했으며 최신 probe는 `source_v3`/`probe_inputs_v3.json`으로 구분한다.

## 검수한 현재 소스 SHA256

| 파일 | SHA256 |
| --- | --- |
| local_skills/__init__.py | `513300af2013cc94b84138b1bc49dc17ce80e976dfe294053a533e8dcd04b9c1` |
| local_skills/controls.py | `decfaa916bc193b7f7952bf05a251b1ef7950563a859e8936a8a3c21d750ae1e` |
| local_skills/probe.py | `144766bde3facd05d4c3a53900451c2c5bfbd78fe5b26c5efc5d9343c539f7f5` |
| local_skills/learning.py | `f92aa9c66bc12a8da792e4689281ef8cdc08c974fc01dd59c3db43042a42ef15` |
| local_skills/train.py | `e4593b1687e37733d3bf96c2091eaf93e7d716e523e3eb6dcc2dd767cc97a97e` |
| local_skills/evaluate.py | `0678754566877e43f9fdfba1d093b439ed3449dfb8b371a61672bb8a42df624c` |
| tests/test_local_skill_learning.py | `d2204e30f1235d40eac2bb298e4cd6ac59977b47ea4d29b2e776fe42e6e955b4` |
| tests/test_local_skill_dispatch.py | `ccec3aa248c30fe8b07bfebf4f341469756cc9196c56cb32d15d0caf47f6c0da` |
