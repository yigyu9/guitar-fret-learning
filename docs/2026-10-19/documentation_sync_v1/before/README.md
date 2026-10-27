> **현재 신규 학습 코드:** [guitar_learning](/home/ajou/yigyu/3/guitar_learning/README.md). 앞으로 환경·측정·학습 연결은 이 최상위 디렉토리에서 개발한다. 아래 기존 실행 경로와 결과는 당시 실험의 기록이다.

최신 권장 문서 쌍: [타현 결과V3](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_strike_v1/README_v3.md) · [실제 영상V3](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_strike_v1/media_index_v3.md) · [자세 경로V3](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_strike_v1/POSE_PATHS_v3.md). 표시 PNG와 native 원본 PNG의 경로를 구분한 정정이며 물리 결과는 동일하다.

권장 타현 문서: [결과V2](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_strike_v1/README_v2.md) · [실제 영상V2](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_strike_v1/media_index_v2.md) · [자세 경로V2](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_strike_v1/POSE_PATHS_v2.md). 표시영상의 실제 생성 범위를 반영한 문서 정정이며 물리 결과는 같다.

## 2026-10-16 팔꿈치·손목만의 타현 검증 완료

정면 source9에서 오른팔꿈치·손목6축만 새 타현 목표를 요청해 실제 여섯 줄 내려치기·올려치기를 통과했다. 어깨·쇄골의 요청/최종 목표는 고정했으며 실제 상대회전은 각각0.089°/0.157° 이내다. 가슴·오른상완·오른허벅지 동시 실제 접촉98.7513%, 양발 접지와 원 기타/몸통 안정성 기준을 모두 통과했다. 관절의 강도·감쇠·상한을 유지하고 말단6축 오차를 child SO3 좌표로 교정했다. Root 고정·하체16축 유한 제어·원영범위8축·기타 자유/중력ON/스트랩OFF를 유지했다.

실제 대조와 타현은 각각 준비5초+정지5초+동작4초이며 최신36개 판정과 별도 양측 준비·매체 검사를 통과했다. 현 표식의 기하 통과이며 현 힘/진동/음향은 뜻하지 않는다. 이동 중 최대 위치 오차7.051mm, 새 자세의 결합 압현·15초 왼손 해제는 남아 있다. 새 PPO는0이다. [결과와 실패 이력](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_strike_v1/README.md) · [실제 영상](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_strike_v1/media_index.md) · [자세/실행 경로](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_strike_v1/POSE_PATHS.md).

<!-- 2026-10-16 하체 자유도·기타 지지 우선 재검사 -->
최신 필수 조건은 하체 고정 해제와 가슴·오른상완·허벅지의 기타 지지다. source9의 실제 정지 원자료 재검사에서 가동16축 유한 제어와 세 부위 동시 지지100%를 확인했다. 발 정면·좌우 정렬은 선호이며 작은 전방 숙임을 허용한다. 현재 자세/gain 유지, 새 물리/PPO0. [검사 결과와 남은 범위](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/support_priority_audit_v1/README.md) · [실제 영상](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/support_priority_audit_v1/media_index.md).

<!-- 2026-10-16 정면 자세 -->
[발끝·상체 정면 자세](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_pose_v1/README_v2.md): 새source9는실제준비5초+정지5초/동일반복의모든25기준과raw4동일검증을통과했다. [초기자세/제어설정 경로](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_pose_v1/POSE_PATHS.md). 기타자유·하체유한조건이며새자세의압현/타현·해제성공은아직상속하지않는다.
새 자세의 왼손 해제는 전신FK 사전검사 미달(검지20.3155μm/0.0193876°)로 실제 미실행이다. [실패와 다음 과제](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_pose_v1/RELEASE_PREFLIGHT_FAILURE.md).

<!-- 2026-10-16 grounded_guitar_support_v1 결과 -->
**준비 5초 후 정지 5초, 압현·타현·순차 결합, 별도 왼손 완전 이탈 15초가 실제 기준을 통과했다.** 정지 2회는 각각 23개 기준과 원자료 4종 SHA exact 반복을, 연주 4조건은 각각 26개 기준을, 총 28초 해제 시험은 25개 기준을 통과했다. Root 고정·하체 유한 제어·양발 접지·기타 자유/중력ON/스트랩OFF·원래 영범위8축과 105입력을 유지했다. 전체 기타 이동 최대5.792mm, 회전1.766°, 넥고도1.009°, 좌우오차1.786mm다.

성공 절차에는 준비 5초가 필요하다. 프렛을 유지하고 결합 동작의 마지막 유한 관절 목표에서 종료하며, 해제는 별도로 초기화한 시험이다. 원초기 즉시5초의 16개 실패와 휴지 복귀 실패를 보존했다. 연주→해제 연속 수행·다른 곡·현 압력/음향은 아직 검증하지 않았고 새 PPO는0이다. [최신 결과](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/grounded_guitar_support_v1/README.md) · [실제 영상](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/grounded_guitar_support_v1/media_index.md) · [자세 경로](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/grounded_guitar_support_v1/POSE_PATHS.md) · [완료/남은 범위](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/grounded_guitar_support_v1/RESULT_CHECKLIST.md).

# Tab2Body — 전신 기타 연주 학습 시스템

## 2026-10-16 이전 단계: 낮춘 좌석과 양발 접지5초 통과, 당시 기타 안정성 미완료

좌석 높이를49.2→45.6cm로 낮추고 Root·상체·기타 초기높이를36mm 함께 내렸다. 새 유한 하체 목표로 정지5초의 양발 접촉·발바닥 높이/기울기·속도/미끄럼 기준을 통과하고 같은 설정으로 반복 확인했다. Rootfixed/하체finite/기타FREE·중력ON·strapOFF다. 기타 전체 회전·넥·가슴 지지 실패는 남으며 이 설정의 새 압현/타현·손해제15초·PPO는 실행하지 않았다.

[현재 자세·제어·상세 결과](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/seated_foot_support_v1/README.md) · [실제 영상](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/seated_foot_support_v1/media_index.md) · [완료/남은 일](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/seated_foot_support_v1/RESULT_CHECKLIST.md). 아래10월15일 연주 시험은 이전 접지 조건의 이력이다.

## 2026-10-15 이전: 교정 자세의 압현·타현 시험, 연주 중 안정성 미달

기존 교정 자세를 같은 제어로5초 재현한 뒤 정지 대조·압현·타현·결합을 각각4초 더 실행했다. 네 조건 모두9초를 완료했지만 세 동작 조건의 안정성 통과는0회다. 기타 몸통의5초 대비 최대이동/회전은 압현10.511mm/5.278°, 타현26.831mm/17.505°, 결합11.135mm/7.634°였다. 내려치기는6줄 모두 검출됐지만 올려치기는 누락이 있었으며, 가슴 실제 접촉은0이다. 압현은 실제 검지 움직임과 접촉·위치·유지 후보 판정이고 타현은 비충돌 가상 피크 통과 판정이다. 압현력·현 진동·음향 성공을 뜻하지 않는다.

Root고정·하체유한제어·기타자유/중력ON/스트랩OFF를 유지했다. 새15초 손해제/PPO는0회이며 현재 설정을 연주 안정 설정으로 채택하지 않는다. [최신 상세 결과](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_horizontal_play_v1/README_v2.md) · [실제 영상](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_horizontal_play_v1/media_index_v2.md) · [결과 계획](/home/ajou/yigyu/3/docs/plans/upright_horizontal_play_result_v2_20261015.md). 아래 교정과 이전 연구는 당시 조건의 기록이다.

## 2026-10-15 이전 교정: 기타 좌우 복원·넥 수평화, 전체 안정화 미완료

기타가 humanoid 왼쪽으로 이동하고 넥이 올라간 문제를 새 phase에서 교정했다. 초기 넥0°/원래 몸통좌우좌표를 복원했고, 최신 실제5초 종료는 넥−0.707°/원위치보다 오른쪽5.209mm다. 그러나 시작 구간 넥최대5.269°/Chest최대5.003207623°/가슴접촉0으로 이번6개 실행 모두 전체기준 실패다. 오른팔 첫 목표변화0.049969rad를2.38e−7rad로줄였지만 이를 동적성공으로 부르지 않는다. Root고정/하체finite/기타free·중력ON·strapOFF를 유지했고 새해제15초/PPO는 진행하지 않았다.

[최신 상세 결과](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_horizontal_v1/README.md) · [실제 전후 비교·영상](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_horizontal_v1/media_index.md) · [완료·미해결](/home/ajou/yigyu/3/docs/plans/upright_horizontal_result_20261015.md). 최신 진단재현은run_horizontal_v7/static_v7.json/native_static_v6이며 채택된 안정 설정이 아니다. 아래 raised 자세의 정지성공·해제실패와 원하체안정화 결과는 이전 조건의 이력으로 보존한다.

## 2026-10-15 이전 자세 연구: 직립 정지 성공·왼손 해제 미완료

Root 고정·하체 유한 제어·기타 자유 강체/중력 ON·스트랩 OFF 조건에서 허리를 세우고 기타 목을 올린 새 자세를 검증했다. 정지5초에서 Chest 좌우 기울기 최대0.973°/전체3.998°이며,1초 후 가슴과 오른쪽 위팔의 동시 실제 접촉이100%다. 왼손 해제는4.108초에 기타 이동 한계를 넘어 실패했으므로 전신 동적 안정화/최종 연주 자세로 채택하지 않는다. 새 PPO 학습은 실행하지 않았다.

[최신 상세 결과](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/README.md) · [실제 영상](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_chest_support_v1/media_index.md) · [완료/남은 작업](/home/ajou/yigyu/3/docs/plans/upright_chest_support_result_20261015.md). 정지 재현은 `lower_body_release_v1.run_upright_v16`/`static_v17.json`이며,`release_v17.json`은 실패 재현용이다. 아래의 하체 완전 고정·학습 기록은 당시 조건과 결과를 보존한 이력이다.


오디오 입력을 기타 탭·운지 데이터로 변환하고, 이를 Isaac Gym 기반의 왼손 `fret` 및 오른손
`strike` 물리 학습으로 연결하는 프로젝트입니다.

현재 자유 기타 연구는 [StabilityAdapter 2 실행 계획](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1)에 따라
`stability_adapter_2/`에서 진행한다. 목표는 기타를 사용자 허용 범위에 유지하면서 실제 압현·타현을 수행하는 것이다.
Root/하체 고정·자유 기타 환경과 Fret·Strike 개별 체크포인트 연결·종료까지 녹화를 구현했다.
양손 연주 통합과 안정화 보정 학습은 미완료다. 전체 목표·우선순위는
[전체 연구 메인 계획](/home/ajou/yigyu/3/master_plan/README.md:14), 최신 결과와 다음 작업은
[프로젝트 현재 상태](/home/ajou/yigyu/3/PROJECT_CONTEXT.md:1)를 따른다.
기존 `stability_adapter/`의 3초 WAIT 경로·계획·결과는 별도 과거 경로로 보존한다.

## 프로젝트 구조

```text
.
├── data/                  # 곡별 오디오·annotation·학습 입력
│   └── song_bundles/      # 검수된 곡 단위 입력과 목표 데이터
├── docs/                  # 설계·검증·사용 문서
├── master_plan/           # 오디오부터 최종 연주까지의 연구 기준 설계
├── stability_adapter_2/   # 현재 자유 기타 초기 배치·연주 전이·안정화 실험
├── fret/                  # 왼손 fret 학습 문서와 실행 결과 위치
├── strike/                # 오른손 strike 학습 문서와 실행 결과 위치
├── full/                  # Full G0 계약·구현 상태와 역사적 병합 prototype
├── isaacgym/              # NVIDIA Isaac Gym Preview 4 런타임
├── tab2body/              # 물리 환경·reward·PPO·평가·학습 코드
├── tab2fingermapping/     # 오디오→탭·코드·운지 Stage1 파이프라인
├── PROJECT_CONTEXT.md     # 프로젝트 전체 상태와 결정 기록
├── .gitignore
└── .gitattributes
```

| 경로 | 용도 |
|---|---|
| `data/song_bundles/` | 학습에 사용하는 곡별 입력과 목표 데이터 |
| `tab2fingermapping/` | 오디오에서 탭·코드·왼손 운지 생성 |
| `master_plan/` | 전체 연구 흐름, 모듈 책임, 공통 계약, 승급 기준 |
| `stability_adapter_2/` | 현재 자유 기타 실험의 실행 계획·구현·설정. 결과는 docs/2026-10-12/stability_adapter_2/ |
| `tab2body/` | Isaac Gym 환경, PPO 학습, checkpoint·평가 도구 |
| `fret/` | 왼손 압현 학습 문서와 결과 관리 |
| `strike/` | 오른손 타현 학습 문서와 결과 관리 |
| `full/` | Canonical PlayEvent·Synchronizer·105D named ABI(실질 가동 97D) 조립 계약과 구현 상태 |
| `docs/` | 공통 설계·검증·실행 문서 |
| `isaacgym/` | 물리 시뮬레이션 런타임 |

`tab2fingering`이라는 폴더는 없으며, 실제 폴더명은 `tab2fingermapping`입니다.
`related_work/`는 참고·보관용 디렉토리이며 현재 실행에 필수는 아닙니다. 과거 `DIGIT/` 실패 구현은
정리되어 현재 저장하지 않으며, 핵심 안티패턴은 설계 문서에 요약되어 있습니다.

## 처리 흐름

```text
오디오
  → tab2fingermapping
  → data/song_bundles/<song_id>/
  → Fret-v2 / Strike-v2 곡별 기술 prior 학습
  → Canonical PlayEvent + rule Synchronizer (G0)
  → StabilityAdapter (자유 기타 연주 전이·제한 보정 검증 중)
  → FullBodyPlayer (105D named ABI / 97D effective movable DOF)
```

현재는 Fret·Strike 독립 학습과 G0의 CPU 계약 조립까지 구현되어 있다. 한 simulator에서
두 손을 물리적으로 실행하는 FullG0Task는 아직 완료되지 않았다. StabilityAdapter 2에서는
Fret·Strike 단독 연결과 제어권 진단을 실행했지만 지속 연주 성공과 보정 학습은 아직 확인되지 않았다.

## 실행 환경

물리 학습은 CUDA GPU와 Isaac Gym Preview 4가 설치된 `rl38` conda 환경에서 실행합니다.
오디오 변환 Stage1은 별도의 `tab2fm` 환경을 사용합니다.

물리 학습 환경:

```bash
cd /path/to/yigyu/3
conda activate rl38
export PROJECT_ROOT="$PWD"
export PYTHONPATH="$PROJECT_ROOT/isaacgym/python:$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export TORCH_EXTENSIONS_DIR="/tmp/torch_extensions_tab2body"
```

Stage1 환경 설정과 ACE 관련 의존성은 [`tab2fingermapping/SETUP.md`](tab2fingermapping/SETUP.md)를
참조합니다.

## 사용 방법

### 1. 오디오에서 탭·운지 입력 생성

```bash
conda activate tab2fm
cd tab2fingermapping
python pipeline.py /path/to/audio.wav --bpm 117
```

생성 결과를 검수한 뒤 `data/song_bundles/<song_id>/`에 등록합니다.

### 2. 물리 학습 배관 확인

아래 Fret·Strike의 `--smoke`는 시뮬레이터·PPO·checkpoint·평가 저장 경로를 짧게 확인합니다.
최대 8개 환경, 1 iteration으로 실행되며 자동 영상은 생성하지 않습니다.

Fret:

```bash
conda activate rl38
cd "$PROJECT_ROOT"
python -m tab2body.train \
  --task fret --song 02_Jazz1-200-B_solo \
  --smoke --num-envs 8 --run-name fret_smoke
```

Strike:

```bash
python -m tab2body.train \
  --task strike --song 02_Jazz1-200-B_solo \
  --smoke --num-envs 8 --run-name strike_smoke
```

### 3. Fret 학습 시작

기본 설정은 1,024개 병렬 환경, 5,000 iteration입니다.

```bash
python -m tab2body.train \
  --task fret --song 02_Jazz1-200-B_solo \
  --num-envs 1024 --iterations 5000 \
  --run-name fret_s0
```

GPU 메모리가 부족하면 환경 수를 낮춥니다.

```bash
python -m tab2body.train \
  --task fret --song 02_Jazz1-200-B_solo \
  --num-envs 512 --iterations 5000 \
  --run-name fret_s0_512env
```

### 4. Strike 학습 시작

기본 설정은 512개 병렬 환경, 50,000 iteration입니다.

```bash
python -m tab2body.train \
  --task strike --song 02_Jazz1-200-B_solo \
  --num-envs 512 --iterations 50000 \
  --run-name strike_main
```

### 5. 학습 설정과 결과 위치

| 항목 | Fret | Strike |
|---|---:|---:|
| 기본 환경 수 | `1024` | `512` |
| 기본 iteration | `5000` | `50000` |
| PPO horizon | `32` | `32` |
| minibatch 크기 | `4096` | `2048` |
| PPO epoch | `5` | `5` |
| checkpoint 주기 | 500 iteration | 500 iteration |
| 자동 영상 | 1000 iteration | 단계별 paired 영상, checkpoint 간 최소 1900 iteration |

실행 결과는 `--run-name`에 따라 다음 위치에 저장됩니다.

```text
fret/training/runs/<run-name>/
├── checkpoints/fret_*.pt
├── logs/metrics.jsonl
├── logs/training.log
├── evaluations/
├── videos/
└── plots/

strike/training/runs/<run-name>/
├── checkpoints/strike_*.pt
├── logs/metrics.jsonl
├── logs/training.log
├── evaluations/
├── videos/
└── plots/
```

checkpoint는 기본적으로 500 iteration마다 저장되며, 학습 종료 시 마지막 iteration도 저장됩니다.
실행 폴더에 이미 학습 기록이 있으면 덮어쓰지 않으므로 새 실험에는 다른 `--run-name`을 사용합니다.

자동 영상이 필요하지 않으면 다음 옵션을 사용합니다.

```bash
python -m tab2body.train --task fret \
  --num-envs 1024 --iterations 500 \
  --no-auto-video --run-name fret_no_video
```

### 6. checkpoint 재개

`--checkpoint`는 모델, optimizer, iteration, global step, curriculum 상태를 복원합니다.
`--iterations`는 checkpoint 이후에 추가로 실행할 iteration 수입니다.

```bash
python -m tab2body.train \
  --task fret \
  --checkpoint fret/training/runs/fret_s0/checkpoints/fret_005000.pt \
  --num-envs 1024 --iterations 500
```

위 명령은 같은 실행 폴더에서 학습을 이어갑니다. 현재 코드와 checkpoint의 학습 계약이 다르면
안전하게 실행을 중단합니다.

정책 가중치만 가져와 새 실행을 시작하려면 Fret에서 `--initialize-from`을 사용합니다.

```bash
python -m tab2body.train \
  --task fret \
  --initialize-from fret/training/runs/fret_s0/checkpoints/fret_005000.pt \
  --num-envs 1024 --iterations 5000 \
  --run-name fret_warmstart
```

### 7. checkpoint 평가

`--eval`과 `--checkpoint`를 함께 사용합니다.

```bash
python -m tab2body.train \
  --task fret --eval \
  --checkpoint fret/training/runs/fret_s0/checkpoints/fret_005000.pt \
  --num-envs 64 --eval-episodes 64
```

평가 결과는 해당 실행 폴더의 `evaluations/`에 저장됩니다.

## 상세 문서

- [`master_plan/README.md`](master_plan/README.md): 오디오 입력부터 `FullBodyPlayer`까지의 기준 설계
- [`tab2body/TRAINING.md`](tab2body/TRAINING.md): 물리 학습·평가·checkpoint 상세 사용법
- [`fret/03_training/README.md`](fret/03_training/README.md): Fret 학습 문서
- [`strike/03_training/README.md`](strike/03_training/README.md): Strike 학습 문서
- [`tab2fingermapping/SETUP.md`](tab2fingermapping/SETUP.md): Stage1 설치와 실행 환경
- [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md): 프로젝트 전체 상태와 결정 기록
- [`docs/DOCUMENT_INDEX.md`](docs/DOCUMENT_INDEX.md): 문서 정본·실행 문서·보관소 탐색 안내

Isaac Gym, ACE, 오디오, annotation, checkpoint를 외부에 배포할 때는 각 구성요소의 라이선스와
재배포 조건을 확인해야 합니다.


## 하체 동적 유한 제어 V2 검증

2026-10-15 재개한 별도105진단에서 원모델/초기상태를 보존하고 회전오차·질량행렬 기반 하체 EFFORT와 Hip3축의.01rad 안쪽 유지목표를 사용했다. Root고정·기타자유/중력ON·strapOFF에서 정지5초/1200step과 왼손해제 전체실험15초/3600step을 완료했다. 실제 왼손 raw접촉은2.254167초가마지막이고 후속12.741667초무접촉표본을관측했다. 기타최대이동/회전은정지18.432mm/3.402°,해제18.301mm/4.532°다. 이는기존fixed-lower기본값이나학습환경의자동변경이아니며PPO는시작하지않았다. [결과·실패·영상V2](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/README_v2.md), [API/재현V2](/home/ajou/yigyu/3/stability_adapter_2/lower_body_release_v1/README_v2.md), [재개체크리스트](/home/ajou/yigyu/3/docs/plans/lower_body_release_diagnosis_20261015.md)를따른다. 원native POSITION 평형/limit좌표의정확한내부원인과재파지·타현·자유Root균형은미해결로구분한다.


## 2026-10-16 초기 자세 전체 조건 검증 재개

사용자 기준에 따라 기존source9/오른팔꿈치·손목타현 성공을 보존하고 왼손 완전해제15초·해제중반복타현·넥재접촉·연속수행을 새 front_facing_ready_v1에서 검증한다. 기존전신FK 실패는 보존하며 엄격한 손목 task chain 검증과 actualnative 손 형상/접촉 검사를 분리한다. [요구사항](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/REQUIREMENTS.md) · [실행계획](/home/ajou/yigyu/3/docs/plans/front_facing_ready_20261016.md) · [진행상태](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/WORK_STATE.md). 새물리/PPO는 아직0이며 전체성공을선언하지않는다.


## 2026-10-17 신규 학습 코드 개발 경로 분리

앞으로 신규 환경·측정·학습 연결 코드는 프로젝트 최상위 [guitar_learning](/home/ajou/yigyu/3/guitar_learning/README.md)에서 작성한다. 기존 free_guitar_learning_v1은 과거 실험 재현용으로 보존한다. 최신 환경/기하/압현·제어 규약/실행기/검사를 새 경로에 모으고 import·루트·소스 감사 경로를 조정했으며 CPU40개와 도움말 확인을 통과했다. 새 물리/PPO0. [정리 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_code_organization_v1/README.md).


## 2026-10-18 학습 준비 시간을 기본 2초로 변경

사용자 요청으로 현재 학습 진입점을 [guitar_learning.environment](/home/ajou/yigyu/3/guitar_learning/environment.py)로 정하고 준비 완료 상태를 reset 시 한 번 초기화한 뒤 2초만 손 준비·안정화한다. 과거 22초 스케줄은 반복하지 않는다. CPU59개와 실제2초+유지1초 단1회 연결 시험 통과, 유지241표본에서 삼중 지지·진단 접촉 후보 유지. 전체V3재검증/새PPO0. [결과·현재 코드](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_short_preparation_v1/README.md).
