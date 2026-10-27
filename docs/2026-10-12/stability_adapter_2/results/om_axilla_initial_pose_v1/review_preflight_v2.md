# OM 겨드랑이 초기 자세 후속 사전 검수

판정: **문제없음 — 새 정적 검색과 거절 처리는 타당하다. 현재 native 승인 후보는 없다.** Critical 0건, Warning 0건, Suggestion 0건. 이전 계획·거리 계산·검색·리뷰를 보존한 새 v3 계획/helper 및 검색 v2만 읽기 전용 검수했다. 추가 native·학습·원본 수정은 수행하지 않았다.

[거리 helper v3:37](/home/ajou/yigyu/3/stability_adapter_2/om_axilla_source_geometry_v3.py:37)는 기존 QP를 유지하고 상완 segment 끝점을 fraction_limit=0.55로 줄이며 반환 fraction을 원 segment 기준으로 환산한다. 원 캡슐의 근위 subset 거리 진단이며 실제 물리 geometry를 변경하지 않는다. [검색 v2:33](/home/ajou/yigyu/3/stability_adapter_2/search_om_axilla_initial_v2.py:33)의 18° 몸통 전경·기타 뒤 30/35/40mm 초기 이동·왼 palm 동일 이동·Head world 방향 유지·관절 native 교집합을 대조했다. [전체 간섭 검사:56](/home/ajou/yigyu/3/stability_adapter_2/search_om_axilla_initial_v2.py:56)는 깊은 복사된 상태에서 모든 기타 body pose를 새 root p/q로 변환해 실제 이동을 반영한다. [수락:64](/home/ajou/yigyu/3/stability_adapter_2/search_om_axilla_initial_v2.py:64)는 근위 영역, 전체 지정 capsule 양의 간격, Chest 5mm 이내, 오른손목 50mm 및 왼 palm/몸통/Head 오차를 hard gate로 검사한다. source 통과와 native 접촉·지지는 별개다.

[완료 정적 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/search_v2/search.json:1)는 입력 SHA 516개가 현재 일치하며 selected가 비어 있다. back30은 sourceclear·Chest 3.215809mm·근위 gap 약 3mm를 통과하지만 근위 G_y=−0.44355873m로 하한 −0.44m 밖이므로 거절됐다. back35는 Chest gap −1.767693mm, back40은 −6.751195mm와 전체 source overlap으로 거절됐다. 세 조건 모두 accepted_for_native=False이므로 부적합 후보를 native로 보내는 오류를 발견하지 않았다.

거절된 현재 후보를 겨드랑이 끼움 성공이나 native 승인 조건으로 설명하지 않는다. 위치 범위·초기 이동·관절 폭 등의 수락 기준을 다시 바꿀 경우 근거를 남긴 새 버전으로 검색하고 재검수한다. 기존 스트랩 길이 법칙·자산·손가락을 유지하더라도 기타/팔/몸통 초기값이 함께 변하므로 몸통 굽힘 단독 효과는 인증하지 않는다.
