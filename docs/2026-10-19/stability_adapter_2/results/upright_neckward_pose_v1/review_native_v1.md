# Native 검수 — 펴진 넥 방향 자세

요약 판정: **문제없음.** 기록·수식 및 한정된 정지/팔꿈치 비교 판정이 원자료와 일치한다. Critical 0 / Warning 2 / Suggestion 0. 성공 범위는 선택19° 초기값의 5초와 팔꿈치 scalar 목표 ±5° 한 주기이며 연주·반복 강건성·장시간 유지 인증이 아니다.

완료7회 모두 1200 physics/300 control/5초다. 앞선30°·26°·follow10·follow20의 후기 상완 접촉은0/120이고20°는120/120이나 최종SO3 3.001326°로 기존<3° gate가 실패했다. 이를 완화하지 않고 별도19° source를 생성한 경로가 맞다. 고정world26/follow10/follow20 초기 JSON 전체가 exact다. 입력902개 및 새19° source 입력629개 SHA를 검수 시점에 대조했고, 고정54·모델·genuine FK·기타회전/BB범위도 통과했다.

- [runnerV1:114](/home/ajou/yigyu/3/stability_adapter_2/run_upright_neckward_pose_v1.py:114), [runnerV2:118](/home/ajou/yigyu/3/stability_adapter_2/run_upright_neckward_pose_v2.py:118), [runnerV3:119](/home/ajou/yigyu/3/stability_adapter_2/run_upright_neckward_pose_v3.py:119)의 고정/추종 목표·COM 점속도·cap 및 인간 Jᵀ 합산/model clip을 앞선6000행과 선택조건2400행에서 재계산했다. 최대 합산 요청 오차1.78e−15Nm다. 총2100 control의 POSITION69/state 보존과 single actor owner 경로, forearm pointforce0·right12 effort·root/하체 고정·strap OFF·자유 기타·금지 API0 계약을 확인했다. 관측 `safety_stopped`는 토크 중단으로 해석하지 않는다.
- [motion gate:11](/home/ajou/yigyu/3/stability_adapter_2/prepare_upright_neckward_motion_v1.py:11)의 final/settling 기준은 그대로다. 선택19° 정지는 BB9.548665mm/SO3 2.995398°, 후기상완120/120,2→2.5초 .221586mm/.067815°, Head/왼쪽/오른원위접촉0으로 통과했다. 실제 앞기울기39.846996°/heading27.986843°는 이전48.347770°/22.198890° 대비 −8.500774°/+5.787953°다. source −6°/19°를 실제 절대각으로 부르지 않는다.
- [비교:15](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/compare_elbow_motion_v1.py:15)의 두 조건 initial JSON 전체와 2.5초까지 trace exact를 확인했다. 실제 동작 scalar 왕복10.094022°와 moving-minus-static 왕복10.092677°는 다른 양이다. 후자의 상관 .999946426/incremental RMSE .04832764°, absolute q-target RMSE .09859979°를 재계산했다. 동시간 기타 추가 BB최대 .077660mm/SO3 .042115°는 임시 비교 gate 안이다. 동작 최종BB9.574004mm/SO3 2.990860°다.
- [공간분류:22](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/analyze_contact_region_v1.py:22)의 native local-origin feature+offset 변환/캡슐 축 투영/G상부영역을 raw로 재분류했다. 정지·동작 각각 지정근위0~35%+G상부영역1117/1200, 양의 raw lambda1113/1200이다. 최대 feature pair오차1.28e−7m/캡슐반경차 .360079mm가 quality 범위 안이다. 전체 상완1173/1200·오른Hip1194/1200이며 Head/왼쪽/오른원위·전완·RThorax0이다. source 근위0~30% 최소 gap과 native 엄격35% 판정은 구분한다.

Warning 1 — [gate:11](/home/ajou/yigyu/3/stability_adapter_2/prepare_upright_neckward_motion_v1.py:11)은 최종값 기준이다. 정지 회전 여유는 .004602°뿐이고 최대BB10.380810mm/SO3 3.313974°는 최종 gate 수치와 다르다. 전체5초 내내10mm/3° 아래였다거나 반복 강건성이 확보됐다고 설명하지 않아야 한다. 근위 접촉 발생·raw lambda는 힘/모멘트 분담·N단위 접촉력·해부학적 겨드랑이 조직 또는 연주 가능성 인증이 아니다.

Warning 2 — [runnerV1:13](/home/ajou/yigyu/3/stability_adapter_2/run_upright_neckward_pose_v1.py:13)의 실행 metadata는 원PLAN1과 [runnerV1:134](/home/ajou/yigyu/3/stability_adapter_2/run_upright_neckward_pose_v1.py:134)의 search_v1을 계속 참조한다. source20/19의 추가 실행 맥락은 별도PLAN4/5이며 실제candidate/config pins로 초기값을 검증했다. 최종 문서는 실행 맥락의 후속 계획과 원attempt metadata를 구분하고 소비본을 수정하지 않아야 한다.

검수 한계: 새 원자료·수식·core 입력 SHA 및 접촉/자세/비교 producer를 읽기 전용 대조했다. 추가 native/학습/소스 수정0. 최종 artifact 문서·PNG·영상 복사 SHA와 main append/preservation 전수 봉인은 별도 후속 검수/root 범위다.

주요 증거 SHA256:

- comparison: `12725d777b88440778fa1d4cf2875727836cd677fb399359cfa9cfe539891a21`
- contact region: `acb40e54b7a984b6e3baaeb8fd679856492eb352d50eccf6f7cd6021271fd86f`
- torso posture v7: `660118c6cea1557cbb7587bd7b27e8e8d0086816e8c102e96902958fe7d358c7`
- motion verification: `4d23de8f1dfdb261c7194071c1eb3ea030344154d8036982f65cb72ec5bff7d1`
