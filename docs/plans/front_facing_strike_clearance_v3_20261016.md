# 촘촘한 손 형상 검사 실패 후 방향 후보 확장

source_clearance_v2의6개후보중41점통과후보3개를241점으로검사했으나모두실패했다. 최선depth2.5mm/G-Y−10°도12.8333초약지끝–기타source signed gap−79.45μm였다.41점통과를실제동작clearance로확대하지않았고새native는실행하지않았다. 기존모든code/소스/결과/입력은보존한다.

다음단계는같은solver/6축/원gain/원cap/원timing/lane/근위목표유지조건에서G-Y손방향−12°와−15°만추가하고깊이4/2.5mm를다시비교한다. 전체soft방향은현재기타좌표기준이고world회전축명령이아니다. 조합4개를41점확인하고통과후보를241점검사한다. 초기접근/종료hover를포함한다. 새source기준은기존음수관통금지에더해전체활성쌍2mm이상설계여유를요구한다. 원2mm도달/float32원관절범위/q_ref±1rad/principal160°/다른99축동일조건을유지한다. source2의실패는그대로이며기준을완화하지않는다.

−12°추가는best dense gap부족이작았고약지offset+G-X가약95mm여서음의G-Y방향회전이약지를들어올린다는원기하진단에근거한유한확장이다. 선형추정으로성공을주장하지않고원형상과모든241표본이판정한다. 후보선택은절대방향변화최소/그다음깊이변화최소순서다. 적합후보가없으면추가각도확장보다자세/손가락형상및초기기하문제를진단한다.

source_clearance_v3/prepare_v3/run_v3/analyze_v3를새로만들며motion_v2/runtime_v2는검수한동일코드를사용한다. 새입력은baseline_v4/strike_v4,실제선택시험은native_strike_v4다. source2불가로native_strike_v3는실행하지않는다. 새source/producer/실제실행전에새계획·원모델및모든mesh·코드·입력/이전실패결과를사전SHA봉인하고독립검수한다. 실제14초전체안정gate/가슴+상완+허벅지95%/양측준비/실제6줄왕복/근위상대회전1°/원prefix를모두유지한다. 정지대조V1은재실행하지않고원자료비교한다. source형상은native접촉·지지나타현성공이아니다. 기타자유/중력ON/strapOFF·Root고정·동적하체16/원zero8·상태주입금지·PPO금지를계속지킨다.
