# 손가락4축 유한 압현 도달 진단 v1

승인된 전체 실패진단 계획 단계2~3의 후속이다. 검지 row1/중지 row8의 원 목표를 바꾸지 않고, 정확해진 wrist v3 아래에서 선택4축 목표만 유한하게 탐색한다. source에서 추출한 순간 drive target은 실제 접촉 자세와 같지 않으며, 현재 reference0/4를 장기 RL로 넘기지 않는다. 이번은 정책 학습·성공 모델이 아닌 scripted oracle 진단이다.

유지: 현재 ShortPool/wrist v3,035 reset,고정 기타,2초 ramp/3초 onset/원 음길이/기존 tail,기존 PD·범위·rate·충돌·엄지035·비선택B·보상·종료·접촉/clean/wrong 판정. 실제 상태 덮어쓰기나 기타 강제력은 추가하지 않는다. 활성 package/기존 원문·결과·봉인 수정0, 도구는 이 새 support 폴더에만 둔다. GPU는 root가 하나씩 실행한다. 저장공간 정리 중단 및 진단자료 제외를 유지한다.

1. [ ] CPU 준비 → verify: 기존 ShortPool/make_settings/trajectory_actions/compact_episode/원판정 재사용. MCP x/z 각각 source reference 대비[-10,-5,0,5,10]도, PIP/DIP 각각[-5,0,5]도의 사전 고정 Cartesian225개를 원순서로 나열. 이름 기반 선택4만 변경. native 범위 밖은 사전 명시 제외(조용한 clamp/사후 선택 금지), 중복 검출. 전체표·기준행·제외사유·seed7·settings·입력SHA·실행명령·정해진 trace행 기록. 임의 모델/체크포인트를 생성하거나 과거 checkpoint 검사를 완화하지 않는다.
2. [ ] 별도 CPU code/preparation review → verify: grid/기준행/범위·원천SHA·firstattempt 분모·실패/종료 포함·최대tick·후검증·장면닫기·실행실패 전파. CPU에서 native실행 없는 수학/준비 검사. 상세 자료는 사전 지정 기준행+각축±극값 단독행 최대9개만60Hz; 전체225개는 원 musical ledger와 가벼운 관절/하중/gate 요약. 성공 후 특정원시행 추가기록은 별도 재현 실행으로 구분.
3. [ ] 직렬 GPU 검지/중지 각1회 → verify: 모든 유효 grid행에 env당첫시도1개를 할당하고 실패를 포함. 원 음시각 달성/clean/wrong·물리/손목종료·하중과 gate·동일입력·native장면종료·실제exitcode를 기록. 환경수에 따른 자원사용을 측정하며 장기학습/보상조절로 대체하지 않는다. 범위를 벗어난 행은 실행 분모에 넣지 않고 전체225표에서 제외를 명시.
4. [ ] 실제 자료 재계산/독립 검수 → verify: reference 기준행도 동일 분모에 포함; scripted oracle이며 정책 성과가 아님. 60Hz 순힘은 실제 현압력·접촉쌍·240Hz최대로 해석하지 않는다. endpoint gate와 ledger음전체를 구분.
5. [ ] 사전 지정 분기 → verify: 달성/clean≥70%/wrong≤10%/물리·손목실패0 후보가 있으면, 선택 기준은 squared angle perturbation 최소→최대 변화 최소→grid index 순이다. 새4시도에서 재현하고 힘/자세를 별도로 점검한 뒤 다음 학습 단계로 복귀한다. 없으면 원 gate/actual/target 근거로 경로·손목 위치/방향과 손가락 도달을 분리한다. 임계값 완화·무한 탐색·범위를 좁힌 성공 보고는 금지한다.

이 grid가 실패해도 전체 도달 불가능의 증명은 아니다. 고정 wrist/유한225개/기존2초 경로 조건에서의 결과이며, 성공하더라도 자연스러운 자세/하중·해제·전곡 성능은 별도 미완료다. source native pose 누락 row8은 여전히 미확인으로 남긴다.
