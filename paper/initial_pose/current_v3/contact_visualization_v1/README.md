# 29초 저장 접촉점과 형상 비교

![29초 기록 접촉점과 원본 source 시각·충돌 형상 비교](/home/ajou/yigyu/3/paper/initial_pose/current_v3/contact_visualization_v1/render_v1/recorded_contacts_29s.png)

17초와 29초 표본 분석 중, 이 그림은 왼손 넥 해제 상태인 29초(physics step 6960)만 보여줍니다. 왼쪽은 source 시각 메시, 오른쪽은 해당 신체와 기타 몸체의 투명한 source 충돌 형상과 양의 raw lambda 접촉 특징점입니다. 시점은 위쪽이 정면, 아래쪽이 비스듬한 각도입니다. 색상 번호는 가슴(1), 오른쪽 상완(2), 오른쪽 허벅지(3), 척추 몸통(4)을 뜻합니다.

표시한 점은 각 body의 저장 quaternion을 정규화하고 `p_world = p_body + R_body · localPos`로 복원한 원기록의 특징점이며, 두께·COM·offset을 더하지 않았습니다. 기록에는 8개의 기타–인체 접촉 행이 있고 이 중 양의 raw lambda는 7개입니다. 반복 좌표가 있으므로 7개 마커를 고유 접촉 위치 7곳으로 세지 않습니다. lambda 값은 원자료 그대로이며 뉴턴으로 보정하거나 힘으로 해석하지 않습니다. 무반응 후보 `lambda=0` 행은 표시하지 않았습니다.

양의 행의 기타 점과 보이는 기타 source triangle 사이 최대 unsigned 거리는 약 0.0754 mm입니다. 이는 기록 점과 source 시각 표면 사이의 거리 관측이며 전체 메시 간격이나 PhysX cooked 표면·접촉 정책 비교를 증명하지 않습니다. 오른쪽의 충돌 오버레이도 선택된 source 선언 형상이며 PhysX cooked mesh가 아닙니다. 투영 표식은 가림을 무시하고 점 크기도 실제 접촉 면적을 나타내지 않습니다.

새 물리 적분은 0회입니다. 입력 지문 118개가 실행 후 모두 유지됐고, 네 장면 패널 모두 106개 몸체 변환 readback이 통과했습니다. 산출 상세는 [render_report.json](/home/ajou/yigyu/3/paper/initial_pose/current_v3/contact_visualization_v1/render_v1/render_report.json)과 [inputs_before.json](/home/ajou/yigyu/3/paper/initial_pose/current_v3/contact_visualization_v1/render_v1/inputs_before.json)에 있습니다. 기준은 [BRIEF.md](/home/ajou/yigyu/3/paper/initial_pose/current_v3/contact_visualization_v1/BRIEF.md)입니다.
