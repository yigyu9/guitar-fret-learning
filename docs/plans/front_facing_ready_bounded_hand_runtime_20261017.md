# 유한 손 유지 제어의 command 좌표 범위 보완

## 근거

실제native9의첫새명령3844에서desiredfit는통과했으나desired−e16 명령2축이원범위를초과해제출전중단했다. 원실패를그대로보존했다. 독립검수·RootACK후새readonly bounded IK 진단에서두seed모두첫3844와oldbaseline8/repeat8 각719controlgrid를통과했다(총1438시각×2+첫2=2878실제IK평가). 새source/물리실행0이며동적성공아니다.

## 최소 보완

- 새Motion3은Motion2상속,Controller10은9상속,Scene8 alias. oldhandmode·thumb−.1·기존모든gain/cap/foot/RH/기타/초기배치는유지한다.
- 추가cfg3keys: ready_hand_bias_bounds_mode=`finite_desired_actual_intersect_command_bounds_held_plus_e16_v1`; ready_hand_bias_bounds_diagnostic=검증된result경로; ready_hand_bias_bounds_diagnostic_sha256=8e678b16e461cc97245322ca1497e95f757e16801b855687f68674b496b853c7.
- gripped 비경계에서만desiredactual허용범위를원범위∩(원command범위+e16)∩(command qref±.8+e16)로구성한다. 원solver의1e−6내부여유/desired qref범위를유지하며bounds사본만전달한다. mappedseed=held+e16,최적화초기값투영만기록하고최종명령clip을하지않는다.
- 원solve_left 본문/codeobject·원solve_wrist수학을그대로실행한다. raw64증거는copiedglobals observer로받고globalpatch는motion2.solve_left한개로제한한다. 정상·예외binding/native상태복원을검사한다.
- 16초까지모든rowliteral유지,다른phase arm/RH/finger/foot원문유지. 이후hm.bias_bounds는적용/호출수/원·변환·effective범위/held→mapped→optimizerseed/desired64·F32/commandraw·F32/실제불변증거를기록한다. oldparent중간과새실제요청scope를계속구분한다.
- 새coreAnalyzer10은독립식으로증거를검사하고core29/30·원수치기준은유지한다. Root정규경로는새inputs_maintenance_v3/native_*_v10/analysis_*_v10/run11/execute14로분리한다. source5/remaining6/manual8/health5/fretting3/hold1을원수학그대로연결한다.

## 진행 기준

- [x] readonly첫3844+두719grid 실제IK통과·입력불변.
- [ ] Motion3/runtime10 및독립analyzer/Root연결CPU·독립FINAL·RootACK.
- [ ] 새baseline28초에서11..16 및보정완료후17..22정지5초/전기간source·feet·health·압현준비를검증.
- [ ] 통과뒤repeat→release→free_strike→regrasp와같은실행연속동작·fresh재시작.

기존native9는16.0167초실패로남기고wrapper요청28초를실제경과로집계하지않는다. 새runner는요청초와실제report경과초를구분해기록한다. 원EPS0잔차/solver원인False/최종채택False·선택현힘미검증·fullfingerFK진단도계속보존한다. 새PPO0.
