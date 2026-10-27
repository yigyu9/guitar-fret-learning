# 독립 검수 — Strike waypoint velocity v1

판정: **문제없음(PASS)**. Critical / Warning / Suggestion: 남은 항목 없음. 구현·저장 원자료·native 이미지/영상·최종 README/CHANGED_FILES를 읽기 전용으로 대조했으며 신규 native 초기화·physics 실행은 하지 않았다.

- 1,200 physics steps, 300 controls, 24개 계약, PREPARE/PLAY/HOLD 49/239/12를 확인했다. Trace 152행은 151개 정규 표본과 step 1152·4.8초의 PLAY/HOLD 중복 행을 포함하며, 카메라 151프레임과 구분된다.
- PLAY 239행의 위치 차분 속도, 최대 5 mm 보정, phase별 목표 합성과 최종 float32 native/rate clipping을 재계산했다. READY/닫힌 APPROACH/열린 APPROACH/RECOVER는 28/69/30/112행이다. 열린 APPROACH의 PI 및 포화 시 적분 복원, 나머지 분기의 적분 유지가 일치한다. 다른 NumPy 환경에서 보정 재계산 차이는 최대 1.74e−18 m였다. 저장 native pick anchor 119개와 목표·상태 보존 범위도 대조했다.
- 5회 PD 전환에서 전체 81개 요청/readback과 상태 보존을 확인했다. 기존 일정에 따른 R9 damping 변경 외 PD 필드는 유지됐다.
- Native closure 1,100개는 현재 파일과 보존된 main 문서 2개로 연결되며, 별도 분석 7개 및 velocity audit 6개 SHA도 일치한다. 이전 조건과 PREPARE controls 49개·native prefix 25개·첫 actor observation/action exact는 해당 비교 범위에 한정된다.
- 두 뷰의 PNG 302개 SHA, MP4 2개 SHA/ffprobe(1280×720, 151프레임, 30 fps, 5.033333초), 대표 hands/whole-body 이미지를 확인했다. 첫 hit control 1.483333초와 가장 가까운 카메라 1.466667초를 문서가 구분한다.
- Physical/accepted hit 2회는 각각 −107.446640 ms, −191.687698 ms의 조기 타현이며 적시 hit은 0이다. 일반 회복 pulse 2회와 scheduled 회복 완료 2회가 완성 연주 성공을 뜻하지 않는다. Source 종료 4.8초 이후 HOLD에서 5초까지 기록한 범위와 기타 p/q·region 집계가 문서와 일치한다.

검수한 정확한 SHA256: runner `7988c9d9af63897fc6f566f32ffc230a61f71598167b588a52115f1d18e67443`, wrapper `37a8b82fafc39ef37ffeddc8290081d2ca3f9555520bb7142b5cac2090151099`, analysis summary `06fe00af674b2a23b9bf8acb0f2fb67005b4b06dc26b0c56639ac4c0c08b3a13`.

한계: 표본 차분은 순간 속도·접촉 인과성·source drive 동등성을 인증하지 않는다. 전체 궤적 동등성, 적시 타현 및 완성 연주 성공은 확인되지 않았다. Root의 이후 최종 보존 감사·봉인은 이 검수에서 완료했다고 주장하지 않는다.
