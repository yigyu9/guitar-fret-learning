# 추가 감사기의 올려치기 signed 속도 판정 교정

실제 audit_manual_v3 baseline은19측정 모두통과, repeat는 original_strike_events만실패했다. 실제36events는 내려치기 속도+.1146..+.1294m/s, 올려치기−.1175..−.1241m/s이고 방향/순서/깊이 조건은원core에서통과했다. 추가감사기는 signed across_speed를 항상+.05이상으로검사해 모든올려치기를거부했다. 원native제어 실패나 속도부족으로해석하지않는다.

- [ ] 원manual3/실제manual_repeat_v1 FAIL/75+7검수/입력/로그를보존한다.
- [ ] 새audit_manual_v4는protocol2와모든문턱을그대로유지하고, 타현속도를 direction * across_speed >= .05로검사한다. 올려치기의음의속도를절댓값으로만숨기지않고기록방향과부호의일치를검사한다. 동작/초기자세/힘을바꾸지않는다.
- [ ] 실제36events와반대부호·느림·깊이부족·방향순서변조CPU 반례, 입력사전/사후SHA와독립검수·RootACK후새out에서읽기전용감사한다.
- [ ] 기존75검수는이signed실행분기를실제타현event로검사하지못했다는범위공백을남긴다. v4통과가원실제물리의새실행이나원manual3판정의소급수정은아니다.

다른건강·sourceplane·재접촉·전체연속/재시작미검증과최종채택false는유지한다. Root소유로새버전만작성하며native0/PPO0.
