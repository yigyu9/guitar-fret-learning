# 기타 바디 쪽 기울임 V1 사전 독립 검수

요약 판정: **문제없음 — source 거절 유지, native 진행 후보 없음.** Critical 0 / Warning 0 / Suggestion 0. 새 계획/source 코드와 완료 source 결과를 읽기 전용으로 검토했다. 새 물리 실행·학습은 하지 않았다.

[방향 정의](/home/ajou/yigyu/3/stability_adapter_2/search_body_side_lean_axilla_v1.py:21)는 수평 오른쪽 어깨 축과 world up의 `+cross(up,right)`다. 기준 world up의 작은 회전이 player-right를 향함을 직접 확인했다. 이번 확정 방향은 **정면 화면 왼쪽·기타 바디 쪽·휴머노이드 오른쪽**이며, 이전 넥 쪽 player-left와 다른 방향이다. 실제 Chest 추가 회전 투영은4.00000022°/7.99999985°다. DOF suffix를 world 회전축으로 해석하지 않는다.

Torso25%·Spine62.5%·Chest100% world 방향 목표의 오차는 약7.1e−7° 이하, Head world 방향 오차는 약1.9e−6° 이하다. body9 최대 scalar 변화는4°/8°에서1.322/2.645°, Head/Neck6는1.813/3.634°로 각각±0.12/±0.15rad와 native 모델 한계 안이다. 다른66개 초기 q는 저장81각도를 직접 비교해 exact였으며0° 행은 body/head 변화와 방향 오차0이다. 기타 초기 p/q를 바꾸는 변수를 추가하지 않았다.

**4°와8°는 전체 source clear를 통과하지 못했다.** 전체 R_Shoulder gap은 각각−26.315/−52.100mm, 근위0~65% 구간 최소 gap은−5.242/−28.969mm다. 음수는 source analytic 겹침 지표이며 실제 PhysX cooked 관통 깊이 인증이 아니다. [수락 코드](/home/ajou/yigyu/3/stability_adapter_2/search_body_side_lean_axilla_v1.py:33)가 이 조건을 거절하고, [완료 결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/search_v1/search.json:1)의 selected는 비어 있으며 native 수는0이다. 입력585개 현재 SHA 불일치0개를 확인했다.

[row의 full81 저장](/home/ajou/yigyu/3/stability_adapter_2/search_body_side_lean_axilla_v1.py:32)은 진단 원자료다. 거절된4°의 body/head를 후속 배치 탐색의 seed로 사용할 수 있지만 **겹친 raw를 native 초기 후보로 사용해서는 안 된다.** 후속 기타·팔 조정 뒤 새로운 전체 source/모델/방향 gate를 통과한 후보만 사용해야 한다. 현재 스크립트는 수락 행에만 candidate/config를 생성한다.

이번 검수는 source 방향·초기 상태 계약·거절 판정의 범위이며 실행용 새 runner나 후속 coupled 탐색을 검수한 것은 아니다. 근위 구간 최소 gap을65% 단일 지점·실제 겨드랑이 연질 조직·지지력으로 확대하지 않는다. 기존 모델·기타 자산·실험·반대 방향 자료를 수정하지 않았다.

검수 SHA256:

- 계획 V1: `3371c5fd9982f32b9a6ff76c4c4bbeba11c092a6be4c9a3d2520df455241a85d`
- search V1: `953e04a43fb7d7e9b8bae2dc0819c8665fa7927341d37aaa0994a55512655360`
- 완료 search.json: `618c733ddc099542e92e489c74b0d71bb6e7261ace9e92d85f75d0d5c5113d84`

이 새 리뷰 파일만 작성했다.
