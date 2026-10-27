# 최종 보정 뒤 정지5초를 포함한 절대시간 검증 일정

## 보완 이유와 보존

Body9 후보 baseline_v5는 실제28초/6720step의 core28·발전행·영상검사를 통과했다. 다만 원52초 continuous 일정은 준비5..10초 뒤 Body9/preload가10..10.5초에 전환되고 첫타현10..14초와 겹친다. 보정 전 정지5초와 별도baseline의 보정 후정지는 유효하지만, 같은 실행에서 **최종보정완료→정지5초→타현** 순서를 증명하지 못한다. 독립검수도 이 범위 부족을 확인했다.

diagnose_baseline_body9_v1/summary.json SHA e90f9cd82712679e7a3d8324f93e2d902f3c7981f8040c1b5d3ff5c250f613a3: allaction 삼중지지4259/4321=98.5651469567%, 가슴누락62개는 전부10..10.5초전환이며 그뒤28초까지100%였다. 가장긴가슴λ0구간은2448..2505step(10.2..10.4375초)58표본이다. R상완/R_Hip는4321/4321양성. source형상/FK를재실행하지않은실제접촉집계이며 미래타현성공/실패보장이아니다. 소비한v1 protocol/cfg/기록/성공범위는수정하지않는다. 진행중이던repeat_v5는22초정상완료했고판정중이다. 새후속v5 action실험은진행하지않는다.

## 새 절대시간 일정

protocol_v2.PROTOCOL='front_initial_pose_ready_full_cycle_v2_settled_hold5'. 모든case는 기존0..10초준비와10..10.5초Body9/Chest preload를그대로둔다. **11..16초5초 settled_ready_hold**를명시한다. baseline은28초그대로이며 나머지실제손동작과끝시각만기존일정보다6초늦춘다. 실제physics step/time/동작길이/경로/속도를바꾸거나숨은clock offset을넣지않는다.

|case|끝초|R왕복시작초|LH해제|완전해제15초|접근|닫기|재접촉유지5초|
|---|---:|---|---|---|---|---|---|
|baseline|28|없음|없음|없음|없음|없음|없음|
|repeat|28|16,20,24|없음|없음|없음|없음|없음|
|release|34|없음|16..19|19..34|없음|없음|없음|
|free_strike|34|21,25,29|16..19|19..34|없음|없음|없음|
|regrasp|42|없음|16..19|19..34|34..36|36..37|37..42|
|continuous|58|16,20,24,33,37,41,54|28..31|31..46|46..48|48..49|49..54|

## 최소 구현

- [ ] 새protocol_v2는위명시표/hold상수만정의하며원참조/geometry/taskchain을재사용한다. 새cfg는원inputs_body9_pose_v1에서 validation_protocol/seconds/ready_schedule/ready_baseline_summary와추가 ready_settled_hold_s=[11,16]만변경한다. Body9정밀9/기존Chest+.005/10mm가상목표/모든gain·cap/원105초기/기타/큐브/모델/충돌정책을바꾸지않는다.
- [ ] runtime_v5는Scene를원runtime_v4.Scene로재사용하고Controller는원runtime_v2.Controller를상속한다. 원runtime_v1.Controller.__init__의PROTOCOL/schedule와원motion_v1.schedule만생성자동안새protocol_v2값으로명시patch해원Motion의self.plan을새절대일정으로구성한다. 생성자종료/예외에도세global원객체가복구되고실제상태가보존됨을검사한다. 실제effort/targets/Motion.apply/SO3/Foot/Body9/Chest 구현은상속그대로다. Motion 실제class는motion_v1.Motion,Scene실제class는runtime_v4.Scene로기록한다.
- [ ] run_v7은새protocol/Controller5와동일새후보baseline_v6·core/발/원자료SHA를확인한다. 원ready_spec와preflight는초기geometry/원경로·축범위근거로재사용하며spec.schedules는원protocol_v1 표와대조한다. 새실제일정은protocol_v2/새cfg로별도검증하고원preflight가새타이밍의물리성공을인증한다고설명하지않는다.
- [ ] analyze_v6는원analyze5의모든28/29기준·first10·전N수학·목표ownership·LH/RH·근위실제1도·삼중95%·몸통5도·실제손source2mm/raw0·재접촉5초를유지한다. 새settled_ready_hold5를추가AND한다: 실제11..16초1201상태/301개60Hz목표,양끝정확5초,모든손동작시작≥16,Body9/Chest ramp완료후상수,각LH26/R12유지목표가원latch와동일하고명령소유권/단계가맞음.16초첫stroke경계는boundary hold여야한다. hold의삼중/발/pose는별도window로원문턱을적용한다. 숨은시간재해석/새tolerance/기준완화없다.
- [ ] feet_audit_v2/media_audit_v2는새절대일정/길이를명시import하고원발전행/영상수학·문턱을유지한다. foot window에11..16도추가한다. readiness_v1.evaluate는절대strike_starts인자를사용하므로원수식재사용하며CLI의구일정으로실행하지않는다.
- [ ] 문법/실제생성자본문adapter+원global복원·예외복원/새일정전case·hold경계·길이/기존목표helper·원28gate보존·숨은offset변조거부CPU와독립검수완료/SHA를RootACK한다. 기존v5실제후처리완료전새package파일을발행하지않는다. CPU/fixture실패원문은새버전별로보존하고JSON직렬화전에numpy scalar를builtin형으로변환한다.
- [ ] Root새prepare_settled_hold_v1/execute_v6/execution_inputs_v8를동결하고모든기존code/leaf/config/native/실패/검수/CPU/model106+manifest2를사전후보존한다. 새inputs_settled_hold_v1와native/analysis/feet/media_<case>_v6에저장한다. baseline28→repeat28→release34→free_strike34→regrasp42→continuous58을각core+발통과뒤순차검증한다. 실패자료보존/진단우선,새PPO0.
- [ ] 최종한국어자료는기존52초미실행과새58초실제의구분,보정후정지5초,필수접촉/왼손해제15초/엘보손목타현/넥재접촉/같은실행연속을보고한다. Root고정·하체16유한/원zero8·Gfree중력ONstrapOFF·G힘0/부착0/매step상태주입0를유지한다. 현은기하통과이며힘/진동/음향인증아니다.

소유권: 구현담당protocol_v2.py/runtime_v5.py/run_v7.py와자기CPU,분석담당analyze_v6.py/feet_audit_v2.py/media_audit_v2.py와자기CPU,Root설정/외부wrapper/closure/main문서/최종보존,reviewer검수만. 다른담당작업/소비자료를되돌리지않는다. 사용자자율실험승인범위에서필수순서를정확히검증하는보완이다.
