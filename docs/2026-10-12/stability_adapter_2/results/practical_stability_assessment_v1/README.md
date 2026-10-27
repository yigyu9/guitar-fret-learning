# 정지 유지 목표의 실용적 평가

사용자의 미세 떨림 허용을 반영하면 현재 결과는 **초기 움직임 이후 정지 자세를 유지하는 서브목표를 상당 부분 만족**한다. 완전한 정적 평형 여부를 필수 조건으로 강조한 이전 답변은 실용적 목적에 비해 엄격했다.

| 기존 실제 기록에서 측정한 항목 | 값 |
|---|---:|
| 분석 구간 |2~5초|
|2초 시작점 대비 최대 위치 차이 |0.001899241mm (약1.90µm)|
|2초 시작점 대비 최대 회전 차이 |0.001245157°|
|5초 종료의 초기 목표 위치 오차 |14.050564mm|
|5초 종료의 초기 목표 회전 오차 |2.856298°|

정지 유지와 초기 이탈량을 분리해 평가한다. 미세 pose 떨림/속도 field 비영 자체를 근거로 정지 유지 실패로 분류하지 않는다. 초기14mm/2.86°가 허용된 것으로 확대 해석하지 않는다. 이번 설정을 유지 성능의 기준으로 삼고 초기 이탈 감소와 작은 손·팔 동작 중 유지 성능을 후속 검증한다.

![평가 대상인 기존 실제 Isaac Gym 스트랩 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/native/hands.mp4)

[주요 제어·유지 기준 결정](/home/ajou/yigyu/3/stability_adapter_2/QUIET_HOLD_BASELINE_DECISION.md:1), [재계산 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/practical_stability_assessment_v1/assessment.json:1)에 남긴다. 원본 실행과 기존 실패 기록은 수정하지 않았다. 추가 native/physics0이다.
