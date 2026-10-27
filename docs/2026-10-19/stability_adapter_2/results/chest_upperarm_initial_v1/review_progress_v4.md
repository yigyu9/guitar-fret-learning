# 초기 가슴·위팔 지지 진행 검수 V4

요약 판정: **수정 권장**. Critical0건. 실제5초 실행은 정상이고 EW6만으로 왕복6현 crossing이 원래detector rawrelease에 관측된다. 그러나 현재leftclear후보는왼손없이유지조건을충족하지못하고,두후보모두후반Chest접촉이사라진다. 후속새후보/분석으로확인해야하며 최종채택검수가아니다.

## Critical

없음.

## Warning

- `/home/ajou/yigyu/3/stability_adapter_2/run_chest_upperarm_initial_v3.py:104`: 이경로로기록된native_strike_left_clear_v1 실제query는왼팔/손접촉326/1200step,첫3.645833초다. 접촉부위는LH:pinky3/LH:middle3–guitarroot(넥)다. 최초정적분리성공을실제5초무접촉으로판정하면안된다. root가계획한더큰초기분리후보를새경로로검증하고 실제전체접촉0을채택조건으로둔다.
- `/home/ajou/yigyu/3/stability_adapter_2/run_chest_upperarm_initial_v3.py:101`: Chest/R_Shoulder접촉은시작.25초이내에형성되지만지속Chest지지는아직아니다. leftclear의Chestpositive는2–3.75초152/420,3.75–5초0/300;near는325/420,0/300이다. R_Shoulder/R_Hip은두경로모두2초이후720/720positive다. 따라서처음부터접촉한다는결과와타현전구간가슴으로끼워유지한다는결과를구분해야한다.
- `/home/ajou/yigyu/3/stability_adapter_2/analyze_elbow_wrist_ready_v1.py:41`: 이legacy집계의upcutoff3.95초는현재V7desired_point의up시작3.75초와맞지않아첫두string을제외한다. rawrelease는leftclear기준1..6이3.832272/3.940570/4.043171/4.153056/4.257204/4.363132초에모두lane/globalallowed로기록돼있다. 원래detector나과거결과는보존하고현재V7시점에맞는새phase집계로정규화해야한다. root가이후속분석을준비하고있다.

## Suggestion

없음.

## 현재 코드·원자료 확인

- Native_hold_v2/native_strike_left_clear_v1/native_strike_near_v1모두1200physicsstep/5초,completed=True/failure=None/inputs_unchanged=True/forbidden_calls=[]다. 카메라V1실패는0step으로보존됐다.
- RightWrist/RH:* 실제기타접촉은세정상실행모두0이다. 새로운초기ring/pinky굽힘완화가source61점에서0bad/min1.386mm였고실제접촉에서도현재손/기타간섭을관측하지않는다. 선행39/61표본충돌결과를삭제하거나덮어쓰지않았다.
- V3는오른손초기6finger각의변경을허용하고왼손21초기보존을검증한다. 런타임목표변경권한은R_Elbow/R_Wrist6이며other75targetexact다. 양손·몸통실제상태가고정되었다는뜻은아니다.
- Rawdownrelease는두타현경로모두6,5,4,3,2,1이다. V7기준3.75초부터uprelease를수집하면1,2,3,4,5,6이다. 이는검출기의방향/영역/재무장판정결과이며checkpoint·전곡·학습·접촉력보증이아니다.
- Leftclear에서Chest양의접촉시작.1125초/R_Shoulder.029167초이고near는.120833/.029167초다. 초기접근목표의.25초조건은통과하지만이를후반접촉보장으로확장하지않는다.
- 초기Source검색·candidate/configSHA·directXML/모든선언mesh·actualnativeinitial·helper의사전/사후pin범위를앞선검수에서확인했다. 독립freshnamespace를포함하지않고기존실행에소비된원본은보존하는새버전방식을유지한다.
- Leftclear후보에남아있는oldleft_neck_near삼면metadata는앞선V3검수Warning대로권위자료로사용하면안된다. 새phase분석/실제contactquery가분리유지여부의근거다.
- 리뷰어추가GPU/물리실행은0회이며원자료를읽어독립집계했다. Root의더큰왼손분리/정규화집계/최종봉인단계는후속검수대상이다.

## 검수 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/run_chest_upperarm_initial_v3.py`: `cc0990efa81a1e3380e3cf242d1f89a7b1fdaeecda885592a2f8e3b78d54071d`
- `/home/ajou/yigyu/3/stability_adapter_2/search_chest_strike_fingers_v2.py`: `fef441878f50986b4dae3fe1e6536fcae341332ce145f0f5923280b27c35ae8d`
- `/home/ajou/yigyu/3/stability_adapter_2/analyze_elbow_wrist_ready_v1.py`: `7830d3e00df03a45fe1fb1fc6b428b560cb5ed75b0cb29a9ac24adb73485743b`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/strike_detector_v1.json`: `247512ac1d0a61629a7e7bc6207c85b7242775aeff1d4b05c65c995f4b516904`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/native_strike_left_clear_v1/report.json`: `44142b78cc43748d4d070c6b08273e6d6d64d26be542490fa4e12604beec5568`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/native_strike_near_v1/report.json`: `051d6626ed3f7c9153d072b975b2607a715338773837a569db0ed1feba876875`
