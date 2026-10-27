# Automatic-start 독립 최종 검수

이번 저장 native 초기값/controls/trace/report/closure·source 사본·분석·영상·최종 README/CHANGED_FILES에 한정했다. 이 파일만 작성했으며 물리·actor·solver·분석·봉인 producer를 실행하지 않았다. 이전 phase review와 소비 자료는 보존했다.

- 실제1200 physics steps·300 controls·151 native/capture 표본, 15 runtime checks 참/실패 없음/closure 변경0을 확인했다. PREPARE49개 뒤 PLAY251개, 실제 시작 step196/0.816666667초, 끝 PLAY/중단 없음이다. 진입은 기타 region·25mm·finite/finger/up/front/grip/RHnoncontact가 처음 함께 참인 표본이다. 앞선49행에는 이를 모두 만족한 행이 없다. 임의2초 대기나 손바닥 지속접촉 조건은 사용하지 않았다.
- 시작 거리24.949897817mm, 이전 PREPARE 최소25.211254562mm, PLAY 최소10.766369781mm를 원controls에서 대조했다. 전이 행은 PLAY로 바뀌므로 시작 값이 PREPARE 최소 집계에서 제외된다는 [README:22](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/README.md:22) 설명이 맞다.
- 전체 제어 범위 참103/300은 PREPARE와 PLAY를 합한 값이며 정책 중은57/251이다. source 관측 motor phase는 `[0]`, target hit/physical target hit/accepted release는0, physical release2/miss10/wrong crossing2를 정책 info에서 독립 합산했다. 원본 source10mm/6frame·detector 유지와 외부25mm 연결은 별개다. gate 통과/정책 실행을 타현 성공으로 확대하지 않고, pulse/running 값은 미완료 episode의 부분 결과다.
- 초기 native/81각/PD와 PREPARE 첫49개 최종 목표는 aligned-play와 exact다. 300 requested→float32 phase별 cap/native bounds→최종81목표 재조립, held other36 및 오른쪽30 history 역변환은 exact다. PLAY251개의 현재 관측 마지막30 history는 직전 실제 제출 목표의 저장 source history와 exact이며 source progress가1~251로 증가한다. PREPARE current-G IK는 PLAY 목표와 경쟁하지 않고, 상태 재배치나 기타 외력은 없다.
- 초기 raw 기타 p/q로 최대 위치46.353645732mm/회전46.860685417°와 종료29.535284535mm/45.653963859°를 독립 계산했다. 접근/연결과 기타 범위 유지의 tradeoff를 원자료대로 기록했으며 성공으로 채택하지 않는다. automatic 마지막 전신 native PNG도 직접 확인했다.
- native closure1006개·after 변경0, 사전 source 사본262개를 manifest SHA와 대조했다. analyzer 직접 입력7개 현재 SHA exact/after unchanged, summary SHA는 `40ee6d969015e3b48976476af2ac0736eded58434acd039edc11de75d06dca91`이다. 302 PNG SHA·151 capture readonly와 두 영상의 현재 SHA/실제 ffprobe가 저장 metadata와 exact다:151프레임·30fps·5.033333초, 마지막 sim 표본5.0초다.

[README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/README.md:3)와 [CHANGED_FILES](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_automatic_start_v1/CHANGED_FILES.md:3)의 현재 결과·문서화 범위와 모든 절대 링크를 확인했다. main232/1537은 이 실행의 사전/진행 맥락이며 최종 관측은 위 자료와 구분한다. native source_before의 main 원문은 현재 문서의 exact prefix다. 새 residual 후보의 예상 효과를 이번 성공으로 합치지 않았다.

확인한 최종 문서 SHA: README `e03a5a003fb024d71a6c27df1f4b2b257452ed3c6c02c2e76e2d030ccade0137`, CHANGED_FILES `7964cf0a79c58754ee3433d6f89c702d850f88eb249f607c605e26e9e2c1cbfd`.

Critical/Warning 없음. PASS는 실제 연결 진단의 결과·제어 경계·보존·문서 검수이며 인정 타현·전체 곡·운지·지속 연주·기타 경계 복귀 제어 인증이 아니다.

최종 판정: PASS
