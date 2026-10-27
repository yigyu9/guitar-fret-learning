# OM 가슴·상완 초기 받침 사전 검수 v3

판정: **문제없음 — 수정 기준 자세 lean0 및 source v4 lean18_back30의 제한된 두 5초 native 진단을 막는 Critical 없음.** Critical 0건, Warning 0건, Suggestion 0건. 실제 겨드랑이 양면 지지·초기 위치 유지·연주 성공은 사전 승인 대상이 아니다. 기존 리뷰·검색 결과는 보존하고 새 계획 V4/검색 v4/저장 정적 결과만 읽기 전용 확인했다. 추가 native·학습 실행이나 원본 수정은 수행하지 않았다.

[검색 v4:64](/home/ajou/yigyu/3/stability_adapter_2/search_om_axilla_initial_v4.py:64)는 기존 v3와 동일한 관절 한계·간격·전체 source 간섭·머리/몸통/왼 palm 오차·손목 이동 gate를 유지하고 근위 접점의 기타 로컬 Y 하한만 −0.44→−0.45m로 바꾼다. 출력 경로·계획 참조도 새 버전이다. 기존 v3는 0.996mm 영역 미달로 거절되어 보존됐고, v4는 모든 계산 수치가 v3와 exact인 채 위치 영역 정정으로 승인됐다. 이를 최적화 개선이나 안전 간격 증가로 설명하지 않는다.

[완료 source 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/search_v4/search.json:1)의 입력 SHA 518개는 현재 일치한다. 선택 후보는 source_clear=True, Chest gap 3.215809mm, full R_Shoulder gap 2.977334mm, 근위 subset gap 2.987634mm, fraction 0.55, 근위 G 좌표 약 `[−0.178574,−0.440996,−0.003903]m`이다. 지정 6 capsule의 최소 간격은 0.2mm 이상이며 오른손목 이동 21.216065mm·왼 palm/Head/몸통 오차 gate도 통과했다. float32 저장 후보에서 변경된 채널은 body9+head6+양팔24이고 손가락은 그대로다.

[계획 V4](/home/ajou/yigyu/3/stability_adapter_2/OM_AXILLA_INITIAL_POSE_PLAN_V4.md:5)는 기타 Y의 넥 방향과 world 높이를 구분하고 위치 영역 수정 이유를 공개한다. 원 기타 quaternion의 `G −X`를 world로 변환하면 `[0,0,1]`이므로 이 초기 quaternion에서 음수 X 접점의 ‘위쪽’ 표현은 일치한다. G_y≈−0.441m는 바디 중심 −0.4m보다 꼬리 쪽인 사실도 유지한다. 물리 중 기타가 회전한 이후 높이에 같은 설명을 자동 적용하지 않는다.

근위 subset은 원 capsule 일부의 거리 진단이며 실제 geometry 변경이 아니다. 기타 뒤 30mm·몸통 추가18°·팔/머리 초기 조합과 왼 palm 동반 이동을 함께 시험하므로 몸통 굽힘 단독 효과를 인증하지 않는다. source상 양의 3mm 접근은 접촉 또는 지지력 증거가 아니며 PhysX cooked clearance 인증도 아니다. 실제 initial pose·Chest/상완 동시 접촉·자체 초기 기타 변화·왼손 관계·수동 스트랩 경로는 native 후속 검증에서 판단한다. 왼손 철수·연주는 이번 범위 밖이다.

검수 SHA256: 검색 v4 `a8673e8063e3406c11b192cb5a29e7fa730d1dc83362b5459381da21d5b99b8f`; 계획 V4 `f340f006362c3b123ae6bccdcbe5b41c0ffd5a3ed222e9c599a9490f642830e2`; 거리 helper v3 `ad37dc3e0164834bb0f5068a4aaa6012d1655c3b1313f49d6499e02c85131ac8`.
