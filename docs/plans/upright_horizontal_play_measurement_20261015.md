# 압현·타현 실제 성립 판정의 구체화

첫분석실행전의측정규칙이다. pressure band/contact/dwell만으로정지baseline의접촉을새동작으로인정하지않는다. 기존후보판정(XY10mm/Z−6..+10mm/지정index3 실제guitar양의접촉/연속100ms)은그대로보고하며,실제요청압현동작은추가로5초marker_G_z 대비hold(6.3~8s)최저z가2mm이상낮아지고finger4 actualq peak-to-peak최대가.02rad이상이어야한다. 이는측정압력이나정확한단일줄압현인증이아닌observable동작+기존후보의조합이다. baseline의동일후보/진입/변위도보고한다. 사전preflight의목표깊이와단독/결합입력은바꾸지않는다.

native접촉은named human body와실제guitar collisionshape를가진모든body를포함한다. guitar root만인정하면G:body의상완접촉이나G:fret의손가락접촉이누락된다. 원XML에서geom을가진body집합을구하고무충돌stringmarker/끝marker/가짜pluck_range/thumb_support_proxy를제외한다. 각nativepair/positive lambda를분리기록한다. lambda를N으로환산하지않는다.

원PickStrikeDetector는60Hz endpoint/dt1/60/rearm_min_frames2로적용한다. 실제pickG와stringfinite양끝은normalizednativepose로재구성한다. 압현+타현combined는down6→1/up1→6모두성립하고,허용zone/lane에서발생한지정pressstring의모든event(최소down/up2개)의직전·직후240Hz표본이ready/dwell100ms를만족해야한다. 하나의ready crossing만있다고동시수행통과로판정하지않는다. 초기0~5s와동작5~9s/단독동작/원fullChest지원기준을분리한다.

분석은새runtimepackage/실제모델XML/이leaf/spec/원기록/참고beforemap/실제detector·설정/재사용helper를사전핀하고후대조한다. 원기존누락전후기록을고치지않는다. nativeinner와outerwrapper의입력불변을모두필수로한다.
