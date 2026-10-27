# 제한 예측·회전 적분 가설의 substeps 대조 진단

## 관측과 범위

원4/2와8/4의각5초는정상완료했다. 원4/2첫5초4raw는baseline_v6와모든필드exact다. 그러나RThorax_x의실제원범위초과max는step3에서.000140748918→.000140003860rad로거의같고,zero8은네축증가/네축감소했다. 계산반복수만으로원인을확정하지않는다. 원solver_comparison_v1의passedFalse는마스크전raw요청을제출0과동일하게요구한추가집계gate오류로보존했고,source2가진단/제출필수를구분해독립검수중이다.

담당자의원자료/공식reduced-coordinate소스대조에서RThorax actualbody회전은exp(Bq)와일치하고,scalar초과를worldEuler오독으로없앨수없었다. 반면native dq는상대각속도와맞고Log좌표미분과다르다. step3의관측dq_x≈−3.50e−6rad/s,SO3 Jacobian으로회수한순간qdot_x≈+.0336402rad/s의차이가관측됐다. .0336402/240≈.00014017rad로초과규모와맞지만이한시점은단독인과증명이아니다. 공식PhysX4.1reduced의futureP=jointP+jointV*dt 및회전적분후Log회수루틴과일관가설이다. 현재Gym binary의정확revision/루틴동일성은미확정이고maximal의twist/swing한계설명으로대체하지않는다.

## 사전 계획

- [ ] readonly diagnose_limit_coordinates_v1의근거·한계·사전입력SHA를먼저동결한다.
- [ ] 별도생성자조건으로원4/2를유지하고SimParams.substeps만1→2로변경한다. environment.py가physics_parameters.get('substeps',1)을생성자에서사용하는실제경로를CPU로확인한다.
- [ ] original baseline_v6 cfg28/모델/initialq·pose/원목표/모든gain·cap/Root고정/Gfree·중력ON·strapOFF/외부callback240Hz/target60Hz/실제clock을그대로둔다. cfg나시간을변조하지않고원bounded5초runner를사용한다.
- [ ] 원PRESETS객체를고치지않고생성자동안복사binding에substeps=2만추가,정상·예외모두원객체·내용복원. native实际SimParams구조가저장되는probe를사용한다. 새입력/새out로실행하고기존실패/모든source보존한다.
- [ ] CPU/독립검수·RootACK·사전소스/모델108/원4_2referenceSHA보존후별도5초1200외부step을실행한다. 내부적분은2400substeps이며정규안정화실험횟수에합치지않는다. 정규43초와동시에native를돌리지않는다.
- [ ] 원4_2의실제0..5초와새조건을105 q/dq/원bound·zero8qref/최초·최장/시간패턴·feedback명령변화로비교한다. 원target/cap/실제제출zero8=0은필수,마스크전raw는진단이다.
- [ ] 각속도component와rotvec미분의차이·시간분할의잔차민감도가데이터에의해반증가능하도록보고한다. residual감소를미리성공게이트로두지않고증가/동일도그대로남긴다. 작은값/단일축/공식소스일반론만으로전체원인을확정하지않는다.

## 측정 한계와 채택

CC_LAST_SUBSTEP 정책이므로substeps2의접촉raw는마지막내부step을반영하며두내부step의모든접촉기록이아니다. q/dq는외부240Hz관측이고내부480Hz최댓값을보증하지않는다. 외부force요청은각simulate전240Hz에한번이며그안의두적분동안유지된다. 서로다른시간을합치거나clock을재해석하지않는다.

이실험은5초준비구간진단이며28초/정지5초/연속59초성공이나새solver후보채택이아니다. 현재유지제어는원4/2·substeps1을유지한다. 관측과독립물리해석으로설명이부족하면최종미채택이고새제어로숨기지않는다. PPO0. Root는leaf/원자료보존·실행·최종해석,impl은확정brief의새producer/CPU만,reviewer는독립검수이며기존source/leaf/결과를수정하지않는다.
