# 가슴·오른쪽 위팔 초기 지지와 Elbow/Wrist 타현

초기 배치를 만들고 실제 Isaac Gym 5초 실행으로 검증했다. **왼손을 떨어뜨린 비교에서도 가슴/오른상완 동시 지지가0.1125초에 형성되고, 기타는 최대4.915mm/2.833° 움직이며 유지됐다.** 오른 Elbow/Wrist6개만 목표를 바꿔 원래 가상피크 검출기로 down6→1/up1→6 왕복 타현을 확인했다.

기타는자유·스트랩OFF이며 root/하체고정·자기충돌ON이다. 기타고정·강제손부착·외력·지속pose덮어쓰기는없다. 몸통/오른근위팔의유한제어는유지한다. 다른75목표는준비값이며실제상태를고정한것이아니다. 학습체크포인트를연결한곡연주성공은아니다.

## 조건별 실제 결과

240Hz 물리 상태와 접촉 기록으로 계산했다. 이동은초기바디BB중심대비유클리드거리, 회전은초기대비SO(3)각이다. 각항목최댓값의시각은다를수있다.

|조건|동시양의lambda첫시각|최대이동|최대회전|왼팔·왼손접촉step|왕복6현|
|---|---:|---:|---:|---:|---|
|hold: 초기각유지|0.125초|2.759mm|0.680°|804/1200|미실행|
|near: 왼손넥근처|0.125초|4.287mm|1.219°|1090/1200|통과|
|clear: 왼손약60.2mm물림|0.1167초|4.601mm|2.486°|326/1200|통과|
|far: 왼손약106.3mm물림|0.1125초|4.915mm|2.833°|0/1200|통과|

네조건모두오른손목·손–기타접촉0이다. full5초완료4회이며각1200physicsstep/300controlstep/영상151frame이다. 영상은초기0초프레임을포함해30fps에서5.033초로저장된다. 종료는예정된5초관찰종료이며물리적평형판정으로정지한것이아니다. native_hold_v1은카메라이름충돌로0step에서실패한이력으로보존했다. 테스트viewer의0.2초2회는별도이며5초시험횟수에더하지않는다.

## 배치와 남은 한계

near와far의초기기타·몸통·오른팔은같다. 바디BB중심월드좌표는 **(0.143238,−0.001125,0.683019)m**, actor-root는 **(−0.258565,−0.005698,0.723789)m**다. actor-root쿼터니언xyzw는(−0.471704,0.446243,0.592982,0.476168)이다. 두중심을혼동하지않는다. 원래도면기타형상·질량·재질은그대로다.

초기source간격은Chest/오른상완/오른허벅지각0.2mm다. 정적source기하검사와실제PhysX cooked접촉은구분한다. 오른약지/소지는기존준비각대비1_x−0.21/2−0.30/3−0.18rad씩굽힘을완화했다. 이는절대각이아니며타현중이각을추가로움직이지않는다. 61점source경로의손/기타·비인접인체검사와실제오른손접촉0을확인했다.

**가슴접촉은타현후반계속유지되지않는다.** far의3.75~5초300step에서Chest접촉0, 오른상완/오른허벅지양의rawlambda각300step, 왼허벅지도259step이었다. 따라서오른상완·오른허벅지만의수동평형이나항상가슴에끼워진상태로해석하지않는다. rawlambda는보정된N단위지지력이아니다. 이번결과는시작직후정착과단일왕복궤적의5초검증이며장기연주·외란대응은후속검증대상이다.

왼손준비기본값은near다. 손바닥은아래면, 엄지는뒷면, 다른손가락은앞면근처로두며물리적접촉은허용한다. far는왼손무지지비교전용이고삼면준비로부르지않는다. 이전clear candidate의상속된near메타데이터는 [별도정정기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/metadata_scope_correction_v1.json:1)에범위를명시했으며소비된원본을수정하지않았다.

## 시각자료·초기값·재현

- [이미지·장면설명·영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/artifacts_v1/README_v3.md:1).
- [영상모음](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/chest_upperarm_initial_v1/README_v2.md:1).
- [VS Code 테스트실행V2](/home/ajou/yigyu/3/stability_adapter_2/chest_upperarm_pose_test_v1/README_v2.md:1), [전체81초기값](/home/ajou/yigyu/3/stability_adapter_2/chest_upperarm_pose_test_v1/initial.json:1).
- [계획완료체크](/home/ajou/yigyu/3/stability_adapter_2/CHEST_UPPERARM_INITIAL_COMPLETION_V1.md:1), [변경파일·줄번호](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/changed_files.md:1).
- [권장물리분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/analysis_v1.json:1), [viewer검증V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/viewer_verification_v2.json:1).

기존strike분석기의up3.95초집계창은실제V7시작3.75초와달라첫두줄을누락했다. 원래raw RELEASE에는1~6줄이모두있다. 기존strike_detector_v1/v2.json의False는이집계오류로보존하고,analysis_v1.json에서실제명령구간3.75~4.45초로보완했다. 검출기임계값/판정자체는바꾸지않았다.

실제생성/초기값/재질/PD/자기충돌/입력SHA검사와headless0.2초경과를확인했다. 실제GUI창·키통합은DISPLAY부재로미검증이다. viewerV1의nestedhelper사전SHA누락/상속로그설명은원본을보존하고새V2로보완했다. 기존stability_adapter/·공유모델·독립fresh학습작업은수정하지않았다.
