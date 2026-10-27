# 새 학습 v5: 대역폭 조건·오류 보존 변경 검수

2026-10-15 change-reviewer 검수. 기존 [review_v1.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/review_v1.md)와 소비된 코드·실행 결과는 보존하고 이 기록만 새로 작성했다.

## 요약 판정

**현재 v5 핵심 구현은 문제없음. Critical 없음.** 아래에 기록한 이전 실패·감사 범위의 Warning을 보존하는 조건에서, 유한 Stage A 파일럿의 실행을 중단할 구현 결함은 발견하지 못했다. 최종 64갱신 완료 및 평가 결과는 본 검수의 판정 대상이 아니다.

검수한 현재 진입점은 [launch_v5.sh](/home/ajou/yigyu/3/stability_adapter_2/fresh_learning_v1/launch_v5.sh) → [run_v5.py](/home/ajou/yigyu/3/stability_adapter_2/fresh_learning_v1/run_v5.py) → [environment_v5.py](/home/ajou/yigyu/3/stability_adapter_2/fresh_learning_v1/environment_v5.py)다. 정책·두 Critic·PPO는 기존 새 학습 구현을 유지한다. 과거 Fret·Strike·잔차 정책 가중치는 사용하지 않는다.

## 이전 실패와 guard의 해석

- [pilot64_v3](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/pilot64_v3/report.json)는 23갱신·6067개 정상 control 후 중단했다. episode20/seed121의 physics268에서 현재 COM Jacobian과 native 속도의 최대 차이가 0.014021685m/s였다. 원래 runner는 실패 행동을 step 뒤에 기록하므로 해당 시도의 행동이 보존되지 않았다. 실제 최신 정규 저장은 checkpoint20이며, 메모리상의 완료 갱신 수23과 구분한다.
- [diagnostic_v4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/diagnostic_v4/report.json)의 저장 Jacobian·qdot·native 상태에서 65 body×8 tick의 520개 비교를 독립 재계산했다. 한 tick 전 COM Jacobian을 사용하면 해당 상태의 최대 차이는 0.001217094m/s였다. 두 실제 지지점의 current/previous 비교도 0.01m/s 이하였다. 그러나 앞선 tick에서는 현재 Jacobian이 더 정확한 경우가 많았으므로 이를 보편적인 native 시간 규약의 증명으로 해석하지 않는다.
- [pilot64_v4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/pilot64_v4/report.json)도 **23갱신·6067개 정상 control에서 중단했다. 64갱신을 완료하지 않았다.** 다음 시도가 physics268→269로 한 tick 진행한 뒤 current/previous 잔차가 각각 0.015675742/0.016331718m/s여서 양쪽 모두 기존 한도를 넘었다. 따라서 시간 정렬만으로 문제를 해결했다고 주장할 수 없다.
- v3/v4의 checkpoint20은 모델 tensor15개가 모두 정확히 같았다. 이는 그 학습 접두 구간에서 실제 제어·학습의 결과가 같다는 근거이며 이후의 안전성 증명은 아니다.

현재 v5도 동일 에피소드의 정확한 k−1 Jacobian만 검증에 쓰고, 현재 k Jacobian으로 중력·task 토크를 계산한다. 초기 step0은 이전 이력 없음과 속도0을 요구한다. 유한성·shape·속도·권한·고정 하체 검사, 0.01m/s 전신/지지점 기준과 fail-fast를 유지한다. 검증 오류를 정상 terminal이나 임의 보상으로 바꾸어 PPO에 넣지 않는다. 이 속도 잔차 기준이 접촉·적분·투영 후의 모든 상태에서 유효한지는 아직 보편적으로 검증되지 않았다.

## v5의 실제 변경과 검증

v5는 새 제어 대역폭 조건이다. 54D 행동을 기준각 주변의 제한된 raw 목표로 바꾼 다음, 관측에 이미 포함된 직전 최종 목표에서 α=0.2만큼 접근하고 기존 contract의 관절 한계·변화율 제한을 적용한다. 이는 기존 guard의 타당성을 입증하거나 Jacobian 문제를 수학적으로 수정한 변경이 아니다.

- 보간은 직전 최종 목표와 raw 목표 사이의 convex 조합이다. 별도 숨은 필터 상태를 추가하지 않으며, 나머지27개 준비 목표를 보존한다. 지속 명령은 원래 목표 범위까지 접근할 수 있다. Actor의 log probability는 선택한 원래 54D 행동에 대응하고 필터는 환경의 결정적 상태 전이이므로 기존 PPO 수집과 정합한다.
- [diagnostic_v7](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/diagnostic_v7/report.json)는 v4에서 보존한 해당 에피소드의 68개 행동 후 중립 행동을 이어간 조건, 중립 조건, 무작위 조건 두 개를 각각 **300 control/1200 physics step, 5초** 실행했다. 새 필터 때문에 기존 실패 궤적과 같은 물리 상태를 재현하는 실험은 아니다.
- 네 조건의 4800개 물리 guard 기록에서 검증 이력의 step−1 정렬과 토크 계산의 현재 step 사용을 확인했다. 최대 검증 잔차는 0.002172468m/s였고 기존 한도 이하였다. 오류·금지 API 호출이 없었다. 검수 시 입력 SHA1297개를 재대조하여 불일치0개를 확인했다. 이는 시험한 네 궤적의 결과로 한정한다.
- 실행 중인 pilot64_v5의 첫 완료 에피소드 300개 전이만 별도로 대조했다. raw54→목표 매핑과 α 보간의 재계산 오차는0이며, 기존 rate clip 후 float32 최종 목표가 저장 전이와 정확히 같았다. 나머지27개 목표와 실제 노력 제어기에 전달된 최종 목표도 정확히 일치했다. 이 접두 구간 검사를 전체 파일럿 완료로 해석하지 않는다.
- CPU 테스트10개 재실행 통과: v5 보간3개, 시간 이력·의도적으로 불일치한 속도의 fail-fast4개, 정책·GAE·체크포인트3개. 추가로 v5 Python AST와 launcher shell 문법을 확인했다. 이전 v2 행동 소유권 검사는 앞선 검수에서 통과했고 매핑 함수는 변경되지 않았다.

## 오류 기록과 복원 자료

runner는 action54·에피소드·seed·적용 전 physics step을 commands.jsonl에 먼저 쓰고 flush한다. 정상 전이가 반환된 경우에만 PPO buffer에 추가한다. 오류 시 가능한 경우 model·Adam·CPU/CUDA/NumPy/Python RNG·진단을 fault checkpoint에 보존한다. 실제 저장 성공 뒤에만 checkpoint 경로를 보고하며, 추가 저장 실패는 원래 오류와 별도로 기록한다.

이 경로는 v4의 실제 실패에서 확인했다. commands6068행/정상 transitions6067행으로 실패 행동이 분리되어 있고, 마지막 command가 오류 기록과 일치한다. fault_checkpoint0023의 updates23·optimizer/RNG 및 진단의 native 상태가 저장 최종 상태와 일치한다. 마지막 부분 진행은1 physics step, 완료 갱신에 사용되지 않은 정상 수집은179 control이며, 정규 저장20과 오류 보존23이 구분된다. 중간 물리 상태의 완전한 연속 재개를 지원한다는 뜻은 아니다.

v4의 마지막 control 진행량을 현재 scene에서 계산하면 에피소드 reset 경계에서 음수가 될 수 있는 보고 문제는 v5에서 수정했다. env.step 주위의 동일 active_scene에서 적용 전후 step을 기록하여 계산한다. 추가된 loaded_project_python_modules는 실제 남아 있는 프로젝트 Python 모듈 목록을 보완 기록하며, 엄격한 changed_inputs 검사를 생략하지 않는다.

## Warning: 과거 입력 감사의 제한

[environment_v5.py의 collect_inputs](/home/ajou/yigyu/3/stability_adapter_2/fresh_learning_v1/environment_v5.py:63)는 A의 모든 최상위 Python 파일을 보수적으로 포함한다. v5 환경 채택 이전의 diagnostic_v5와 pilot64_v4 실행 중 이 목록의 analyze_left_grip_release_cycle_v1.py가 다른 작업으로 바뀌었다. 정적 참조 검색에서 해당 모듈을 참조하는 다른 A Python 파일은 없었고, 실제 제어·정책 핵심 소스 변경은 확인되지 않았다. 그러나 이 자료의 전체 입력이 불변이라고 주장해서는 안 된다. pilot64_v4 원 보고서의 changed_inputs와 completed=false를 그대로 보존한다. 실제 Jacobian 중단과 이 보존 감사 제한은 서로 별개의 사실이다. 이 분석 파일의 변경을 되돌리거나 과거 hash를 현재 값으로 덮어쓰지 않는다.

## 주장 범위와 검수 시 SHA256

v5는 작은 손 이동 준비 과제의 유한 학습 후보다. t0 손바닥 목표의 약20mm 정착 편향, 비영 비용에 대한 실제 학습 미검증, 고정 비용 계수1, epoch 후 KL 조기중단의 한계를 유지한다. 압현·타현·음악 수행, 3mm 추종 성공, 전역 안정성·강건성을 주장하지 않는다. 최종 학습·held-out 평가·사후 입력 감사는 실행 담당자가 별도로 확정한다.

| 파일 | SHA256 |
|---|---|
| environment_v5.py | 175f92b1d6f72bff47072a2030fbf42edfe0284ee7db543e072abdc372c80ed7 |
| run_v5.py | febe2fe05d40f789ee5a03efe5a3ab21d12cb1d8ca661cdbc1cdd2b639d23728 |
| launch_v5.sh | 8413f0aa2babbee9de2bc49347da28a1cdffa29ceb39ed14b2a3b93d6f1ef81e |
