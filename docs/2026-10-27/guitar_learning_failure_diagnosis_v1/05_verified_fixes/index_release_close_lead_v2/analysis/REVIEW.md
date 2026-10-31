# V2 결과 분석 독립검수

2026-10-28 **PASS**, actionable finding 없음. 분석코드와 원 JSON/NPZ를 읽기전용으로 대조했으며 GPU/native 실행0. `review.json`은 원입력60개와 최종 분석코드·JSON·문서·세 그래프의 SHA를 기록한다. 원입력 전후 SHA 및 현재 바이트가 모두 일치한다. 최종 `analyze.py` SHA는 worker가 보고한 `70b2ce85b172d1338ba57cfbeaee2a781a5a97404c354a8286edbb8f6aa4665c`와 같다.

원128개 고유env episode와384음 전체 분모를 직접 확인했다. 네 조건의 all3는 baseline128, V1후보121, V2결정론124, V2잡음34이고 V2 A해제는 결정론128/128·잡음102/128이다. 결정론 stage_ready=true와 잡음 stage_ready=false가 원 acceptance 및 episode 개수와 일치한다. 음별 달성·해제·동시달성, clean/wrong/missing 평균, reward/cost 총합과9개 보상항 합을 원 episode에서 별도 재계산했다. 원 report의 completed/closed/128attempts/noNN과 inputs_after verified·변경입력/미핀소스 없음도 확인했다.

각 조건의 env0..3 표면232행이 모두 valid·post_failure 아님을 확인했다. 세 시간창의 행수·signed-height 최소·5mm 충족행·loaded/candidate 수를 NPZ에서 별도 계산해 모두 일치했다. V2결정론 공통phase3 최소3.178095mm,5mm충족80/104는 원값이며5mm 전체충족이라고 확대하지 않았다. onset 전후 실제 q/target 각도도 원trace와 일치한다. 표면4환경 및 env0 대표 추종을128환경 전체 기하로 일반화하지 않은 문서 범위가 적절하다.

과거/현재 저장 env0..3 scaled_noise 배열과 전체stream SHA의 동일성을 확인했다. 결정론 대비 noisy decoded-goal RMS, 음별 실패와 A미해제 교차, env0 actual-target/decoded-goal RMS를 독립 재계산했다. 무차원 latent sigma와 실현 각도차를 구분하고, 과거잡음대비32개 증분을 closing lead 단독 인과효과로 해석하지 않은 점을 확인했다. 다음 MCP성분 분리검증은 제안이며 이 분석에서 실행하지 않았다.

세 그래프를 실제 렌더링하여 축·범례·조건·창 표시를 확인했다. 범례가 일부 곡선/막대 위에 있으나 수치를 오독하게 하는 결함은 없었다. 재사용 baseline을 새 native 실행으로 세지 않았고 고정기타·검지3음·원seed/잡음조건 한정이라는 한계를 문서가 유지한다. 실제 native video는 별도 검수 대상이며 이 분석 PASS에 포함하지 않는다.
