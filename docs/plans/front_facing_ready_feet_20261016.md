# 초기 자세의 전체 동작 구간 발 접지·미끄러짐 검사

새 source producer/물리 실행 전 추가 계획이다. 원 controller·초기값·하체16축 유한 gain/cap·영범위8축·큐브·기타 조건·core 분석기의28개 gate는 바꾸지 않는다. 기존 `sole_summary`가 마지막1초만 검사하므로 중간에 발이 움직였다 돌아오는 경우를 놓칠 수 있어, 독립 `feet_audit_v1`을 새 필수 AND 판정으로 추가한다.

- [ ] 준비5..10초, 준비 후 전체5..T초, 전체동작10..T초와 release/free/approach/close/dwell/각4초타현창의 모든240Hz 실제 표본을 확인한다.
- [ ] 네 발 부위(L/R Ankle/Toe)의 정규화 native body pose와 원 XML 발바닥 box로 계산한 원 기준을 그대로 적용한다: 전체 아래쪽4점 높이 −1..+3mm, 발바닥 기울기2도 이하, body origin xyz peak-to-peak의 norm3mm 이하, body origin 선속도.02m/s 이하, 각속도.2rad/s 이하. 각창의 원 양발 양성 접촉95%도 유지한다.
- [ ] 전체 raw state/contact 행 수와 step/time 연속성을 검사한다. Native COM 선속도와 body origin 선속도를 구분하고, source box 간격을 PhysX cooked 형상 clearance로 부르지 않는다.
- [ ] 중간 미끄러짐 뒤 복귀 및 중간 높이 이탈을 거부하는 CPU 검사를 수행하고, 새 파일을 동결·독립 검수한 뒤 실행 전에 소스·helper·계획·원XML/모든mesh를 pin한다.
- [ ] 각 native 실행의 core 분석과 발 전행 검사 모두 통과해야 다음 물리 단계로 진행한다. 마지막1초의 기존 판정과 전행 판정을 각각 남긴다. 이 추가 검사를 core28개 gate가 이미 포함했다고 소급 설명하지 않는다.

측정 한계: 이는 Root 고정 조건의 양발 지지·원 source box 자세/움직임 검사다. Root 자유 균형, 지면 압력 분포, 연속시간 무관통을 인증하지 않는다. 새 물리 적분은 아직0회이며 결과를 보고 문턱을 고친 것이 아니다.
