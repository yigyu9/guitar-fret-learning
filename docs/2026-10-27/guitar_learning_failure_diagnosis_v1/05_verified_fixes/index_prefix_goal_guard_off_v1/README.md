# Frozen GoalPolicy DIP 보호 off 진단

원70e 모델을 원full strict loader로 읽고, 기존 후보std4·seed7·deterministic/stochastic·GoalPool 변환1회·128첫시도 평가를 재사용한다. 모델·metadata·계약·checkpoint bytes는 변경하지 않는다. 별도 실행sidecar에 **DIP 추가양증분 보호만off**를 선언하며 원contract의 guard-on 문구를 바꾸지 않는다.

`probe.py`는 검수된 precheck의 launch/adapter/finish를 재사용하고 원 `target_filter(..., guard=False)`로 위임한다. 새controller/collector는 없다. 원 `blocked`와 새 `actual_blocked`는 실제False, `would_block`는 같은 precontrol 후보·원목표의 `eligible & (raw>old)`이다. 다른104열·음/0증분·native범위·4rad/s·0.25Nm·90쌍·손목·9보상·종료는 유지한다.

CPU검사는 고정snapshot의 on/off 한열차이·memory alias/rate/bounds·scope복원·실행전gate·첫오류보존에 한정한다. 모델/std/mode/RNG/실제before-after callback의 기존검수SHA를 재사용하며 GPU/fullCUDA/물리효과를 CPU성공이라 부르지 않는다.

- `--self-test`: 선행actual PASS 없이 실행가능한 CPU delta fixture만.
- `--prepare`: 선행precheck actual review PASS와 원2117입력 검증 후 준비봉인. 독립review 전native거부.
- `--execute deterministic` / `--execute stochastic`: root만 실행. 신규 `runs/<mode>`, 기존출력·symlink거부.
- `execution_override.json`: 원std/mode/RNG/model 감사. `guard_execution_override.json`: 추가off개입·actual blocked0·would-block·첫시도scope. 원guard-on 계약을off로 위장하지 않는다.
- `current_goal_DIP60.npz`: 원전128 first-attempt mask/실패endpoint/retry제외에 bool2열을 추가한다. env0상세trace·bounded4관측은 원형식이다.

기존on 두조건은 재실행하지 않는다. closed-loop 실행개입으로 후속관측/NN행동이 변할 수 있으며 동일행동의 물리대조가 아니다. 기본보호삭제·PPO·자연스러움·압력안전성을 증명하지 않는다. 별도analysis는 runtime입력에 포함하지 않는다.
