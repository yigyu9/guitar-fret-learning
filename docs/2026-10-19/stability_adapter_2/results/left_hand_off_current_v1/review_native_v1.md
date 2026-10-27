# 왼손 OFF native 독립 검수

요약 판정: 검증 문제없음, 물리적5초 유지 실패. t0부터왼손이떨어진조건에서실제LEFTcontact/추종task0을확인했으나0.933333초에기타안전중단됐다. 원본 수정·native 재실행은 하지 않았다.

Critical: 0

Warning: 1

- [분석기:11](/home/ajou/yigyu/3/stability_adapter_2/analyze_left_hand_off_current_v1.py:11), [동시각 분석:12](/home/ajou/yigyu/3/stability_adapter_2/compare_left_hand_off_current_v1.py:12): 개별before-map은import helper를직접포함하지않는다. **독립map만으로helper보존을주장하지않고 currentnative/timeline의합성pin근거를사용한다.** initial_pose_noise_v1.py와upper_arm_static_geometry_v1.py가 nativeattempt/timeline/currentSHA 모두exact임을확인했다. 숫자·물리조건 검증은유효하며 standalone분석기map의범위를구분한다.

Suggestion: 0

- [report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/native_back100_static/report.json):224physics/56control·0.933333초,completed=false/guitar safety displacement. 입력불변true/금지호출·strap·checkpoint·학습0이다. 부분MP4는29frame/0.966667초이며5초로늘리지않았다.
- [명령/시계 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/timelines_v1.json): save를메모리로우회한 read-only실행으로224행 전체의G점속도/가상요청/Jacobian·좌우명령/body9중력PD 합성·float32 cap/33EFFORT소유권·48POSITION·56control시계를 재계산해canonical과1e−10이내일치했다. current_G_point_tracking=true는오른쪽/몸통 제어이며LEFT추종을뜻하지않는다.
- [LEFT 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/left_off_analysis_v1.json): native초기고정69q/G39fullstate/right·trunk지원bodyfullstate와two_block_configuration이baselineexact이다. 모든224endpointLEFT팔·손contact0,enabled=false/force3/task12exact0을read-only재계산해canonical전체와일치했다. 왼팔전체torque0이나passive평형이아니며gravity/PD가유지된다.
- rawtrace에서actorroot최대/최종208.335mm,BB중심77.452mm,SO3 35.625°를독립재계산했다. 두안전기준(actorroot200mm/SO335°)을종료표본에서초과했다. root/lower9body초기→최종stateexact와81=33EFFORT+48POSITION을확인했다. 상완185행(step5~189,마지막0.7875초),허벅지222행(step3~224),LEFT0을원시접촉에서확인했다. 허벅지local접촉을Gframe으로별도변환해narrowwaist presence/positive222행도확인했다. rawlambda는측정Newton힘이아니다.
- [동시각 결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/same_time_v1.json): 실제57개60Hz공통표본의종료0.933333초까지BB추가차55.547114mm/SO3차26.192832°를read-only재계산해exact일치했다.5초비교/외삽·서로다른peak의차·왼손접촉제거의단독인과효과가아니다. 초기왼팔질량배치와목표변경도포함한다.
- sourceV1/V2/V3 총6행중2수락,작은V3/back100만native실행했다. 실제LEFT0이므로추가후보를쓰지않은판단이현재질문에맞다. native·analysis입력map(1619/60)현재SHA를독립확인했고같은helper의native/timelinebeforeSHA연결을확인했다. 이후main추가는별도prefixsnapshot으로구분한다.

LEFT 분석기 SHA256: `4f1be34ea49724a14bfefb4118729c29e7a0ed5a2f9d4c39ff5b19752a943e7b`.
