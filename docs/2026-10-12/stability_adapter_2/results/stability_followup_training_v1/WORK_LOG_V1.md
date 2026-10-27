# 추가 학습·결과 분석 작업 기록

기존 long_on_v1이 정상 실행 중이므로 중복 학습을 시작하지 않고 이어간다. 기존 STABILITY_SUPPORT_NOMINAL_V2 계획의 후속 검증이며 제어·보상·스트랩·초기값을 변경하지 않는다. source closure가 읽는 동안 A/main 문서는 갱신하지 않고 이번 작업 기록은 결과 폴더에 남긴다.

1. [x] 실행 PID와 추가 갱신, 입력·baseline 불변 조건을 확인한다.
2. [ ] 첫30분 새 checkpoint와 종료까지 실제 평가 영상을 확보한다. 준비2초/982control/3928physics 기준이며 조기 안전 종료가 있으면 그대로 구분한다.
3. [ ] CP1과 새 checkpoint의 위치 범위 밖 비율·최대/평균 거리·초기 대비 SO(3) 회전·음악42event/crossing·관절/목표/rate·RMS/KL을 분석한다. stochastic 학습 episode return은 deterministic 평가 품질과 구분한다.
4. [ ] 원자료와 producer SHA를 보존하고 한국어 설명·실제 이미지·영상·절대경로/줄 번호 색인을 생성·검수한다. 기존 산출물은 보존한다.

학습은 기존11:40 cutoff/30분CP영상/원본 길이 스트랩ON을 유지한다. 이번 단일 비교를 자연스러움·반복성·음악 성공의 인증으로 해석하지 않는다.
