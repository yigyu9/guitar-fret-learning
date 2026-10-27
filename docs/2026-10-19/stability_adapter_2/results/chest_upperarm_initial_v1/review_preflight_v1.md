# 초기 가슴·위팔 지지 독립 사전 검수

요약 판정: **수정 권장**. Critical 0건. 실제 유한 제어/초기 상태 검증에는 차단할 오류를 찾지 못했다. Warning 1건은 source검사의 경로 범위이며 root가 별도 새 helper로 보완하기로 했다. 실제 hold/strike 진단 실행을 막는 오류로 보지는 않는다.

## Critical

없음.

## Warning

- `/home/ajou/yigyu/3/stability_adapter_2/search_chest_upperarm_initial_v1.py:56`: source_audit는55행의 초기 자세에서만 수행하고 타현은5waypoint+1midpoint의 IK 오차/forearm capsule 간격만 검사한다. 손목/손가락/비인접 자기충돌을 포함한 전체경로 비관통 검증은 아니다. 별도 새 source helper로 실제V7 시간 궤적을 샘플링해 fullhuman/self/guitar 거리검사를 추가하고, native R_Wrist/RH:* 실제 접촉도 결과로 확인할 것을 권장한다. 기존 source결과를 전체경로 clear로 설명하면 안 된다. Root가 이 범위를 명시하고 새 helper를 계획했다.

## Suggestion

없음.

## 확인한 사항

- 기존 V7 factory/controller를 그대로 사용하므로 타현 요청/최종 목표의 변동은 R_Elbow/R_Wrist6만 허용한다. other75 logicaltarget을 exact 검사하고 기존 모델/160°/3rad/s 및 finite human effort caps를 유지한다. 실제 물리상태를 고정한다는 뜻은 아니다.
- 새 runner는 초기 native q_ref exact, scalar 모델 한계, root/하체 exact, 원래 finger42 exact, PD/mass, 실제G prediction 및 bodyFK, fullsource initialoverlap를 대조한다. 기타 또는 관절 상태를 실행 중 덮어쓰는 추가 경로가 없다.
- 선택 near020의 초기몸통/양팔 주요 ball norms를 직접 계산해 모두160°미만임을 확인했다(최대R_Elbow103.130°,L_Wrist95.768°). source6EW sample은 최대113.407°, 최대pick 오차.000000447m, 최소forearmgap.009724m다. 현재 후보에 principal/model 위반을 발견하지 못했다.
- near020/near050 candidate/native-reference SHA가 config와 일치한다. sourceinitialclear/왼손준비 조건은 후보에 기록되어 있다.0.2mm sourcegap은PhysX cooked 실제 접촉 인증이 아니므로 실제 초반0.25초 내Chest+R_Shoulder positive접촉을 별도로 확인해야 한다.
- source측정은 전체R_Shoulder capsule witness를 사용하며 기존 proximal_upper_arm30 등의 키는 호환용alias임을 source row scope로 명시한다. 사용자 요청의 shoulder–elbow위팔을 의미하며 무조건 capsule30%위치라 해석하면 안 된다.
- 새 runner99–105행의 readonlyactualquery는 Torso/Spine/Chest/R_Thorax/R_Shoulder/R_Elbow/R_Wrist/R_Hip/L_Hip과 실제 양손기타 접촉을별도로 기록한다. 왼쪽Hip을 왼팔/손 집계에 포함하지 않는다. raw lambda를 N단위힘이나 forceclosure로 해석하지 않는다.
-153–156행에서 실제 inherited encode의tracking.save를 patch하므로 이전 lefttracking/leftarm 로그를 superseded_by=pick_feedback_effort_rows.json으로 명시한다. 알려진 V7의legacy scope오류를 기존파일변경 없이 새runner에서해소했다. 권위적인 최종 human81벡터는 pick_feedback_effort_rows다.
- shallowA.py pin은 실제flathelper를 포함하고 독립fresh namespace를 제외한다. sharedXML/선언mesh/직접config/OMmass/FACETS/contractinputs를 사전·사후 SHA로 대조하며 mainPLAN concurrentappend를 실제제어입력처럼 pin하지 않는다.
-5초/1200physics/300control 전체영상과 support_side 추가카메라, 예외 시 부분영상·실패자료보존 구조를 확인했다. hold는config의six_joint_strike_enabled=False에서 새trajectory/ramp0이며 원래유한준비제어를 유지한다.
- 두새Python AST parse 통과. 리뷰어 실제GPU물리실행은0회이며 source경로보완/실제조기접촉/왕복검출/왼손없는유지는 후속실행 검증대상이다.

## 검수 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/run_chest_upperarm_initial_v1.py`: `8876df5e397f80677ec3b068df20369e1c69848490fd52b5314ee19123f6aa0b`
- `/home/ajou/yigyu/3/stability_adapter_2/search_chest_upperarm_initial_v1.py`: `500303b9db80bb2d6498b495cb860e47e8d010e4143e67728f84cade2980dd2a`
- `/home/ajou/yigyu/3/stability_adapter_2/CHEST_UPPERARM_INITIAL_PLAN_V1.md`: `df5acfa2a16b8ee086c0b1d3844374f4e8d4a82ff5187de6dbc2b3cf69fae749`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/search_v1/near020/candidate.json`: `ee693a8a4623b28d38b52f3f1d48e0b56cfd63690bd1e78df4681b89e976683a`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/search_v1/near020/config.json`: `4c3dab14ea97ce44584f0ed086c49835b5b46b4d9957796ae30f806e57304894`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/search_v1/near020_audit.json`: `c776605d2b286cd27a1c0eca3b49c57f4205165dcf9c6b9056e8972793119bd0`
