# Index proximal pair isolation — CPU 준비

현재 wrist candidate v3의 검지 row1 finite reference를 두 **새 장면**에서 비교하는 진단이다. 원래 허용된 손가락 충돌을 생산 기본값에서 제거하는 변경이 아니다. `baseline`은 원 hand-collision 90쌍, `refilter`는 index1/middle1 단일 shape 쌍만 제외한 89쌍이다. 조건마다 4환경 첫 시도 1개씩이며 실패도 전체 분모에 남는다. NN·trainer·checkpoint 생성/이전/학습은 없다.

현재는 CPU 준비이며 GPU/native 실행은 하지 않았다. 실행 순서는 root가 다른 GPU 작업 종료 후 직렬로 인계한다. 별도 사용자 재승인을 뜻하지 않는다. 실행 전 독립 code/preparation 검수가 필요하다.

```bash
CUDA_VISIBLE_DEVICES='' /home/ajou/miniconda3/envs/rl38/bin/python -B docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/index_proximal_pair_isolation_v1/probe.py --self-test
CUDA_VISIBLE_DEVICES='' /home/ajou/miniconda3/envs/rl38/bin/python -B docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/index_proximal_pair_isolation_v1/probe.py --prepare
/home/ajou/miniconda3/envs/rl38/bin/python -B docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/index_proximal_pair_isolation_v1/probe.py --dry-plan
```

CPU 준비는 새 `cpu_inputs/`, `cpu_verification.json`, `preparation_seal.json`만 만든다. 기존 경로가 있으면 덮어쓰지 않는다. 검수 완료 기록 후 root가 `preparation_seal.json`의 `independent_review`를 `passed_no_findings`로 최종화한다. 실행 시 이 최종 seal 자체도 source pin에 포함한다. root 소유 PLAN은 실행에서 읽지 않는 상위 계획이며 입력 pin에 포함하지 않는다.

root 전용 실행(프로젝트 루트, Isaac Gym 경로/라이브러리 환경은 기존 native 실행과 동일):

```bash
/home/ajou/miniconda3/envs/rl38/bin/python -B docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/index_proximal_pair_isolation_v1/probe.py --execute --condition baseline
/home/ajou/miniconda3/envs/rl38/bin/python -B docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/index_proximal_pair_isolation_v1/probe.py --execute --condition refilter
```

출력은 각각 `runs/baseline`, `runs/refilter`다. 기존 출력·dangling symlink·symlink 상위 경로를 native import보다 먼저 거절하고, exclusive mkdir의 dev/inode를 후처리 때 확인한다. 두 조건은 같은 seed7/settings/index teacher/reference, 2초 ramp·3초 onset·원 음길이/tail·PD/범위/4rad/s·035 엄지·비선택 B·wrist v3를 사용한다.

진단 wrapper는 **hand_collision 모듈의 함수**를 `ShortPool` constructor 동안만 교체한다. 원 함수가 검증한 baseline 반환값을 복사하고 미사용 bit25를 `LH:index1`, `LH:middle1`의 단일 shape에만 OR한다. `finally`에서 원 함수를 복원한다. 원 `GpuScene`의 native setter/readback, actual external-filter assert와 `prepare_sim` 순서를 재사용하며 late GPU refilter를 하지 않는다. CPU에서 55 shape/1485쌍 중 정확히 1쌍만 바뀌고 나머지1484·external `[0,4096]`·모든 비filter 속성이 보존됨을 검사한다.

`collision_condition.json`에는 원90 contract, 제출 contract, 두 전체 pair matrix와 SHA, 전후 mask, wrapper 범위를 남긴다. refilter contract의 `preserved_other_human_shape_pairs=1396`은 **원 준비 mask와 비교**한 보존 쌍 수다(원 준비에서는 해당 한 쌍도 제외됨). baseline과 비교한 보존은 별도1484다. 원90 contract/matrix SHA를 새89 조건의 것처럼 쓰지 않는다. native 장면의 실제 4환경 shape readback도 원 코드에서 확인하며, 실행 report에 constructor 호출 1회와 close/source 검증을 남긴다.

평가는 원 `runner._evaluate`/`compact_episode`/summary/ledger를 그대로 사용한다. 원 reference branch가 전체 action을 다시 계산하기 전 필요한 shape의 zero tensor만 공급하는 stateless placeholder를 둔다. 이는 NN이 아니며 임의 명령·RNG draw를 추가하지 않는다. 목표나 실제 q를 덮어쓰지 않는다. 첫 시도 quota·실패 끝점·종료·기존 predicate/reward 및 원 reset 경로도 유지한다. 학습 결과나 과거 baseline 재현을 보장하지 않는다.

원 env0 trace는 60Hz 첫 시도이며 q/target/body pose, executed action, candidate/wrong, nearest geometry, body-force 벡터, wrist 목표/실제 오차/요청/후보 필드를 보존한다. `pair_forces_env0.npz`에는 이름으로 찾은 index1/2/3 및 middle1 네 body의 같은 시각 벡터와 resultant만 파생 저장한다. 원 trace에는 다른 body 힘도 있으나 **env0/60Hz 끝점**이며 240Hz 최대·다른 환경 하중·접촉쌍 압력으로 확대하지 않는다. 실패 endpoint는 raw에 포함하되 이후 분석에서 성공/무실패 통계와 구분해야 한다.

실패 시 원 예외를 전파하고 새 출력에 원인·close 오류·핀 검사 결과를 보존한다. CPU 검사는 선택4 codec/한도/스케줄과 필터 불변성·출력 보호를 확인한다. native 물리 적합성, 실제 성과/하중 변화 및 한 쌍의 실제 접촉 여부는 CPU 준비로 인증하지 않는다. 좋아져도 생산 필터 변경을 자동 채택하지 않는다.
