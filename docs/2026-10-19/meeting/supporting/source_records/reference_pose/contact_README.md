# 29초 저장 접촉점과 형상 비교 — V2

![29초 실제 기록 접촉점과 source 형상](/home/ajou/yigyu/3/paper/initial_pose/current_v3/contact_visualization_v1/render_v2/recorded_contacts_29s.png)

그림은 `free_strike_v14`의 29초(physics step 6960), 왼손 넥 해제 상태를 보여줍니다. 위쪽은 정면, 아래쪽은 비스듬한 시점입니다. 왼쪽 패널은 source 시각 메시이고, 오른쪽은 투명한 source 충돌 형상과 기록된 양의 raw lambda 접촉 특징점입니다. 숫자는 가슴(1), 오른쪽 상완(2), 오른쪽 허벅지(3), 척추 몸통(4)을 가리킵니다.

양의 raw lambda가 있는 원기록 7행을 표기했으며 같은 위치의 중복 행이 있으므로 7개 고유 접촉점이나 접촉 부위 7곳을 뜻하지 않습니다. `lambda=0` 후보는 표기하지 않았습니다. 각 특징점은 해당 body의 저장 pose와 body-local `localPos`로 변환했습니다. COM·contact offset·형상 두께를 더하지 않았습니다. 원자료 raw lambda는 뉴턴 단위의 힘으로 해석하지 않습니다. 점은 가림을 무시해 투영하며 점 크기는 접촉 면적이 아닙니다.

이 표본의 양성 접촉 특징점에서 보이는 기타 source triangle까지 측정된 최대 unsigned 거리는 **0.0754 mm**입니다. 이는 이 7개 raw row 점에 대한 관측이며, 전체 두 메시 사이의 간격이나 PhysX cooked 충돌 표면과의 비교를 뜻하지 않습니다. 투명 충돌 표시는 선택된 source 형상이며 native cooked mesh가 아닙니다.

렌더링은 MuJoCo source 형상 시각화로, 새 물리 스텝은 0입니다. 네 패널 모두 106개 몸체의 변환 readback이 통과했고 입력 지문 118개가 유지됐습니다. [세부 보고서](/home/ajou/yigyu/3/paper/initial_pose/current_v3/contact_visualization_v1/render_v2/render_report.json) · [입력 SHA 목록](/home/ajou/yigyu/3/paper/initial_pose/current_v3/contact_visualization_v1/render_v2/inputs_before.json) · [현재 자세 미디어 목록](/home/ajou/yigyu/3/paper/initial_pose/current_v3/MEDIA.md)
