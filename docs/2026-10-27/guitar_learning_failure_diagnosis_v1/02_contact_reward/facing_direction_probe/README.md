# Facing direction diagnostic — CPU prepared, GPU pending root handoff

사용자가 구현과 진단 진행을 이미 승인했다. 여기서 **GPU 승인/인계는 root의 내부 실행 순서 인계**를 뜻하며 사용자에게 별도 승인 질문을 하지 않는다. 현재 seed17 두 제어 모드가 GPU를 사용하므로 이 준비 작업에서는 GPU를 실행하지 않는다.

단일 원음 middle row8,8조건×2개 첫 시도=16환경이다. 조건은 env_id%8, 반복은 env_id//8이며 조건당 배정 분모2를 유지한다. 기존 checkpoint/teacher/reference와 활성 소스는 수정하지 않는다. 모든 변경은 이 docs 진단 driver의 명시된 finite trajectory이며, 기존 동일 과제 정책 성과나 학습 성공으로 보고하지 않는다.

| 조건 | finger goal | wrist 방향·위치 |
| --- | --- | --- |
| 0 | 원래 reference 중지4축 | 원래2초 teacher ramp/hold 대조 |
| 1 | 원래 reference | 동일 방향 +15mm clearance 접근 대조 |
| 2 | x/PIP/DIP는 기존 하한, spread는 reference | 동일 방향 + clearance |
| 3 | reference에서 DIP만 기존 상한 | 동일 방향 + clearance |
| 4·5 | 원래 reference | 원래 string 평면 내 축 u에 ±90° 회전 요청 + clearance |
| 6·7 | 원래 reference | 평면 내 v=n×u축에 ±90° 회전 요청 + clearance |

회전은 기타 좌표의 quaternion **왼쪽 곱**이며 실제 wrist 관절에90°를 더하지 않는다. 조건1~7은0→2초에 wrist clearance 위치/방향까지 기존 bounded feedback으로 요청하고,2→2.8초에15mm offset을0으로 줄여 접근한다. 모든 중지 goal은035에서2초 ramp다. 상태 순간 이동·새 solver·force 보조가 없다. 기존 팔3rad/s·보정0.5°/tick·범위·평활화, 손가락4rad/s·native 범위·PD·힘·충돌·실패 종료는 그대로다. 물리적으로 방향/위치/하중에 도달한다는 보장은 없다.

원래218control ticks=872physics steps=3.633333초와 press2.9787/onset3.0/end3.1174초를 보존한다. 조기 종료된 환경은 원래 pool 경계에서 reset하되 그 뒤 표본은 first-attempt mask로 제외한다. root의 GPU handoff 후에도 원래 safety 실패를 꺼서 끝까지 유효한 척 진행하지 않는다.

## 재사용과 정체성

`driver.py`는 기존 `ShortPool`, strict `DecisionPPOTrainer.load`, `ShortPolicy`, 원래 inverse codec과 `interpolated_pose`/`wrist_error_and_jacobian`/`bounded_wrist_target`을 사용한다. 실제 조작은 selected4 finite actions와 per-row wrist goal뿐이다. 팔 feedforward·다른 손가락 B·엄지·오른손 zero는 원래 ShortPool에서 처리한다. 원래 checkpoint의 architecture/control/config 모델 로드는 strict하게 유지하고 배치 수만128→16으로 명시한다. 모델/버퍼 동일과 updates0을 사후 검사한다.

`original_training_contract.json`은 원래 checkpoint identity 검증용 base contract다. **실제 새 방향·접근 조건은 별도 `diagnostic_conditions.json`이 명시적으로 덮어 쓰는 진단 입력**이며, 원래 teacher와 동일한 실행 조건이라고 가장하지 않는다. 정책 행동을 성과로 사용하거나 PPO update/save를 호출하지 않는다. 원래 소스·teacher evidence·초기 checkpoint·reference·기존 mask helper·이 driver/protocol/CPU 검사/README·precommit bytes를 모두 pin한다.

## 측정·실패·판정

240Hz callback은 원래 `environment.substep(snapshot)`의 계산과 native safety **뒤에** 실행한다. 현재 `_control_failures()`가 참이면 그 동일 표본부터 `failed`를 latch한다. 이 mask는 다음 control에서 tick flag가 초기화되어도 유지된다. 따라서 실패를 처음 감지한240Hz 표본과 모든 후속 표본을 witness에서 제외한다. native flag를 수정하거나 실제 종료를 지연시키지 않는다.

negative는 `first_attempt & ~failed & assigned distal resultant>=0.01N & any(position_mask) & ~any(facing_mask)`다. 기존 `current_contact_replay.sample_masks`를 pin/import해 same-point 위치·cosine conjunction을 노출하고 원래 environment aggregate와 일치하는지 검사한다. 별도 정상 episode flag를 기록한다. **유효 witness 뒤에 episode가 실패하더라도 실패 이전의 실제 witness를 무효화하지 않는다.** `safe_episode_witness`와 `safe_episode_stable50ms`는 완주/무실패 부분집합을 별도로 보고한다. 이 분류는 진단용이며 원래 성공·보상·실패 계산을 바꾸지 않는다.

최대 연속 구간은 eligible sample의 인접 index와 실제 clock+1을 모두 요구한다. span=(last−first)/240≥0.05초이므로13개 endpoint가 필요하다. 한 표본과50ms 증거를 분리한다. 원래 geometry를 통과한 표본이 모두 facing을 실패했지만 resultant<0.01N이면 `negative_geometry_unloaded`, position 노출이 없으면 `position_not_observed`, facing이 남으면 `same_sample_facing_remained`로 기록한다. 실제 wrist 방향 오차와2.8초 뒤 최소 오차/10° 이내 여부도 별도 기록한다.10°는 방향 추종을 설명하는 공학 표시값이며 native contact/실패 문턱이 아니다.

- `physics240.npz`: actual clock/local/source time, first/failed/physical/wrist failure masks, distal/guitar/wrist pose, distal force벡터, q4/target4·실제 arm target, 목표 wrist pose·실제 방향오차, 모든128개 원래 pad 표본의 point/normal·valid/cell/height/lateral/normal/position/facing/positive mask와 cosine. 모든 body의 force/pose trace를 추가하지 않는다.
- `control60.npz`: bounded wrist 요청·preclip 요청·clip flag·요청 변화·pose error, selected requested/executed actions, 실제 reward/cost와9항 증분/누적값. 누적 endpoint 값은 합산하지 않는다.
- `first_attempt_episodes.json`:16개 첫 시도의 원래 전체 ledger/종료/cost/9항 보상, serialized ledger에 빠진 필드도 포함한 selected raw note. 실패도 모두 보존한다.
- `report.json`, `inputs_before/after.json`, `failure.json`: 조건별 배정2분모, missing env, 모델·update·clock·finite·same-point·bounds/rate·핀·GPU scene closed 감사. 오류와 partial trace를 보존하며 기존 출력 경로는 거부한다.

net body resultant는 접촉 상대 pair·실제 현 압력·해부학적 피부 뒷면 접촉을 특정하지 못한다. 이16환경 결과로 이전 전체 몸체212N 문제를 해결했다고 주장하지 않는다. negative가 없으면 그 사실과 방향/위치/하중 도달 실패를 그대로 남긴다.

## CPU 검사와 동결 인계

```bash
PYTHONPATH="$PWD" /home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/facing_direction_probe/verify_cpu.py
PYTHONPATH="$PWD" /home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/facing_direction_probe/driver.py precommit --out docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/facing_direction_probe/precommit.json
```

CPU 검사는 native scene/GPU 없이 수학·단계 경계·전체218개 endpoint의 기존 codec/bounds/rate·원래 wrist clamp·same-point 조건·실패 동시/후속 제외·13표본 span을 검증한다. CPU 합성 사례는 실제 물리 도달 증거가 아니다.

독립 change-review는 root가 기존 reviewer에 위임한다. 수정이 있으면 기존 seal을 보존하고 새 seal로 동결한다. seed17 두 모드의 GPU 종료 뒤 root가 인계하면, established Isaac 환경에서 CPU0~13 affinity·KMP_AFFINITY=disabled와 함께 `driver.py run-gpu --precommit ABSOLUTE_SEAL --out NEW_ABSOLUTE_OUTPUT`을 실행한다. 이 문서 작성/CPU 검사는 GPU 실행을 포함하지 않는다.
