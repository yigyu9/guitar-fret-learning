# 학습 보조·전문 실험 도구

기본 GPU 왼손 finger-skill v2 학습은 [기본 실행](../README.md)의 `python -m guitar_learning.train`을 사용한다. 여기는 입력 생성·검수·시각화와 전문 학습·평가·시연을 위한 실행 코드다. 기본 실행은 이 디렉토리를 import하지 않는다. 전문 경로는 내부에서 공용 라이브러리와 다른 전문 경로를 재사용할 수 있다. `archive/`는 실행하지 않는다.

| 위치 | 역할 |
| --- | --- |
| 이 디렉토리의 기존 도구 | 곡 등록·압현/타현 입력·계획 생성·감사·로그 복구·렌더 |
| `training/` | 구형 song·CPU/오른손·v24 실행과 기존 단계별 학습·설정 |
| `evaluation/` | finger-skill·모방·타이밍·준비·음악 품질 평가 |
| `demonstration/` | finger-skill 손/전신 영상·모방 자료·타이밍 시연 |
| `validation/` | 결정적 rollout과 검증용 압현 환경 |
| `experiments/` | 초기 전문가·양손 단음·전곡·전환·정밀화·접촉 회복8개 패키지 |

## 별도 보관한 학습 실행

이전 song·오른손·CPU·finger-skill-v24 실행은 `training.train_legacy`로 분리했다. 기본 `guitar_learning.train`에서는 이 family들을 선택하지 않는다.

```bash
# 기존 GPU song (오른손은 --hand right)
python -m guitar_learning.tool.training.train_legacy \
  --hand left --learning-family song --physics gpu --device cuda:0 \
  --size large --num-envs 1024 --horizon 32 --updates 100 \
  --out /home/ajou/yigyu/3/runs/legacy_song_01

# 기존 CPU song
python -m guitar_learning.tool.training.train_legacy \
  --hand left --learning-family song --physics cpu --device cpu --updates 1 \
  --out /home/ajou/yigyu/3/runs/legacy_cpu_song_01

# 기존 R/F/J 분리 학습 v24
python -m guitar_learning.tool.training.train_legacy \
  --hand left --learning-family finger-skill-v24 --physics gpu --device cuda:0 \
  --size large --num-envs 128 --horizon 32 --updates 100 \
  --out /home/ajou/yigyu/3/runs/legacy_finger_skill_v24_01
```

모두 새 출력 경로를 사용한다. song 전용 GPU 실행기는 `training/legacy_gpu_runner.py`에 있고, v24는 활성 공용 `guitar_learning.training.finger_skill_runner`를 사용한다. 이번 분리는 실행 위치 변경이며 이전 결과의 성능·성공·checkpoint 호환성을 새로 보장하지 않는다. 변경 전 원문은 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261026_before_finger_skill_default/manifest.json)에 있다.

현재 v2와 v24의 평가·영상은 각각 `evaluation.evaluate_finger_skill`·`demonstration.render_finger_skill`을 사용한다. [기본 안내의 실행 예시](/home/ajou/yigyu/3/guitar_learning/README.md)를 따르며, 저장된 소스 SHA와 실제 환경·정책 계약을 엄격히 확인한다. 이번 정리 이전 checkpoint는 소스 이동·수정으로 재개·평가·렌더가 거부될 수 있고, 검사를 우회하지 않는다.

## 기존 단계별 실행

아래 이름 앞에 `python -m guitar_learning.tool.`을 붙여 실행한다. 실제 입력·전제는 [단계별 문서](../docs/CODE_STRUCTURE.md)를 따른다. 기존 실행기와 설정의 위치만 바꾸었으며, 새 기본 학습에 이 경로의 사전 gate를 추가하지 않는다.

| 목적 | 모듈 |
| --- | --- |
| 준비 상태·손별 단계 | `training.train_persistent`, `training.train_skills`, `training.train_skills_v2`, `training.train_specialists` |
| 모방 학습 | `training.train_imitation`, `training.train_imitation_ppo`, `training.train_imitation_ppo_v2` |
| 타이밍 학습 | `training.train_timing`, `training.train_timing_v2` |
| 준비·음악 품질 학습 | `training.train_actionable_preparation`, `training.train_musical_quality` |
| 평가 | `evaluation.evaluate_imitation_v2`, `evaluation.evaluate_timing`, `evaluation.evaluate_actionable_preparation`, `evaluation.evaluate_musical_quality` |
| 자료 수집 | `demonstration.capture_imitation`, `demonstration.timing_demonstration` |

## 전문 실험

전문 실행기는 각 패키지 문서에 지정한 계약·초기화·자료를 요구한다. 같은 상태 차원이나 파일 이름만으로 checkpoint를 혼용하지 않는다.

| 패키지 | 역할 |
| --- | --- |
| [local_skills](experiments/local_skills/README.md) | 초기 손별 시연·전문가 생성·검증 |
| [joint](experiments/joint/README.md) | 단음 양손 정책·초기화·평가 |
| [song](experiments/song/README.md) | 기존 전곡 BC 이전·양손 정책·전문 학습·평가 |
| [song_reward_v2](experiments/song_reward_v2/README.md) | 전곡 보상 V2·이전·평가·PPO |
| [transition](experiments/transition/README.md) | 두 음 전환·접촉 교사·BC·원자료 수집 |
| [transition_refinement](experiments/transition_refinement/README.md) | 왼손 준비·유지·해제 정밀화·시연 PPO |
| [transition_refinement_runtime_v2](experiments/transition_refinement_runtime_v2/README.md) | 정밀화 JSON 계약·runtime 감사 |
| [contact_recovery](experiments/contact_recovery/README.md) | 회복 평가·교사 수집·자료 감사·내보내기 |

기본 finger-skill v2가 사용하는 공용 환경·정책·곡·원장은 활성 라이브러리로 남긴다. `song/task.py` 등 기존 checkpoint의 원문 검증 대상은 보존하며, 보관본을 import하지 않는다. 전문 도구는 각각의 제어·보상·성공 계약을 따른다.

## 곡 입력 생성

곡 번들의 등록·학습 입력 생성·검수·타임라인 렌더는 아래 명령을 사용한다. 오디오·탭·운지 추론 파이프라인은 기존 `tab2fingermapping`에 남아 있으며, JAMS에서 운지를 생성하는 fret 도구도 그 운지 모듈을 사용한다.

프로젝트 루트에서 다음 순서로 실행한다. 입력은 사람이 검수한 Stage1 결과이며, 아래 `<song_id>`를 실제 곡 이름으로 바꾼다.

```bash
python -m guitar_learning.tool.register_song_bundle <song_id> --stage1 /path/to/reviewed_stage1
python -m guitar_learning.tool.build_fret_training_data --fingering data/song_bundles/<song_id>/mapping/fingering.json --audio data/song_bundles/<song_id>/source/audio.wav --out data/song_bundles/<song_id>/training/fret_training.json
python -m guitar_learning.tool.build_strike_training_data data/song_bundles/<song_id>/mapping/fingering.json --out data/song_bundles/<song_id>/training/strike_training.json
python -m guitar_learning.tool.build_strike_plan data/song_bundles/<song_id>/training/strike_training.json --out data/song_bundles/<song_id>/training/strike_plan.json
python -m guitar_learning.tool.register_song_bundle <song_id>
python -m guitar_learning.tool.audit_strike_goal_quality --bundle data/song_bundles/<song_id> --format both
python -m guitar_learning.tool.render_timeline data/song_bundles/<song_id>/mapping/fingering.json data/song_bundles/<song_id>/preview/fingering.png data/song_bundles/<song_id>/training/strike_training.json
python -m guitar_learning.tool.register_song_bundle <song_id>
```

파일을 생성하거나 렌더를 갱신한 뒤 등록 명령을 다시 실행해 manifest의 SHA를 갱신한다. 기존에 다른 내용이 등록된 파일은 원래 규칙대로 `--replace`가 있어야 덮어쓴다. 위 곡 입력 도구는 `--help`와 `python guitar_learning/tool/<도구>.py` 직접 실행도 지원한다. 새 하위 디렉토리의 실행기는 안내된 모듈 명령을 사용한다.

| 파일 | 역할 |
| --- | --- |
| `register_song_bundle.py` | 검수한 Stage1 파일 복사, 곡 식별자·manifest·입력 SHA 기록 |
| `build_fret_training_data.py` | JAMS 또는 운지 JSON에서 압현 목표와 손 위치 목표 생성 |
| `build_strike_training_data.py` | 운지 onset을 60Hz 타현 입력으로 변환; 현 순서 1회 반전 |
| `build_strike_plan.py` | 방향·strum 그룹·전이 여유를 포함한 고정 타현 계획 생성 |
| `audit_strike_goal_quality.py` | 운지→타현→계획 일치, 전이·검수 근거 점검 |
| `render_timeline.py` | 누름·타현·strum 그룹 타임라인 PNG; matplotlib 필요 |
| `song_bundles.py` | 현행 `data/song_bundles` 경로와 곡 식별자 검증 |
| `_strike_goal_compiler.py` | 오프라인 계획 생성에 필요한 원본 stdlib compiler |
| `_strike_goals.py` | Torch 없는 원본 타현 입력 검증 부분 |

타임라인의 재준비 2프레임·follow-through 1프레임·초기 허용 오차 100ms는 원래 렌더에 사용되던 기본값이다. 필요하면 CLI로 명시한다. 이 도구의 기준은 현재 학습 환경의 물리 판정과 별개다. 기존 JSON schema 이름은 입력 호환성을 위해 유지했다.

`score/`는 현행 학습의 읽기·정본화 경로이며, 여기의 `_strike_goal_compiler.py`는 새 계획을 만드는 오프라인 도구다. 원본과 이전 경로·SHA·수정 내용은 `provenance.json`에 기록했다. 보관본은 실행 입력으로 사용하지 않는다.

검사:

```bash
python -m unittest guitar_learning.tests.test_tool_migration -v
python -m unittest guitar_learning.tests.test_tool_cleanup guitar_learning.tests.test_validation guitar_learning.tests.test_training_logging_integration -v
```

검사는 임시 곡 등록부터 현행 정본 입력 구성까지, 7곡 원본 compiler JSON 일치, 잘못된 입력 거부, 타임라인 strum 표시, 직접/모듈 실행, 과거 디렉토리·Torch·Isaac Gym 접근 차단을 확인한다. 실제 곡 번들을 수정하지 않는다.

## 진단·운영과 저장 상태 렌더

### 현행 GPU 압현 도달·접촉 진단

`validation.press_acquisition`은 현재 source 메시로 손가락별 4개씩 총16개 목표의 후보 자세를 찾고, 기존39차원 행동 경로와 실제 GPU 물리로 고정/자유 기타를 비교한다. 고정에서도 현재 단일 강체·89충돌형상 자산을 사용한다. 일반 학습의 고정 옵션이나 성공 기준 완화가 아니다.

```bash
python -m guitar_learning.tool.validation.press_acquisition geometry --out /path/to/new_geometry
python -m guitar_learning.tool.validation.press_acquisition replay --geometry /path/to/new_geometry --mode fixed --hold-s 6 --feedback joint_error_integral --out /path/to/new_fixed
python -m guitar_learning.tool.validation.press_acquisition replay --geometry /path/to/new_geometry --mode free --hold-s 6 --feedback joint_error_integral --out /path/to/new_free
python -m guitar_learning.tool.validation.press_acquisition render --source /path/to/new_free --row 0 --out /path/to/new_video
```

출력은 모두 새 디렉토리여야 한다. `--feedback none`이 기본이며 같은 준비 프레임의 유한 q 궤적을 재생한다. `joint_error_integral`은 초기 ramp 뒤 팔12축과 지정 손가락4축의 추종 오차를 최대0.1rad·gain1.5/초로 보정하는 진단 전용 모드다. 기본 학습 제어·PD를 바꾸거나 목표/DOF 상태를 직접 덮어쓰지 않는다. feedback 대조에서는 실측오차가 달라 실제 명령도 달라지므로 동일궤적 대조와 구분한다.

모든 목표의 위치·법선·하중·wrong·연속접촉·안전 요약과 입력 SHA를 저장하고, 사전 지정 row0/4/8/12만240Hz trace와60Hz 자세를 저장한다. 후보 탐색 실패는 도달 불가능의 증명이 아니며 정적50/100ms 지표는 곡의 음 달성과 다르다. 자세 재생 영상은 저장된 실제 물리 자세를 렌더하며 새 물리나 정책평가가 아니다. [실제 진단·검증 결과](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/README.md)를 따른다.

루트에 있던 다음 여섯 실행기는 이 디렉토리로 옮겼다. 이전 위치와 원문은 `../archive/20261019_before_structure_cleanup/manifest.json`에 보존한다. 새 실행은 아래 모듈 경로를 사용한다. 직접 파일 실행도 지원하며, 예전 루트 경로에는 실행기를 남기지 않는다.

| 모듈 | 역할·범위 |
| --- | --- |
| `audit_musical_quality_v2` | 저장된 단음 평가의 압현 품질·타현 준비/회복을 다시 측정. 물리 재실행·정책 평가·보상 재계산을 하지 않음 |
| `recover_training_log` | CRC로 검증한 로그 prefix를 새 디렉토리에 요약. PPO 재개·반영 여부를 추정하지 않음 |
| `run_fretting_probe_v3` | 준비 자세와 기존 손 정착 조건의 native 압현 연결 검사. 학습하지 않음 |
| `validate` | 기존 환경의 결정적 행동 probe와 엄격한 checkpoint 평가. 학습하지 않음 |
| `render_timing_video_v1` | 과거 타이밍 평가의 저장된 body pose를 60fps 영상으로 재생 |
| `render_pick_grip_v1` | 과거 준비 동작 평가의 저장된 오른손 pose·피크 위치를 시각화 |
| `_rendering.py` | 두 렌더 실행기와 `experiments/local_skills/render.py`가 공유하는 원본 초기 상태·폰트·60fps 인코딩/검증 함수 |

```bash
python -m guitar_learning.tool.audit_musical_quality_v2 --out /path/to/new_audit
python -m guitar_learning.tool.recover_training_log --run /path/to/saved_run --out /path/to/new_summary
python -m guitar_learning.tool.run_fretting_probe_v3 --config /path/to/baseline_v1.json --out /path/to/new_probe
python -m guitar_learning.tool.validate --stage B --mode zero --seconds 3 --out /path/to/new_validation
python -m guitar_learning.tool.render_timing_video_v1 --out /path/to/new_timing_video
python -m guitar_learning.tool.render_pick_grip_v1 --out /path/to/new_pick_views
```

`validate`와 압현 probe는 기존 과제 검사이며, 최신 전곡·전환·정밀화 평가를 대체하지 않는다. 렌더 도구의 입력은 코드에 명시된 과거 평가 기록이다. 렌더에는 MuJoCo·Pillow·NumPy와 해당 시스템 폰트가 필요하고, 영상에는 ffmpeg/ffprobe도 필요하다. 새 물리 step이나 정책 추론을 만들지 않으며 출력 영상은 원래 평가의 성공 범위를 확대하지 않는다. 현재 렌더 소스와 공통 helper도 새 출력의 입력 SHA에 포함한다.

전체 이동표와 검증 범위는 [메인·도구 정리 기록](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_main_tools_v1/README.md)을 따른다.

## 손가락 제어의 실제 동작 기록·재생

[demonstration/finger_motion.py](demonstration/finger_motion.py)는 정책 학습 없이 정해진4초 손가락 동작을 실제 native240Hz 물리에서 실행한다. `flexible`은 새 왼손 프로필, `legacy`는 원래 세션을 사용한다. 출력은 각각 아직 없는 새 디렉토리여야 한다.

```bash
python -m guitar_learning.tool.demonstration.finger_motion capture --profile flexible --out /home/ajou/yigyu/3/runs/finger_flexible_01
python -m guitar_learning.tool.demonstration.finger_motion capture --profile legacy --out /home/ajou/yigyu/3/runs/finger_legacy_01
python -m guitar_learning.tool.demonstration.finger_motion render --capture /home/ajou/yigyu/3/runs/finger_flexible_01 --out /home/ajou/yigyu/3/runs/finger_flexible_video_01
```

`render`는 저장된 실제 native 자세에 원본 메시를 배치해 앞·뒤 영상을 만든다. 재생 과정에서는 새 물리나 학습을 수행하지 않는다. 기록·영상은 관절 반응을 확인하는 자료이며 자연스러운 압현·힘 조절·곡 연주 성공의 증거가 아니다.
