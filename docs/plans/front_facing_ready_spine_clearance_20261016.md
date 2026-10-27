# Spine source 여유를 보완하는 초기 자세 후보

사용자 REQUIREMENTS_v2를 최종 기준으로 유지한다. 현재 oldBody9의 정지·반복·LH해제·해제타현과 새43초 재접촉은 각각 부분 통과했으나, 실제 source60Hz 검사에서Spine↔기타body55 방향분리이동상한1mm를넘는표본이남았다. 자유타현 최악1.042988289528mm,재접촉1.018814706320mm이다. 이값은PhysX cooked 침투깊이가아니며원실패판정을보존한다.

새 후보는원Body9상수에Spine material point의법선방향0.15mm 분리를요청한상수증분을더한다. Chest법선접근변화0/RShoulder원재료점worldxyz변화0/Chestup.z변화0의6제약 설계를사용하며전체가슴·상완고정이아니다. .05mm는source여유가약7µm로작고,.10/.15는각약57/107µm여유를예측했으므로.15를전행검사·실제검증대상으로선정한다. 실제추종이나기타운동을예측과같다고가정하지않는다.

## 고정 조건

원initial q105/Root/cube/G pose/model108/하체16유한PD·원zero8·전gain/D/cap/Gfree중력ONstrapOFF/Chest가상목표10mm와인체관절한정힘·원RH파지/pick자식·Rprox목표·Rdistal6타현/LH목표·속도/횟수·protocol3 정착일정은유지한다. 원Root/모든G state 주입·인위G힘·PPO는0이다. 새상수는기존과같이10..10.5smoothstep으로추가하고Chest+.005는기존대로그뒤에가산한다. 원첫10초4raw exact검사는유지한다.

원42초literal exact gate는oldBody9의시간연장만증명하기위한후보특정검사였다. 새자세는10초뒤제어목표가달라져기존42초와같다고요구하거나성공을소급하지않는다. 새run/analyze는이비교를inapplicable로명시하며원사용자물리/속도/지지/발/형상문턱은동일하다. 기존old42실패·old43성공·literal보고서는그대로보존한다.

## 실행 체크리스트

- [ ] 정적후보·전행scheduled ramp 조건부FK를독립검수한다. 변경9/원제출105·float32/다른96·zero8 불변,전5run tilt5/right3 및free/regrasp Spine/Torso 1mm예측을확인한다. 원actual105 EPS0 실패와G원pose고정/동역학미검증은명시한다.
- [ ] 새Scene/run/analyze/readonly감사·Root입력생성·실행guard를새버전으로작성한다. 원source/leaf/config/raw/result는수정하지않는다. 독립검수·RootACK·실제source/모델expected SHA/CPU exactcopy후새config를생성한다.
- [ ] 새baseline28에서보정후11..16 정지5초를확인한다. 발전행·originalfirst10 exact·105실제/명령·원모든core gate와Spine/Torso 및기타활성source접촉형상을재검사한다. 지지/기타이동/Spine5°/진동/속도/limit잔차가부적절하면다음단계로넘기지않는다.
- [ ] 새repeat28·release34·free_strike34·regrasp43을차례로검증한다. 각최초실패는원자료전체를보존하고수정은새버전으로만한다. 원95%/15초/5초/속도·횟수문턱을완화하지않는다.
- [ ] 단독조건통과뒤continuous59를검증한다. 재접촉후LH의무게지지의존은접촉개수만으로단정하지않고후속완전해제15초와해제타현시험으로확인한다. 후속77초일정·fresh restart는새leaf/새버전에서구체화한다.
- [ ] 실제압현준비의원표면거리·지정줄/프렛접근성은별도수치기준을실제최종후보평가전에정한다. 현재현marker기하와실제현접촉력·진동·음향은구분한다.
- [ ] 관절수치건강은원EPS0 False를보존하며별도1/2/4 시간분할·PD좌표교차항진단을근거로평가한다. source형상통과가관절잔차원인설명을대신하지않는다. 설명부족·불안정·예산초과조건은최종채택하지않는다.

결과는같은P자료디렉터리에관측/조건부예측/실패·미충족을분리해보존한다. Root고정한정이며자유Root균형·보행검증이아니다.
