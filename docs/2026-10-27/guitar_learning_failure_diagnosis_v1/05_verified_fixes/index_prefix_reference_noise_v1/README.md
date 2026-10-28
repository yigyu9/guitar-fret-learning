# NoNN 참고 목표각 잡음 진단

원 `goal.launch('reference')`·reference 일정/encode·GoalPool convert/before-after·128첫시도 evaluator·native cap/close/pins를 재사용한다. 참고 encode 직후 선택4에만 `tanh(atanh(raw_reference)+noise)`를 적용한다. 현재 후보를 원float32 log→exp 경로로 만든 유효std4와 `Normal(zeros[128,4],std).sample()`을 사용한다. 다른35raw행동은 exact 보존한다. 원DIP 한열guard 자체의 다른104target 보존과 noise4 개입전체는 구별한다. 실제 후속관측/행동은 변할 수 있다.

NN 생성/모델 load/새checkpoint/fit/PPO0이다. 기존 gate가 provenance용으로 pin하는 checkpoint는 실행모델이 아니다. 원reference의 `model_RNG_frozen=True`는 stage 분기 진리값으로, 새sampling 감사 근거로 사용하지 않는다. `reference_noise_report.json`이 pool 생성 후 seed7·호출별RNG전진·변환1회·actualNN0·분포/스트림hash와 alias복원을 별도로 기록한다. 원metadata/계약/report를 위장 변경하지 않는다.

- 실제 정책의 active mask는17..20이다. 128×39 영벡터는 RNG0이고 실제Gaussian은128×4만 소비한다. 같은평균/latent/action 또는 원NN에 미저장된epsilon 실현과의 bitexact동일성을 주장하지 않는다.
- 원raw reference354×4에서 `abs(raw)>=1`은0이다. 실행도 매번 `abs(raw)<1`을 검증하며 atanh clamp로 label을 바꾸지 않는다. sigma0 CPU왕복 최대잔차는 결과에 기록한다.
- 정상일정354호출, 원조기완료/실패/reset/firstmask는 유지한다. 통계용 firstmask로128×4 draw를 압축하거나 reset시 재seed하지 않는다.
- `reference_noise4.npz`는 env0..3 첫시도의 원raw reference/scaled noise/`epsilon_standardized=noise/std`/noisy raw goal과 시작시계만 저장한다. 표준화값에는 반올림이 포함되며 primitive epsilon을 추가draw하지 않는다. 전체128은 스트림hash/집계만 남긴다.
- 원 `observations4.npz`·`goal_codec_env0.npz`·trace·current-goal guard·9항 원장 형식을 유지한다. 이 실행의 `requested_reference_action`은 noisy reference가 변환된 physical 요청이다. 비교baseline 원reference128은 재실행하지 않는다.

단일 명령은 `cpu_inputs/commands.json`의 `noisy_reference`; 새출력은 `runs/noisy_reference`다. root만 native실행하며 기존출력·symlink는 거부한다. CPU준비는 noNN 수학/원callback/scope/error 경계만 검증하고 실제물리·128성과를 보장하지 않는다. 준비 이후 source/PLAN은 동결, 진행문서/후속analysis는 runtime핀에 넣지 않는다. 기본설정 채택이나 NN단독원인의 증명이 아니다.
