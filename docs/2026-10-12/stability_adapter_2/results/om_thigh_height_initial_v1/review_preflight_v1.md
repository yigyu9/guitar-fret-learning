# 낮은 OM 기타 초기 높이 사전 검수

판정: **문제없음. Critical 0건, Warning 0건, Suggestion 0건.** source v2의 통과 후보 두 개를 지정된 정상 PD 5초 진단에 보내는 코드에서 차단 오류를 발견하지 않았다. source 결과·새 계획/runner·기존 제어 계약만 읽기 전용 확인했으며, 실제 낙하 감소·지지·연주 성공은 인증하지 않는다. 추가 native·학습·원본 수정 없이 이 리뷰만 작성했다.

[검색 v2:27](/home/ajou/yigyu/3/stability_adapter_2/search_om_thigh_height_initial_v2.py:27)는 기타 x/y/quaternion과 인체 고정 초기값을 유지하고 world z만 내려 **양쪽 Hip capsule–OM 최근접 거리의 최솟값**을 맞춘다. 양팔24채널만 기준±0.6rad∩native 한계로 IK해 양 palm의 기타 상대 초기 p/r를 보존한다. [최종 gate:42](/home/ajou/yigyu/3/stability_adapter_2/search_om_thigh_height_initial_v2.py:42)는 전체 source 간섭·모든 지정 인체 capsule 양의 0.2mm 간격·양Hip 최소 목표·양손 2mm/1° 오차를 함께 검사한다. v1의 왼Hip 교차 후보는 거절·보존됐으며 v2는 교차 허용 완화가 아니다.

저장된 두 v2 후보는 source_clear 및 모든 gate를 통과했다. 8mm 조건은 z를 100.558260mm 내려 L/R Hip gap 약 8.000000/17.138540mm, 3mm 조건은 107.109548mm 내려 약 3.000000/11.666880mm다. 전체 capsule 최소도 각각 8/3mm다. 후보 변경 채널은 양팔24개뿐이고 최대 scalar 변화는 각각 0.274691/0.293286rad이며 body/head/finger/root/lower와 기타 회전은 그대로다. 양손 위치 오차는 최대 약 5.5×10⁻⁸m, 방향 오차는 10⁻⁵° 미만이다. 검색 입력 SHA 735개는 현재 파일과 일치한다.

[runner:17](/home/ajou/yigyu/3/stability_adapter_2/run_om_thigh_height_initial_v1.py:17)의 metadata wrapper는 attempt에 V1/V2 leaf와 searchV2 SHA를 추가하고 동일 공유 closure를 갱신하므로 기존 종료 후 SHA assert에도 포함된다. 실제 config는 후보 경로/SHA만 바뀌며 정상 단일81D POSITION PD·arm rate1rad/s·기존 physics 4step 및 passive strap ON 경로를 재사용한다. PI/별도 target 제출/상태 setter를 추가하지 않는다. side camera 생성과 strap 명령 기록은 native_state 전후 exact를 검사한다. 현재 계산 장력과 직전 적분 명령을 센서 힘으로 해석하지 않는다.

[권위 계획 V2](/home/ajou/yigyu/3/stability_adapter_2/OM_THIGH_HEIGHT_INITIAL_PLAN_V2.md:5)는 간격이 수직 높이와 다르고, 가까운 **왼쪽** 허벅지가 이번 선택 기준이며 오른 Hip의 실제 간격은 별도 값임을 정확히 구분한다. source 통과는 PhysX cooked clearance·실제 무관통 또는 지속 지지 보증이 아니다. 높이와 양팔 초기 배치가 함께 바뀌는 비교이며, native 초기 pose·자체 초기 기타 변화·허벅지/몸통/팔 접촉·속도·금지 API는 후속 결과로 판단한다. 손가락 동작·왼손 철수·연주·기타 고정 성공을 주장하지 않는다.

검수 SHA256: 검색 v2 `c1d647ecf21319061ebdcb512b4193ba7e9a3009f65504741430467303ea3c0e`; runner v1 `ef969cc86ca7defe133ce37ca7a08df7942b7bfa9d092d4f168d6a8369e1d2d9`; 계획 V2 `a3ea376ecd186debb3e0232a93633418b5c1b83422c8712e6fa3d5f8d80e7fd5`.
