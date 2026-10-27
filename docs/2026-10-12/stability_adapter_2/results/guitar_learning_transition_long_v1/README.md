# 첫 음 왼손 장시간 학습

사용자 요청에 따라 첫 두 음 전환 경로의 장시간 학습을 준비·실행한다. 이번 장기 PPO 대상은 **A: 2번 줄 7프렛 약지**이며, 오른손 타현·B·두 음 전환·전체 곡 성공으로 확대하지 않는다. 현재 진행 상태는 아래 실행 기록과 실제 producer 결과를 함께 확인한다.

## 현재 상태: 20회 모델의 압현 퇴행을 확인해 23회에서 중단

**현재 실행 중인 학습은 없다.** `anchored_training_v2`의 checkpoint20을 새로 실제 평가한 결과 clean 압현 유지율81.6667%로 선언한90% 기준에 미달했다. 이 결과를 확인해 해당 학습 부모에만SIGINT를 전달하여 정상 정리했다. 총23update·44,160전이가 반영됐고 중단 중96전이는 제외했다. 최대128회 계획은 완료되지 않았다. 이번 중단은 수치 오류가 아닌 실제 음악 품질 실패에 따른 의도적 중단이다.

| 실제 결정론적 평가 | clean 유지율 | 해제 | 물리 안전 | 음악 기준 |
| --- | --- | --- | --- | --- |
| checkpoint4 | 100% | 통과 | 통과 | 통과 |
| checkpoint8 | 100% | 통과 | 통과 | 통과 |
| checkpoint20 | 81.6667% | 통과 | 통과 | 실패 |

checkpoint20은2.0~2.5초의0.5초 발음 구간 중0.408333초만 clean을 유지했다. 원래 목표 접촉 후보는2.091667초에 처음 나타나 약91.7ms 늦었다. 해제는 통과했으므로, 이번 실패는 음 시작 전 접촉 준비의 부족으로 확인된다. 작은 출력 변화 제한이 실제 접촉·궤적 성공을 보장하지 못한다는 사례다. 현재 범위는 왼손 첫 음 A이며 두 음 전환·전곡의 결과가 아니다.

학습184episode 중 물리 실패0·탐색을 켠 품질 성공57회(30.98%)였다. 초기10update26/80(32.5%), 다음10update22/80(27.5%)로 뚜렷한 개선 추세는 없다. 탐색 중 성공률과 탐색을 끈 개별 평가는 분리한다. checkpoint20의 동일240개 BC 관측 분석에서 Actor는 변했으나 std는 초기 약0.02 그대로였다. 평균 출력 제한0.0002보다 탐색 크기가 훨씬 큰 상태와 작은 Actor LR가 개선을 제한했을 가능성이 있으나 원인 확정은 아니다.

- [최종 분석](anchored_assessment_after_stop_v1.json), [중단 보고서](anchored_training_v2/report.json), [최신 실제 평가](anchored_checkpoint20_eval_v1/result.json)
- [정책 출력 진단](anchored_checkpoint20_diagnostic_v1.json), [학습 로그](anchored_training_v2.log), [학습 집계](anchored_training_v2/learning_metrics.jsonl)
- 성공했던 [checkpoint8](anchored_training_v2/checkpoint_000007.pt)과 BC는 보존했다. 마지막 복구 모델은 학습 재개 자료이며 성공 모델로 채택하지 않는다. cleanup 오류·입력 변경·누락 worker 감사는0이었다. 전체 초기화 입력도 변경되지 않았다.
- 다음 검토는 탐색량의 별도 조절과 음 시작 전 접촉 준비·여유를 확보하는 보상이다. 이 분석에서는 코드·보상·물리 설정을 추가 변경하거나 새 학습을 시작하지 않았다.

### 이전 무제한 PPO의 중단 근거

`training_v3`는 실제 PPO 10회까지 실행한 뒤 중간 평가의 압현 퇴행을 확인하여 정상 중단했다. 19,200전이가 PPO에 반영됐고, 중단 시 진행 중이던816전이는 반영하지 않았다. worker 정리 오류와 누락 감사는 없었으며 전체 입력은 변경되지 않았다. 복구 checkpoint는 `training_v3/failure_last_valid.pt`에 보존했다. 이 모델을 다음 성공 기준 모델로 채택하지 않는다.

8회 시점까지 탐색을 켠64episode 중19회가 품질 성공이고 물리 실패는0회였다. 하지만 **탐색을 끈 checkpoint8의 실제 정책 평가는 clean 유지율0%로 실패**했다. BC 초기 정책의 독립4회100%와 비교하면 성공 동작이 보존되지 않았다. 안정성이 유지됐다는 사실을 압현 개선으로 설명하지 않는다.

- [중단 보고서](training_v3/report.json), [중간 실제 평가](checkpoint8_policy_eval_v1/result.json)
- [8회까지 학습 요약](early_training_after8_v1.json), [학습 로그](training_v3.log)
- 다음 실험은 성공 BC Actor를 고정 참조로 두고 결정론적 출력 변화 폭을 제한하는 새 정책이다. 새 검수·소스 봉인·초기 실제 평가 후 새 실행에서 시작한다. 평균 출력 제한은 접촉 성공이나 탐색 행동 전체의 보장이 아니다.

## 학습 전 실제 확인

| 단계 | 결과 |
| --- | --- |
| 새 실제상태 피드백 교사 A | 4초 안전 완주, 2~2.5초 clean 유지율100%, 접촉 해제 통과 |
| 같은 교사 B | 4초 안전 완주, clean0%; 성공자료에서 제외 |
| A 성공자료 BC | 2,000step, MSE0.0160730→0.000179809 |
| 교사 없는 A 정책 | 독립 native 실행4회 모두 clean 유지율100%, 해제·안전 통과 |
| PPO 시작 gate | 전체 원자료 재계산·4회 정책 재현·모델/계약/출처 검사 통과 |

BC 최대 단일 행동 오차는0.9983으로 수치 fitting tolerance1e-6을 만족하지 않았다. 실제4회 재현 성공과 학습자료 오차는 별도 결과다. 평가4회는 독립 단회 실행이며, 같은 native scene의 반복reset 안정성이나 새로운 초기상태·다른 목표로의 일반화 증거가 아니다.

- [학습 전 검증](verification_before_ppo_v1.json), [PPO 시작 증거](ppo_gate_v1.json)
- [성공 교사 A](single_a_contact_v1/result.json), [실패 교사 B](single_b_contact_v1/result.json)
- 보조 없는 평가: [v1](single_a_bc_eval_v1/result.json), [v3](single_a_bc_eval_v3/result.json), [v4](single_a_bc_eval_v4/result.json), [v5](single_a_bc_eval_v5/result.json)

## 설정

[single_a_ppo_settings_v1.json](single_a_ppo_settings_v1.json): medium, 관측500·행동39 중 왼손33만 학습/오른손6은0, N8/H240, 최대128update/14,400초. 최대245,760개 전이와1024개4초 episode에 해당한다. 실제 처리량과 종료 시점에 따라 달라진다. Actor LR1e-5, Value LR3e-4, KL0.02/retries3/초과 시LR×0.25, 기존 안전 비용과 메모리 가드 유지. 매 update checkpoint를 저장한다. 과거 전곡2환경 처리량으로 새 단음 소요시간을 단정하지 않는다.

BC의 선택 Actor/std만 초기화하고 Critic·Adam·PPO 카운터는 새로 시작한다. 학습 중 교사 보정은 없다. Root만 고정·하체 유한제어·105/97/8·자유 기타/중력ON/스트랩OFF·원 gain/행동범위/속도 제한/240Hz안전 판정을 유지한다. 해제에 대한 직접 보상이 없는 기존 보상 구조이므로, 학습 보상 증가만으로 해제 유지나 실제 정책 개선을 판단하지 않는다.

## 새 코드

- `guitar_learning/transition/contact_teacher.py`: 측정한 관절·손·기타 상태로 실제 프렛 source 표면에 접근하는 bounded 목표 보정. native 접촉 판정을 성공 기준으로 사용한다. A clean+B positive 준비와 B clean 발음을 구분한다. 해제 시 피드백 누적을 지운다.
- `guitar_learning/transition/probe_contact.py`: 기존 감사 가능한 probe를 재사용해 실제 환경을 교사에 전달한다. 상태/힘/gain 변경 없이 명령만 보정한다.
- 신규 검사10개 통과, 별도 change-reviewer 검수 통과. 원래 전환 검사53개와 봉인된24파일은 변경하지 않았다. [추가 검사](cpu_contact_v1.log), [소스28개 봉인](source_pins_v1.json).
- `guitar_learning/transition/train_with_teacher_proof.py`: 실제 native 자산과 오프라인 교사 보조 입력의 증거 유형을 분리하는 진입점. 원BC/4gate/전체 입력 SHA/strict resume/native parity는 유지한다. 실제 generic preflight 통과·unknown XML 거부·변조·예외·Isaac-first 검사6개가 통과했다. [검사](cpu_teacher_proof_v1.log), [새 소스30개 봉인](source_pins_v2.json). [권장 명령](../../../../../guitar_learning/transition/CONTACT_TRAINING.md)을 따른다.

## 보존한 실패와 시작 연결 문제

- BC v1은 원모델을 상대경로로 지정해 fitting 전에 거부됐다. 필수 절대경로를 사용한 v2를 채택했다. 실패 로그는 보존했다.
- 반복 평가 `single_a_bc_eval_v2`는 첫 case 성공 뒤 두 번째 case에서 SIGFPE/exit136으로 종료됐다. 최종 producer/lifecycle가 없어 전체를 gate에서 제외했다. 뒤의 독립4회 성공과 혼동하지 않는다. native 오류의 정확한 원인은 아직 확정하지 않았다.
- 첫 `training_v1`은 실제 장면 생성/PPO update 이전에 `original model/config parity failed`로 중단됐다. 참고 FK 모델 `stability_adapter_2/assets/humanoid_fixed_lower.xml`을 실제 native 자산과 똑같이 분류한 것이 원인이었다. 실제 자유 하체 모델/물리 설정이 달라진 것은 아니다. 해당 보조 XML의 증거 유형을 구분하는 새 진입점을 준비하며, 기존 native 모델 parity·전체 BC·4회 평가 검사는 유지한다.
- 해당 연결을 수정한 `training_v2`도 native 생성/PPO0 상태에서 SIGFPE로 중단됐다. faulthandler는 원자료 안전값을 JSON으로 변환하는 CPU 감사 구간을 가리켰다. 같은 기록을 실제 Isaac import·원wrapper import·GDB에서 총6회 감사했으나 재현되지 않았고 FPU 상태는 정상이었다. [진단 기록](fenv_diagnostic_v1.json). 따라서 FPU 모드·직렬화·물리 설정은 바꾸지 않았으며, 같은 코드/설정의 `training_v3`로 새로 실행해 실제 PPO 반영까지 확인했다. 수치 오류의 근본 원인을 해결했다고 주장하지 않는다.

[첫 시작 기록](launcher_started_v1.json), [첫 시작 종료 코드](launcher_exit_v1.json), [첫 시작 로그](training_v1.log)는 실패 기록이며 학습 진행으로 세지 않는다.

장기 native 실행에는 `PYTHONFAULTHANDLER=1`을 사용한다. worker 비정상 종료 시 마지막 유효 PPO checkpoint와 미반영 전이를 구분한다. 실패 run과 원자료를 덮어쓰지 않으며, 재개가 필요하면 동일 계약으로 새 output에서 strict resume한다.

## 보존형 정책 v1 — 새 검증 중

`anchored_policy.py`는 BC 왼손 Actor의 사본을 학습하지 않는 참조로 저장한다. 학습 가능한 Actor의 평균은 `BC + 0.0002*tanh((학습Actor-BC)/0.0002)`로 결합한다. 초기 결정론적 행동은 BC와 정확히 같고, 같은 관측에서 latent 평균 및 tanh 행동의 차이를 제한한다. 출력의 초기 미분은1이다. 원 Gaussian 탐험과 학습 가능한 std/clamp[-5,2]는 유지하므로 확률적 행동·궤적·접촉 성공까지 보장하지 않는다. 관절 gain·행동 범위·보상·안전·물리는 변경하지 않았다.

참조 Actor만 추가되며 참조 Critic은 없다. 새 Critic·Adam·PPO 카운터에서 시작한다. 새 모델의 strict identity는 BC SHA·제한 폭·수식·탐험 범위를 포함하며, 이전 PPO와 혼용하지 않는다. 새 모델용 성공 평가4개는 동일한 behavior_prior와 실제 새 코드 해시까지 검증한다. 원 BC·교사·입력·native 모델 감사도 유지한다.

- [검사9개 통과](anchored_cpu_tests_v1.log), [소스33개 봉인](source_pins_v3.json). 기존30개 활성/보관 소스의 변경은0개다.
- [동일 BC 관측에서 기존 PPO 출력 편차](bc_drift_diagnostic_v1.json). 기존 checkpoint8의 작은 출력 편차와 실제 실패를 근거로 보수적인 제한을 택했다. 이 오프라인 비교만으로 실제 퇴행 원인을 확정하지 않는다.
- [새 초기 평가 설정](single_a_anchored_eval_settings_v1.json), [새 장기 설정](single_a_anchored_ppo_settings_v1.json). 초기 native 평가가 진행 중이며 아직 장기 PPO를 시작하지 않았다.
- 실행 진입점: `python -m guitar_learning.transition.anchored_run eval|train --settings ... --out ...`. 평가에 `--checkpoint`, 재개에 `--resume`을 사용한다. 결과는 기존 파일을 덮어쓰지 않는 새 경로로 남긴다.

이 실험은 단음 A의 성공 보존과 제한된 개선을 확인하는 실험이다. 최신 실제 장기 설정은 settings_v3이며, settings_v1/v2는 준비 과정의 보존본이다. 두 음 전환·B·오른손·전곡 성공으로 설명하지 않는다.

초기 평가v3은240Hz 결과를 기록하는 JSON 구간에서 SIGFPE로 종료돼 최종 producer가 없으므로 제외했다. v1/v2는 성공했으며 v4/v5는 GDB 감독 아래 독립 평가한다. GDB 실행 자체는 성공 증거가 아니며 실제 producer와 원자료로 판정한다.

장기 실행은 [settings_v2](single_a_anchored_ppo_settings_v2.json)를 사용한다. 기존 업데이트1의 실제 Actor 가중치를 BC와 보간한 [출력/미분 진단](anchored_lr_scale_diagnostic_v1.json)을 근거로 Actor LR를1e-8로 낮췄다. 기존1e-5를 쓰면 작은 출력 제한의 경계에 바로 포화할 위험이 있었다. 이 진단은 새 PPO 업데이트 실측이 아니므로 첫 실제 업데이트에서 다시 확인한다. Critic LR3e-4·N8/H240·128update/4시간 예산은 유지한다.

### 첫 실제 업데이트 점검

[checkpoint1 진단](anchored_checkpoint1_diagnostic_v1.json): 성공 BC 재생의240개 관측에서 초기 출력 일치와 실제 Actor 변경을 확인했다. 평균 경사 전달률99.13%, raw 차이/제한폭의95백분위0.1496, 큰 포화 표본0, 결정론적 행동 변화 최대0.0000698이었다. 참조 Actor17개 tensor와 오른손17개 tensor는 불변이며 오른손 출력0, 학습 Actor16개·Critic18개 tensor는 변경됐다. std는float32에서 변경되지 않았다. 이 분석은 동일 관측에서의 출력·가중치 검사이며 새 native 성공의 증거는 아니다.

### 수치 오류의 현재 범위

[실제 GDB/관찰 진단](native_sigfpe_diagnostic_v3.json)에 v5 및 장기 시작v1의SIGFPE와 v6관찰 실행을 보존했다. 현재 확인된 것은 JSON float 문자열 변환 도중의x87 precision예외다. 저장된 제어워드는 정상이고 현재 제어워드는 비정상인 순간을 포착했지만 원인 라이브러리는 확정하지 않았다. 현재 프로세스의 과거FIP 주소 매핑은SciPy/Boost의 마지막x87명령을 가리켰으나 과거 당시mapping이 없어 원인 확정에 쓰지 않는다. FPU모드·직렬화·physics·CPUaffinity·신호를 바꾸지 않았다. GDB감독은 첫fatal에서 중단하고 실제프로세스 exitcode를 반환한다. 재시도v2가 실제PPO를 반영한 사실은 근본원인 해결과 구분한다.
