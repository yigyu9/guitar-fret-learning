# Finger16 native effort cap — CPU 준비

고정 기타·원90 손가락 collision·wrist candidate v3 조건에서 원 grid 선정 **index115/middle114**를 각각4환경 첫 시도로 다시 관찰한다. 유일한 준비 입력 변경은 검지~소지16축의 native POSITION `effort`20→0.25Nm다. **0.25Nm는 사전 공학 진단값이며 인체 정답이나 접촉력/현 압력 상한을 뜻하지 않는다.** 다른 cap/gain 탐색, reward/종료/범위/속도/codec 변경은 없다.

source/원 prepared JSON/cache/state/target105는 보존한다. 진단 subclass `_create_scene` 안에서만 `prepared_reset_v1.load_prepared_reset_contract` 모듈 함수를 교체한다. wrapper는 원 검증 loader를 먼저 호출하고 결과를 deepcopy한 뒤16 effort 필드만 바꾼다. 원 함수는 `finally`로 복원하며 controller 생성·후속 reset에서는 교체하지 않는다. 실제 상태는 원035 에피소드 경계 reset만 사용한다.

기존 `reproduction_v1.document_for/identify/acceptance`와 parent `collect`를 import해 재사용한다. 두 조건 모두 cap0.25이며 원20Nm baseline을 여기서 다시 실행하지 않는다. 독립 검수된 별도 baseline4시도의 실제 분모를 그대로 비교 기준으로 쓴다. **baseline 자료 검수 PASS와 원4/4 성능 수용 PASS는 다르며, baseline이3/4여도 그 값을4/4로 바꾸거나 기준을 낮추지 않는다.** 원 수용 조건은 달성4/4·clean≥.70·wrong≤.10·물리/손목실패0 그대로다.

현재 CPU 준비만 수행하며 GPU는 root가 직렬 인계한다. 별도 사용자 재승인을 요구하는 흐름이 아니다. 실행 전에 이 준비의 독립 검수 PASS와 아래 실제 baseline 검수 PASS가 모두 필요하다.

`finger_only_oracle_acquisition_v1/reproduction_v1/analysis/results_v1/review.json`

실행 guard는 이 review의 PASS/findings0/검수파일 SHA, 두 baseline 실제 launcher 및4첫시도 원평가/원 acceptance 기록을 확인한 뒤 native를 import한다. 미래 baseline 실제 증거는 실행 시 입력 pin에 추가한다. CPU preparation seal에는 이미 동결된 baseline 준비/원 grid 근거를 pin하며, 아직 존재하지 않는 baseline 실제 자료를 CPU에서 검증했다고 주장하지 않는다.

프로젝트 루트에서 CPU 준비:

```bash
CUDA_VISIBLE_DEVICES='' /home/ajou/miniconda3/envs/rl38/bin/python -B docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/finger_effort_limit_v1/probe.py --self-test
CUDA_VISIBLE_DEVICES='' /home/ajou/miniconda3/envs/rl38/bin/python -B docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/finger_effort_limit_v1/probe.py --prepare
/home/ajou/miniconda3/envs/rl38/bin/python -B docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/finger_effort_limit_v1/probe.py --dry-plan
```

검수 뒤 preparation seal의 status/review SHA만 최종화한다. 코드·settings·선정 target·CPU근거는 동결한다. root 전용 native 명령(Isaac Gym 경로/라이브러리 환경은 기존 실행과 동일):

```bash
/home/ajou/miniconda3/envs/rl38/bin/python -B docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/finger_effort_limit_v1/probe.py --execute --finger index
/home/ajou/miniconda3/envs/rl38/bin/python -B docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/finger_effort_limit_v1/probe.py --execute --finger middle
```

출력은 새 `runs/index`, `runs/middle`만이다. 기존 출력·dangling/symlink 상위 경로는 native import 전에 거절하고, exclusive mkdir의 dev/inode를 후처리에 확인한다. 오류/close 오류·source변경은 새 report에 남기고 원 예외를 전파한다. 원prepared loader의 strict 검증이나 checkpoint 검증을 완화하지 않는다. NN/trainer/checkpoint는 생성하지 않는다.

`native_effort_readback.json`은 다음을 기록한다.

- 원 검증 입력 SHA, 변경16 이름/native index와 전후 값, engineering scope.
- 원 scene의 동일 LH K/D profile을 적용한 baseline105 PD 배열과 실제105 native readback의 **모든 dtype field**. effort16 외 다른89축 및 K/D/driveMode/한계/속도/friction/armature 등이 exact 같아야 한다.
- 원 scene constructor가 매 환경 전체 property를 native getter로 exact assert한 근거와4환경/90collision 확인. 저장된 전체 배열은 마지막 환경 readback이며, 다른3환경도 원 assert를 통과해야 한다.

training contract는 기존 baseline 계약과 먼저 exact 비교한 뒤 `native_backend.diagnostic_native_effort`에 이 변경을 명시한다. 원 source SHA를 고쳐서 다른 effort를 원래 값으로 가장하지 않는다. native drive cap·controller cap tensor도 실제 readback과 같아야 한다.

기존 env0 first-attempt60Hz trace의 q/target/body pose·각 body force·geometry/gate·손목 request/candidate/goal을 보존한다. 같은 post-step 시각의 선택4 `selected_native_qd`만 추가 관찰한다. 이는 native velocity 좌표이며 특히 MCP2축에서 qpos 시간차분과 같다고 가정하지 않는다. 원 `step` 반환/제어/보상/RNG를 바꾸지 않으며 첫 시도 종료 뒤 관찰을 중단한다. 실제8시도 원장/통계·acceptance는 원 함수 그대로다.

body resultant는 contact-pair 압력이나240Hz 최대가 아니고, DOF total force sensor도 motor/constraint를 구분하지 못하면 cap 준수의 motor torque 실측 증거가 아니다. 이 도구는 sensor torque를 그런 증거로 사용하지 않는다. 하중만 낮고 도달을 잃으면 생산 채택 근거가 되지 않으며, 실제 결과·자세/힘 검수와 별도 자유기타 회귀가 남는다.
