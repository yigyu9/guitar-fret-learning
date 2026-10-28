# 곡 단위 학습의 공용 코드

현행 기본 실행은 [루트 안내](../README.md)의 `python -m guitar_learning.train --out NEW`이며 GPU 왼손 finger-skill v3(J 전용)·557상태·J33 공동 학습·K1을 사용한다. 기본 곡의67음을 합의한035/v14 준비 자세에서 새 정책으로 학습하며 BC·전문가 모델·과거 성공 평가를 요구하지 않는다. 이 디렉토리는 기본 GPU와 별도 CPU·오른손 song 경로가 공유하는 라이브러리다. 기본 구현24개·초기화8개, 활성 Python281개를 유지한다.

별도 CPU·오른손 song은 `python -m guitar_learning.tool.training.train_legacy --hand left/right --song SONG_ID --out NEW`다. 아래500/512상태·song 보고서 설명은 이 별도 경로를 뜻하며, 기본 GPU의 모델·로그는 `--out/J/`와 [로그 안내](../docs/LOGGING.md)를 따른다.

| 파일 | 역할 |
| --- | --- |
| `task.py` | 전체 곡의 원음표·시간축·검수 입력·목표 계약 |
| `measurement.py` | 실제240Hz 접촉·연속 타현 측정 |
| `metrics.py` | 음별 유지·타현·협응·안전 판정과500상태 이력 |
| `quality.py` | 실제 발음 구간의 오압현 비용 |
| `progress.py` | 오른손 목표 접근의 potential 차이 보상 |
| `environment.py` | 단일 native 장면에서 전곡 시계·원장·물리 진행 |
| `reward_environment.py` | 전곡 품질·진행 보상을 적용한 환경 |
| `hand_environment.py` | 선택한 손의 보상·전곡 성공·비활성 손0행동 계약 |
| `curriculum.py` | 별도 CPU/GPU song의 단계 가중치·설정·저장 상태 |
| `task.py`의 손목 안내 | 준비 손목·기타 프렛 기준의 목표·자세 측정 |
| `left_environment.py` | 왼손512관측·손목/접촉/시각 보상·성능 근거 |
| `curriculum_runtime.py` | 부모 단계 집계·checkpoint buffer·worker 동기화 |
| `runtime.py` | spawn worker·간결한 전이 기록·`song_report.json` 요약 |

native 대기0초, 정책 준비3초+원오디오+말미0.5초를 사용한다. 기본 곡은1969tick·32.8167초이며 첫 tick부터 정책이 행동한다. 짧은 수집 길이로 PPO를 갱신해도 장면·곡 시계·음별 원장을 유지하고 곡 종료/물리 실패 때만 초기 자세를 복원한다. 손별 전곡 성공과 양손 협응·strict50/100ms 음악 판정은 별도로 기록한다.

환경·측정·판정·보상6개 모듈은 과거 `tool/experiments/song/`·`song_reward_v2/`에서 공용 코드로 승격했다. 기존 BC 이전·양손 전문 학습·평가는 [보관한 전문 전곡 V1](../archive/20261028_before_legacy_retirement_v1/guitar_learning/tool/experiments/song/README.md)과 [보관한 전곡 보상 V2](../archive/20261028_before_legacy_retirement_v1/guitar_learning/tool/experiments/song_reward_v2/README.md)에 원문으로 보존했다. 과거 gate·Actor 이전 계약은 역사 기록이며 현행 기본의 선행조건이 아니다. [보관 범위와 원문 SHA](../archive/20261028_before_legacy_retirement_v1/ARCHIVE_INDEX.md)를 참조한다.

이전 checkpoint가 검증한 `task.py`, `__init__.py`, 상위 `music_task.py`의 원문은 추가 통합 archive에 보존했다. 현재 목표 자료형·일정·손목 안내는 `task.py`에 통합했으며 과거 입력 SHA를 현재 소스로 다시 쓰지 않는다. 기존563 단음 모델의 strict resume를 새500 전곡 계약에 허용하지 않는다. [이번 변경 기록](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_song_start_v1/README.md)을 따른다.

별도 CPU 왼손 song은512상태이며 최근 완료 에피소드의 도달·clean 접촉 성능으로 보상 비중을 점진 변경한다. 전곡 성공은 원 시간축의 clean 유지 판정을 유지한다. 현행 GPU 기본557상태·9개 보상은 [학습 흐름](/home/ajou/yigyu/3/docs/2026-10-26/learning_flow/README.md)을 따른다.

별도 CPU 왼손의 `finger_control` 설정은 [core/control.py](../core/control.py)의 고정 프로필을 사용한다. LH21만 전체 native 관절 범위·목표 변화율4rad/s·평활화0.45를 적용하고, 실제 native K/D는 검지~새끼12/1.5·엄지8/1.25다. [runtime/finger_session.py](../runtime/finger_session.py)는 원래035/v14 복원 후 물리 step0에서 해당 PD를 한 번 적용하고, 이후 reset은 같은 속성으로 준비 자세를 복원한다. 원래 POSITION 모드·엄지4Nm/다른 손가락20Nm 상한·다른 축·안전 판정은 유지한다. 비교 이미지의 엄지 B 자세는 적용하거나 고정하지 않았다.

관측은512로 같아도 제어 계약이 달라 프로필 적용 전512 왼손 모델은 strict resume할 수 없다. 별도 오른손500은 기존 계약을 유지한다. 프로필 자체를 자연스러운 압현·음악 성공의 근거로 사용하지 않는다.
