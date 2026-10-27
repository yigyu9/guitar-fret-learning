# 손별 사전학습·전문가 결합 구조 구현 결과

왼손33/오른손6 독립 Actor, 공통 reward/cost Critic, 손별 독립 성공 판정과 기존 안정성 제어를 연결했다. CPU168개 검사와 실제5개 실행을 통과했다. **연결·저장·역할 분리의 검증이며, 손별 기능 학습 성공은 아직0회다.** 장시간 학습은 시작하지 않았다.

실행법·보상·성공 정의·후속 범위는 [SPECIALIST_TRAINING.md](/home/ajou/yigyu/3/guitar_learning/SPECIALIST_TRAINING.md)에 정리했다. 현행 초기 자세·모델·gain·충돌 정책을 바꾸지 않았다.

## 구현

| 파일 | 역할 |
| --- | --- |
| [specialist_policy.py](/home/ajou/yigyu/3/guitar_learning/specialist_policy.py) | 독립 Actor 두 개, 활성 채널의 탐색/likelihood, 전체 전문가 전달과 동결 |
| [specialist_environment.py](/home/ajou/yigyu/3/guitar_learning/specialist_environment.py) | LH 접촉·연속 유지와 RH 기하 타현의 독립240Hz 이력, 기존 안정성·음악 기록 보존 |
| [specialist_settings.py](/home/ajou/yigyu/3/guitar_learning/specialist_settings.py) | left/right/joint, 전문가 경로, 양의 비용 가중치, B 단음 범위 검사 |
| [specialist_parallel.py](/home/ajou/yigyu/3/guitar_learning/specialist_parallel.py) | 기존 spawn pool과 persistent native 환경 연결, 손별 지표 저장 |
| [train_specialists.py](/home/ajou/yigyu/3/guitar_learning/train_specialists.py) | 기존 PPO·RAM 보호·진행 로그·체크포인트 재사용, 전문가 SHA와 결과 요약 |
| [왼손 설정](/home/ajou/yigyu/3/guitar_learning/configs/specialist_left_B_v1.json) · [오른손 설정](/home/ajou/yigyu/3/guitar_learning/configs/specialist_right_B_v1.json) | 각8환경/H256/최대128업데이트/2시간 예산. 이번 실제 검증에는 아래 별도 작은 설정 사용 |

기존 `policy.py`, `ppo.py`, `train_parallel.py`, persistent 구현과 원 실험 Python은 수정하지 않았다. 새 CLI는 독립 프로세스 안에서 기존 실행기의 의존성을 선택하며 종료·예외 시 복원한다. 원래 CLI는 비교·재현 경로로 남는다. 이전 기능·검사·문서68개를 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_specialists/manifest.json)에 기록했고, 실제 실행 전 Python69개를 [실행 소스 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialists_v1/source_run_v1/manifest.json)에 복사·봉인했다.

## 단계별 성공과 안정성

- `left`: `[press_s,end_s]` 안의 올바른 손가락·현·프렛 접촉 후보를 연속50ms 유지. RH 타현은 전제하지 않는다. 음 전체 유지와 해제를 모두 성공해야 하는 단계는 아직 아니다.
- `right`: 지정 현·방향의 유효한 기하 타현을 onset ±50ms 안에 수행. LH 접촉을 전제하지 않는다.100ms와 시간 무관 기하 통과도 별도 기록한다.
- `joint`: 기존 접촉 조건이 포함된50ms 매칭. 기존 유지·해제 기록과 보상은 그대로 남는다. 단계 성공 자체가 음 전체 유지·해제나 음향 완수를 뜻하지 않는다.
- 위 단계 성공은 안전한 시간표 종료까지 요구한다. 중간 성취는 provisional로 구분하고, 물리 실패가 발생하면 성공을 무효화한다. 원래 `music`과 별도 `specialist`를 같이 저장해 단독 성공을 통합 음악 성공으로 바꾸지 않는다.

Root 고정·하체 유한 제어·105/97/8·양발 접지 검사·자유 기타/중력ON/스트랩OFF·2초 준비를 유지한다. 기타 힘/부착/지속 state overwrite를 추가하지 않았다. 기존240Hz 기타/발/접촉/관절 속도 비용과 종료를 계속 사용한다. 실제 신경망 출력은39이며 나머지66축은 기존 유한 제어다. 이는 Root 자유 균형이나 신경망 전신 제어의 검증이 아니다.

## 실제 제한 실행

모든 실행은 같은 첫 음(물리2번 줄·7프렛·약지·down),60Hz 정책/240Hz 물리,medium,CPU 정책,준비2초다. 각 실행에서 PPO 업데이트1회만 수행했다. joint는2worker, 나머지는1worker다.

| 실행 | 전이 수 | 완료 episode | 손별/통합 단계 성공 | 물리 실패 |
| --- | ---: | ---: | ---: | ---: |
| [왼손 단독](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialists_v1/native_left_v1/report.json) | 88 | 1 | 0 | 0 |
| [오른손 단독](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialists_v1/native_right_v1/report.json) | 88 | 1 | 0 | 0 |
| [왼손 동결·오른손 적응](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialists_v1/native_right_with_left_v1/report.json) | 88 | 1 | 0 | 0 |
| [양손 공동·2worker](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialists_v1/native_joint_v1/report.json) | 176 | 2 | 0 | 0 |
| [왼손 strict resume](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialists_v1/native_left_resume_v1/report.json) | 4 | 0 | 0 | 0 |
| 합계 | 444 | 5 | 0 | 0 |

PPO에 반영한 정책 물리 표본은1,776개다. 4개 제어 단계의 재시작 실행은 시간표를 끝내지 않았으므로 완료 episode에 세지 않았다. 다른 실행은 worker마다1개 전체 시간표를 수집하고 collector가 다음 episode를 준비한 뒤 종료했다. 준비 물리 표본은 위1,776개와 별도다.

결합 검증에는 **성공한 기능이 없는1업데이트 checkpoint**를 연결 fixture로 사용했다. actor 전달·동결·동시 실행을 확인하기 위한 것이며, 기능을 학습한 전문가의 결합 성능을 확인한 결과가 아니다.

각 실행은 입력 무변경·원 모델/설정 parity·native guard·worker 정리와 persistent lifecycle 감사를 통과했다. 새 모델의 장기8환경 메모리/수렴은 검증하지 않았다. 기존 실제 실행의 경고 출력은 console 원문으로 보존했다.

## 수치·가중치 대조

[analyze_native.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialists_v1/analyze_native.py)로 [native_verification_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialists_v1/native_verification_v1.json)을 생성했다.

- 비학습 Actor와 해당 std가 업데이트 전후 정확히 동일했다. 단독 실행의 반대 손 행동은 모든 기록에서 정확0이었다.
- 전문가 결합 초기값에서 양손 인코더·출력층·std가 각각 source와 정확히 일치했다.
- 동결 왼손은 적응 실행의 전체88개 관측에서 원 전문가와 결정적 출력이 정확히 같았다.
- strict resume 직후 저장한 초기 checkpoint는 원본의 model·두 optimizer·업데이트 수·cost weight·Python/NumPy/Torch/CUDA RNG·identity와 정확히 같았다. 이후 업데이트 수1→2를 확인했다.
- 저장한 실제 행동과 rollout latent의 tanh 출력이 일치했고, 모든 최종 모델이 유한하며 KL guard를 통과했다.

안정성 위치·회전·지지율의 정량 통계는 검증 JSON의 `stability_endpoint60Hz`에 있다. 저장한444개60Hz 말단 표본에서 전체 지지와 양발 접지는 모두100%였고, 세 부위 동시 지지는393/444(88.51%)였다. joint의 삼중 지지는78.41%로, 모든 부위가 매 순간 동시에 닿은 결과는 아니다. 전체 최대 기타 이동1.457mm·회전0.00506rad·발 이동0.253mm다. 물리 실패 검사는 모든240Hz substep에서 수행하며 실패 사유의 합집합을 기록하지만 전체240Hz 원자료를 매 tick 저장하지는 않는다.

CPU전체 결과는 [168개 검사 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialists_v1/cpu_tests_v1.log), 최종 양의 비용 가중치 검사는 [추가5개 검사 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialists_v1/cpu_runner_final_v1.log)에 있다. 별도 검수는 [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialists_v1/review.md)를 참조한다. 최종 보존 감사는 `final_verification.json`에 별도로 봉인한다.

## 다음 순서

1. 현재 행동 범위와 native 판정에서 실제 압현·타현 성공 궤적을 각각 확보한다. 거리 감소나 합성 CPU fixture를 이 성공으로 대신하지 않는다.
2. 각 손을 별도로 학습하고 여러 reset에서 성공·안정성을 확인한다. 현재 ready 설정은 이 단독 학습용이다.
3. 성공한 두 전문가를 결합해 상대 손의 움직임에 적응시키고 공동 미세조정한다. 단독 성공률이 그대로 유지될 것이라고 가정하지 않는다.
4. 결정적 영상 평가, 압현의 onset/end 유지·해제, 음 전환·구절, 안정적인 지지의 정책 잔차 확대는 후속 단계로 다룬다. 기존 `validate.py`는 원 공유 Actor 전용이며 새 모델용 영상 평가기로 아직 연결하지 않았다.

현재 단계가 확인한 것은 새 구조의 실행 가능성과 안정성 회귀 보존이다. 역할 분리가 학습 병목을 해결하는지, 새로운 곡으로 일반화되는지는 이 결과만으로 판단하지 않는다.
