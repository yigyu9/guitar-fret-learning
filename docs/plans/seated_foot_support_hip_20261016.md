# 접지 V4: 오른 Hip 지지 목표와 지면 도달의 경쟁 완화

2026-10-16. V3 source/native/analysis불변보존. 새36mm낮춘좌석은양발positiveground응답을만들었으나2.3초에RAnkle목표span1.038136mm로중단됐다. 이때Rhipactual−1.704251rad(initial−1.675481),legacytarget−1.755481(초기−.08),submittedRhip−40.395Nm. L/Rfootpositiveground접촉이둘다있었다. 앞선읽기전용V1hip6시점검사는새접지로달라지는실제hip궤적을보장하지못했다.

V4는source_v3의36mm초기하강/cube.400×.280×.456m를유지하고최종command에서R_Hip_x의목표bias만−.08→−.01rad로줄인다. 과거상수−.08은이전공중발조건의유한지원목표였으며새접지에서도정답으로고수하지않는다. 나머지hiptargets·상체지원·zero8·원gain/cap·actualhip세계수평IK/desiredfootZ−1.5mm/rate/같은guard는유지한다. 상체/G초기상대배치·방향도그대로다.

원Controller.targets의legacybiasdict assert를바꾸지않고새runtime_v4 Scene.command직전명시적override로소유한다. cfg는right_hip_final_bias_rad=-.01을추가하고foot mode V4로명시한다. targets행에는legacyRhip요청과새최종요청을둘다기록한다. 새run_v4/native_static_v4와동일gate인analyze_v4. 형상/힘/동적기준완화없음. 오른허벅지·기타지지는바뀔수있으므로실제접촉과기타유지도별도판정한다. 성공하면동일config새경로에서5초반복검증. 새PPO/15초해제는실행하지않는다.
