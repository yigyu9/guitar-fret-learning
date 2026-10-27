# 음악 목표 발견 개선 구현 기록

소유 파일은 `guitar_learning/dense_environment.py`, `task_sampling.py`와 두 신규 CPU 검사다. 기존 TrainingEnvironment, 음악 ledger, 타현 판정, 원 모델·제어·물리는 수정하지 않았다. 이 담당 작업에서는 실제 native 실행을 하지 않았다.

## 확인한 제한과 변경

기존 왼손 approach 보상은 `press_s <= now <= onset_s` 구간에만 제공된다. 첫 단음에서는 약1.00~1.12초다. 오른손에는 목표를 향하는 연속 거리 보상이 없다. 따라서 기존 음악 성공0이 버그라고 단정하지 않으면서, 성공 이전 탐색에 필요한 신호가 짧거나 없다는 구현상 제한을 개선했다.

`DenseTrainingEnvironment`는 원 환경을 상속하며 원 step 이후의 같은 실제240Hz 표본4개와 음악 측정4개를 짝지어 추가 보상만 적분한다.

- 왼손 초기 접근: `[0, press_s)`에서 `0.2 exp(-(d/0.03)^2)`/초. d는 기존 측정의 지정 손가락 distal body 원점과 현재 기타 프렛 목표 사이 거리다. 손끝 패드·압력 보상이 아니다. 기존 approach는 그대로다.
- 오른손 가이드: 실제 기타 프레임의 목표 현에서 y=-0.32m, 깊이8mm를 중심으로 앞쪽에서 뒤쪽으로 이동하는 짧은 피크 목표. onset±0.08초 동안 방향에 따라 ±6mm를 이동하므로 중심 통과 시각은 onset이고 속도는0.075m/s다. normal은 실제 detector와 동일하게 `[-line_y,line_x]`를 정규화하고 x<0이면 뒤집는다. down/up 방향 부호도 그대로다.
- 오른손 거리: 음악시간0부터 onset+0.08초까지 `0.2 exp(-(d/0.02)^2)`/초. sweep 이전에는 앞쪽 준비점이다. 여러 목표가 있을 때 최근 onset 하나만 가이드를 소유한다.
- 오른손 방향: onset±0.08초에서 거리 credit × `0.1 clip(direction × across_velocity / 0.075,0,1)`/초. 실제 연속 표본 간 피크 상대 이동으로 계산한다. 정지에는 방향 credit이 없다.

추가 reward_terms의 합을 반환 reward·누적 total_reward·terminal episode.reward에 반영한다. 원 ledger의 접촉/타현/유지/해제와 안정성 비용·실패·종료는 그대로다. 이 기하 shaping을 실제 압현·타현 성공으로 사용하지 않는다.

진단 `info.pick_guide`에는 마지막 실제240Hz 표본의 physics_step, target_id, task_time_s, goal_G_m, pick_G_m, distance_m, normal_G_xy, phase, direction, sweep_active와 proxy 범위를 저장한다. reset에서도 시간0의 준비점 진단을 기록한다. 활성 가이드 목표가 없는 경우 None이다. CPU 검사에서 마지막 측정 표본과 진단 step/time/pick/distance가 일치함을 확인했다.

`reward.dense_v2` 계약에 설정과 해석을 명시했다. 기존 legacy checkpoint는 dense 계약으로 strict resume되지 않는다. 고정 legacy 경로는 원 TrainingEnvironment를 그대로 반환한다.

## 명시적 목표 pool

`task_sampling.build_environment`의 `music`에는 `reward_mode=legacy|dense_v2`와 `goal_event_indices=null|list`만 허용한다. null은 기존 고정 목표다. list는 B 단계의 지원되는 단일 압현 이벤트를 전부 사전 검증하고, 미지원·개방현·다중 목표를 묵시적으로 제외하지 않고 실패시킨다. 목록은 사용자가 선택한 명시 입력이며 자동 난이도/거리 필터가 아니다.

각 worker는 seed+worker_id로 독립적인 순서를 만들고 매 cycle 목록을 한 번씩 섞어 비복원 추출한다. 에피소드마다 원 환경의 task를 교체한 뒤 reset하므로 관측 builder와 ledger도 해당 목표로 다시 구성된다. 정책 contract.task는 pool의 모든 원 provenance/SHA/시간/목표를 포함하는 공통 계약으로 유지한다. 실제 선택 index와 개별 task 계약은 reset/step info.episode_task 및 완료 episode에 기록한다. raw native audit에는 reset info도 별도로 보존해야 한다.

읽기 전용으로 확인한 지원 단음 후보:

| index | 물리 현 | 프렛 | 손가락 |
|---:|---:|---:|---|
|0|2|7|약지|
|1|2|5|검지|
|2|3|7|약지|
|3|3|6|중지|
|4|3|4|검지|
|17|3|9|소지|

`[0,1,2,3,4]`는 4~7프렛·세 손가락을 포함하는 소규모 선택 후보다. 기하 도달 가능성 또는 학습 성공이 검증된 목록이라는 뜻은 아니다. 우선 첫 음 고정으로 dense 효과와 안정성을 확인한 뒤 별도 pool 설정을 비교할 수 있다. event42는 unsupported이므로 포함하면 명시적으로 거부한다.

## CPU 검사

신규7개 검사 통과: `python -m unittest guitar_learning.tests.test_dense_environment guitar_learning.tests.test_task_sampling -v`. 최종 실행은 아래 진단 추가 후에도 통과했다.

원 TrainingEnvironment 검사4개와 함께 실행한11개도 통과했다(4.546초, 최종 strict-resume assertion 추가 직전). 신규 검사에는 다음이 포함된다.

- 실제 StrikeDetector에 synthetic 정상 가이드를 넣으면 목표 현·방향·깊이8mm 통과가 생성되고, 반대 방향/90ms 늦은 추종은 정상 추종보다 보상이 작다.
- 초기 왼손 접근이 press 이전에 활성화되고 그 이후 중복 추가되지 않는다.
- 입력 geometry/measurement는 수정되지 않는다.
- 실제 기록을 읽는 CPU fixture에서4표본 적분·누적/terminal reward가 일치한다.
- 동일 기록·동일 행동의 legacy 대비 관측·음악 지표·안정성 비용·실패 이유가 동일하다. 타현 매칭/hold는 기존과 같이0이며 shaping으로 허위 성공이 생기지 않는다.
- dense 항목을 제거한 계약은 legacy와 정확히 같고, legacy→legacy PPO 복원은 성공하며 legacy→dense PPO 복원은 mismatch로 거부된다.
- worker별 결정성·cycle 균형·episode metadata·공통 계약·미지원 event 사전 거부를 확인했다.

native 학습 성능과 음악 수행 개선은 아직 이 구현/CPU 검사만으로 주장할 수 없다. 실제 실행은 root 담당이다.
