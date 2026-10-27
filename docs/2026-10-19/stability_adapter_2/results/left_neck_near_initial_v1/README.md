# 왼손을 넥 주변에 둔 새 초기 자세

손바닥은 넥 아래, 엄지는 넥 뒤, 네 손가락은 줄 앞의 가까운 위치로 초기 배치를 만들었다. 실제 시작은 손바닥 약1.3cm·엄지1.1cm·네손가락0.5~1.0cm의선택표면간격으로 강제접촉이없다. 기존몸통·오른팔·기타초기배치는보존했다.

현재값은 [설정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/config_v1/config.json:3)과 [81 초기각](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/search_v5/station20mm/candidate.json:85)을 쓴다. [완료 문서](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_NEAR_INITIAL_COMPLETION_V1.md:1)에 초기면 규약·실제5조건·후속계획을 기록했다. 최신 사진·영상 설명은 [결과 문서 V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/artifacts_v1/README_V2.md:1)를 따른다.

![실제 초기 손 배치](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/artifacts_v1/native_hold4_hand_close_crop_v1.png)

## 유지와 정책 연결은 구분

준비 위치의 유한 관절 보정5초에서는 손목 최대오차17.018mm, 왼팔·손–기타접촉presence0/1200, 기타collisionBB중심변화9.296mm/전체회전2.835°였다. 5초 끝 손바닥면간격은약3.2cm라서 모든부위를초기간격에고정한것은아니다. 모델cap의사람관절토크만쓰고기타힘/강제부착/실행중pose쓰기는없다.

![준비 자세 5초 실제 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/hold_v4/whole_body.mp4)

같은초기상태에서2초뒤준비보정항을끄고등록Fret/Strikebaseline을연결했다. 각26추론·2.433333초에원Strike의잘못된현교차조건으로종료했다. 이전Fret손목/finger-back안전종료는이번PLAY에서False였으나압현0·타현hitFalse이고곡완주가아니다. 정산된공동음악event2건은둘다실패였으며현crossing4건이다. 다음은오른손pick READY·타현진입과왼손음별압현확인이다.

## 자료와 검증

- [공식 실측 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/native_analysis_v3.json:1) · [분석 보완 이력](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/ANALYSIS_NOTES_V1.md:1)
- [5가지 조건의 영상10개](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/INDEX_V1.md:1) · [원본·사본 SHA 및 실제 프레임 수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/manifest_v1.json:1)
- [독립 실측 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/review_native_v1.md:1)

native4개는실행을정상종료(그중pair는음악실패)했고높은gain1개는1.833333초물리속도안전중단이다. source1/2 계산중단과source3/4/5의6후보(거절5/수락1)는native시도집계에넣지않는다. sourcefacet/endpointpresence/가상task요청힘을cooked연속clearance나실제접촉력인증으로확대하지않는다. 학습업데이트0회다.

[변경 파일과 실제 줄 번호](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/CHANGED_FILES_v1.md:1)에서 구현·초기값·보존 이력을 확인할 수 있다.
