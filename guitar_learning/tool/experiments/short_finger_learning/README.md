# 원곡 1음 진단 학습 v2 · 손목 제어 v3

기본 학습과 분리된 fresh PPO 비교 경로다. 고정 기타에서 035 reset 후 첫 tick부터 선택 손가락 4축을 정책이 제어한다. 팔은 외부 SHA 봉인 JSON의 feedforward와 기타좌표 고정 손목 pose를 2초간 보간해 유한 제어하고, 음 시작 3초까지 1초의 정착 여유를 둔다. 다른 손가락은 B, 엄지는 준비 기준을 유지한다. teacher는 손목 원점·방향 오차만 읽으며 패드 오차와 학습 손가락을 교정하지 않는다. 보상9개·물리/손목 종료·557상태/J/K1과 원곡 음 길이를 유지한다.

**최신 손목 v3의 GPU 추종 개선은 확인했으나 압현 성공은 미해결이다.** 검지 row1과 중지 row8의 reference/출력0/난수는 각각0/4달성이며, 이 결과는 정책 학습 성과가 아니다. 현재는 같은 목표에서 손가락4축의 유한 도달 진단을 진행한다. 장기 학습 전에 아래 작은 실행과 출력0/난수/유한 reference 대조를 수행한다. row8의 원곡 음은 0.1174초이며 local press2.9787초, onset3초, end3.1174초다.

Isaac Gym 환경에서 프로젝트 루트(`/home/ajou/yigyu/3`) 기준으로 실행한다. 모든 출력은 새 경로다.

```bash
python -m guitar_learning.tool.experiments.short_finger_learning train \
  --teacher docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/short_finger_wrist_teacher_middle_row8_v2.json \
  --mode incremental --initial-std 0.1711710544767014 \
  --size small --num-envs 2 --horizon 32 --updates 1 --save-every 50 \
  --seed 7 --out /tmp/short_middle_wrist_v2_incremental_smoke
```

position 비교는 동일 입력에서 `--mode position --initial-std 0.01`과 새 출력 경로를 사용한다. 이 std들은 03_short_learning/exploration_calibration.json의 CPU 첫 tick target 변화 pooled RMS 교정값이다. 축별 차이·장기 누적 차이와 실제 물리 응답까지 같다는 뜻은 아니다. 초기 std는 정책 clamp와 같은 `[exp(-5),1]` 범위만 허용한다.

```bash
python -m guitar_learning.tool.experiments.short_finger_learning evaluate \
  --checkpoint /tmp/short_middle_wrist_v2_incremental_smoke/initial.pt \
  --control zero --episodes 4 --out /tmp/short_middle_wrist_v2_incremental_zero

python -m guitar_learning.tool.experiments.short_finger_learning evaluate \
  --checkpoint /tmp/short_middle_wrist_v2_incremental_smoke/initial.pt \
  --control random --episodes 4 --out /tmp/short_middle_wrist_v2_incremental_random

python -m guitar_learning.tool.experiments.short_finger_learning evaluate \
  --checkpoint /tmp/short_middle_wrist_v2_incremental_smoke/initial.pt \
  --control reference \
  --reference docs/2026-10-27/guitar_learning_failure_diagnosis_v1/03_short_learning/reference_middle_row8_v2.json \
  --episodes 4 --out /tmp/short_middle_wrist_v2_incremental_reference

python -m guitar_learning.tool.experiments.short_finger_learning evaluate \
  --checkpoint /tmp/short_middle_wrist_v2_incremental_smoke/final.pt \
  --control policy --episodes 4 --out /tmp/short_middle_wrist_v2_incremental_policy
```

`zero`는 선택 손가락 출력0이고 나머지 teacher는 유지한다. `random`은 자체 initial checkpoint(update0)의 고정 초기 확률분포를 사용한다. `reference`는 별도 봉인 JSON의 선택4축 목표를 2초 유한 ramp로 실행하는 스크립트 대조이며 학습 성과가 아니다. 모드별 출력0의 실제 의미가 다르므로 target/q trace를 함께 비교한다. 부분 reset 안에서 추가 physics step이나 시간 되감기를 하지 않는다.

teacher JSON은 `schema=short_finger_teacher.v2`, `condition=fixed_wrist_pose`, 정수 `finger=1..4`, 원곡 `source_target_id`, 이름별 `arm_targets_rad`12개, `ramp_s=2`, 기타좌표 `wrist_position_G_m`3개와 정규화된 `wrist_quaternion_G_xyzw`4개, `source_evidence`의 절대 경로→SHA를 요구한다. reference JSON은 `schema=short_finger_reference.v2`, 같은 target ID, 이름별 `selected_targets_rad`4개, `ramp_s=2`, evidence SHA를 요구한다. 목표는 실제 controller 범위 안이어야 한다.

저장물은 설정·계약·실행명령·입력 SHA, 업데이트별 보상9항/실패비용/PPO 지표, 축약 에피소드 성과·관절 통계, initial/final 및 지정 간격의 evaluation checkpoint다. raw transition/decision 원장은 저장하지 않는다. 평가는 환경별 시도 수를 미리 배정하며 실패를 분모에 포함한다. env0 첫 평가 시도의 target/q/action/전신 pose·candidate·wrong·순접촉힘 trace를 따로 저장한다. 순힘은 접촉 상대나 현 압력의 인증이 아니다.

학습 재개/전이 옵션은 없다. 평가는 동일 source SHA·architecture·control·teacher 계약의 자체 checkpoint만 읽는다. production 기본 CLI는 여전히 incremental만 허용한다.


v1 소스·신규 검사는 [보존본](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/03_short_learning/source_before_wrist_teacher/manifest.json)에 원래 경로와 SHA로 보관했다. v2는 새 학습/정책/teacher/reference 계약을 사용하며 v1 checkpoint와 strict 호환되지 않는다.

손목 위치 제어는 native COM Jacobian을 손목 원점으로 옮긴 뒤, 이름으로 확인한 팔12축의 **q-position 미분 Jacobian**으로 변환한다. native Jacobian의 속도/힘 좌표를 위치 증분에 그대로 쓰지 않는다. world 위치 오차(m)와 `0.1m × world 회전벡터(rad)`를 쌓아 damping1e-5 DLS 증분을 구한다. 이 변환은 팔의 full3축만 검증했으며 MCP2축·발 제어로 일반화하지 않는다.

손목 v3는 `candidate=actual_arm_q+DLS_increment`, `proposal=feedforward+stored_correction`을 계산하고, `candidate−proposal`을 축당 ±0.5°/control tick으로 제한해 보정한다. 이후 기존 controller action bounds와 팔3rad/s 요청 변화 상한을 적용한다. ±0.5°는 feedforward에 대한 보정 상한이며 전체 요청 변화가 항상 ±0.5° 이하라는 뜻은 아니다. native 팔 smoothing0.2·PD·힘 상한과 손가락21축 속도 상한4rad/s는 유지한다. 실제 위치·각도를 덮어쓰지 않는다.

partial reset은 해당 행의 초기 손목 pose와 보정 누적값만 초기화한다. reset 직후 첫 제어 tick은 stale Jacobian을 쓰지 않고 feedforward만 적용한다. 보정 여부·원래 pose 오차·요청 delta/팔목표·실제각 기준 candidate·목표 손목 pose는 평가 trace에 기록한다. 요청 delta는 candidate−proposal에 대한 보정이다. 손목 pose 오차는 제어 시작 시각의 실제 pose와 다음 목표 사이의 값이며, physics 이후 도달 오차가 아니다. 2초 ramp와1초 정착으로 실제 목표가 도달한다는 보장은 없으므로 새 GPU reference 대조를 먼저 확인한다.

현재 wrist 계약은 `guitar_learning.fixed_wrist_teacher.v3`다. 단음 task/teacher/reference의 v2 schema와 구분하며, 이전 wrist v1/v2 checkpoint는 현재 소스·계약으로 strict load하지 않는다. 과거 성공 수치는 당시 소스 조건에 속하며 현재 성공으로 상속하지 않는다.

[최신 실제 비교·검수](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/wrist_position_candidate_v3/analysis/results_v1/RESULTS.md)에서 env0 음 중 손목 위치/회전 오차 중앙값은 검지0.205mm/0.041°·중지2.808mm/2.255°다. 검지는 패드 위치/방향이 통과하지만 끝마디 하중이0이고, 중지는 wrong source가 남았다. 4환경 전체의 추종 통계나 실제 줄 압력의 인증은 아니다. [source 자세 감사](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/source_finger_pose_consistency/RESULTS.md)는 같은 drive target만으로 원래 실제 손가락 자세가 재현되지 않음을 확인했다.

문서 갱신 전 원문은 [보존 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261027_before_short_finger_readme_v3_update/manifest.json)에 있다. 전체 진단은 [계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_failure_diagnosis_20261027.md)을 따른다.
