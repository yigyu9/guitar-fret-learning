# 자유 기타 학습

현재 환경·측정·학습·평가 코드는 이 패키지에서 관리한다. 새 손별 학습은 아래 기본 실행에서 시작한다. 연구 범위·실험별 성과는 [master_plan](/home/ajou/yigyu/3/master_plan/README.md)을 따른다. 상태 차원이나 파일 버전이 같아도 목표·보상·입력 SHA가 다른 checkpoint를 혼용하지 않는다.

## 곡 단위 손별 학습 시작

`guitar_learning.train`은 합의한 초기 자세에서 새 손별 정책으로 곡 전체를 학습한다. 기본 곡은 검수된 `data/song_bundles/05_BN2-131-B_solo`의67음 전부다. 왼손은 손목 위치 잡기·압현·곡 연결을 단계적으로, 오른손은 타현을 학습하며 선택하지 않은 손의 정책 행동은0이다. 시작 전에 BC·전문가 모델이나 과거 성공 평가4회를 준비할 필요가 없다.

프로젝트 루트에서 Isaac Gym Preview4가 설치된 `rl38` 환경을 사용한다. 먼저 실행 환경을 설정한다.

```bash
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3${PYTHONPATH:+:$PYTHONPATH}
export PYTHONDONTWRITEBYTECODE=1
```

학습할 손을 골라 아래 명령 중 하나를 실행한다. `--out`은 아직 존재하지 않는 새 출력 경로로 지정한다.

```bash
python -m guitar_learning.train --hand left --device cuda:0 --physics gpu --song 05_BN2-131-B_solo --out /home/ajou/yigyu/3/docs/2026-10-20/left_song_01
python -m guitar_learning.train --hand right --device cuda:0 --physics gpu --song 05_BN2-131-B_solo --out /home/ajou/yigyu/3/docs/2026-10-20/right_song_01
```

흐름은 **곡 입력 확인 → 하나의 GPU PhysX 장면에 환경들을 배치 → 합의한035/v14 초기 자세 복원 → 준비3초와 곡을 연속 진행 → 32tick마다 GPU PPO 업데이트 → 모델 저장**이다. native 대기는0초이며 첫 tick부터 정책이 행동한다. 기본 곡은 원오디오29.3064초에 정책 준비3초·말미0.5초를 더하고60Hz 경계로 올린1969tick, 약32.8167초다. 원곡 시간축과67음 전체를 유지하며왼손512상태/오른손500상태·39행동·실제240Hz 접촉/안전 측정을 사용한다.

기본 GPU 실행은 환경128개·수집32tick·PPO100업데이트·`--device cuda:0`·seed7·medium 모델이다. `--num-envs`는1~1024를 지원한다. `large` 모델과1024환경의 검증 결과는 [GPU 전환 기록](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_gpu_batch_v1/README.md)을 따른다. 곡 전체는1969tick이며32tick의 PPO 경계에서도 시계와 음별 원장이 이어진다. `--horizon`을 짧게 지정해도 PPO 업데이트 경계에서 장면·기타·곡 시계·음별 원장을 초기화하지 않고 다음 수집으로 이어간다. 곡 종료나 물리 실패 때만 초기 자세로 돌아간다. `--updates 1`은 PPO 업데이트 한 번을 뜻하며, 물리 실패가 있으면 곡 완주를 보장하지 않는다.

기본 실행은 GPU가 없으면 오류로 종료한다. `--device auto`를 명시하면 CUDA를 사용할 수 있으면 `cuda:0`, 그렇지 않으면 CPU를 선택하며 실제 장치를 `settings.json`에 저장한다. 필요하면 `--num-envs`, `--updates`, `--horizon`, `--device auto/cpu/cuda:0`, `--physics auto/cpu/gpu`, `--seed`, `--size`로 바꾼다. `--physics auto`는CUDA 정책이면GPU 물리, CPU 정책이면CPU 물리를 선택한다. 이전 CPU 물리 경로는 `--device cuda:0 --physics cpu` 또는 `--device cpu --physics cpu`로 명시하며 환경1/2/4/8/16·기본수집전곡 조건을 유지한다. `--device cuda:0`를 명시하면 CUDA를 사용할 수 없을 때 오류로 종료한다.

`--song`은 `data/song_bundles` 아래의 곡 식별자다. 시작 전에 전체 악보·타현 계획·오디오 길이를 확인하고 지원하지 않는 입력은 거부한다. 현재 검수된 압현음·일반 타현/명시적 재타현 곡을 지원하며 열린현이나 지원되지 않는 동작을 임의로 생략하지 않는다. 확인된 곡은 아래와 같다.

| 곡 식별자 | 목표 음 수 | 준비·말미 포함 길이 |
| --- | ---: | ---: |
| `02_Jazz1-200-B_solo` |42|17.9초|
| `03_Rock1-130-A_solo` |59|25.65초|
| `05_BN1-129-Eb_solo` |46|25.8333초|
| `05_BN2-131-B_solo` |67|32.8167초|
| `05_Rock2-142-D_solo` |84|30.55초|

실행 설정은 출력의 `settings.json`에 자동 저장한다. 자산·현재 소스 SHA와 물리 안전 조건은 내부에서 검사한다. 같은 계약의 checkpoint를 이어 학습하려면 기존 실행과 같은 손·설정으로 새 출력 경로를 지정하고 `--resume /절대경로/checkpoint.pt`를 추가한다. checkpoint의 관측·행동·목표·보상·물리·PPO 계약은 strict하게 비교하고, 현재 실행 입력의 SHA는 별도로 기록·검사한다. 이전563상태 단음 checkpoint와 이전500상태 왼손 전곡 checkpoint는 새512상태 왼손 계약의 `--resume`에 사용할 수 없다. 손가락 제어 프로필 적용 전512상태 왼손 checkpoint도 제어 계약이 달라 strict resume할 수 없다. 오른손의 상태 차원은500이지만 GPU 물리·제어·접촉 계약이 달라 기존 CPU checkpoint를 재개할 수 없다. 자동 Actor 이전은 하지 않는다.

같은 실행 안에서 PPO 수집을 나눌 때는 곡 중간 상태를 유지한다. 새 프로세스의 `--resume`은 모델·optimizer·난수 상태를 복원하고, 물리 환경은 초기 자세에서 새 곡 에피소드를 시작한다.

선택한 손의 보상과 전곡 성공을 학습 기준으로 삼는다. 양손 협응 성공과 원래50/100ms 음악 판정은 별도 진단이다. `song_report.json`은 실제 종료 에피소드와 손별 성공·물리 실패를 저장한다. 진행 중인 곡의 원장은 메모리에 유지하며 이 파일에 부분 원장 snapshot을 저장하지 않는다. 부분 수집을 완주 성공으로 세지 않는다. 접촉·기하 타현의 성공을 실제 음향 성공으로 해석하지 않는다.

## GPU 물리·관측·보상

기본 실행은 환경마다 프로세스를 만들지 않는다. 하나의 GPU PhysX 시뮬레이터에서 모든 환경을 동시에 진행하고, 관절·몸체·접촉 힘·Jacobian·유한 하체/상체 제어·관측·보상·PPO를CUDA 텐서로 처리한다. 완료 에피소드 요약과 로그만 CPU로 옮긴다. 물리240Hz·정책60Hz이며 선택한 환경만 에피소드 경계에서 초기화한다.

사용자 선택에 따라 GPU 전용 접촉 판정을 새로 설계했다. 실제 손가락 충돌 STL의 표면 샘플이 유한한 현·프렛 영역에 들어오고 해당 몸체의 GPU 접촉 합력이 있을 때 새로운 압현 후보로 판단한다. 접촉 몸체 쌍·실제 witness를 제공하지 않는 GPU API 특성 때문에 기존 CPU의 pair-feature clean 판정과 구분한다. 이를 실제 현 압력·음향 성공으로 해석하지 않는다. 보상 단계 구조는 유지하되 새 후보로 계산한다.

하체는 GPU 기하 질량행렬·유한 stable PD·반복 IK, 상체는 중력 보상·Chest/오른팔 지지 제어를 사용한다. native힘 상한과관절 제한을 유지하며 세부 solver 차이를 새 계약에 기록한다. 초기035/v14·자유 기타·중력ON·스트랩OFF·왼손 유연 프로필을 유지한다. 기존 CPU512/500 checkpoint도 새GPU 실행에 strict resume할 수 없으며 새 GPU 계약의 checkpoint끼리 재개한다.

구현은 `gpu/scene.py`·`gpu/control.py`·`gpu/environment.py`·`gpu/geometry.py`, 수집과 학습은 `training/gpu_pool.py`·`training/gpu_runner.py`다. CPU 재현 경로와 전문 실험기는 기존 구현을 유지한다.

## 왼손 손가락 제어

기본 왼손 커맨드는 `guitar_learning.flexible_left_fingers.v1` 프로필을 사용한다. 왼팔12축과 손가락21축은 정책이 함께 움직이되, 손가락21축은 초기 기준의 고정±0.5rad 대신 각 관절의 기존 native 하한~상한 전체를 목표 범위로 사용한다. 행동0은 여전히035/v14 기준 목표다.

| 항목 | 기본 왼손의 손가락21축 |
| --- | --- |
| 목표 변화율 | 최대4rad/s; 목표 변환과 최종 native 제출 양쪽에서 동일하게 적용 |
| 목표 평활화 | 0.45; 왼팔 등 나머지 활성 축은 기존0.2 |
| 검지·중지·약지·새끼16축 native K/D | 12/1.5 |
| 엄지5축 native K/D | 8/1.25 |
| 기존 effort 상한 | 엄지4Nm, 다른 손가락20Nm 유지 |

장면 생성과 원래 준비 자세 복원이 끝난 뒤, 물리 step0의 초기화 구간에서 실제 native PD 속성을 한 번 적용한다. 이후 에피소드 reset은 같은 제어 속성을 유지하면서 준비 자세만 복원한다. 관절의 native 한계·POSITION 제어 모드·원래 힘 상한과 물리 안전 판정은 유지한다. 더 부드러운 PD와 넓은 탐색 범위 자체가 자연스러운 압현이나 음악 성공을 보증하지는 않는다.

초기 자세는035/v14 그대로이며, 비교 이미지의 엄지 B 후보는 적용하거나 고정하지 않았다. 오른손과 기존 전문 실행기는 기존 제어 계약을 사용한다. 구현은 [손가락 목표 설정](core/finger_control.py)과 [왼손 native 세션](runtime/finger_session.py), 상세 흐름은 [학습 흐름](/home/ajou/yigyu/3/docs/2026-10-26/learning_flow/README.md)을 따른다.

## 왼손의 보상 단계

같은 왼손 커맨드에 성능 기반 보상 전환이 자동 적용된다. 전곡을 처음부터 반복하면서 **손목 위치 잡기 → 새 GPU 압현 후보 → 곡 시간에 맞춘 유지·전환**으로 비중을 바꾼다. 첫 단계부터 손가락 보상은0이 아니며 손목 도달을 압현의 선행 gate로 삼지 않는다.

손목 목표는 현재035/v14 자세의 실제 손목을 기준으로 곡의 anchor 프렛 변화만큼 현재 기타 좌표계에서 이동시킨다. 기존 곡 자료의 절대 손목 오프셋은 사용하지 않는다. 손 방향은 초기 상대 방향의 약한 보조 기준이며, 도달 가능성·접촉·음향 성공을 보증하지 않는다.

최근8회 완료 에피소드에서 최소4회 기록, 안전 전곡 비율75% 이상·전체 목표의 손목 도달 평균70% 이상이면 진행도0→1을 늘린다. 1→2에는 준비/수행 구간의 새 GPU 압현 후보 달성 평균60%도 요구한다. 새 안전 전곡이 있는 PPO 업데이트당 최대0.1만 진행하며 실패는0점으로 포함하고 부분 궤적은 진급 근거에서 제외한다. 모든 기준은 최초 학습용 설정이며 수렴 검증 결과가 아니다.

단계와 최근 이력은 checkpoint에 저장한다. 비중은 수집 중 고정되며 업데이트 후 전체 GPU 환경에 동시에 적용하고, 물리 장면·곡 시계는 이어간다. 관측에 목표 오차·접촉 이력·비중을 추가해 왼손은512상태다. `left_curriculum`은 완료 episode·업데이트·`song_report.json`과 checkpoint에서 확인한다. GPU 전이 로그에는 완료 episode가 있는 행에만 그 단계 요약이 포함된다. [상세 학습 흐름](/home/ajou/yigyu/3/docs/2026-10-26/learning_flow/README.md)과 [구현·검증 기록](/home/ajou/yigyu/3/docs/2026-10-26/learning_flow/left_curriculum_v1/README.md)을 따른다.

## 전문 실험과 이전 실행 재현

2026-10-20 기준. 실험 수치·완료 여부는 [master_plan의 검증 결과](/home/ajou/yigyu/3/master_plan/09_curriculum_and_evaluation.md)와 연결된 원자료를 따른다. 루트 CURRENT_STATUS의 첫 전곡 V1 요약을 최신 실행 경로 전체의 결과로 해석하지 않는다.

| 목적 | 진입점 | 계약·범위 |
|---|---|---|
| 접촉 회복 평가·교사 수집 | `guitar_learning.tool.experiments.contact_recovery.run evaluate/collect` | 상태500·왼손33/전체39. native 원자료·240Hz 회복 기록. 새 PPO를 시작하지 않음 |
| 회복 자료 감사·내보내기 | `guitar_learning.tool.experiments.contact_recovery.dataset_v2` | 실제 회복·원 음악·안전·교사 보정이 감사된 행만 채택 |
| 왼손 정밀화 평가·PPO | `guitar_learning.tool.experiments.transition_refinement_runtime_v2.run eval/train` | 상태500·오른손0. 새 보상·탐색·시연 자료·초기 평가4회와 runtime 감사 |
| 전곡 보상 V2 | `guitar_learning.tool.experiments.song_reward_v2.train/evaluate` | 전곡67음·500상태·33+6행동·정책 준비3초·1969tick |
| 단음 양손 기준 경로 | `guitar_learning.tool.experiments.joint.train/evaluate` | 상태1132·Actor 각569·33+6행동 |
| 초기 전문가 생성·검증 | `guitar_learning.tool.experiments.local_skills` | 이전563상태 품질 경로. 이후 초기화 검증이 일부 함수를 재사용 |
| 입력 생성·검수·진단 | `guitar_learning.tool` | [도구별 명령](tool/README.md) 참조 |

실제 명령·설정·전제는 [회복](/home/ajou/yigyu/3/guitar_learning/tool/experiments/contact_recovery/README.md), [정밀화 runtime V2](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement_runtime_v2/README.md), [전곡 V2](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song_reward_v2/README.md), [양손 단음](/home/ajou/yigyu/3/guitar_learning/tool/experiments/joint/README.md) 문서를 따른다. 기존 결과는 해당 원입력 또는 명시적 이전 절차에서 재현한다. 파일 정리만으로 기존 checkpoint의 계약 불일치를 허용하지 않는다.

## 코드 구조와 공용 기반

루트의 실행 진입점은 `train.py` 하나다. 일반 학습은 아래 공용 코드로 이어지고, 전문 실험·평가·시연·입력 생성은 `tool/`에서 찾는다.

```text
guitar_learning/
├── train.py                 # 곡 단위 손별 학습 시작
├── music_task.py            # 공통 악보·목표 계약
├── historical_inputs.py     # 이전 입력의 정확한 원문 검증
├── training/                # 설정·runner·정책·PPO·수집·기록
├── gpu/                     # 기본 GPU 물리·배치 제어·관측·접촉 후보·보상
├── core/ · runtime/         # 기존 CPU 환경·접촉·안전·native 세션·reset
├── skills/ · imitation/     # 손별 정책과 재사용하는 행동·모방 기반
├── timing/ · quality/       # 시간창·준비·음악 품질 환경과 기록
├── score/ · song/           # 악보·전곡 환경·손별 보상·worker·요약
├── native/ · assets/        # 물리 구현과 모델·자세·설정
├── tool/                    # 부가 실행·전문 실험·검증 도구
├── tests/ · docs/           # 회귀 검사·세부 계약
└── archive/                 # 실행하지 않는 이전 원문
```

`training/start.py → training/gpu_runner.py → training/gpu_pool.py → gpu/`가 기본 GPU 실행을 연결한다. `song/task.py`가 전체 곡을 확인한다. 명시적인 CPU 재현은 `training/runner.py`와 `song/runtime.py`의 worker·요약 및 `song/hand_environment.py`의 손별 보상·성공을 사용한다. 전곡 환경·측정·판정은 `song/`의 공용 라이브러리로 모았으며 기본 실행은 `tool/`의 전문 실행기를 import하지 않는다.

이전 `train_parallel.py`는 `training/runner.py`로 옮겼고, 사용되지 않는 루트 `environment.py` facade는 보관했다. 전문 실행기17개는 `tool/training/`, `tool/evaluation/`, `tool/demonstration/`으로, 검증 전용 환경·rollout은 `tool/validation/`으로 모았다. 전문 패키지8개는 `tool/experiments/`에서 관리한다. [도구 안내](tool/README.md)를 따른다.

공용 환경의 구버전 접미사는 삭제 근거가 아니다. 현재 환경의 상속·호출과 checkpoint 계약에 필요한 구현은 남겼다. `song/task.py`와 `music_task.py`는 이전 checkpoint가 검증하는 경로·원문을 보존한다. 곡 단위 학습이 기본 경로가 되어 환경·측정·보상6개 모듈을 `song/`의 공용 라이브러리로 승격했고, 과거 BC 이전·평가·전문 실행기는 `tool/`에 유지한다. 검사도 이동 전후의 동작·물리·checkpoint 계약을 확인하므로 유지한다. [파일 배치와 유지 이유](docs/CODE_STRUCTURE.md)에 상세히 기록했다.

## 물리와 입력 계약

Root 고정·하체 유한 제어·105입력/97비영 범위/8원 영범위를 유지한다. 정책 행동은 왼손33+오른손6이며 왼손 과제에서는 오른손 정책 행동이0이다. 기타는 자유 강체·중력ON·스트랩OFF이고 직접 보조 힘·부착·실행 중 상태 덮어쓰기를 사용하지 않는다. 가슴 접촉 지속은 성공의 필수조건이 아니다. 물리240Hz·정책60Hz와 실제 표본 기반 음악/안전 판정을 유지한다. 기본 왼손의 손가락21축만 위의 명시적 제어 프로필을 사용하며, 나머지 제어 gain·관절 한계·힘 상한·안전 종료 기준을 유지한다. GPU 제어 solver와 접촉 후보의 차이는 위 새 GPU 계약을 따른다.

초기 자세는 기존035/v14를 기준으로 하며 현재 자산은 내부 `assets/`에서 읽는다. 준비·정착·정책 pre-roll은 경로별 설정을 따른다. 과거 정착2초 규칙을 native0초인 전곡·전환 경로에 자동 적용하지 않는다. 자세 연구의 새 후보도 학습에 자동 적용되지 않는다.

`assets/native_provenance.json`은 원본과 현재 SHA를 구분한다. `historical_inputs.py`와 실행하지 않는 `assets/historical_inputs/` 원문은 기존 gate·checkpoint의 정확한 입력을 검증한다. 내부화·정리 전 원문 검증을 현재 실행 소스의 검증과 섞지 않는다. 외부 Isaac Gym, `data/song_bundles`, 기존 `docs`·`paper`의 checkpoint와 증거는 계속 필요하다.

Actor 초기값 이전과 strict resume를 구분한다. 새 목표·보상·탐색·자료 계약에는 명시적 이전·검증이 필요하다. 이미 성공한 초기 모델이나 교사 자료를 새 정책의 성공으로 상속하지 않는다. 정밀화 단음의90% 유지와 전곡의 원 유지 기준·strict50/100ms는 별도 계약이다.

## 실행과 검사

프로젝트 루트 `/home/ajou/yigyu/3`에서 Isaac Gym Preview4가 설치된 `rl38` 환경을 사용한다. native 진입점은 Isaac을 NumPy·Torch보다 먼저 import한다. 실제 설정과 새 출력 디렉토리를 지정하고 기존 실행 결과를 덮어쓰지 않는다.

```bash
PYTHONDONTWRITEBYTECODE=1 /home/ajou/miniconda3/envs/rl38/bin/python -B -m unittest discover -s guitar_learning/tests -t . -v
```

`settings.json`·`training_contract.json`·`inputs_before.json`은 실행 계약, `transitions.jsonl.gz`는 전이, `episodes.jsonl`은 실제 에피소드 종료다. `learning_metrics.jsonl`, 최종 `report.json`, native/runtime 감사와 checkpoint를 함께 확인한다. sampled/logged/durable/committed/discarded와 완주·음악·안전·런타임 실패를 구분한다. 상세는 [LOGGING](docs/LOGGING.md)을 따른다.

저장 모델의 strict load는 같은 관측·행동·목표·보상·물리·PPO 계약에서만 허용한다. 접촉 후보·기하 타현·음악 성공·안전 완주·정상 실행 완료를 각각 보고한다.

## 이전 단계 문서

[TRAINING](docs/TRAINING.md), [SPECIALIST_TRAINING](docs/SPECIALIST_TRAINING.md), [SKILL_CURRICULUM](docs/SKILL_CURRICULUM.md), [IMITATION_TRAINING](docs/IMITATION_TRAINING.md), [TIMING_TRAINING](docs/TIMING_TRAINING.md), [ACTIONABLE_PREPARATION](docs/ACTIONABLE_PREPARATION.md), [MUSICAL_QUALITY](docs/MUSICAL_QUALITY.md)는 단계별 계약·구현 근거다. 그 안의 과거 실행 설정이나 성공을 최신 과제에 자동 상속하지 않는다. [CODE_LINEAGE](docs/CODE_LINEAGE.md)는 원구현의 역사적 대응을 설명한다.

구형 프로젝트 여섯 디렉토리는 [legacy 보관소](/home/ajou/yigyu/3/archive/legacy_guitar_20261019/README.md)에 있다. 구조 정리 전 소스는 [20261019_before_structure_cleanup](archive/20261019_before_structure_cleanup/manifest.json)에 보존했다.

2026-10-19 구조 정리의 도구 이전·보관 범위·동등성 검증은 [정리 결과](/home/ajou/yigyu/3/docs/2026-10-19/guitar_learning_structure_cleanup_v1/README.md)에 기록했다.

2026-10-20 역할별 파일 이동표·경로 검증은 [재배치 기록](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_role_layout_v1/README.md)에 기록했다.

새 기본 손별 실행의 단기 학습·저장·재개 확인은 [실행 결과](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_simple_start_v1/README.md)에 기록한다.

2026-10-20 메인·도구 재정리의 전체 파일 검토·이동표·검증 범위는 [정리 결과](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_main_tools_v1/README.md)에 기록한다.

현재 곡 단위 기본 실행의 변경·검증 범위는 [전곡 시작 결과](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_song_start_v1/README.md)를 따른다.
