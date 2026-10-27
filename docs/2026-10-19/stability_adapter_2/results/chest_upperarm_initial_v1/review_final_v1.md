# 초기 가슴·위팔 지지 코드·물리 최종 검수

요약 판정: **문제없음**. Critical0건·Warning0건. 현재선호V4/far실행은5초동안왼팔·왼손접촉없이EW6왕복타현을보이며초반가슴/위팔접촉을형성한다. 이전한계와실패원자료는보존하고새후보/집계/뷰어에서보완했다. 산출물Luna와최종봉인검증은아직후속단계이므로본보고는코드·원자료·headless뷰어까지의검수다.

## Critical

없음.

## Warning

없음.

## Suggestion

- `/home/ajou/yigyu/3/stability_adapter_2/chest_upperarm_pose_test_v1/README.md:8`: 과거README는open.sh/V1을가리키므로최종사용자진입점은open_v2.sh와새READMEsuccessor를명시해수정된입력pin/로그scope를사용하게한다. 기존README/기존headless결과는보존한다. 완료문서는이미V2를권장한다.

## 코드 및 입력 보존 검토

- SearchV3는왼손초기분리를G[.070,.080,0]m(노름106.301mm)로키웠다. 기타/몸통/오른팔준비는near와같고왼팔초기목표만다르다. 초기fullLP와61점distal/guitar/nonadjacenthuman source검사를통과한후보만export한다.61개정적표본이연속native clearance인증은아니다.
- Withdrawn후보의left_neck_near는accepted_for_native=False와명시적분리scope로교체돼과거삼면판정metadata를권위자료로승계하지않는다. 과거V2분리후보의남은metadata는별도scope정정으로보존한다.
- RunnerV4는V3에V5leafplanpin만추가한다. 실제제어/물리/초기검증/카메라/관측은같다. 실제helper·directconfig/contract/nativeinitial/공유XML/선언mesh/OMmass/FACETS의사전·사후pin구조를유지하며mainPLAN과독립freshnamespace동시작업을물리입력으로취급하지않는다.
- Far원래attempt의전체사전SHA를현재파일과직접대조해변경0을확인했다. 선호analysis입력SHA도모두일치했다.
- Runtime타현목표소유자는R_Elbow/R_Wrist6이고other75는고정logicaltarget이다. Far의300개최종목표배열에서other75를수치로직접대조해exact,EW6최종목표증분은3rad/scap내임을확인했다. 실제몸/팔상태를강제로동결한다는뜻은아니다.
- Far의1200개실제최종pick_feedback human81effort를읽어finite·각모델cap이내임을확인했다. virtualpicktask는사람EW6토크에만합산되고기타힘/부착/pose덮어쓰기경로가없다.

## 실제 물리 및 타현

- 정상hold/near/작은leftclear/far4실행은각1200physicsstep/300controlstep/5초완료다. V1카메라실패는0step으로구분해보존한다.
- Far의실제왼팔/왼손–기타접촉0/1200,오른손목/손접촉0/1200이다. 처음가슴+오른상완동시positive rawlambda는.1125초로.25초목표를충족한다. source초기간격.2mm를정확한0초native접촉이라고표현하지않는다.
- Far최대BB중심이동4.914567mm/SO3회전2.833108°다. body BB중심과actor-root기준을구분하고실제240Hzpose로계산한다.
- Far는L_Hip접촉318step/positive271step도있다. Chest는up구간3.75–5초positive0/300인반면R_Shoulder/R_Hip은계속지지한다. 따라서가슴지속밀착·오른상완/오른허벅지두부위만의수동평형이라고결론내리지않는다.
- Legacydetector의rawrelease는원본보존하고V7실제명령구간down3.2–3.55/up3.75–4.45로새집계한다. 기존3.95초cutoff가첫두up현을누락한원인을바로잡았으며detectorthreshold/rearm/영역을변경하지않았다. 세타현조건모두down6→1/up1→6이다. 이는단일가상피크왕복의검출성공이며학습checkpoint/전곡/장기강건성성공이아니다.

## 직접 실행 공간

- 새run_v2는nested current_pose_test_v1/run_v2.py/viewer.py와자기producer를명시적으로beforepin하고actualtracking.encode의이전벡터를pick_feedback최종벡터로연결한다. V1missingbeforepin을소급인증하지않고별도V2실행으로보완했다.
- 실제V2beforemap에서세producerpin과viewer_verification의모든입력SHA를직접확인했다.48physicsstep/.2초완료이고native초기값이nearreference와byteexact,기타종료state가near의.2초endpoint와exact다.
- open_v2.sh는해당새module을명시적으로실행하며환경변수/경로인용과인자전달은기존방식을유지한다. 실제GUI창/키조작은DISPLAY없는환경에서미검증임을문서가명시한다.
- 새testspace는leftnear기본준비형태다. near실행왼손접촉1090step을무지지증거로쓰지않으며far는별도진단이다. 이조건구분을최종자료에유지해야한다.

## 검수 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/analyze_chest_upperarm_initial_v1.py`: `f534454cebed14b8946f3b4d0e092cdb22dccfe0532f31436ca67175eb7075ed`
- `/home/ajou/yigyu/3/stability_adapter_2/search_chest_strike_fingers_v3.py`: `f3130e32fe2c84db68e9a0c60122e12e5bbc82aeae703aadf96d18d08b92050d`
- `/home/ajou/yigyu/3/stability_adapter_2/run_chest_upperarm_initial_v4.py`: `583427da7532875917b6b6c7cb8b7931303a7f2c302a0d468988a39a6901d091`
- `/home/ajou/yigyu/3/stability_adapter_2/CHEST_UPPERARM_INITIAL_PLAN_V5.md`: `a8f39c4079b779d08078668e4387e463ecab37cd78b3efe2ca40701079dcbed7`
- `/home/ajou/yigyu/3/stability_adapter_2/CHEST_UPPERARM_INITIAL_COMPLETION_V1.md`: `3463d6892e902020964da61e9cd6be07bc4f1e41f67e80a11c314de960b58045`
- `/home/ajou/yigyu/3/stability_adapter_2/chest_upperarm_pose_test_v1/run_v2.py`: `6d03dfa02c1921ad98c48315afe30ffc49be4e652df59cd486d34ddad723e38d`
- `/home/ajou/yigyu/3/stability_adapter_2/chest_upperarm_pose_test_v1/open_v2.sh`: `f9cc469a6eeabf5f9483a26d7bb0494eca523cf0f83dcd361d6e70f431c35294`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/analysis_v1.json`: `88b028566e040a2837b96ab019ebdbac5e6c8c72ea067201bb956c9c6768756d`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/viewer_verification_v2.json`: `90572a51cdb8ea3ba2b5b978d15186a7b6508bc6ba993ac0a2a83d234025471c`
