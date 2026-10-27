# 독립 native 검수 — 왼손 넥 주변 초기 배치와 양손 연결

요약 판정: **기록·제어 검수 문제없음. Critical 0 / Warning 3 / Suggestion 0.** 준비 추종의 근접 개선은 관측되었으나 양손 연주 성공은 아니다. 최종 문서·그림·아카이브·봉인은 이번 검수 범위 밖이며 후속 검수 대상이다.

| 조건 | 실제 physics/control | 종료 | 기타 BB 중심 최종 변화 / SO3 |
|---|---:|---|---:|
| 원 왼 POSITION hold1 | 1200/300, 5초 | 실행 완주, 왼 근접 유지 실패 | 8.035335mm / 4.723874° |
| 원 K/D 외부 PD hold2 | 440/110, 1.833333초 | 속도 안전 중단 | 5.551465mm / 6.192399° |
| mirrored gain hold3 | 1200/300, 5초 | 실행 완주, 왼 근접 유지 실패 | 9.249565mm / 2.831515° |
| wrist 추종 hold4 | 1200/300, 5초 | 실행 완주 | 9.295643mm / 2.834565° |
| 추종 PREP 뒤 pair | 584/146, 2.433333초 | Strike 첫 source terminal | 33.064722mm / 11.217194° |

5조건의 전체 초기 native state를 직접 대조하여 JSON exact를 확인했다. hold4/pair의 PD 및 기타 property JSON도 exact다. 초기 actual source LP/FK/면 proxy·고정48·기타 fullstate·선언된 왼 모드 변경·mass gate는 통과했다. POSITION hold1과 EFFORT 조건의 PD 자체는 같다는 뜻이 아니다.

실제 제어 검증:

- hold4의1200개 및 pair의584개 오른·왼·tracking 행에서 scalar PD, 오른 상완 가상 힘/Jᵀ, 왼 tracking `1000e+30v`, norm cap30N, Jᵀ 합산 및 최종 float32 effort clip을 독립 재계산했다. actual81 clip 오차0, 오른 합산 요청 오차 최대1.78e−15Nm였다. 57개 effort0·finite·모델 cap 및300/146개 POSITION57/state 검사도 통과했다. 중력값은 저장된 중력항을 사용했으며 전체 native Jacobian tensor/중력 모델의 독립 인증은 아니다.
- 현재G에 대한 목표 위치·속도 재계산 오차는 ≤1.11e−16m/≤8.33e−17m/s였다. J*qdot와 native 손목 속도 오차 최대는 hold4 .000285560m/s, pair .005594840m/s로 .01m/s guard 안이었다.
- pair는 첫480 tracking 행과2초까지 trace가 hold4와 exact였다. step480부터 task enabled false/force0이며26회 양손 actor 추론으로 넘어갔다.146개 action→model/rate target codec도 직접 exact 대조했다. 원 firstdone 규칙·단일81 제출·4 physics/control·금지API0을 유지했다.
- hold2 마지막 L_Elbow_y 속도는 −100.095276rad/s였다. 원 속도50rad/s guard가 중단한 실패와 부분 영상을 보존했다. 5초 완주로 집계하지 않는다.

관측 및 판정:

- hold4 손목 추종 오차는 최종17.000477mm/최대17.018194mm다. 최종 실제 trace에서 palm signed gap31.537460mm/점오차30.592109mm, thumb gap3.362851mm였다. 앞 네 손가락 gap14.447827/17.490221/17.448165/13.586568mm다. 5/8mm 목표를 모두 달성했다는 뜻은 아니다. endpoint1200개에서 왼팔·손–기타 접촉0, 상완1190, Head/오른 distal0이었다.
- pair의 종료는 Strike wrong_crossing_count_termination이다. Fret done/wrist_safety/finger_back false, physical press0이었다. source 결과를26 PLAY tick보다 긴 안전 성공으로 확대하지 않는다. 공동 판정은 resolved event2개 모두 joint_success false, crossing4개다. 원 Strike wrong count1과 공동 crossing4는 서로 다른 detector 집계다.
- 공식 [analysis3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/native_analysis_v3.json:1)의 입력3347개 현재 SHA를 대조해 변경0을 확인했다. [producer3](/home/ajou/yigyu/3/stability_adapter_2/analyze_left_neck_near_v3.py:25)는 계약의 외부 config/candidate/reference와 tab2body Python 의존성을 포함하고 tracking 목표/속도/force 수식을 검증한다. root의 CPU actor replay 결과는 양쪽26회/action error0이며 코드·저장 결과를 검토했다. reviewer는 추가 actor 추론을 실행하지 않았다. 이전 분석 소스/출력은 보존된 별도 버전이다.

Warning 1 — 면 signed gap은 선택 source facet proxy이고 wrist 한 점 위치 추종은 방향/6면 정확 배치 인증이 아니다. endpoint 무접촉은 모든 solver 내부 시각의 cooked 비접촉·해부학적 pad 인증으로 확대하지 않는다. 가상30N/10N은 측정 접촉힘이나 기타에 직접 적용한 힘이 아니다.

Warning 2 — 정지5초와 pair2.433333초를 구분한다. task OFF·양손 target 변경이 함께 발생하므로 이후 변화의 단독 인과 효과는 확정하지 않는다. pair는 조기 실패로 검열됐으며 곡 완주·full Fret/Strike 안전·연주 성공을 주장할 수 없다. MP4는 hold 완주151frame/5.033333초, 안전중단56frame/1.866667초, pair74frame/2.466667초(모두30fps)로 physics 시간과 다르다.

Warning 3 — source1/2는 후보 출력 전 CPU 중단이다. source3/4/5의 완료 rows는 총6개 중 거절5/수락1이다. '거절6+수락1'로 집계하면 안 된다. accepted source5 station20mm와 source_clear이나 지정면 미달로 거절한 station60mm를 구분한다. native는 시도5개 중 실행 report completed4/속도 중단1이고, 완료4가 음악 성공4라는 뜻은 아니다.

이 검수는 새 source/제어 코드와 저장 native5조건·분석3·현재 입력 SHA에 한정했다. 광범위한 과거 봉인 재감사는 하지 않았고 새 native/학습/추론/원본 수정은 없었다.

검수 SHA256:

- producer3: `e0a57e192d93cadcd93de3387d4066ab517aaa218c8af6b28ebe6593caa410f8`
- analysis3: `7b13a49fa4d3d988a8f390b605b4acd3debcbec10889eb20edcdaa837b79d674`
- hold4 report: `b67f1b1ac9410495591455f22bb82a054a8445ba606ed342c510c43320b65a38`
- pair report: `1ec17e93a850826ef46112c0ed9836527bea87158c02ee3706cc18eda2aaaeed`
- pair tracking rows: `55d4730cd1c7239cee5eaa82be8215f8a3efa21f9a147a1463db134f43014429`
