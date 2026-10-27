# 가슴의 양성 지지 유지 여유를 확인하는 작은 후보

기존 native_baseline_v1의28초 정지 유지와 발전행 검사는 통과했다. native_repeat_v2는 실제22초/5280step을 완료했고 세 왕복 모두6→1/1→6, 양측 실제준비, 근위1도, 발 접지/전행 자세, 전체 제어수학을 통과했다. 다만 두 번째 왕복14..18초의Chest+R상완+Hip 동시 양성 지지는906/961=94.276795%로 원95% 기준에 실패했다. 첫/세 번째는952/961와961/961이었다. 원판정과 실패 자료는 보존한다.

진단에서 R상완과R_Hip의 지지는 전행 유지됐고, Chest의 원시 접촉도 계속 존재했다. 실패 표본은 rawcontact 부재가 아니라 양성lambda가 없는 경우다. 가상Chest명령은 약19N으로 지속됐으며20N포화/Chest9관절cap/목표변경/제어중단이 없었다. Source gap은 계속 약−.22mm였으므로 그 부호로 cooked 지지를 대신 판정할 수 없다. 접선drift도 단독 원인으로 확정하지 못했다. 따라서 아래 추가 여유는 해법이 증명된 설정이 아니라 하나의 작은 가설 시험이다.

- [ ] 새 Controller runtime_v2는 기존.5mm Chest action과 오른말단SO3를 그대로 계산한 뒤 Chest9(Torso/Spine/Chest)에만 가상 목표깊이.25mm를 추가한다.10..10.5초 원smoothstep을 사용한다. 기존9.25+.5+.25=10mm는 source 기반 가상 human 목표이며 실제 침투량이나 측정 접촉력이 아니다.
- [ ] K2000/D30/법선cap20N 및 모든 관절cap·105목표·원초기형상·충돌필터·하체16유한제어·영범위8축을 유지한다. 기존 현재Chest raw에서 K×새깊이를 뺀 뒤 같은unilateral[-20,0]으로 다시clip한 force 차이만 원actualJ9 transpose로 human effort에 더한다. cap된 힘에 단순.5N을 가산하지 않는다. Upper33 원cap/float32를 재적용하고 Chest9 밖/하체/POS48/zero8/state/target 불변을 검사한다. 기타 힘/고정/부착/상태주입/PPO는 없다.
- [ ] 새 metadata에 직전 aggregate/Chest record를 보존한다. 새 독립 math를 모든N행에서 확인하고 margin→SO3→원Chest action→원base 순서로 복원한 뒤 기존 모든 제어식과 수치 판정을 유지한다. 원실패를 숨기는 길이/수치 조건 삭제는 금지한다.
- [ ] cfg는기존V1을보존하고 inputs_margin_v1에복사한다. 새3필드 mode='finite_human_Chest_extra0p25mm_v1',extra=.00025m,ramp=[10,10.5]만 추가하며 nonbaseline의baseline_summary는새analysis_baseline_v3를 가리킨다. 기존 source13개 gate/spec과 원입력의SHA가 그대로임을 검증한다. 미래native지지 성공을source경로검사로 대체하지 않는다.
- [ ] 새run_v4/Controller2·analyze_v3/duration2·rootexecute_v3 및 새prospectiveclosure를 독립 검수/동결한다.10초 전 원자료exact/원본 복원/새JTF/clip/torque변조거부 CPU검사를 수행한다. 실제효과는 새물리 실행에서 확인하며 counterfactual 원raw 적용은 실제 안정화로 집계하지 않는다.
- [ ] 모든 새 실제case는 native_<case>_v3,analysis_<case>_v3,feet_<case>_v3에 저장한다. 같은 새조건의baseline28초와repeat22초부터 검증한다. core+발전행+원물리조건을 통과하기 전LH해제는 시작하지 않는다. 통과하면 release28→free_strike28→regrasp36→continuous52를 같은 기준으로 진행한다.
- [ ] 효과/실패/추가미해결을원자료와함께기록한다.95%를완화하거나source음수gap/rawcontact만으로양성지지를소급통과시키지않는다. 후보가실패하면보존후실제첫이탈원인과다음가설을다시검토한다.
