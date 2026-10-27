# 허리 굽힘 완화·오른팔 근접 산출물 brief

- 기준: `right_thigh_waist_v1/native_static_v2`의 오른 허벅지 waist 배치. 선택: 이번 `native_relief4_static` 및 같은 초기값의 `native_relief4_elbow5`; 비교: `native_relief2_static`.
- 입력: 이 phase의 `search_v3/search.json`, `posture_final_v1.json`, `analysis_final_v1/analysis.json`, 세 `native_*/`의 초기값·trace·contact·report 및 실제 Isaac Gym `media/frames/`·MP4. 기준 초기값과 영상은 `right_thigh_waist_v1/native_static_v2/`.
- 기타 초기 39 rigid body p/q는 기준과 최대 1.1151e-7 m / 1.3009e-7 rad 차이. 기타는 자유, 스트랩 OFF, root/하체 고정, humanoid 자체 충돌 ON. 실제 81 목표 중 몸통9+팔24는 EFFORT, 머리6+손가락42는 POSITION. 기타 고정·직접 힘·부착·실행 중 pose 덮어쓰기 없음.
- 초기 Chest local-Z의 world 전방 기울기 proxy: 기준 65.412312°, 4° 후보 61.412311°, 2° 후보 63.412314°. 이것은 임상적 척추 각도나 body9 scalar 관절각 합이 아니다. 4° 후보의 실제 초기 body9 scalar 최대 차이는 1.437231°, 부모–자식 상대 회전 변화는 Pelvis→Torso 1.000°, Torso→Spine 1.500°, Spine→Chest 1.500°.
- 오른 팔꿈치 관절 중심→기타 바디 bounding-box 중심 거리: 기준 0.400908 m, 4° 초기 0.397789 m. 실제 거리 단축 3.119324 mm, 접근 방향 투영 3.135013 mm. 탐색 요청치 8 mm를 실제 결과로 쓰지 않는다.
- 5초 native 세 조건 모두 1200 physics step·300 control tick 완료. 4° 정지: 기타 바디 bounding-box 중심 초기 대비 최대 14.545447 mm, 최종 12.267181 mm; SO(3) 최대 8.012684°, 최종 5.598054°. 2° 정지: 최대 17.004627 mm / 8.473343°, 최종 15.319244 mm / 6.992828°.
- 4° 팔꿈치 목표 ±5° 한 주기: 실제 2.5~5초 scalar 범위 10.078053°. 같은 시각 4° 정지와의 추가 기타 변화 최대 0.180525 mm / 0.083762°; 최초 상태와 2.5초까지의 trace는 exact 일치. 기타 초기 대비 최대 14.545447 mm / 8.012684°, 최종 12.267792 mm / 5.593573°.
- 세 조건 각각 실제 오른 허벅지 waist 접촉 1198/1200, 마지막 120/120 양의 raw lambda. 4° 정지/운동의 Thorax 마지막 120 step 접촉 0, 상완 근위는 120/120, 오른 전완·손 기타 접촉 0. 왼손 손가락 기여도 남아 있다. 따라서 두 블록 지속 끼움, 왼손 없는 수동 안정, 반복 강건성, 연주 성공은 판정하지 않는다. raw lambda를 힘 N으로 표기하지 않는다.
- 이미지: 동일 카메라의 실제 native 기준/4° 초기 전신과 비교 crop, 팔꿈치 운동의 0·2·5초 장면. 각 이미지 caption에 관측 시각·뷰·실제 source를 적고, 생성 뒤 실제 원프레임과 대조한다. 영상: 세 조건 전신/손 확대 6 MP4를 byte-exact 복사해 `video/waist_upright_right_arm_v1/`에 모은다. 각 영상은 물리 5.000 s, 30 fps 151 프레임으로 재생 길이 5.033333 s임을 구분한다.
- 저장 권한: `results/waist_upright_right_arm_v1/artifacts_v1/` 및 `video/waist_upright_right_arm_v1/`만. 원자료·실행 소스·다른 phase·main 문서는 수정하지 않는다. 결과 문서·변경 파일 색인은 한국어와 실제 절대 경로/줄 번호로 작성한다.
