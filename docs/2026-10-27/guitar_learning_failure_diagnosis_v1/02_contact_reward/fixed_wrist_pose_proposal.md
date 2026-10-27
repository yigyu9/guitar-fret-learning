# 접촉 순간의 관절 목표 재생 실패와 고정 손목 pose 안내 후보

2026-10-27. 저장된 추적을 읽고 CPU FK로 검산했다. 이 문서 작성에서는 GPU를 실행하거나 활성 패키지를 수정하지 않았다. teacher/source JSON은 root 소유로 양도했으며 여기서 더 수정하지 않는다.

## 판단

**기타 좌표계의 고정 손목 위치·방향을 팔12축만으로 유한 제어하는 대안은 다음 진단으로 타당하다.** 저장된 source controller의 관절 target이 실제 접촉 관절각과 크게 달랐기 때문이다. 다만 아직 GPU에서 가능한 고정 자세로 검증되지 않았다. 이 안내가 정착돼도 지정 손가락4축의 실제 압현 수행은 별도로 확인해야 한다.

부모 작업에서 source 팔 target과 지정 손가락 reference/contact각을 유한 재생한 신규 row8/9 대조는 실제 음 창의 candidate를 재현하지 못했다. 관련 원본은 [row8 reference 대조](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/03_short_learning/smoke_inc_row8_reference/report.json), [row9 reference 대조](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/03_short_learning/smoke_inc_row9_reference/report.json)에 있다. 이 실패는 학습하기 전에 준비 조건의 재현성을 먼저 검증해야 함을 보여준다.

## 저장된 target은 실제 접촉 자세가 아니다

[원시 teacher trace](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/teacher_fixed_B_export/teacher_trace60.npz)에는 모든24행의 actual q105·controller target105·candidate가 있다. 그러나 native body_state는 사전 지정6행만 저장했으므로 중지 row8/9의 손목 native pose는 직접 저장돼 있지 않다.

준비 상태로 보정한 source FK로 actual q를 손목 pose로 재구성했다. 저장된 대표6행×14시점, 총84개의 실제 native 손목 body pose와 교차 검산한 최대 오차는 **위치2.10µm, 방향9.60e−7rad**였다. 실제 row8/9 pose는 이 검산을 통과한 FK 재구성값이며, 해당 행의 native body 직접 readback으로 표기하지 않는다. 근거와 SHA는 [읽기 분석 JSON](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/wrist_pose_proposal_readonly.json)에 있다.

| source 표본 | row8 중지 | row9 중지 |
| --- | ---: | ---: |
| 실제 접촉 표본 시각 | 5.450초 | 5.067초 |
| distal body resultant | 1.59N | 10.24N |
| 다른 q를 실제값으로 둔 채 arm12만 controller target으로 바꾼 FK 위치 차이 | **56.57mm** | **57.59mm** |
| 같은 FK의 방향 차이 | **23.50°** | **13.47°** |

예를 들어 row8의 `L_Wrist_z`는 실제0.24673rad에 target0.01615rad로 target−actual이−13.21°였다. `L_Thorax_y`는 실제0.03431rad, target0.17453rad로+8.03°였다. 이것은 접촉 당시부터 존재한 차이다. target을 복사했다고 실제 접촉 손목을 복사한 것이 아니다.

source teacher는 실제 pad 오차를 계속 읽고 팔12+지정 손가락4의 target을 바꿨다. 접촉력·중력 보상·다른 관절·과거 궤적의 영향 아래에서 얻은 실제 자세이며, 이 순간의 명령 target만 고정한 새로운 접근이 같은 자세나 평형을 만들 것이라는 보장은 없다. 현재 자료만으로 PD 고장이나 특정 force cap을 원인으로 확정하지 않는다.

## 최소 대안

다음 대조는 **원래 성공 표본의 실제 손목 pose 하나를 고정 기준으로 사용**한다.

1. source actual q에서 재구성한 손목 위치3개와 quaternion4개를 기타 좌표계 G로 고정한다. 다른 상태를 따라 목표 pose를 다시 탐색하지 않는다.
2. 실제 기타 pose로 이 고정 G pose를 world 목표로 변환한다. 실제 `L_Wrist` 위치·방향과의 오차만 계산한다. 팔 teacher는 지정 손가락의 pad 오차·접촉·정책 행동을 목표 보정에 사용하지 않는다.
3. 실제 native 손목 Jacobian에서 팔12축만 골라 위치3+방향3 DLS를 계산한다. 원점 Jacobian은 COM offset을 보정하고 native body−1 인덱스를 사용한다. 방향 오차와 angular Jacobian은 같은 world frame으로 맞춘다.
4. 유한 arm 행동으로만 적용한다. 기존 native 관절 범위·속도·PD·힘 상한과 종료 조건을 유지하고, 보정 step은약0.5°/control tick 이하로 제한한다. joint target이나 실제 상태를 직접 쓰지 않는다. 큰 target−actual 오차가 다시 누적되는지 별도 기록한다.
5. 정책은 지정 손가락4축만 제어한다. 다른 손가락 B와 엄지는 정해진 유한 준비 경로를 사용한다. teacher가 지정4축 target을 대신 바꾸지 않는다.

실제 worker 계약은 `schema=short_finger_teacher.v2`, `condition=fixed_wrist_pose`, ramp_s=2.0이다. audible onset-local3초 전에 약1초 정착 여유를 두려는 새 조건이며, 이전 press-local3 원장 실행이나 source2초 ramp의 검증 결과와 동일하지 않다.

[중지 row8 고정 손목 후보](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/short_finger_wrist_teacher_middle_row8_v2.json), [중지 row9 후보](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/short_finger_wrist_teacher_middle_row9_v2.json), [export SHA 목록](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/wrist_teacher_exports_v2.json)을 root에 전달했다. 기존 arm_targets는 source feedforward 기록으로 보존했지만 actual 접촉 관절 해라는 의미를 부여하지 않는다. source actual 팔각·finger contact각은 진단 metadata에 따로 남겼다.

## 성공을 판단할 순서

- **팔 안내 재현**: 지정4축을 정해진 reference로 두고 실제 손목 위치/방향 오차·target−actual·관절 경계 체류·하중·종료를 확인한다. source pose를 못 따라가면 손가락 학습으로 넘어가지 않는다.
- **압현 가능성 분리**: 같은 팔 안내에서 지정4축의 사전 고정 reference/contact각 대조만 수행한다. 이 진단 대조는 정책 성공으로 집계하지 않는다. source contact각을 사용해도 실제 원래 음 창의 candidate와 원장이 성립하는지 확인한다.
- **정책 기여 분리**: 팔 pose teacher를 고정하고 지정4축0/준비각 대조와 실제 정책을 같은 조건으로 비교한다. policy가 움직이지 않아도 접촉하는 경우를 별도 기준으로 남긴다.
- **실제 음별 지급**: actual clock에서 원래 onset/end/required와 종료를 유지한다. candidate, wrong, clean streak, 보상9항목과 비용을 함께 확인한다. 늦은 정적 contact를 짧은 음 성공으로 확대하지 않는다.

현재 후보는 낮은 수준의 팔 pose 안내 가설이다. 실제 finger policy가 압현을 배우는 문제, 높은 접촉 하중, 부정 사례 전체를 해결했다고 볼 수 없다.
