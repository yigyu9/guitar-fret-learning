# 현재 자세의 왼손 OFF 초기조건 사전검수

요약 판정: 문제없음. source/새 tracking-off init/reversible wrapper가 계획과 일치한다. 원본 수정·source 탐색/native 재실행은 하지 않았다.

Critical: 0

Warning: 1

- [계획:5](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_OFF_CURRENT_PLAN_V1.md:5), [clearance helper:26](/home/ajou/yigyu/3/stability_adapter_2/left_arm_clearance_source_v2.py:26): 사람 몸통/골반3mm 조건은 L_Shoulder↔Torso capsule과 L_Elbow↔Pelvis box 두proxy를 검사한다. **사람의 모든형상에 대한3mm 여유로 확대하지 않고 두proxy 여유와 전체source 비겹침을 구분한다.** 기타20mm 검사 및 actualLEFTcontact0 수락조건에는 영향 없는 설명범위다.

Suggestion: 0

확인 근거:

- [source:39](/home/ajou/yigyu/3/stability_adapter_2/search_left_hand_off_current_v1.py:39): 실제15~26 L_Thorax/Shoulder/Elbow/Wrist12 초기각만 ±0.8rad/모델교집합에서 변경한다. bounds가비어있지않고 frozen69 exact gate를 유지한다. 모든L축0.05rad FK perturbation에서 right/body의p/q가 exact임을 확인했다. 기타초기 p/q를 seed그대로 유지하므로 cached오른지지점참조의 전제가맞다.
- [source:52](/home/ajou/yigyu/3/stability_adapter_2/search_left_hand_off_current_v1.py:52), [query_pairs:61](/home/ajou/yigyu/3/stability_adapter_2/initial_overlap.py:61): 전체source audit 후 왼팔/LH와 모든활성guitar geom을cross-actor20mm로query한다. farther pair는truncated이므로 결과를무한정확거리로해석하지 않는다. importer에서사용하지않는proxy/비활성geom 제외는 기존probe규칙대로다. 현재freshcapsule min·target5mm/두humanproxy3mm와fullmodel/frozen69 gate를 유지한다. actual왼팔/손 접촉0은 native에서별도확인한다.
- [source:22](/home/ajou/yigyu/3/stability_adapter_2/search_left_hand_off_current_v1.py:22): discovery→활성기타XML발견SHA→전체입력SHA→Contract/FK/geometry구축 순서다. 새source/off/wrapper/PLAN 및 config/candidate/reference/helper, humanXML37mesh·guitarXML69mesh/manifestunion70이988개beforemap에포함되고 종료SHA검사가있다. 현재source/계획/새helper SHA와소비map이일치한다.
- [source:67](/home/ajou/yigyu/3/stability_adapter_2/search_left_hand_off_current_v1.py:67): 새candidate에는실제q/FK/G39와`left_hand_off`freshrow를기록하고 right-support metadata를그대로승계한다. 기존right/trunk/G 기준의cached참조는물리적으로유효하지만 그안의기존전체q/전체audit을새왼팔상태의fresh검사로설명하지않는다. 새왼팔검사는`left_hand_off`와 actualnative초기검증을 사용한다. config는candidatepath/hash와off flag만변경한다.
- [off init:18](/home/ajou/yigyu/3/stability_adapter_2/left_wrist_tracking_off_v1.py:18): legacyV3의init를교체할때 explicit parentV2.__init__를호출한다. 실제recording상속은 Chest→bodyV5→rightBlockV6→legacyV3→leftV2→기존right이므로 lexical zero-argument super의type 문제나중복init을피한다. parentV2에서기존왼팔gravity/scalarPD를설치한뒤 off tracking closure를추가한다.
- [off control:48](/home/ajou/yigyu/3/stability_adapter_2/left_wrist_tracking_off_v1.py:48): enabled=False가 physics0부터항상적용된다. 실제force/task AST문장을in-memory로실행해3force와81task exact0을확인했다. 기존왼팔gravity+PD requested값/원cap을그대로제출하므로 왼팔전체 actuator torque0을뜻하지않는다. native state변경없는assert와Jacobian검사를유지한다.
- [wrapper:36](/home/ajou/yigyu/3/stability_adapter_2/run_left_hand_off_current_v1.py:36): 원래fourpatch(factory/guard/create_scene/GymRecording)와 read-onlyChest/trunk recorder를유지하고 legacyTracking클래스의__init__만context manager로일시교체한다. 디스크원본수정과충돌filter제거/기타직접힘/새PDgain변경은없다. 기존encode는legacyV3/bodyouter경로로유지돼33EFFORT/48POSITION기록구조와호환된다.
- [계획:3](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_OFF_CURRENT_PLAN_V1.md:3): 첫진단은t0부터왼손이떨어진조건이다. 안정화후손을빼는연속release나수동무제어/반복/연주인증으로설명하지않는다. native69scalar/G39/right지원강체/configexact, trackingfalse/force-task0,모든endpoint LEFTcontact0과실제기타유지는실행후별도검수한다.

세Python AST 및CPU환경의FK/pin검증통과. MuJoCo renderer를비활성화한기존CPU환경에서read-only확인했으며source main이나새물리실행을호출하지않았다.

- Source SHA256: `05d969923163433c7158b1e13536068ef0d8e5d031a9f6f13beeaf119add8270`
- Tracking OFF SHA256: `2bd9c9d03c1abfc5a099d94b663df8d48860038049f0d7feaf1c9187e3062766`
- Wrapper SHA256: `47d760a6aff86de7977457b3212d83d97f70b6844ffc4ab6171a236afe7874ed`
- Plan SHA256: `6a3a52a4b2bb8bab4eda5fa5e3a45ac52c42db811e5887c502960741c4fe10d9`
