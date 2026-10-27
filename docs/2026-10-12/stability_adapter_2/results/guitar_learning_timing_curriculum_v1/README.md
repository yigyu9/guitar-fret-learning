# 사전 준비·완화 타이밍 단계 구현과 실제 검증

가슴 접촉의 지속을 필수 성공조건으로 요구하지 않고, 기타의 기존 이탈·회전·접지 안전을 유지하면서 손별 음악 타이밍을 학습하는 경로를 구현했다. native 정착2초 뒤 정책이 행동할 수 있는 pre-roll1초를 추가했고, 시간창을 ±1.5초에서 ±50ms로 단계별 축소할 수 있다. 전체 정책 구간은5초다.

**새 관측으로 초기화한 정책은 양손 각각2/2 안전하게 성공했고, 손별 PPO1업데이트·300전이 후 저장 모델 재평가도 각각2/2 성공했다.** 이번은 첫 완화 단계(stage0)의 구현·연결 검증이다. 장기 수렴이나 모든 단계의 학습 완료, 양손 동시 연주·음향 성공을 뜻하지 않는다.

## 현행 코드와 실행

- [구현·시계·단계·실행법](/home/ajou/yigyu/3/guitar_learning/TIMING_TRAINING.md)
- [계획·진행·실패 보존](/home/ajou/yigyu/3/docs/plans/guitar_learning_timing_curriculum_20261018.md)
- 학습: `python -m guitar_learning.train_timing_v2 --settings /절대/설정.json --out /절대/새출력`
- 평가: `python -m guitar_learning.evaluate_timing --run /절대/학습출력 --out /절대/새평가 --episodes 2`
- 시작 설정: [왼손](/home/ajou/yigyu/3/guitar_learning/configs/left_timing_stage0_v1.json) · [오른손](/home/ajou/yigyu/3/guitar_learning/configs/right_timing_stage0_v1.json)

기본 설정은 검증된 새536차원 BC초기화를 참조하며 손별N2/H300/24업데이트 상한이다. 실제 이번 스모크는 `left/right_smoke_settings_v2.json`의N1/H300/1업데이트다. 이 둘을 장기 학습 결과로 혼동하지 않는다. 시간창은 한 실행 동안 고정한다. 반복 평가를 확인한 뒤 stage_index를 바꾼 새 설정·새 출력으로 Actor만 이전한다. 자동 승격·자동 결합은 하지 않는다.

## 구현 내용

`timing_curriculum.py`는 창경계·실제 후보 연속유지·중복 통과·성공1회·중심 시각 정밀도 보상·미스·안전 무효화를 관리한다. 단계별 시간창은1.5/.5/.2/.1/.05초다. 왼손0~3단계는 확장된press/end 구간에서 음 길이의20/40/60/80%(최소50ms,음 길이 이하)를 연속 유지하고, 마지막 단계는 원onset~end 전체가 유효해야 한다. 실제 지정 손가락·현·프렛·기하 통과의 물리 판정은 완화하지 않았다.

`timing_environment.py`는 정책시간u>=0과 곡시각t=u−1을 구분한다. 실행 목표에만 동일1초를 더하고 원목표·source시각·provenance를 보존한다. 준비 중에도 실제 정책 행동과240Hz 안전 검사가 작동한다. 원래50/100ms joint music ledger는 같은 상대 시각의 원판정을 그대로 기록한다.

기존505개 관측의 순서·정규화(time4/count960)를 보존하고 타이밍 이력31개를 추가해536차원으로 만들었다. 역할별39출력·기존제어범위·물성·Root고정/하체유한·105/97/8·기타자유/중력ON/strapOFF는 그대로다. 가슴·삼중 접촉은 진단으로 기록하고 그 비율만으로 실패나 단계 진행 금지를 만들지 않았다.

`timing_transfer.py`는BC/PPO활성Actor/std만 명시적으로 이전한다. 505→536 첫입력행렬은31개의0열을 추가하며 다른 활성 가중치는 유지한다. Critic·optimizer·counter는 새로 만든다. 새로운 준비/시간/목표offset/이력 외의 행동·안전·관측 변경을 거부하고, 같은 실행의 strict resume 검사는 완화하지 않는다.

새 시간 입력에 기존 모델을 그대로 넣어 성공을 가정하지 않는다. `timing_demonstration.py`는 원240행 교사 행동을 그대로 재생하고 마지막 행동을60행 유지해 실제300×536자료를 수집한다. 안전 완주와 해당 단계 성공을 확인한 자료로만300행 전체batch BC를 수행한다. Critic/반대손/std 불변을 검사하고 별도 BC형식으로 저장한다.

## 실제 검증

| 항목 | 왼손 | 오른손 |
| --- | --- | --- |
| 새 교사 native 재생 | 300tick·성공 | 300tick·성공 |
| BC fit | 2000step·MSE1.49315e−5 | 2000step·MSE2.64786e−5 |
| BC 수치tolerance1e−6 | 미달 | 미달 |
| 새BC 정책 실제 평가 | 안전5초2/2 | 안전5초2/2 |
| PPO 실제 업데이트 / 전이 | 1 / 300 | 1 / 300 |
| PPO 탐색episode 기술성공 | 1/1 | 1/1 |
| PPO후 결정적 평가 | 안전5초2/2 | 안전5초2/2 |
| 최종 LH 원음 구간 접촉후보 coverage | 두 회100% | 해당 없음 |
| 최종 RH 최소목표방향 시간오차 | 해당 없음 | 두 회약17.42ms |
| 원래joint music50/100ms매칭 | 0/0 | 0/0 |

BCfit 수치목표는 미달했지만 실제 정책의 반복 성공을 별도로 확인했다. PPO 초기actor_lr1e−5/std.02/cost_weight1을 사용했고, KL보호가 재시도2/1회 후 실효lr6.25e−7/2.5e−6으로 낮췄다. 수용KL은.01154/.01419이며 거절 시도 포함 최대1.09885/.07279와 구분한다.

이번 단일 손의 시간 정확도가 원joint music 매칭은 아니다. 원매칭은 압현과 타현 조건을 함께 요구하고, 두 손은 아직 별도 실행이다. 접촉 후보는 현 압력이 아니고 기하 통과는 실제 소리가 아니다. stage0에서 좋은 오차가 나온 사실도 stage1~4의 학습·검증 완료로 확대하지 않는다.

[실제 원자료·시계·접촉·통과·안전 집계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_curriculum_v1/runtime_analysis_v1.md) · [독립 구현 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_curriculum_v1/review_implementation_v1.md). 전체 회귀의 정본은 `cpu_tests_v3.log`: **238개 통과**다.

## 모델과 로그 위치

| 용도 | 왼손 | 오른손 |
| --- | --- | --- |
| 권장 초기화 | [새BC모델](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_curriculum_v1/left_bc_v1/actor_initialization.pt) | [새BC모델](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_curriculum_v1/right_bc_v1/actor_initialization.pt) |
| PPO연결 검증 최종모델 | [스모크모델](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_curriculum_v1/left_ppo_smoke_v2/final.pt) | [스모크모델](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_curriculum_v1/right_ppo_smoke_v2/final.pt) |

각 모델은 현재단계·동일준비·첫단음의 검증 후보이며 최적 모델 선정은 하지 않았다. 실제평가는 left/right_bc_eval_v1과 left/right_ppo_eval_v1, 새교사는 left/right_demonstration_v1에 있다. 학습은 initial/final/checkpoint·update·timing_report·transitions·status/events/resources·원제어 audit/lifecycle을 보존한다. 평가에는 관측/행동과 매tick4개 native/음악/안전 측정·두시계·stage와원음악의 별도 결과를 남겼다.

## 실패와 수정 보존

1. 기존505 PPO Actor의 직접 이전에서는 LH가u.183333초에 기타80mm 변위 기준으로2회 종료됐다. 실제 최대는약94.94/95.96mm다. 초기 물리 관측은 같았으나 목표시간 token의 변화가 극단적인 팔 명령을 만들었다. 같은 원본Actor로 실제 행동이 재현됐고31개0열 자체의 영향은 없었다. [원인 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_curriculum_v1/timing_source_shift_analysis_v1.md). 이 실패를 숨기거나 안전한계로 해결하지 않고 새관측 BC로 보완했다.
2. 초기RH평가/CPU_v1 도중 optional 소스 보완이 겹쳤다. old/new두 변형과원핀SHA를보관하고원본복원, 해당실행은최종인증에서제외했다. source_interruption_v1.json에기록했고현재확정검사는동결코드의CPU_v3/새native실행이다.
3. 첫PPO_smoke_v1은freshspawn의lazy logger참조가순환해update0에서실패했다. 원실패/초기checkpoint/원runner를보존하고, train_timing_v2가원logger를먼저캡처하도록했다. 별도새interpreter재현검사와실제v2수집/업데이트로확인했다. 이실패는학습성공이나물리실패통계에넣지않는다.

작업 전106파일과 v1runner2파일을 각각 archive/20261018_before_timing_curriculum와 archive/20261018_before_timing_worker_v2에 원경로·SHA로 보관했다. 중간변형은 archive/20261018_timing_source_interruption에 있다. 기존소스와직전phase720산출물/115소스/1637소비입력 보존을 확인했다. 최종명세는 final_verification_v1.json을 정본으로 삼는다.
