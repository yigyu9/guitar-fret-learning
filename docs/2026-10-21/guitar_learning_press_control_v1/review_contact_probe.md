# N4 원시 접촉 분석 독립 검수

요약 판정: **문제없음**. `contact_probe_analysis.json/.md`를 읽고 실제4개 NPZ를 별도 CPU 계산으로 재집계했다. GPU/native/GL이나 분석main을 실행하지 않았으며 원자료·435동결 소스·이전phase를 수정하지 않았다.

- 실제 report/scene_final의 완료·정상close·1969control/7876physics와582개 입력SHA·4개NPZ SHA가 일치한다. 각 행의 episode/global clock은1..7876이며 총31,504표본이다. 네 첫 에피소드 모두 안전 시간축 완료다.
- raw 현재/직전candidate의 논리곱에 각240Hz 구간과 onset..end 또는 press..end 교집합을 곱해67음 clean/contact_time을 재구성했다. geometry_time과선택 body_load_time도 원장과 재대조했다. 제 독립식 `(clock−1)/240`에서는 원장과 최대 차이0초였고 분석의 약1.14e−13초 차이는 같은 구간 산술의 반올림 범위다.
- 원래40%/최소50ms clean 문턱과 contact 문턱의 bool67개를 모두 재현했다. 성공은 네 환경 모두 검지·canonical3번 현·6프렛의 원장41/52/62/63/64 다섯 음이다. 준비 자세·zero39의 기존 후보 가능성이지 목표로 이동하는 학습 정책의 결과가 아니다.
- selected sample/70→finger body 매핑·지정finger 일치와 raw 몸체 순힘의0.01N load flag를 확인했다. candidate인데 지정finger2/3에 하중이 없는 표본은0개이며 이번 기록의 최근접 선택 body도 같은 결과다. 검지2/3 최대8.5317543/7.4961166N, 나머지8개 기록 finger 몸체의 force는0이다. 이것을 접촉 상대·국소 압력·현 진동으로 해석하지 않는다.
- 검지 press창 합계 geometry7.6276초, candidate4.4347초, clean1.1181초를 네 행에서 재현했다. 선택 body-load는 env0 14.7651초, 나머지15.1870초다. 음별 겹치는 창의 합계이므로 벽시계와 구분한다. shared press 시작을 갖는62/63/64를 독립 새 손동작3회로 세지 않는다.
- 선택점+delta의 새 목표가9.3mm plane에 놓이고 원래 wire보다약3mm 낮음이 raw와 일치한다. 모든 press창에서 plane/선분1mm 근접은0초다. 성공5음의 선택 source sample은 plane보다4.347..4.377mm 위, 목표 선분에서는4.652..4.831mm 떨어져 있다. 따라서 실제 cooked plane에 직접 눌렀거나 새 목표1mm 이내 접촉을 달성했다는 증거가 아니다. 최근접 source sample과 다른 표면의 기존 후보·몸체 순힘을 명확히 구분한 설명이 적절하다.
- `loaded_target_time`은 원래 모든 표면의 qualifying mask가 raw에 없어 독립 재현하지 않고 원장 보고로 구분했다. 다른finger 도달성·감속 보상의 학습 효과·N1024 안전성·압력/음향 성공으로 확대하지 않는다.

최신 CPU 범위도 원문과 실제 retry 로그로 확인했다. 최초 파일별 sweep은141모듈856검사 통과, transition_capture setUpClass SIGFPE(-8)로9개 미실행이다. 대상 모듈의 별도 GDB retry는9개/47.579초/OK/정상inferior 종료다. `cpu_tests.json`은 합산865개 coverage와 첫sweep/단일프로세스 전체 통과false·root_cause_fixed=false를 분리한다. 최초 JSON decode/encode 실패를 보존하며 하나의 깨끗한865개 전체실행이나 FP 근본 해결로 주장하지 않아 해석에 문제없다.

검수 대상 SHA256:

- 분석 JSON: `7ae3c3493a3b460dd47f2a024dd0c1e6fb7eea6bb4e435b73a9b4b4d8da67ec1`
- 분석 Markdown: `3ba0061b5533031d027ee84c95075a8e18d3644de3f8f2f07264c232f1af8b6c`

Critical/Warning: 없음. 이 검수에서는 새 `review_contact_probe.md`만 작성했다. 기존 `review_preflight.md`는 변경하지 않았다.
