# 몸 옆 뒤쪽 왼팔 배치 사전 검수

판정: **문제없음. Critical 0건, Warning 0건, Suggestion 0건.** source v4/계획 V5/runner v4의 변경만 읽기 전용 대조했다. 추가 native·학습·원본 수정 없이 이 리뷰만 작성했다. upper_arm_close 단일 진단의 실행 차단 오류를 발견하지 않았으며 실제 무왼팔·상완 지지 성공은 아직 인증하지 않는다.

[검색 v4:21](/home/ajou/yigyu/3/stability_adapter_2/search_om_no_strap_upper_arm_v4.py:21)의 변경은 왼 palm 초기 목표 `[0,−0.30,−0.10]m`와 새 계획·출력 경로다. ±0.8rad∩모델 한계·전체 간섭/모든 capsule·상완 접근 gate는 유지된다. 저장 두 source후보는 통과했으며 입력 SHA746개가 현재 일치한다. 왼 palm 오차0.070793mm/0.083907°와 오른상완 근위 gap1.000532mm·전체 capsule 최소0.498090mm를 확인했다. 왼팔 최대 delta0.800000011921rad는 float32 저장 경계의 미세 차이이며 두 config를 독립 EnvironmentContract로 읽어 native 한계/81D codec 통과를 확인했다.

[runner v4:6](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v4.py:6)는 현재 계획 V5/searchV4 SHA·초기 target 설명만 바꾸고 검수한 EndpointRecording·정상 constantPD·실제 strap OFF·배타 기록·상태 불변 검사를 그대로 사용한다. metadata→endpoint→base→원save 경로와 공유 closure pin도 유지된다. 배너는 지속 무접촉을 미리 단정하지 않는 ‘left-away initial target’이다. 새로운 힘/목표 제출/적분/상태 setter를 추가하지 않는다.

[계획 V5](/home/ajou/yigyu/3/stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V5.md:7)는 source reference 파일 생성과 실제 실행을 구분하며 신규 native는 상완접근1개만 실행한다. 앞선 두 비독립 pilot의 왼팔 접촉·PD 오차·원영상/소스는 보존하고, 세 번째 단일 실행을 서로 다른 왼팔 조건의 인과 짝비교로 쓰지 않는다. 같은1200 post-physics endpoint의 왼팔/손–전체 기타 presence/양lambda·상완–바디 접촉과 최대/종료 기타 이동·SO3·후기 경과를 직접 판단한다. source 통과·endpoint 접촉 표본은 cooked clearance·solver 내부 연속시간 비접촉·힘 분담이나 연주 성공을 인증하지 않는다.

검수 SHA256: 검색 v4 `a342e7b89d3a6eeb6cd1e5a76f0cc876f72a10417b9ba56341d5f6091ab1607e`; runner v4 `fd647d4a1eab2750c295750eb74e0589be94c6d93f004845afa43c22ba98d500`; 계획 V5 `514a17596ce54c7ae9cc8374121fd42b268b049d1e28ca88799095cdc2d9c13e`.
