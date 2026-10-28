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

각 조건은 첫128시도·111,616개 물리 endpoint·27,904개 control 관찰이다. 모든 런의 launcher exit0, scene closed, source/model/RNG/업데이트 불변 감사와 rate/box/halfspace 검사를 확인했다. 원본의 전체 배열·원장·평가값 재현과 세 조건 첫480 endpoint는 실제 exact 비교 결과이며 일반적 결정론 보장은 아니다.

| 조건 | audible 중지 press-normal p50/p95 N | 엄지 press-normal p50/p95 N | 엄지 rear-normal p50/p95 N |
|---|---:|---:|---:|
|original|89.61 / 94.972|-45.879 / -36.63|45.879 / 51.869|
|no_new_inward|30.228 / 34.28|-18.268 / -15.607|18.268 / 20.081|
|no_new_inward_and_relax|0 / 4.4972|-10.621 / -2.2193|10.621 / 16.105|

중지와 엄지 press-normal은 같은 실제 press-plane 바깥법선을 기준으로 한다. 엄지 rear-normal은 반대 후면 바깥법선 기준이며 두 부호를 합쳐 쓰지 않는다. 힘 표는 물리 endpoint 가중이며 환경별 peak 평균이 아니다.

| 조건 | 2초 후 gate/전체control | 실제 target 변경/gate | audible gate/1024 | audible box/rate 경계 좌표 |
|---|---:|---:|---:|---:|
|original|12544/12544|0/12544|1024/1024|2048 / 0|
|no_new_inward|12544/12544|12544/12544|1024/1024|0 / 0|
|no_new_inward_and_relax|5347/12544|5347/5347|408/1024|132 / 132|

gate는 첫120 control 뒤 signed press-normal resultant>0.01N인 유효 행이다. 세 조건 모두 stale reset128행 외 prior failure/invalid state/J=0행이며, 유효 gate의 zero J도0이다. 경계 수는4축 좌표 기준(음 구간4096좌표)이고 native/action/rate 교집합 box다. native 단독 한계 체류와 같다고 주장하지 않는다.

| 조건 | audible 고정Jn·기존 target−q p50 mm | 최종 target−q p50 mm | raw/filtered 증분 p50 mm/control | 접선 변경 p50/p95/max mm/control |
|---|---:|---:|---:|---:|
|original|-55.066|-55.381|-0.31318 / -0.31318|0 / 0 / 0|
|no_new_inward|-22.269|-22.269|-1.9033 / 7.7518e-08|0.7187 / 0.7686 / 0.795|
|no_new_inward_and_relax|-2.7999|2.1501e-08|-2.1234 / 2.7999|1.3562 / 6.4273 / 8.6151|

위 표는 gate true인 control만 비교한다(original/A1024, relax408). 고정점의 순간 J를 큰 관절오차에 곱한 선형 외삽이며 실제 침투 mm가 아니다. A는 새 법선 증분을 numerical tolerance 안에서0으로 바꾸지만 기존 target−q 법선오차는 남는다. relax의 gate 없는616 control에 저장된0을 오차0으로 포함하지 않았다. 접선 변경도 분명히 존재한다.

| 조건 | audible 실제/예측 속도 잔차 RMS m/s | 실제 속도 RMS m/s | 잔차/실제 RMS % | original 대비 팔12 요청차 norm p50 rad | 손목 위치/회전오차 p50 m/rad |
|---|---:|---:|---:|---:|---:|
|original|0.0003568447|0.07334123|0.4866|0|0.011101 / 0.083853|
|no_new_inward|8.744731e-05|0.04030785|0.2169|0.43031|0.016153 / 0.034963|
|no_new_inward_and_relax|7.818862e-05|0.0335837|0.2328|0.48095|0.023572 / 0.13978|

속도 잔차는 유효 고정점에서 확인했으며 큰 target−q의 선형 외삽 정확도를 보장하지 않는다. 팔12 요청차는 같은 env/clock의 original과 비교한 유클리드 norm이고 실제 팔 관절각 차이가 아니다. 첫2초 이후 wrist feedback 혼입이 있으므로 중지 target override만의 고립된 효과로 확대할 수 없다.

| 조건 | 전체128 평균 최초 접촉 / 유지 / 달성 지급 |
|---|---:|
|original|0.250000 / 0.992644 / 0.248047|
|no_new_inward|0.250000 / 1.000000 / 0.250000|
|no_new_inward_and_relax|0.000507 / 0.000000 / 0.000000|

추가 안쪽 증분 억제는 이번 finite tape에서 원래 성공을 유지하며 관측 하중을 낮췄다. 음 종료 뒤에도 중지 합력 중앙값35.88N이 남으므로 저부하 제어 해결로 선언하지 않는다. 유한 누적오차 완화 조건은 하중은 더 낮지만 달성0/128이므로 같은 방식의 성공 해법 근거가 아니다. 성공한 A의 한 번 실험을 정책학습 성과나 일반 controller 채택으로 확대하지 않는다.

force_by_phase.csv는 실제 guitar pose에서 재계산한 press/rear signed normal을 포함한다. pooled240Hz 하중은 실패 endpoint부터 제외하며 모든128 성공·실패 분모는 유지했다. environment_peaks.csv는 노출 없는 환경도 null로 보존한다.

control_by_phase.csv/summary.json은 시작 clock 기준60Hz의 gate/skip/개입 수, box·rate 경계, 고정Jn 오차·증분·접선 변경·속도잔차, original 대비 팔 teacher 요청과 손목오차다. 실패로 끝난 control은 전체를 보수적으로 제외했다. gate 꺼짐의 저장0을 실제0오차로 평균하지 않는다. 구간별 gate 노출이 서로 달라 조건부 통계의 분모도 다르다.

reward_payments.csv는 원래9보상 실제 지급이다. increment 합·최종 cumulative·episode·음 원장과 대조했다. 원래 성공/보상은 새 하중 목표나 힘 상한 판정으로 재정의하지 않았다.

body resultant는 접촉쌍 압력이 아니다. 고정 material point는 any-candidate witness와 다를 수 있다. Jn·큰 target−q는 국소 선형 외삽이며 침투깊이가 아니다. 실제/예측 점속도 잔차와 실제 속도를 함께 검토해야 하며 큰 잔차 구간의 방향 해석은 보류한다. 접선 보존을 보장하지 않고 이후 팔 teacher feedback도 달라진다. 이는 finite tape 진단이며 새 정책 성과·정책 단독 인과·저부하 제어 해결·일반 controller 채택을 증명하지 않는다.

summary.png는 작은 개요이며 원본 재현/prefix/실패·gate 분모와 원래 지급 근거는 summary.json 및 verification.json을 함께 확인한다.
