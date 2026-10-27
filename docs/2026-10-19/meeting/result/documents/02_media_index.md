# 미디어 재생 순서와 관찰 지점

## 기본 발표 자료

| 파일 | 종류와 구간 | 보여줄 내용 |
|---|---|---|
|`images/00_guitar_initial_and_current_native.png`|Isaac Gym native 정면·1920 × 1440|왼쪽 초기 사각 바디, 오른쪽 현재 OM v3. 같은 장면·배율 1, 물리 시간 진행 없는 형상 비교. [설명](00_guitar_model_comparison.md).|
|`videos/01_reference_pose_release_strike_regrasp.mp4`|저장 몸체 자세 재생·33초|0–23초는 원시험17–40초의 왼손 해제와 오른손 타현. 23–24초 전환 카드. 24–33초는 별도 재접촉 시험의 원40–49초. 새 물리 시뮬레이션 영상은 아님.|
|`images/01_reference_prepared_pose.png`|기준 자세 이미지|035 설정의 준비 후 원22초 모습. Root 고정·하체 유한 제어.|
|`images/02_reference_recorded_contact_points.png`|29초 접촉 시각화|왼손 해제 상태의 기록 접촉 특징점. source 시각·충돌 형상 비교이며 점의 크기는 접촉 면적이 아님.|
|`videos/02_separate_hand_policies_upper.mp4`|정면 상체·15초|0–7초 왼손 단독 평가, 7–8초 전환 카드, 8–15초 오른손 단독 평가. 동시 양손 연주가 아님.|
|`videos/02b_separate_hand_policies_full_body.mp4`|같은 시험의 전신·15초|전신 지지 자세를 함께 볼 때 사용.|
|`images/03_single_hand_left_preview.png`|왼손 정책 재생의 한 프레임|단음 압현 자세 확인.|
|`images/03b_single_hand_right_preview.png`|오른손 정책 재생의 한 프레임|단음 타현 자세 확인.|
|`images/04_full_song_note_outcomes.png`|보상 개선 전 전곡 시험|각 환경67음에서 압현·타현·협응의 충족 여부. 초록은 기준 충족, 회색은 미달. 고정 최종 정책 평가가 아님.|

## 기존 초기 자세 탐색 이미지

[과정 설명과 이미지 목록](01b_initial_pose_search.md)에 기존 PNG 10개를 모았다. 척추 분산 굽힘, 추가 전방 숙임 18°, 넥 쪽·바디 쪽 4° 기울임, 숙임 감소·몸통 회전, 허리 펴기를 포함한다. 원본 그대로 복사했으며 새 촬영은 수행하지 않았다. 모든 계열은 Root/하체 고정이며 스트랩과 왼손 지지 조건이 다르다. 실패 후보와 짧은 진단 후보를 구분해 설명한다.

## 세 시점 접촉 지점 이미지

[설명과 PNG 6개 목록](01c_contact_visualization.md): 기존에 저장한 0.5/3.5/5.333/6.5/10.5/14초의 앞·오른쪽 옆·위 접촉 표식 이미지다. Root/하체 고정·스트랩 OFF·오른손 타현 OFF인 별도 잡기·놓기 시험이며 원 크기는 힘이나 접촉 면적을 뜻하지 않는다.

## 현재 학습 기준 자세의 native 녹화

[이미지·영상 안내](01e_current_initial_pose.md)에 현재035/v14 준비 완료22초 이미지와 5개별 시험의 실제 Isaac Gym 5fps 전신 녹화를 추가했다. Root 고정·하체 유한 제어다. 오늘 별도 진단의 초기 이미지·16초 영상은 같은 안내에서 물리 조건을 나누어 확인한다.

## 새 초기 자세의 별도 진단

아래는 Root/하체 고정·오른손 타현 OFF·자유 기타 조건이다. 기존 하체 유한 제어 시험의 연속 장면으로 설명하지 않는다.

| 파일 | 관찰 지점 |
|---|---|
|`videos/03_current_pose_grip_cycle_full_body.mp4`|전신16초 진단. A잡기3–4.5초, 첫 분리4.5–6초의 기타 이동, 마지막13–16초의 분리 유지.|
|`videos/03b_current_pose_grip_cycle_hands.mp4`|손 확대. 3–4.5초와10–11.5초 두 위치의 잡기, 6–7초와13–16초 왼팔·손 접촉 해제.|
|`videos/03c_current_pose_grip_cycle_support.mp4`|가슴·위팔 지지 근접 시점. 접촉 부위 변화와 기타 이동을 확인.|
|`images/05_current_pose_grip_four_moments.png`|실제 native 카메라의3.5/6.5/10.5/14초 네 장면.|
|`images/06_current_pose_guitar_motion.png`|정규화 quaternion 계산을 적용한 V2 위치·회전 그래프. 큰 순간 변화와 마지막 정착을 함께 설명.|

모든 MP4는 선택한 기존 완성본의 바이트 동일 사본이다. 이 미팅 정리 작업에서 동작을 새로 생성하거나 다시 시뮬레이션하지 않았다. 영상 길이·해상도·프레임과 전체 decode 결과는 `supporting/qa/verification_v1.json`, 파일별 원본 경로·SHA는 `supporting/provenance/copied_files_v1.json`에 있다.
