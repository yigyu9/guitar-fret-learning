# POSITION 어깨 목표 pulse 사전 검수

요약 판정: 문제없음 — 사전 검수 PASS. Critical 없음 / 미해소 Warning 없음 / 미해소 Suggestion 없음. 실제 native 실행과 조건 간 초기 상태·반응 비교는 아직 이 판정에 포함하지 않는다.

- `run_shoulder_position_goal_probe.py:27–31,70–80`: 기존 81항 POSITION PD와 초기 절대 목표를 사용한다. OFF 또는 오른쪽 어깨 한 축에만 float32 +0.02rad 목표를 첫 4 physics steps 동안 제출하고, step 4 상태를 기록한 뒤 baseline 목표로 복원한다. 나머지 목표·gain 변경과 runtime actual-state write는 없다.
- `:32–35,44–50,62–69`: 센서 활성화·mass matrix 조회·목표 setter의 native 상태 보존, target getter exact, native 범위를 확인한다. Mass matrix는 제어에 쓰지 않는다. DOF force는 step 이후 total 값이며 drive 전용 토크나 구동 원인으로 해석하지 않는다. 센서는 t0 값으로 0을 꾸미지 않고 None을 기록한다.
- `:52–61,71–88`: target/force getter는 복사한 81요소·finite 벡터를 검사한다. 물리 상태 finite/속도 제한, root/하체 구조 상태, 최종 PD 보존 및 native 카메라 상태 보존을 검사한다. 1,200steps/151frames 설계이며 step1–4에 추가 raw 표본이 있다.
- `shoulder_position_goal_preserved_run.py:40–70`: 입력 SHA와 source_before를 native runner import 전에 저장하고 종료 후 재검사한다. argv는 finally 복구하며 외부 실패는 task_error로 기록한다. 기존 Underneck no-strap 환경·고정 하체·자유 기타를 재사용하며 actor/music clock은 시작하지 않는다.
- 해소된 Warning 2건: `run_shoulder_position_goal_probe.py:52–66` getter layout/finite 검사를 추가했고, `:92–107`에서 states/commands를 먼저 저장한 후 close/encode 예외를 cleanup_failures로 보존하여 report에 실패를 반영한다. 수정 전 소스는 `source_before_pre_review_fix/run_shoulder_position_goal_probe.py`에 보존됐다.

읽기 전용 소스·재사용 helper 검토 및 두 신규 Python 파일의 AST Python3.8 문법 검사를 완료했다. Gym import/native 초기화/physics 실행은 하지 않았다. 단순 축 교환·정확한 virtual inertia·연주 성공은 인증하지 않는다. 파일 저장 자체가 실패하는 상황의 완전한 원자료 보존은 보장 범위가 아니다.

확인 SHA256: runner `e2932dc577a0698e7bd3a5ac3c97ac76b617acc303ebf1bb41111d95bb25abad`, wrapper `336c61faafac5c86cd03284a251f2b12a840fd895bed7edd05aff75f6a65b7cd`, 계획 `c2a717476e998cee724beabe13b06233c8573759e8dbe8bcb137fd939f983197`. 이 사전 검수는 동결한다.
