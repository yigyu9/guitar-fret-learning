# 곡 단위 기본 학습 변경 독립 검수

2026-10-20. 요약 판정: **문제없음**.

- Critical: 없음.
- Warning: 없음.
- Suggestion: 없음.

## 변경 검토

변경 전459파일 보관본과 현재 Python diff를 대조했다. 공용6모듈은 import 경로만 바뀌었고 전문 경로의 기존 gate·Actor 이전·성공 계약을 완화하지 않았다. `song/task.py`, `music_task.py`, `song/__init__.py` 원문과 경로를 보존했다.

- [training/start.py:21](/home/ajou/yigyu/3/guitar_learning/training/start.py:21): 안전한 등록곡 식별자와 전체 곡 입력을 확인하고, 원곡 길이에서 기본 수집 tick 수를 정한다. [training/runner.py:112](/home/ajou/yigyu/3/guitar_learning/training/runner.py:112)는 선택한 bundle을 실제 worker와 입력 pin에 함께 사용한다.
- [song/hand_environment.py:41](/home/ajou/yigyu/3/guitar_learning/song/hand_environment.py:41): 선택한 손의 전체 음표 달성과 안전을 성공 조건으로 삼으며 기존 joint 진단을 별도 보존한다. [같은 파일:62](/home/ajou/yigyu/3/guitar_learning/song/hand_environment.py:62)는 비활성 손의 비영 행동을 물리 실행 전에 거부하고, 선택한 보상만 반환하며 누적·episode 보상을 함께 보정한다. 기존 실패 양성 억제와240Hz 비용 처리를 유지한다.
- [training/parallel.py:361](/home/ajou/yigyu/3/guitar_learning/training/parallel.py:361): collector의 관측·누적 episode 상태는 여러 collect 사이에 유지되며 종료/중단된 worker만 reset한다. 실제 수집 기록에서도 PPO 경계의 곡 시계가 연속이다.
- [tests/test_simple_start.py:184](/home/ajou/yigyu/3/guitar_learning/tests/test_simple_start.py:184): 실제563상태 checkpoint를 실제500상태 HandSong 계약의 strict load가 모델 변경 없이 거부한다. 신규 worker의 persistent factory와 terminal 음별 원장 보존 검사도 유지한다.

## 완료된 실제 증거 확인

요약 JSON만 읽지 않고 아래 원자료를 별도로 대조했다.

- 현재396 Python 파일 SHA가 `source_manifest_final.json`과 정확히 일치한다.
- `module_tests/`의122개 원로그 끝에 모두 `OK`가 있으며 `Ran N test/tests`를 직접 합산하면702검사다. 도움말54개 결과와 원로그 파일 수도 확인했다.
- 실제3실행의 `report.json`, `song_report.json`, 입력 pin을 확인했다. 모두 completed=true이며 소스 변화·누락 pin·원본 parity·worker 실패·금지 호출·물리 flag 오류가 없다. persistent audit도 모두 completed=true/errors=[]이다.
- `transitions.jsonl.gz`를 순차 읽어 왼손2048개·오른손1969개·재개20개 전이를 직접 계수했다. 동일 episode에서 매 tick의 시간 차이는1/60초이고 control_tick이 하나씩 증가한다. 왼손 PPO 경계512/1024/1536에서도 연속이다. 왼손은1969전이 뒤에만 다음 episode로 돌아갔다.
- 좌우 `episodes.jsonl`에 각각 valid=true인 timeline_complete episode1개가 있다. 각 episode는1969tick·32.8167초·67개 음별 원장·song.completed=true·safety_invalidated=false이다. 손별 음악 성공은 양쪽 모두0이며 학습 성능 달성을 뜻하지 않는다.
- 이전 왼손 `final.pt`와 재개 `initial.pt`를 직접 로드해 metadata를 제외한 전체 payload를 재귀 비교했다. identity·model·두 optimizer·cost weight·업데이트 수·Torch/NumPy/Python/CUDA RNG가 동일하다. 재개 final의 optimizer 업데이트는4회에서5회로 증가했다. native 장면은 새 곡 episode에서 시작한다.

검사는 **모듈마다 별도 프로세스**로 실행했다. 단일 프로세스 discover 전체 통과나 이전 JSON/float SIGFPE 원인 해결을 확인한 것은 아니다. 이 변경에서 그 문제의 해결을 주장하지 않는다.

소스 수정은 수행하지 않았다.
