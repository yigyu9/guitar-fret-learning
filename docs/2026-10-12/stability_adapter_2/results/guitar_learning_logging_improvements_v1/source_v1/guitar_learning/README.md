# 자유 기타 학습 — 현재 개발 코드

**2026-10-19 로그 개선:** 기존 학습 명령에 역할별 음악·240Hz 안전 요약, PPO 통계, 중단 시 prefix/전이 회계, 최종 모델 중복 축소를 적용했다. [새 로그 읽는 법·상세 모드·복구](/home/ajou/yigyu/3/guitar_learning/LOGGING.md). 이전 실행 결과는 유지하며 코드는 `archive/20261019_before_logging_improvements`에 보관했다.

**최신 음악 품질 보완 경로는 `guitar_learning.train_musical_quality` / `evaluate_musical_quality`다.** [구현·판정·보상·실행법](/home/ajou/yigyu/3/guitar_learning/MUSICAL_QUALITY.md). 압현 correct/wrong/missing와 금지 접촉 veto, audible 유지·해제, 타현 준비·추가 통과·현재 회복을 실제 보상/성공에 연결했다. 상태563·39행동·native0초/정책7초다. 아래 actionable536 등은 이전 단계와 공용 기반이며 새 조건의 성공으로 상속하지 않는다. 물리 피크 파지·음향·전곡 화음/뮤팅은 여전히 별도 범위다.

**현재 권장 타이밍 경로는 `guitar_learning.train_actionable_preparation`이다.** [앞2초를 정책 준비에 사용하는 구현·실행법](/home/ajou/yigyu/3/guitar_learning/ACTIONABLE_PREPARATION.md). native 정착0초·정책7초로 전환해 첫2초도 음악 목표를 보고 행동·보상·안전 비용을 PPO에 수집한다. 기존 첫 타현 시각4.12초와 총7초를 유지하며 원래 유한 지지 제어·안전 기준은 유지한다. 이하 native정착2초 경로는 이전 구현·재현 기록이다. 새 초기화에서 오른손 정밀도 변화와 조기 접촉 미달이 있어 기존 성공을 그대로 상속하지 않는다.

**2026-10-18 손별 타이밍 학습 완료:** [실제 학습·로그·모델·결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/README.md). stage0±1.5초 각24회와 stage1±0.5초 각12회, 총43,200전이를 학습했다. 학습 목표 성공은 LH70/72·RH72/72, 물리 실패0이며 최종 결정적 평가는 양손 각각2/2 안전 성공했다. LH 음 구간 접촉 후보 유지율100%, RH는 같은 stage1 안에서 최초 기하 통과 오차15.712→12.286ms로 소폭 개선됐다. 추가 down/up와 양손 음악 성공0은 남아 있다. 동일 단음·같은 준비 시작의 결과이며 전곡·음향·일반화 성공과 구분한다.

**현재 타이밍 구현:** [사전 준비·시간창 단계 학습](/home/ajou/yigyu/3/guitar_learning/TIMING_TRAINING.md) · [실제 검증·실패와 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_curriculum_v1/README.md). 학습 진입점은 `guitar_learning.train_timing_v2`, 평가는 `guitar_learning.evaluate_timing`이다. native 정착2초 뒤 정책이 행동하는 pre-roll1초를 추가하고, ±1.5초에서 ±50ms까지 고정 단계로 좁힌다. 기존505입력에 타이밍 이력31개를 붙인536입력·39출력이다. 가슴 접촉 지속은 성공 필수조건이 아니며 기존 기타 이탈·회전·접지 안전은 유지한다. 새 시간 관측으로 초기화한 정책은 양손 각각 실제2/2 성공했다. 이는 한 손의 접촉/기하 타이밍 단계이며 원래 양손 음악·음향 성공과 구분한다.

**이전 단계 검증: 성공 궤적으로 Actor를 초기화한 손별 학습.** [구현·실행법](/home/ajou/yigyu/3/guitar_learning/IMITATION_TRAINING.md) · [실제 학습·평가 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_imitation_training_v1/README.md). 현행 진입점은 `guitar_learning.train_imitation_ppo_v2`다. 초기화한 신경망의 실제 평가에서 LH접촉유지·RH목표줄기하통과가 각각2/2 성공했다. 같은 단음·동일 준비 시작에서의 결과이며 음악 타이밍·압력·음향·양손 결합 성공은 아니다. PPO는 손별24업데이트·11,520전이를 완료했고 최종 결정적 평가도 각각2/2 성공했다. LH삼중지지 저하가 남아 양손 결합은 진행하지 않았으며, 초기 BC와 최종 PPO를 모두 보존한다. 최종 PPO가 BC보다 모든 지표에서 개선된 결과는 아니다.

**단계 환경과 이전 비용 비교:** [도달→접촉·타현→유지·타이밍 커리큘럼](/home/ajou/yigyu/3/guitar_learning/SKILL_CURRICULUM.md). 진입점은 `guitar_learning.train_skills_v2`, 상태505·행동39이며 단계 이력을 입력에 포함한다. 실제 안정성 비용1/0.1 비교와 궤적 검증은 [이번 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_skill_curriculum_v1/README.md)에 정리한다. 기존 [손별 전문가 구조](/home/ajou/yigyu/3/guitar_learning/SPECIALIST_TRAINING.md)와 아래468차원 공유/독립 Actor 경로는 과거 비교·재현용이며, 새505차원 전문가의 양손 결합은 아직 진행하지 않았다.

**앞으로 새 환경·압현·타현·학습 연결 코드는 이 디렉토리에서 작성한다.** 이전 실험 코드와 구분하기 위해 프로젝트 최상위로 분리했다. 현재 학습 초기화는 저장된 준비 자세에서 시작해 **손 준비·안정화 2초**만 수행한다. `preparation_seconds`로 1~2초 안에서 조절할 수 있다. 이전 22초 검증 절차는 학습 reset에서 반복하지 않는다. 관측·음악 목표·타현·보상/비용·종료·네트워크·PPO 수집을 연결했으며 실제 96단계 수집과 업데이트 1회를 확인했다. 연주 학습 성과를 확인한 단계는 아니다.

상세 차원·입출력·보상식·종료·망 구조·실행법은 [TRAINING.md](/home/ajou/yigyu/3/guitar_learning/TRAINING.md), 실제 결과와 남은 범위는 [이번 구현 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_interface_v1/README.md)에 정리했다.

**추가 검증 결과:** 기본 행동 범위의 실제9개 실행과 제한 학습4회, 전체 CPU89개 검사를 완료했다. 연결은 정상이지만 왼팔/복합 큰 정현파에서 기타 이동 실패가 발생했고 음악 수행 개선은 확인되지 않았다. [최신 검증 결과·도표·실패·다음 순서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_validation_v1/README.md) · [학습 전후 실제 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_validation_v1/media_index.md).

**현재 장기 학습 시작 설정:** 16환경 실행에서 host 메모리 부족과 worker timeout이 발생했고, 14업데이트 동안 음악 매칭은0이었다. 이후 권장은 독립 CPU환경8개/GPU정책/medium/H256/batch2048/actor_lr3e-5/초기std약0.05로 변경했다. RAM 여유4GiB 보호,10초 진행 출력,5초 자원 기록,5업데이트 주기 저장과 실패·중단 시 유효 checkpoint 저장을 추가했다. 새 `dense_v2`는 왼손 조기 접근과 기타 상대 우손 타현 경로의 접근 보상을 보완하며 기존 접촉·음악 성공 판정은 유지한다. [장기 설정·실행·재시작](/home/ajou/yigyu/3/guitar_learning/PARALLEL_TRAINING.md). 이전 [환경 수 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1/README.md)와 [실패 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_16env_analysis_v1/README.md)은 원자료로 보존한다. 새 설정의 장기 음악 수렴은 아직 확인하지 않았다.

**개선 검증 완료:** CPU127개와 실제8환경 단기학습·기존모델 중단/복구·다섯단음pool을 확인했다. 실제음악성공과거리감소는아직확인되지않았다. [개선결과·실패보존·남은범위](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reliability_music_v1/README.md).

## 파일 안내

**시뮬레이터 재사용 학습 진입점은 `guitar_learning.train_persistent`다.** 각 worker에서 sim/env/actor/asset과 제어기를 한 번 만들고, episode 경계에서 관절·기타 상태와 목표·제어/측정 이력을 초기화한다. 실제 준비 시간은 계속 2초다. 기존 실행 중인 학습은 원래 방식으로 계속되며 새 진입점은 다음 실행부터 적용한다. 원래 `train_parallel`은 장면을 재생성하는 대조·재현 경로로 보존한다. [구현과 실제 검증 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_reset_v1/README.md).

| 파일 | 역할 |
| --- | --- |
| [environment.py](/home/ajou/yigyu/3/guitar_learning/environment.py) | TrainingEnvironment와 기존 진단용 환경을 내보내는 진입점. 기본 준비 2초 |
| [training_environment.py](/home/ajou/yigyu/3/guitar_learning/training_environment.py) | 실제 240Hz 음악·안정성 측정과 Gym 방식 관측/보상/종료 연결 |
| [observations.py](/home/ajou/yigyu/3/guitar_learning/observations.py) | 상태468·이벤트64×24·우선토큰2×24, 필드/scale 규약 |
| [music_task.py](/home/ajou/yigyu/3/guitar_learning/music_task.py) | 정본 이벤트 선택·시간표·50/100ms 매칭·유지·해제 이력 |
| [strike.py](/home/ajou/yigyu/3/guitar_learning/strike.py) | 움직이는 기타 기준 240Hz 피크 선분 통과와 재준비 판정 |
| [task_measurement.py](/home/ajou/yigyu/3/guitar_learning/task_measurement.py) | 목표별 압현/열린현·타현·유지/해제를 실제 표본으로 측정 |
| [safety.py](/home/ajou/yigyu/3/guitar_learning/safety.py) | 기타 편차·실제 지지/접지·발 이동 비용과 실패 조건 |
| [policy.py](/home/ajou/yigyu/3/guitar_learning/policy.py) | attention과 역할별39출력, 별도 Actor/Value와 reward/cost critic |
| [ppo.py](/home/ajou/yigyu/3/guitar_learning/ppo.py) | PPO·GAE·KL 복원·입력 계약/optimizer/RNG 체크포인트 |
| [rollout.py](/home/ajou/yigyu/3/guitar_learning/rollout.py) | 단일 환경 수집과 terminal/time-limit/bootstrap 처리 |
| [train.py](/home/ajou/yigyu/3/guitar_learning/train.py) | 명시한 실행 예산으로 native 수집·PPO·원자료/소스 SHA 기록 |
| [train_parallel.py](/home/ajou/yigyu/3/guitar_learning/train_parallel.py) | 새 실행기가 재사용하는 병렬 PPO 핵심. 직접 실행은 장면 재생성 대조용 |
| [train_persistent.py](/home/ajou/yigyu/3/guitar_learning/train_persistent.py) | 권장 학습 실행기. 기존 PPO와 저장을 유지하고 같은 시뮬레이터에서 episode reset |
| [persistent_parallel.py](/home/ajou/yigyu/3/guitar_learning/persistent_parallel.py) | 독립 spawn worker의 재사용 환경 선택 |
| [persistent_environment.py](/home/ajou/yigyu/3/guitar_learning/persistent_environment.py) | 기존 음악·보상·관측 환경의 session 유지와 예외 정리 |
| [persistent_session.py](/home/ajou/yigyu/3/guitar_learning/persistent_session.py) | native 상태 복원·제어 이력 초기화·물성/생성 횟수 검사 |
| [persistent_audit.py](/home/ajou/yigyu/3/guitar_learning/persistent_audit.py) | 종료 후 reset/lifecycle 근거를 최종 report에 결합 |
| [monitoring.py](/home/ajou/yigyu/3/guitar_learning/monitoring.py) | RAM 보호·진행 출력·현재 RSS/PSS와 peak 구분·중단 복구 저장 |
| [dense_environment.py](/home/ajou/yigyu/3/guitar_learning/dense_environment.py) | 기존 성공 판정을 유지하는 조기 왼손 접근·기타 상대 우손 타현 경로 보상 |
| [task_sampling.py](/home/ajou/yigyu/3/guitar_learning/task_sampling.py) | 명시한 B 단음 pool의 균형 선택·공통 계약·episode 원목표 기록 |
| [parallel.py](/home/ajou/yigyu/3/guitar_learning/parallel.py) | 독립 spawn 환경과 중앙 batched 정책, 부분reset·terminal/bootstrap |
| [headless_session.py](/home/ajou/yigyu/3/guitar_learning/headless_session.py) | 원 물리·제어를 유지하며 카메라OFF/물리thread1로 구성 |
| [configs/](/home/ajou/yigyu/3/guitar_learning/configs) | 실측으로 선정한 장기 실행 설정 |
| [validate.py](/home/ajou/yigyu/3/guitar_learning/validate.py) | 기본 범위 역할별 궤적·엄격한 체크포인트 계약의 결정적 평가, 정책 준비부터 종료까지 영상 |
| [prepared_reset_v1.py](/home/ajou/yigyu/3/guitar_learning/prepared_reset_v1.py) | 준비된 관절·기타 상태를 reset 초기값으로 한 번 적용하고 기존 유한 유지 제어를 연결 |
| [geometry_v1.py](/home/ajou/yigyu/3/guitar_learning/geometry_v1.py) | 움직이는 기타 좌표계, 프렛 목표와 피크 상대 이동 계산 |
| [fretting_v1.py](/home/ajou/yigyu/3/guitar_learning/fretting_v1.py) | 지정 손가락·현·프렛 접촉 후보와 유지 시간·목표 접촉 소실 측정 |
| [fretting_environment_v2.py](/home/ajou/yigyu/3/guitar_learning/fretting_environment_v2.py) | 기본 환경에 240Hz 실제 접촉 측정 연결 |
| [control.py](/home/ajou/yigyu/3/guitar_learning/control.py) | 39행동과 상체 81목표의 제어권·범위·속도 규약 |
| [whole_body_control.py](/home/ajou/yigyu/3/guitar_learning/whole_body_control.py) | 105관절 이름·목표 규약. 현재 환경은 이 파일의 이름 집합을 사용하며 실제 하체 유한 제어는 기존 native 제어기가 담당 |
| [run_fretting_probe_v3.py](/home/ajou/yigyu/3/guitar_learning/run_fretting_probe_v3.py) | 준비 후 1초 접촉 측정 확인 및 상태·영상 기록 |
| [native_session.py](/home/ajou/yigyu/3/guitar_learning/native_session.py) | 기존 유한 제어와 관절 규약을 연결하는 공통 native 기능 |
| [recording.py](/home/ajou/yigyu/3/guitar_learning/recording.py) | 검증 실행기의 입력·소스 기록과 결과 저장 공통 기능 |
| [tests/](/home/ajou/yigyu/3/guitar_learning/tests) | 환경·기하·접촉·제어 규약·기록 경로의 CPU 검사 |

현재 권장 파일만 개발 디렉토리에 둔다. 새 버전을 작성할 때 이전 버전과 관련 검사는 [archive/](/home/ajou/yigyu/3/guitar_learning/archive/README.md)에 먼저 보관한다. 파일의 버전 번호는 이전 구현과의 대응을 위해 유지한다. 보관본은 수정용 코드가 아니며 현행 코드에서 import하지 않는다.

## 실행 위치와 검사

프로젝트 루트 `/home/ajou/yigyu/3`에서 실행한다. 기존 `rl38` 환경과 프로젝트 자산이 필요하다.

```bash
/home/ajou/miniconda3/envs/rl38/bin/python -m unittest discover -s guitar_learning/tests -t . -v
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.run_fretting_probe_v3 --help
```

압현 연결을 실제로 실행할 때의 명령은 다음과 같다. 출력 경로는 아직 없는 새 디렉토리를 지정한다. 준비 시간 변경을 확인하기 위해 준비 2초와 유지 1초의 연결 시험을 한 번 수행했다. 이 검증용 실행기를 매 학습 reset마다 호출하지 않는다.

```bash
PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.run_fretting_probe_v3 \
  --config /home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/inputs_spine_margin035_v1/baseline_v1.json \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_organized_probe_v1
```

## 짧은 준비의 동작

준비 완료 상태와 최종 관절 목표를 초기값으로 적용한 후 실제 시뮬레이션 2초만 진행하고 정책 제어로 넘긴다. 기존 유지 제어의 시간별 보정은 이미 준비가 끝난 제어 단계로 평가하지만 실제 물리 시간은 0부터 센다. reset 이후 기타 상태를 반복해서 덮어쓰지 않는다. 준비 입력 검사는 프로세스 안에서 재사용하고, 매 reset마다 과거 전체 실험이나 장시간 검증을 수행하지 않는다.

이전 22초 방식의 `environment_v3.py`, `fretting_environment_v1.py`, `run_fretting_probe_v2.py`, `run_smoke_v7.py`와 해당 검사는 [이전 버전 보관본](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_archive_cleanup)에 모았다. 현재 환경은 `guitar_learning.environment`에서 가져온다.

## 기존 코드와의 구분

원 실험이 사용한 [이전 환경 코드](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1)는 수정하지 않고 보존했다. 이전 경로는 과거 실험 재현용이며, 현재 개발 기준은 이 새 디렉토리다. 복사한 원본과 SHA의 대응은 [origin_manifest.json](/home/ajou/yigyu/3/guitar_learning/origin_manifest.json)에 기록했다.

초기 자세·모델·native 장면과 제어기는 기존 검증 자원을 참조한다. 구체적으로 `stability_adapter_2/front_facing_ready_v1`, `lower_body_release_v1`, `native_contacts.py`, `gym_trial_recording.py` 및 `paper/initial_pose`의 입력이다. 정본 음악 compiler는 기존 `fresh_music_v1/events.py`와 `tab2body/full/events.py`를 재사용한다. 음악 이력·PPO의 검증된 초안 로직을 현재 관측/제어 계약에 맞게 옮겼으며 망 구조는 새로 연결했다. 이 디렉토리는 프로젝트 안의 개발 패키지이며 단독 배포용 패키지는 아니다.

## 유지 조건과 검증 범위

Root 고정·하체 유한 제어, 105입력/비영범위 97축/원래 영범위 8축, 자유 기타·중력 ON·스트랩 OFF를 유지한다. 고정 기타의 상태 덮어쓰기 경로를 상속하지 않는다. 압현 접촉 후보는 실제 현 압력·진동·음향을 인증하지 않는다.

학습 인터페이스 구현 단계에서는 CPU 검사 **84개**와 실제 native 수집 **96단계·PPO 업데이트 1회**를 통과했다. 상태468/medium 망은 **1,931,600 파라미터**다. 실제 첫 음 시간표 종료 후 reset까지 확인했으며 384개 학습 물리 표본에서 양발 접촉과 세 부위 지지가 유지됐다. 작은 행동범위 0.002rad를 사용했으며 타현 매칭0/미스1이었다. 이후의 기본 범위 검증은 위 최신 결과 링크에 따로 정리했다. 현재 B/C/D 선택이 가능하나, 전체 곡의 복합 `alternate_restrike` 이벤트는 명시적으로 거부한다. 정책 출력은39축이며 하체는 기존 외부 유한 제어를 유지한다.

이전 버전 전용 검사11개와 준비2초 변경 당시의 실제 유지1초 결과는 보관했다. 당시 단계의 PPO0 기록은 과거 결과다. 1초 준비 옵션은 CPU 계약 검사로 확인했으며 실제 연결 시험은 기본2초로 수행했다. 기존 native 생성자의 자산 로딩·입력 호환성 검사는 유지한다.

- [단계1 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_learning_v1/README.md)
- [단계2 접촉 측정·영상·한계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/README.md)
- [현재 이름 변경·검증 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_rename_v1/README.md)

- [준비 시간 2초 변경과 실제 연결 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_short_preparation_v1/README.md)

- [이전 버전 보관과 현재 코드 정리 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_archive_layout_v1/README.md)
