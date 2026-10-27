# 손가락 준비 및 왼손 분리 V3 사전 검수

요약 판정: **수정 권장**. Critical 0건. 기존 경로 충돌 Warning은 새 정적 오른손 준비형태로 해소됐다. 새 runtime/초기검증에는 차단할 오류가 없으며 Warning1건은 분리후보의 오래된 왼손준비 metadata다. 실제native 접촉/타현 결과는 후속 검증한다.

## Critical

없음.

## Warning

- `/home/ajou/yigyu/3/stability_adapter_2/search_chest_strike_fingers_v2.py:74`: left_clear_head는seed deepcopy의left_neck_near.accepted_for_native/face_measurements/source_audit를 그대로 승계하므로, 분리된 왼팔 상태에 이전 near 삼면준비 판정이 남는다. Runner는이필드를기하학gate로사용하지않고actualfullFK/sourceaudit를별도로확인해 actuation오류는 아니다. 소비된candidate는보존하고 별도scope정정자료에서 분리케이스의이전near판정이비권위적임을명시하거나 다음producer에서재계산/withdrawn표기할것을권장한다.

## Suggestion

없음.

## 검토 근거

- V2→V3 diff는leafplanpin과fingers42 exact→left_fingers21 exact뿐이다. 오른손새준비각도 모델q_ref81 exact/limit/FK/source검사로검증하며 런타임변경채널은 기존V7의R_Elbow/R_Wrist6만 유지한다. Finger21 POSITION목표도준비q_ref에 고정되고실제상태를덮어쓰지않는다.
- SourceV2는오른ring/pinky1_x/2/3각각−.21/−.30/−.18rad(모델clip)를 적용한다. 실제exportedangle차이도확인했다. 굽힘을 더한 것이 아니라 기존굽힘을완화한방향이다. 엄지/검지/중지는 유지한다.
- XML에서RH:pick은RH:index2→index1→palm→Wrist계열에 연결되고ring/pinky의자손이아니다. 두손가락초기각변경이기존pick FK를바꾸지않으므로이전EW6q표본재사용은정합적이다.
- near와left_clear_head는각각fullLP초기sourceclear,동일61점movingdistal/기타/비인접human 경로음수sample0,최소1.386335mm다. 최초V1의최저−18.04mm충돌을숨기지않고별도후보로해소했다. 이는정적source샘플proxy이며연속PhysX cooked clearance 인증이아니다.
- Leftclear는G[.045,.040,0]m이며총이동노름60.208mm다.넥아래45mm에넥방향40mm를합친대각선이므로총45mm분리라고설명하면안된다. Left12IK는원래모델한계/기준±.8rad및ball160°를검사하고fingers왼21은변경하지않는다.실제LHand/G접촉0여부는nativequery로판정한다.
- Source/runner는실제nativeinitial/config/직접assetJSON/XML/모든선언mesh/helper/leafplan을사전·사후SHA로기록한다. 기존실패batch와부분near결과는보존하고새finger_search_v2를선호한다.
- 새두Python AST parse와선택두candidate의config SHA대조통과.기존카메라키fix/유한human행동guard/currentG타현목표/최종pick effort권위scope도유지한다.
- 리뷰어실제GPU/물리실행은0회다. native조기Chest/RShoulder양의접촉,왼손접촉없음,RHand접촉없음,원래6현왕복검출이최종채택조건이다. 학습곡완주나무지지/수동평형을뜻하지않는다.

## 검수 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/run_chest_upperarm_initial_v3.py`: `cc0990efa81a1e3380e3cf242d1f89a7b1fdaeecda885592a2f8e3b78d54071d`
- `/home/ajou/yigyu/3/stability_adapter_2/search_chest_strike_fingers_v2.py`: `fef441878f50986b4dae3fe1e6536fcae341332ce145f0f5923280b27c35ae8d`
- `/home/ajou/yigyu/3/stability_adapter_2/CHEST_UPPERARM_INITIAL_PLAN_V3.md`: `1809bddf3dee074ed9031e76b5be9000e1b1dcd4f3542235f94465754a43477b`
- `/home/ajou/yigyu/3/stability_adapter_2/CHEST_UPPERARM_INITIAL_PLAN_V4.md`: `83e8c267164e1661567bdb15079403cf76afcc2e9c6c7a6a272957c004988834`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/finger_search_v2/search.json`: `6064f06f5b9b503050963fb906f11d97ea161e3252512b77e50147d62db75048`
