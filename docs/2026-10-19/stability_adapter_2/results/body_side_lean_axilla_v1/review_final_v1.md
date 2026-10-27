# 바디 쪽 몸통 기울임 — 최종 독립 검수

요약 판정: **문제없음.** Critical 0 / Warning 1 / Suggestion 0. 코드·기록·자료 정리 승인이고 **초기 기타 자세 유지 또는 최종 연주 자세 채택의 승인이 아니다.** 새 물리 실행·학습은 하지 않았다.

[native 독립 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/review_native_v1.md:1)에서 두 시험의 초기 JSON 전체 exact, 요청 합산/clip1200행, actor1200회·other69 effort0, 실제 회전·접촉 집계의 일치를 확인했다. 두 조건은 동일한 초기값의 기존 능동 전완 제어 대 상완점 추가 비교다. source1~4 거절과 source5의 진단용5mm 문턱 변경을 최종 자세 채택으로 혼동하지 않는다.

| 조건 | 바디 BB 중심 이동 | SO3 초기 대비 회전 | G+Y 넥 고도 | 상완 / 전완 접촉 존재 |
|---|---:|---:|---:|---:|
| 전완 | 48.051mm | 52.174° | −15.921° | 968 / 1191 of1200 |
| 전완+상완 | 47.501mm | 47.662° | −10.019° | 256 / 1149 of1200 |

두 조건 모두 left/Head 존재0/1200이다. 상완 접촉은 생겼지만 큰 회전과 넥 하강이 남아 초기 기타 방향을 유지하지 못했다. 작은2→5초 변화는 회전된 뒤 정착한 상태다. bbox 중심·actor-root·질량중심, 넥 고도·SO3를 구분한다. 단일 비교의 요청힘·접촉 빈도로 힘/모멘트 기여 또는 반복 강건성을 인증하지 않는다.

최신 [root README](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/README.md:28)의 R_Hip297/300씩·L_Hip3/5표본과 별도60Hz 집계는 원자료와 맞다. 이전 L_Hip 초안은 스냅샷으로 보존한다. [source 정정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/source_scope_note_v1.md:1)도 L0.131/R1.782mm를 구분해 계획의 ‘두Hip 약.1mm’ Warning을 해소한다. 확정 방향은 player-right=정면 화면 왼쪽=바디 쪽이며 이전 넥 쪽 진단과 별개다.

실제 `initial_native_pair.png`와 `native_timeline_0_2_5s.png`를 열어 초기 동일성 및2·5초의 넥 하강/앞판 방향 변화를 확인했다. [artifact README](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/artifacts_v1/README_V1.md:20)는 넥 고도와 전체 회전,60/240Hz 접촉, 후기 정착과 성공을 구분한다. 두 점 목표는 인간 actuator 요청이며 기타 고정이나 직접 기타 힘이 아니다. 각 점30N은 합계30N·측정 접촉력과 다르다.

current phase 입력9,008개 기록은 historical/current navigation 스냅샷 예외를 적용해 불일치0이었다. [main append](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/navigation_update_v1.json:1) 세 개의 before/after SHA·prefix 및 직전 phase 연결을 확인했다. Luna provenance 입력28/출력10 SHA, 영상4개 원본/사본 SHA·151프레임/30fps 기록도 일치했다. 물리5.0초와 MP4 5.033333초를 구분한다. 현재 문서·색인의 파일/행 링크를 대조했다.

[봉인 코드](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/seal_outputs_v1.py:17)의 nav 이력별 예외, dict/list provenance, 리뷰 gate·배타적 출력과 Python3.8 구문에 중요한 오류를 발견하지 않았다. **실제 봉인 실행과 이전 전체 inventory 재검사는 root 후속 범위**다. 예정 final/source_final/inventory를 완료 감사로 주장하지 않는다.

## Warning

1. [분석기 경로](/home/ajou/yigyu/3/stability_adapter_2/analyze_body_side_lean_axilla_v2.py:19): relative config lookup 문제는 소비 코드에 남아 있다. 성공 분석과 현재 설명은 절대 CLI 경로로 한정했고 실패 analysis_v1도 보존한다. 재사용은 절대 경로로 수행하거나 새 버전에서 정규화해야 한다. 현 결과의 정확성을 막는 사항은 아니다.

검수 SHA256:

- root README: `314b2b293416a9aed3abeb0548594de6c10e5f93c129704e9e18f81558878f7b`
- artifact README: `32dc331b346174963de69a422374836d521cd845fc0f00f7f5210fcc90c4ca38`
- artifact provenance: `cc65b0faafd3bd954f60094e6a8e419de135ecb0440fbe457efa2571bead8aca`
- 영상 manifest: `49a9985b5d16cc4d061313ca63e15427e7bae3b693a79926d7f934522a546f6e`
- 봉인 코드: `d23206559a0e3d347d926088e761f7022b669bf3355f1541ca94c6939c3b8b37`

허용된 새 리뷰 두 파일만 작성했고 원본·소비 코드·실험·이전 리뷰는 수정하지 않았다.
