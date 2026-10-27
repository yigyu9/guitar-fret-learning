# 왼팔 재접촉 후 초기 철수 보완 검수

판정: **문제없음. Critical 0건, Warning 0건, Suggestion 0건.** 새 source v3/계획 V4/실행 wrapper를 읽기 전용 확인했다. 기존 pilot의 왼 손목 재접촉 결과와 취소한 후보를 보존하고, 새 동일240Hz 기록 두 진단을 진행하는 범위는 타당하다. 추가 native·학습·원본 수정 없이 이 리뷰만 작성했다.

[검색 v3:21](/home/ajou/yigyu/3/stability_adapter_2/search_om_no_strap_upper_arm_v3.py:21)의 변경은 왼 palm 초기 목표 `[0,0.20,0.25]m` 이동 및 새 계획·출력경로다. 기존 ±0.8rad∩native 한계·palm 방향·전체 간섭/모든 capsule gap·오른상완 수락 조건은 유지된다. 입력743개 SHA가 현재 일치하며 두 후보는 sourceclear와 모든 gate를 통과했다. 두 config를 독립 EnvironmentContract로 읽어81개 q_ref/모델 한계/codec 계약도 통과했다.

공통 왼팔 최대 scalar 변화는0.789146rad, palm 목표 오차는 약6.92×10⁻⁸m/2.32×10⁻⁵°다. 상완 후보의 근위 gap1.000532mm·전체 capsule 최소0.498090mm 및 오른 palm 이동0.124825mm는 기존 값과 같다. 쌍의 차이는 오른팔12뿐이며 기타 p/q와 나머지 초기목표·물리 계약은 유지된다. source상 간섭 없음과 큰 초기 철수는 실제 PD 오차로 인한 재접촉 방지를 보장하지 않는다.

[runner v3:20](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v3.py:20)는 검수한 EndpointRecording·원 factory·GymTrialRecording alias·정상 constantPD를 그대로 사용한다. 새로운 힘/목표/상태 setter나 추가 적분은 없고240Hz callback/state 불변 검사가 유지된다. metadata는 v3→endpoint→base→원save 순서이며 재귀를 발견하지 않았다. V4/searchV3 SHA를 공유 attempt closure에 추가해 post 검사에 포함한다. 현재 초기 계획은 `current_initial_pose_plan=V4`로, 보존한 base metadata의 `plan=V2`와 구분한다.

[배너:17](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v3.py:17)는 ‘left-away initial target’으로 명시해 초기 철수와 지속 무접촉을 혼동하지 않는다. 기존 pilot의 L_Wrist 양의 lambda295/300은 무왼팔 유지 증거로 쓰지 않는다. 새 두 조건의 모든 왼팔/손–전체 기타 presence/positive를 동일1200 post-physics endpoint에서 집계하고 상완 접촉·최대/종료 이동·SO3를 함께 보고한다. endpoint도 solver 내부 전체 substep·연속시간 힘0·힘 분담의 인증은 아니다. 왼손 연주 준비 자세나 안정화 성공의 채택은 후속 결과 판단 범위다.

검수 SHA256: wrapper `b145825f95ee96cca7575a7d46600f11dc68a8015295544cd174dca069308933`; 검색 v3 `fbc9ddb5259552dac598bb2dfc7e59cdf29a58182606f9368b9fb2ff8a5c84d5`; 계획 V4 `17e750ad1ac0bd181e76e937edaf883999ded2f4979beb8d7301119c1101bd72`.
