# 교정 기하 4조건의 실제 128환경 하중 관찰

모든 성공·실패 분모는 각 조건의 첫128시도다. 하중 통계만 최초 실패 endpoint와 이후를 제외한다. pooled p50/p95/max는 유효240Hz endpoint 가중이며 환경별 평균이 아니다. 고정 기타·손목 teacher·다른 손가락 B/엄지035 조건의 진단이다.

| 조건 | 달성/128 | clean 평균 | wrong 평균 | 물리/손목 실패 | 실패로 제외한 endpoint | 원래 평가 전체값 동일 |
|---|---:|---:|---:|---:|---:|---|
| initial_zero | 0 | 0.000000 | 0.000000 | 0 / 0 | 0 | True |
| initial_reference | 108 | 0.851203 | 0.141310 | 0 / 0 | 0 | True |
| cp50_policy | 2 | 0.045551 | 0.059009 | 0 / 0 | 0 | True |
| final300_policy | 127 | 0.992644 | 0.006940 | 0 / 0 | 0 | True |

원래 baseline 평가와의 동일성은 이번 실제 JSON 값 비교 결과이며 반복 실행의 동일성을 보장하지 않는다. 구체적인 차이 수·최대 숫자 차이·경로는 summary.json에 있다.

| 조건 | audible body resultant 중지 p50/p95/max N | 엄지 p50/p95/max N |
|---|---:|---:|
| initial_zero | 0.0000 / 0.0000 / 0.0000 | 16.3693 / 31.1387 / 45.5850 |
| initial_reference | 6.0206 / 9.5876 / 12.0455 | 11.8505 / 17.7307 / 20.7177 |
| cp50_policy | 0.0000 / 4.8935 / 9.4262 | 17.2613 / 21.6182 / 26.8784 |
| final300_policy | 89.6102 / 94.9791 / 100.5516 | 84.1126 / 92.0809 / 102.2836 |

before는 local audible onset 전, audible은 onset≤t≤end, after는 end 뒤다. force_by_phase.csv는 모든 구간의 signed normal 및 resultant p05/p50/p95/min/max를 보존한다. 중지·엄지 signed press normal은 **같은 실제 press-plane world 바깥법선**을 사용한다. 엄지 rear-plane 법선 성분은 별도 열이며 부호 기준을 바꾸어 혼합하지 않는다.

environment_peaks.csv는 모든128환경의 노출 유무·달성/물리/손목 실패·audible 최대 및 안쪽 요청 endpoint span을 담는다. 달성 무실패/미달 무실패/실패 분포는 summary.json에 있다. 노출이 없으면 null로 남기고0N 환경으로 바꾸지 않는다.

| 조건 | point velocity residual RMS / max m/s | 실제 점 속도 RMS m/s |
|---|---:|---:|
| initial_zero | 0.00055264955 / 0.024082409 | 0.15009794 |
| initial_reference | 0.00050658832 / 0.023401691 | 0.13815849 |
| cp50_policy | 0.00057492987 / 0.025602251 | 0.14749318 |
| final300_policy | 0.00064211729 / 0.02464526 | 0.16666777 |

J 투영은 최근접 reward-pad 점의 국소 선형 proxy다. target−q 투영의 음수는 안쪽 목표오차 proxy, Jn·(4×executed action)의 음수는 codec 전 안쪽 요청 속도 proxy다. 실제 목표 clipping·접촉 반력·관절 움직임·penetration을 뜻하지 않는다. velocity 잔차가 속도 규모에 비해 크면 방향 해석을 보류해야 하며, 이 표만으로 native J 정확성을 인증하지 않는다.

candidate/positive의 any-sample witness는 최근접 점과 다를 수 있다. 이 불일치 표본 수를 별도로 기록했으며 최근접 cosine과 candidate를 결합해 같은 점의 접촉을 인증하지 않는다. force는 native body resultant이고 접촉쌍 압력이 아니다. 정책·teacher 손목·엄지035의 단독 인과 기여, 새로운 힘 한계, 자연스러운 저부하 압현 또는 제어 문제 해결을 주장하지 않는다.

그림: summary.png. 수치: force_by_phase.csv / projection_by_phase.csv / environment_peaks.csv / summary.json. verification.json은 원래 평가 분모·시계·동일 실패 endpoint censor·선택 행동·속도 잔차의 독립 재검산 근거다.
