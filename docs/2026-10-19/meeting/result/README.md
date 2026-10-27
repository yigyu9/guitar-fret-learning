# 기타 연주 시뮬레이션 연구 미팅

먼저 [미팅 설명](documents/01_meeting_brief.md)을 읽고, [미디어 목록과 관찰 구간](documents/02_media_index.md)의 순서로 재생한다.

| 순서 | 보여줄 자료 | 설명할 내용 |
|---|---|---|
|0|[초기·현재 기타 모델 비교](images/00_guitar_initial_and_current_native.png)|동일 Isaac Gym 장면·원래 축척에서 사각 바디와 OM v3 형상 비교|
|0a|[시각 메시·충돌 형상 비교](documents/00b_guitar_visual_collision_comparison.md)|실제 native 두 표시와 바디 정면·측면 깊이 차이|
|0b|[초기 자세 탐색 이미지 10개](documents/01b_initial_pose_search.md)|척추 굽힘·전방 숙임·양측 기울임·숙임 감소의 기존 기록|
|0c|[초기의 오른쪽 기울임·둥근 허리](documents/01d_right_tilt_and_rounded_spine.md)|추가 초기 이미지·기울임 교정 전후·9°/12° 분산 굽힘|
|0d|[현재 초기 자세 이미지·native 영상](documents/01e_current_initial_pose.md)|035/v14 기준의 준비 자세·개별 시험 5개와 오늘의 별도 후보 구분|
|1|[초기 자세 영상](videos/01_reference_pose_release_strike_regrasp.mp4)|하체 유한 제어 상태에서 왼손 해제·타현·재접촉을 확인한 두 시험 편집|
|2|[접촉 시각화](images/02_reference_recorded_contact_points.png)|기타 지지 접촉의 위치와 시각 형상 비교|
|2a|[현재035/v14 초기 자세의 접촉점](documents/01f_current_pose_contacts_22s.md)|준비 완료22초의 실제 native 정면·측면에 접촉 기록 표시|
|2b|[세 시점 접촉 표시 이미지 6개](documents/01c_contact_visualization.md)|잡기·해제 전환·놓기 상태에서 실제 접촉 특징점 확인|
|3|[손별 정책 영상](videos/02_separate_hand_policies_upper.mp4)|왼손과 오른손의 별도 단음 평가를 이어 보여주는 15초 편집|
|4|[전곡 학습 결과](images/04_full_song_note_outcomes.png)|보상 개선 전 67음 학습에서 드러난 음 전환·협응의 한계|
|보충|[오늘의 잡기·놓기 진단](videos/03_current_pose_grip_cycle_full_body.mp4)|다른 초기 자세·하체 고정 조건에서 손 접촉과 기타 이동 확인|

손별 합본을 양손 동시 성공으로 설명하지 않는다. 초기 자세 영상도 두 실행을 편집한 것이다. 오늘의 자세 진단은 하체를 고정했으므로 기존 하체 유한 제어 학습 결과와 직접 비교하지 않는다.
