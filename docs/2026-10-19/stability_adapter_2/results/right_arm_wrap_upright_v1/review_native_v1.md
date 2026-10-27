# 오른 상완 감싸기 native 독립 검수

요약 판정: 문제없음. 두5초 실행에서 더 곧은 초기 몸통과 전체 R_Shoulder 접촉·waist 유지가 확인됐다. 다섯 보호 중단은 실패/부분 실행으로 분리한다. 반복성·일반 연주·오른팔 단독 지지 인증은 아니다.

Critical: 0

Warning: 2

- [posture_final_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/posture_final_v1.json): 완전 실행의 전체 상완 접촉1196/1200행에 비해 raw 축0~1 접촉은181행이고 근위45%접촉은0이다. 끝점 cap 관여가 크므로 **근위30/45% 감싸기나 축 내부 접촉1196행이라고 설명하지 않는다.** source 최근접0.982890은 전체 R_Shoulder 강체 지점이다.
- [timelines_final_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/timelines_final_v1.json): 정지 bbox중심 최대34.001mm/SO3최대16.503°, 종료26.012mm/11.981°,2→5초 추가7.342mm/3.344°이며 왼팔·손 접촉1189행이 남는다. **5초 관측 유지, 실제 drift와 왼손 기여를 함께 명시한다.** 접촉lambda와 유한human 가상요청을 실제 Newton 접촉력이나 단독 지지로 바꾸지 않는다.

Suggestion: 0

검증 범위와 근거:

- [원시 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/native_wrap55_static/report.json), [파동 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/native_wrap55_elbow_wave/report.json): 두 사례 각각5초/1200physics/300control 완료. 이전 relief12(424),relief20(128),upper20(148),upper40(232),wrap40(180)는 guitar guard 중단. 합계3512physics/878control이며 strap/checkpoint/training/금지호출0, 입력불변true다.
- [timeline 분석기:31](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_timelines_v2.py:31), [명령 감사:56](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_timelines_v2.py:56): 저장을 메모리로 돌린 read-only 실행으로 모든7사례의 실제시계/행수·G추종점 속도·가상요청·Jacobian·child Elbow/Wrist0·좌/우 명령 합성·body9 중력/PD·최종float32 cap/소유권·정적/파동 목표·48POSITION을 재계산했다. canonical cases/comparisons와 차이는 부동소수점끝자리3개(최대약3.6e−15)뿐이었다. source/native 재실행이나 출력파일 재생성은 하지 않았다.
- [실제 초기값](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/native_wrap55_static/initial_values.json): 81DOF=33EFFORT/48POSITION, 후보q_ref와exact. 모든7사례의root/lower9body 초기→최종native state가exact이며 최초FK/초기finger42/모델한계/PD/질량 검증이 모두true다. POSITION 목표 보존과 실제 손가락 상태를 구분한다.
- [posture 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/posture_final_v1.json): 직전Chest53.412°→현재33.412°로 추가20° 완화, Torso13°/Spine17° 완화. 부모상대 회전차는13°/4°/3°로 누적world 완화량과 다르다. 정지 종료Chest35.958°,파동35.909°다. 기타초기 몸쪽25mm와높이+1.030mm, G39 균일이동 잔차0.154µm/회전차0.200µrad(직전기준)이며 원래위치 고정으로 설명하지 않는다. localZ 투영은 자세proxy다.
- [원시endpoint](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/native_wrap55_static/media/physics_endpoint_contacts.json): 모든7사례의 실제240Hz endpoint 순서/시계와 local 상완 축분율을 XML축으로 독립 재계산해 posture 분류와 일치했다. 완전 두사례 전체상완 presence/positive1196행·후기120,Chest/trunk/rightforearm/rightdistal/head0,왼팔·손1189행이다.
- [waist 분석기:24](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_waist_v1.py:24): G:body local접촉점을 실제endpoint body pose→world→guitar actor root로 변환하고 G_X>0/waist_Y구간을 검사한다. 두완전사례의 모든점 좌표·분류를 독립 재계산해 [waist_final_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/waist_final_v1.json)과 일치했다. presence/positive1198행·후기120이다. partial 후기null,입력사전/종료SHA구조가 맞고 read-only다. AST통과.
- [파동 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/timelines_final_v1.json): 완전 두사례 초기전체state와첫2.5초trace exact. 실제elbow2.5→5초범위10.101781°이며, 같은시각 정지 대비 추가bbox중심차최대0.458126mm/SO3차0.200994°다. 이 한주기에서 상완·waist 유지가 관측됐으며 운동학적 점 독립성을 일반 동적 독립성으로 확대하지 않는다.
- Source7배치21행/4수락/17거절 및 각소비입력SHA를 현재파일로 재대조했다. 이전소비본 보존과 원시후보를 확인했다. [선정후보](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/search_v7/relief20_fraction55/candidate.json)는 full 상완witness/axis-soft-guide 및 Thorax10N4mm·상완20N8mm 설정으로 native에 연결됐다.
- 세canonical 분석의 입력3479/33/9개를 각각 확인했다. mainPLAN만 실행후 승인된 완료기록 추가가 있어 [before스냅샷](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/navigation_before_v1/PLAN.md)의 실행SHA `f5d379ac…` 및 현재1234행byte-exact prefix를 대조했다. 명령재계산에서도 이봉인문맥만 사용했다. source/config/mesh/raw의 그외 SHA는현재와일치하며 canonical 원본을 수정하지 않았다.

Waist 분석기 SHA256: `8659984f15b9eb4713e78b15048076e59411600f019cece448dbe4f12af23826`.
