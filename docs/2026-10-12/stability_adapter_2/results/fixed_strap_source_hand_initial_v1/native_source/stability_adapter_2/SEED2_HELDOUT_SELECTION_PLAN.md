# 작은 목표 보정의 결합 검증

SEED2_GUITAR_RESPONSE_PLAN의 7실행 응답을 읽은 뒤 별도 1개 heldout을 만든다.
초기81q·기타p/q·LA·PD·solver를 바꾸지 않고 Shoulder/Wrist6 목표에만
각각 ±0.001rad 이내의 상수 보정을 더한다. 이미 소비된 7row proposal은 보존하고,
heldout_proposal.json과 새 trial을 따로 저장해 같은 runner의 --proposal로 실행한다.

선택 목적은 마지막1초(step960..1200 포함)의 world 오차벡터 평균이다.
위치3(m)와 Log(R_current R_goal^-1)3(rad)를 함께 비교하기 위해 회전행에
잠정 lever 0.1m를 곱한다. 이는 수치적 실험 선택 가중치이며 사용자 성공기준이 아니다.
bounded least squares로 ||W(e_base+Jδ)||를 최소화한다. δ의 각 범위는 ±0.001rad다.
J의 probe 분모는 nominal0.002가 아닌 실제 float32 제출목표 차이다.
heldout의 예측도 float32 합성 후의 실제 제출목표 차를 사용한다.

예측과 새5초 결과를 .1/1/5초와 마지막1초 평균에서 비교한다.
각각 위치(mm)·회전벡터 잔차(rad/deg)와 스칼라 p/q 최대값을 구분한다.
rank·조건수·contact 전환은 선형 근사의 한계로 기록하고 좋지 않은 결과도 보존한다.
실제 raw/초기값/영상/입력hash를 검증한 뒤 다음 방향을 정한다.
이것은 상수 목표의 독립 검증이며 기타복원 runtime feedback 또는 학습을 시작하지 않는다.
