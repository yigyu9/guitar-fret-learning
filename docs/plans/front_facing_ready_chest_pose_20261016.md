# 왼손 해제중 타현의 Chest 양성지지를 위한 작은 유지자세 후보

## 확인된 실패와 근거

기존 margin_v1/현재 native_free_strike_v3는28초/6720step 정상완료지만 삼중지지가각왕복75.7544/16.7534/3.7461%로원95%에실패했다. 기타전체7.148552mm/2.349220도,발전행,실제3왕복6→1/1→6,근위1도,왼팔손3601개raw접촉0/901개형상최소24.357mm,전체수학은통과했다. 가슴양성누락은raw접촉존재/lambda0이며R_Shoulder/R_Hip는타현전행100%다. 타현시작15초전두실행exact뒤Chest-G상대접선/회전차최대1.184mm/.451도와Spine양성lambda증가가동시관측됐다. sourcegap더음수,가상힘19.4~19.5N/20N포화0,관절cap0,JTF오차~1e−17이다. 진단V1/V2/summary/다른부위접촉/입력SHA를그대로보존한다. 단독인과나후보성공을확정하지않는다.

control독립계산에서추가가상깊이.25mm는동일궤적상평균.497N여유가있어cap때문에무효는아니다. 그러나강도증가반복대신작은기하변경을먼저시험한다. 원initial-calibrated FK/실제여덟시각q/G고정에서Torso_x+.001rad는Chest쪽normal접근.174mm이지만Spine도.156mm로거의함께접근한다. Chest_x+.005rad는Chest만.14895~.14951mm접근/Spine직접이동0이고예상Chesttilt4.489~4.766도/right≤1.332도/Spine≤4.282도로원한계내다. .003rad는접근.0896mm다. 아래+.005rad를단일최소후보로선정하며실제응답은새물리실험에서만판정한다.

## 변경과 검증 체크리스트

- [ ] 새 runtime_v3.Scene.command 전단에서10..10.5초smoothstep에따라 **Chest_x 요청유지목표만 +.005rad**를더한다.10초전0,10.5초이후상수이고타현주기/접촉lambda를추종해몸통을흔드는보정이아니다. 원105초기/source9/큐브/기타/원range/영범위8/하체16/중력/충돌필터를유지한다. named요청사본에만적용하고실제상태/Controller.base_target를수정하지않는다. 기존 gain/cap,Chest가상10mm,법선20N,SO3제어와손경로/일정불변이다. Chest_x suffix를world회전축으로해석하지않는다.
- [ ] 원Scene.command의foot/SO3/Motion/제출순서를유지한다. Rprox6은여전히2396step최종목표latch,타현은Rdistal6만변경한다. 원요청/새유지bias식/시간/축/적용후요청·실제제출은metadata로구분한다. 새일정은정적유지목표.286479도조정이며오른어깨타현목표나기타힘이아니다. 첫stroke의준비중ramp를끝내고이후고정한다.
- [ ] 새 analyze_v4는목표ownership의기대값에정확한독립smoothstep Chest_x bias만추가한다. 다른채널불변/원rate·float32·range/영범위8/POS48/Rprox목표/actualtaskchain·LH/RH 경로/각phase/gate모두유지한다. fake원자료를만들어기존gate를통과시키거나기준을완화하지않는다. 기존duration_math_v2/allN원제어와margin복원검사는그대로사용한다. 새bias metadata/요청/제출누락·부호·시각변조를거부한다.
- [ ] 새 run_v5는Scene runtime_v3와Controller runtime_v2를명시하고같은새후보baseline_v4의실제원자료/core+발/입력맵검증후action을허용한다. Root가새inputs_chest_pose_v1의6설정/execute_v4/새closure를생성한다. 원margin3필드와새Chestpose mode/joint/delta/ramp4필드및baseline_summary경로만원V3에서변경한다. frozen전leaf/model108/code/helper/config/source시작·종료SHA와실행원문을보존한다.
- [ ] 새원문으로문법/CPU변조거부/원first10exact·새target합성·원기타/발/근위조건독립검수완료SHA확인후RootACK한다. 초기source13개검사는초기/원계획경로자격이며새bias후미래손가락FK정확도나지지성공보장이아님을명시한다. 새FK posture진단은G고정source예측으로설명한다.
- [ ] 물리출력은native_<case>_v4,분석analysis_<case>_v4,feet_<case>_v4/media_audit_<case>_v4에신규저장한다. 동일후보baseline28→repeat22→release28→free_strike28→regrasp36→continuous52순으로각단계core+발통과전다음실험금지. 원first10 actual4raw는기존정지및새baseline exact를유지한다. 원95%삼중지지/전체안정성/발전행/6줄/양측준비/근위1도/LH해제15초/재접촉5초/연속전체조건불변이다.
- [ ] 실패하면원실행/목표/제어/영상/분석을보존하고진단부터재개한다. 이전전체후보성공으로상속하지않으며새PPO0,기타free/중력ON/strapOFF/기타힘0·부착0·상태주입0이다. 완료시같은자료디렉토리에관측/실패/범위/권장문서·영상·자세경로를기록하고독립최종검수후Root봉인한다.

소유권: 구현담당 runtime_v3.py/run_v5.py와자기CPU증거,분석담당analyze_v4.py와자기CPU증거,Root설정/외부wrapper/closure/main문서/최종봉인,reviewer검수파일. 서로동시작업중이며타담당변경/원파일을되돌리지않는다. 사용자2026-10-07자율실험지침과이번초기자세작업범위에따라진행한다.
