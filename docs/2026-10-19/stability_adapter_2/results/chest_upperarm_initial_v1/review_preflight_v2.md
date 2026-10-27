# 초기 가슴·위팔 지지 V2 사전 검수

요약 판정: **수정 권장**. Critical 0건. V2 카메라 수정은 적절하며 새 helper가 source 경로 충돌을 구체적으로 발견했다. 현재 후보를 비관통 타현 경로로 채택하기 전에 오른손 준비/경로를 조정해야 한다. 물리 진단 실행 자체의 제어 안전 오류는 발견하지 못했다.

## Critical

없음.

## Warning

- `/home/ajou/yigyu/3/stability_adapter_2/check_chest_upperarm_strike_path_v1.py:43`: 현재 source_path_v1.json은 passed=false다.61시간표본 중39표본에 RH:ring3/RH:pinky3–G:body 음수간격이 있고 최악은4.0초pinky3의−18.0403mm다. Pick IK오차는.000000448m미만·ball최대113.407°로 도달성은 통과하지만 손 전체 비관통은 아니다. 원자료를 보존하고 새 후보/오른손 초기 준비 또는궤적을 조정한 별도 검사로 해소한 뒤 clear타현 후보로 채택할 것을 권장한다. Native실제RH접촉 검사도 함께 보고해야 한다. 이39는 시간표본 수이며 다중OMpiece의중복pair행235/104를 물리스텝으로 해석하면 안 된다.

## Suggestion

- 같은 파일44행: console의path passed는ball160°조건을 포함하지 않지만 저장JSON의passed는포함한다. 이번 후보는ball을통과하므로 결과차이는 없으며, 후속 분석은 저장JSON의passed를 기준으로 삼는다.

## V2 수정 및 helper 검토

- V1→V2 diff는 leafplanpin 추가와 카메라key/path support_side→chest_arm_close뿐이다. 기존 제어·초기후보·physics·torque·target 소유권을 바꾸지 않는다.
- `/home/ajou/yigyu/3/stability_adapter_2/run_chest_upperarm_initial_v2.py:93`: 새key는 상속Recorder의support_side1280×960카메라와 충돌하지 않으며 recorder/strapviews와frame디렉터리도 새key로 일치한다.1280×720을 요구하는GymTrialRecording 경로와 맞는다. V1실패는0physics camera오류이고 초기FK/G/source/PD/mass/rootlower 검증은 통과한 기록을 보존한다.
- Sourcehelper는 config/EnvironmentContract직접입력, 실제V1nativeinitial, humanoid/GXML, 선언된전체mesh, 직간접geometryJSON 및flathelper소스에 사전/사후SHA를 남긴다. 무관한freshnamespace/mainPLAN은 실제sourceinput처럼 추가하지 않는다.
-22행에서 actualinitial로 FK를 보정하고 nativeq_ref를 이용한다. V7desired_point의2–5초를61점으로샘플링해 각점R_Elbow/R_Wrist6IK를 구하고 other75exact를검사한다. movingdistal/RH와모든Gpiece·비인접human signedgap을 query한다. 조상거리≤2 및 기존동일손 내부 제외범위는 유지한다.
- StaticsourceIK/간격 검사이며 움직이는기타·rate-limitednative실제상태·샘플사이 연속충돌을 인증하지 않는scope가JSON에 명시돼 있다. helper추가로 V1preflight의미검증경로범위를 보완했으며, 그보완결과 현재후보의실제제한을 숨기지 않고passed=false로남긴다.
- V2와helperAST parse통과. 리뷰어GPU물리실행은0회다. HoldV2의조기Chest/upperarm양의접촉·영상, 실제EW6strum 및왼손분리유지는 root의후속실행 검증대상이다.

## 검수 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/run_chest_upperarm_initial_v2.py`: `712f1e55e08377ca1f577748ec0446f901f259a1a10f04bbd79e0da424b3b691`
- `/home/ajou/yigyu/3/stability_adapter_2/check_chest_upperarm_strike_path_v1.py`: `bffab1ac85f80bf40df90777429a8dc2780e725d38e7ec18d3298012761ae8ff`
- `/home/ajou/yigyu/3/stability_adapter_2/CHEST_UPPERARM_INITIAL_PLAN_V2.md`: `78915b42e4a8151f122a1eceb62849588707960afee93201f172e337b397ebbe`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/source_path_v1.json`: `311e5a28fa24714d4146e886cb9f67f6591ef5ff51fda98c7a9e662979cb8422`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/native_hold_v1/initial_values.json`: `25337d04bd164e92216821a56d9318574fc2b305c4a36c319391ac74bcfab7e7`
