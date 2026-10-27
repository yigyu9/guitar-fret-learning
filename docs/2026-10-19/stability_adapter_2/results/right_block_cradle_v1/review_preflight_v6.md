# 사전 검수 — 현재 기타 기준 근위 두 점 추종

요약 판정: **문제없음. Critical 0 / Warning 2 / Suggestion 0.** 지정된 static_currentG_body4 설정의 bounded5초 정지 진단을 막는 제어 오류는 발견하지 않았다. 실제 두면 접촉·팔꿈치 독립성 결과는 미검증이다.

- helper3는 left_near_arm_effort_v3에서 시작한다. 이전 right_block helper2를 중첩하지 않으므로 옛 Thorax task가 남아 이중 합산되지 않는다. 기존 오른 raw 요청에 포함된 fixed-world axilla task를 저장값으로 감산하고 새 두 점 요청을 더한 뒤 최종 native effort cap으로 clip한다.
- [목표:26](/home/ajou/yigyu/3/stability_adapter_2/right_block_effort_v3.py:26)는 초기 source witness와 안쪽4mm 목표를 G-local 좌표로 저장한다. 현재 기타 pose와 COM linear/angular velocity로 목표·속도를 계산하고 인간 점도 같은 COM→점 속도 규약을 사용한다. `2000e+30v` 요청을 각10N norm으로 제한해 Jᵀ 변환한다. Thorax는3개, Shoulder는 Thorax+Shoulder6개 성분만 합산한다.
- [J/제출:48](/home/ajou/yigyu/3/stability_adapter_2/right_block_effort_v3.py:48)는 Elbow/Wrist child 열0·점 속도오차≤.01m/s를 검사하고 오른12를 최종 clip한다. 왼 gravity/PD/wrist task 및 나머지57 POSITION은 이전 벡터를 그대로 유지한다. native 상태 읽기 전후 불변과 단일 human81 actuator 제출·24 owner window를 상속한다. 기타 직접 힘·구속·pose setter는 없다.
- [기록:63](/home/ajou/yigyu/3/stability_adapter_2/right_block_effort_v3.py:63)의 two_block_rows는 제거한 old task/추가한 두 task/최종81을 기록한다. 부모 tracking의 이전 벡터도 before_two_block_efforts_Nm으로 보존하고 actual_combined_submitted_efforts_Nm을 실제 최종값으로 갱신한다.
- runner4는 helper import만 바뀌며 초기 검증·body4 PD 기대값·camera/부분 실패 저장·50rad/s/기타20cm·35° 안전 검사와5초 녹화 계약을 유지한다. 지정 config는 body4_ON10의 같은 candidate/reference와 초기81/G·제어값을 유지하고 two_block_current_G=True만 추가한다. 새 helper/runner AST는 통과했다.

Warning 1 — 부모의 axilla_effort_rows 및 right contribution은 교체 전 계산 진단이다. 실제 현재G 제어의 권위는 two_block_rows.final_efforts_Nm과 갱신된 tracking actualfinal이다. 기존 analyze_right_block_cradle_v1은 thorax_point_rows를 필수로 읽으므로 새 조건에 그대로 재사용하면 안 된다. 새 분석에서 제거/합산·목표와 속도·각cap·최종 clip을 재검증해야 한다.

Warning 2 — 두10N은 각 가상 요청 cap이며 총10N 제한/접촉력 측정이 아니다. 현재G 추종으로 자유기타 자체가 고정되는 것은 아니며 포화와 실제 이탈이 남을 수 있다. source근접·후기정착 또는 왼thumb/허벅지 접촉을 오른 두 블록만의 받침 성공으로 읽지 않는다. 실제 접촉 영역과 왼손·전완·Head 관여를 별도로 기록하고 같은조건의 scalar elbow 시험을 수행해야 한다. 이전 Jacobian/중력 모델과60Hz 안전 표본의 인증 한계는 유지한다.

코드 diff·계획V4·config 차이·좌표/속도/합산 수식·상속 경로·AST만 검토했다. 추가 native/학습/추론과 다른 담당 파일 수정은0이다.

검수 SHA256:

- 계획V4: `6fe2c3c7bac9af7035ed88c21694e3764bdd9cf3c7d9a71561b9306ae4219bf4`
- helper3: `ce043f02efb289165f93e34ac73f234f3d6e5fd92719cd9089870b9c1e285957`
- runner4: `484a3f91eb644b8f430bc8f2cfda1448efa22c59870d1a550fb9ca486aff9a1a`
- config: `5ec98a1eaa6c60998ba50a36a63b7ae11380aca542ad263ce1877d50cdf9d125`
