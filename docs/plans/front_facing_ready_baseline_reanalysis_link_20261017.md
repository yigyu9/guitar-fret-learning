# 재감사된 baseline과 새 동작 실행의 명시적 연결

기존 cfg83개 항목은물리baseline10에소비되어그대로보존한다. ready_baseline_summary는원analysis10실패경로를가리키므로이를고쳐쓰지않는다. 대신새runner13의명시CLI --baseline-summary는별도analysis_baseline_v10_retry_v1을선택한다. baseline_reanalysis_link_v1.json에원실패/새재감사SHA·동일raw11·동일cfg·독립검수/RootACK/외부결과를고정해이전실패가성공으로덮어써졌다고해석하지않도록한다.

1. run13은원초기화/Scene8/Controller10/Motion3/PD·gain/cap/모든물리설정을유지한다. action에만명시재감사인자를요구하고원선언anchor와링크·원단일실패gate·새29PASS·동일raw/config·실제완료6720step을확인한다.
2. Root17은기존baseline10재실행을차단하고모든baseline10필수후처리의AND를확인한뒤repeat→release→free_strike→regrasp를순서대로허용한다. case/native출력은원계획의미실행v10경로/설정v3을사용한다. action의core는교정analyzer11,부가검사는기소비검수된source5/remaining6/manual8/health5/fretting3/feet4/media3/hold1을유지한다.
3. baseline native외부는기존before11,baseline후처리는before12,새action은before13의실제기록을검사한다. baseline analysis command/외부tag만retry_v1이며원core실패는보존한다. 모든기존summary/log/rootbefore/RAW11+cfg+specSHA연결을유지한다.
4. 실제스키마로guard/CLI/Root기록CPU·독립FINAL/SHA·RootACK후main. 전체baseline감사나직전action이하나라도실패하면새native금지한다. 준비/중단/실패/연속15초를실제절대시각그대로기록한다.

- [x] 동일raw11/config의별도재감사link고정.
- [ ] run13/Root17 최소연결·실제CPU·독립검수·RootACK.
- [ ] baseline10모든감사PASS후repeat실제타현.
- [ ] 통과후15초해제/해제타현/재파지,그뒤연속동작과fresh재시작별도검증.

이연결은새게인/물리학습/기타힘·부착·상태주입을추가하지않는다. 원미세limit잔차·solver원인미확정/최종채택False를유지한다.
