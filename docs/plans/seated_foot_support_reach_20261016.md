# 接地 V3: 수직 도달 여유와 IK 계산 예산

2026-10-16. V2 실제0.383333초(step92)에서오른ankle목표bottomspan1.022594mm로1mm검사중단. 이전실패/13frame영상/원자료/분석은불변보존. 같은failed actualq로max_nfev300을줘도목표잔차가남았고원관절범위의activebound는없었다. 실제오른무릎원점이초기보다1.200521mm올라와지면도달여유가부족한상태다. 임계값완화로해결하지않는다.

독립읽기진단에서같은q와desired−1.5mm를공통Z로추가−4/−8/−12mm했을때모두평탄성잔차약.068mm까지수렴했다. −12mm는ankle_y원하한에닿아피한다. V3는총초기Z−36mm를택해(.592→.556m), cubefullheight .492→.456m(half.228),상체와기타를동일Z이동한다. 초기Hip/upper/Grelative방향과원형상·gain/cap은그대로,source10축을다시맞추고동일BOX/capsule감사한다.

V2의max_nfev35에근접하는31평가가−8mm가상검사에서관측돼새runtime_v3는동일목적/오차gate/범위/rate/힘·원래관절제어를그대로두고IK계산예산만150으로확장한다. 실제접지판정기준은원계획그대로다. source생성은기존source_v1/metadata_v2함수를새중간경로와명시된DZ로재사용하고,새driver자체/파라미터/중간산출물은별도before맵으로닫는다. 권장candidate는새source_v3. 실제native_static_v3 5초와새analyze_v3로검증한다. 성공시동일config새out에서반복재현을검사한다. 전체기타안정성/가슴접촉은별도실패가남을수있다.
