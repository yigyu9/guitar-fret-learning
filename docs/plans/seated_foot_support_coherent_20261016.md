# 접지 V6: 검증된 interior Hip와 일관된 발 목표, 작은 preload

2026-10-16. V5는0.141667초에기존lower coordinate validation gate로중단됐다. mass오차3.4321e−7kgm²는통과범위지만L_Knee childangular오차.0109825rad/s>.01. L_Hip_y actual.217716rad/L_Hip_z actual+.034584rad,목표는한계근처±1e−7였다. 기존기준을완화하지않고이실패를보존한다. V5선호Hip와실제목표는달랐고,원래interior지지목표를그대로대체할근거가없었다.

V6는5초완료·positiveground100%였던V4계열로돌아간다. Hip6개의목표는기존interior L_y+.01/L_z−.01/R_y−.01/R_zsource.025, L_xsource, R_xsource−.01을유지한다. lower10Knee/Ankle/Toe의prediction에서는변하는actualhip이아니라이최종요청hip6을사용해한계안쪽Hip와발목표가일관된정지q목표가되게한다. actualstate는finite rotationalstablePD가계속피드백하며상태고정은없다. source/root/cube/guitar/upper/gain/cap/rate/guard불변.

V4의desiredfootZ−1.5mm는지면반응과hip수동변형·ongoing재목표를키웠다. source+.5mm/λ0와V4negative/positive100의관측에따라V6는초기+.5→desired−.25mm/.5초로작은유한접지목표를시험한다. 낮은preload와일관된Hip가함께바뀌는단일후속조건이며개별효과를인과적으로분리했다고하지않는다. XY는기존softreference2이며가상고정이아니다; actuallast1s3mm/속도/기울기/전체bottom높이/동시contact95%의동일gate를통과해야한다. V5의1mmXYsourceguard는16축source형식에만해당하며V6에는적용대상이아니다. V6는V4의동일10축sourceheight/span조건을유지한다.

새runtime/run/analyze_v6,static5_v6.json. 원래좌표검사·무결성·원본zero8·105/97·Rootfixed/Gfree·gravityON/strapOFF 유지. 성공시동일config를새out에서5초반복한다. 전체기타/가슴지지·연주성공은별도. 새PPO/15초손해제없음.
