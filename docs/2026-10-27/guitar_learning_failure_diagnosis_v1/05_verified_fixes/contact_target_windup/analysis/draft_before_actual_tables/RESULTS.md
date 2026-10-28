# 고정 중지4 tape target 누적 진단

matched 비교 전제: **충족**. 원본 전체 재현과 세 조건 첫480 물리 상태/관찰 필드 exact가 필요하다. 미충족 시 수치는 기술 통계로만 읽고 개입 효과 해석을 보류한다.

| 조건 | 달성/128 | clean/wrong 평균 | 물리/손목 실패 | 실패 제외 endpoint |
|---|---:|---:|---:|---:|
|original|127|0.992644 / 0.006940|0 / 0|0|
|no_new_inward|128|1.000000 / 0.000000|0 / 0|0|
|no_new_inward_and_relax|0|0.000000 / 0.400051|0 / 0|0|

| 조건/구간 | 중지 resultant p50/p95/max N | 엄지 resultant p50/p95/max N |
|---|---:|---:|
|original/audible|89.6102 / 94.9791 / 100.5516|84.1126 / 92.0809 / 102.2836|
|original/after|95.3485 / 103.3956 / 122.6204|88.5225 / 98.1996 / 108.9203|
|no_new_inward/audible|30.2280 / 34.2799 / 39.0267|29.5781 / 34.3685 / 37.1047|
|no_new_inward/after|35.8826 / 41.2740 / 45.0140|32.5723 / 42.2986 / 48.6484|
|no_new_inward_and_relax/audible|0.0000 / 4.7730 / 18.9679|16.0125 / 23.9987 / 31.7510|
|no_new_inward_and_relax/after|0.9339 / 6.4003 / 42.3154|10.9501 / 26.0754 / 96.3162|

force_by_phase.csv는 실제 guitar pose에서 재계산한 press/rear signed normal을 포함한다. pooled240Hz 하중은 실패 endpoint부터 제외하며 모든128 성공·실패 분모는 유지했다. environment_peaks.csv는 노출 없는 환경도 null로 보존한다.

control_by_phase.csv/summary.json은 시작 clock 기준60Hz의 gate/skip/개입 수, box·rate 경계, 고정Jn 오차·증분·접선 변경·속도잔차, original 대비 팔 teacher 요청과 손목오차다. 실패로 끝난 control은 전체를 보수적으로 제외했다. gate 꺼짐의 저장0을 실제0오차로 평균하지 않는다. 구간별 gate 노출이 서로 달라 조건부 통계의 분모도 다르다.

reward_payments.csv는 원래9보상 실제 지급이다. increment 합·최종 cumulative·episode·음 원장과 대조했다. 원래 성공/보상은 새 하중 목표나 힘 상한 판정으로 재정의하지 않았다.

body resultant는 접촉쌍 압력이 아니다. 고정 material point는 any-candidate witness와 다를 수 있다. Jn·큰 target−q는 국소 선형 외삽이며 침투깊이가 아니다. 실제/예측 점속도 잔차와 실제 속도를 함께 검토해야 하며 큰 잔차 구간의 방향 해석은 보류한다. 접선 보존을 보장하지 않고 이후 팔 teacher feedback도 달라진다. 이는 finite tape 진단이며 새 정책 성과·정책 단독 인과·저부하 제어 해결·일반 controller 채택을 증명하지 않는다.

summary.png는 작은 개요이며 원본 재현/prefix/실패·gate 분모와 원래 지급 근거는 summary.json 및 verification.json을 함께 확인한다.
