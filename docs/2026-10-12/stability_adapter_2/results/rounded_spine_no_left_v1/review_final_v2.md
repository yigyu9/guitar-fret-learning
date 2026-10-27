# 분산 척추·왼손 비지지 최종 독립 검수 v2

요약 판정: **문제없음 — 완료된 네5초 진단과 오른손 접촉 정정 범위.** 미결 Critical은 없습니다. 초기 기타 유지는 실패했으며, 오른손목·손 접촉이 남아 있다는 사실을 반영했습니다.

## 원자료와 기존 검수 보존

[기존 최종 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/review_final_v1.md:1)의 SHA `fd14f3cc6c9b13adc83789078d0044b471ea13e1d3ba06b40ebd3f0b40129f1a`와 [33검사 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/verification_v1.json:1)의 SHA `3b165fa30c0b951366e19b4277a39621d73f615a081187119794abc8bfdbaf56`가 그대로입니다. 원자료의 이동·quaternion·300접촉 query·9°쌍 비왼팔 q_ref exact,3PNG 육안 대조,후처리43입력/9출력과8영상 SHA 검수 범위는 기존 기록대로 유지됩니다.

왼손 철수3°/9°/12°는 각각 초기에서36.237/33.536/33.286cm·88.161/83.305/83.414° 이탈했습니다. 모든 왼팔·손 접촉은300query 모두0이며, 9°지지는10.843cm·18.974° 이동했습니다. 작은 후기 변화는 크게 이탈한 뒤의 정착입니다. 원본 strap ON·5초 고정 초기 q_ref PD·실제시간 release 아님·음악/정책/학습0의 조건은 변하지 않았습니다.

## 오른손 접촉 보완 대조

[동반 감사 코드:15](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/audit_right_hand_contacts_v1.py:15)는 R_Wrist/RH:별로 같은 query 내 중복 접촉을 제거해 시점 수를 집계합니다. [감사 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/right_hand_contact_audit_v1.json:1)의5입력 SHA와 네 조건의 표본수·최초/마지막 시각을 원contacts에서 직접 재계산해 일치했습니다.

| 조건 | R_Wrist | RH:palm | RH:thumb1 |
|---|---:|---:|---:|
| 3°·왼손 철수 | 0/300 | 244/300 | 245/300 |
| 9°·왼손 지지 | 0/300 | 0/300 | 0/300 |
| 9°·왼손 철수 | 242/300 | 240/300 | 0/300 |
| 12°·왼손 철수 | 241/300 | 1/300 | 0/300 |

비지지 조건의 R_Shoulder0 및 R_Elbow0/4/6표본 결과는 전체 오른팔·손 비접촉을 뜻하지 않습니다. [정정 설명:47](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/README_V2.md:47)은 손목·손 접촉을 추가하고 이전 넓은 표현을 상완·전완·몸통으로 좁혔습니다. 접촉 발생만으로 해당 부위의 실제 지지력 기여나 원하는 초기 자세 유지 성공을 확정할 수 없습니다. raw λ를 뉴턴 힘·압력으로 해석하지 않습니다.

## 정정·봉인 범위와 Warning

[새 변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/CHANGED_FILES_V2.md:29)의 절대 링크/실제 줄,main4 정정 append의 이전 prefix·전후 SHA를 확인했습니다. [봉인 코드:12](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/seal_phase_v1.py:12)의 동반 감사 입력 exact,4main append chain,최신 v2리뷰/문서 snapshot 반영을 읽기 전용으로 점검했고 큰 범위 누락은 없습니다. 이전2590파일 전체·전체2416프레임·최종 snapshot/inventory 실제 봉인은 root의 후속 실행 대상입니다.

접촉0은60Hz query 결과이며240Hz 전체 substep/연속시간 인증이 아닙니다. 기존 분석의 L_ prefix는 왼하체도 포함할 수 있으므로 향후 명시적인 왼팔·손 목록으로 좁히는 Warning을 유지합니다. 이번 원자료에서는 비지지0/지지 palm·finger만 관측되어 현재 결론에 영향은 없습니다. 이전 소비 문서·그림·리뷰는 보존합니다.

동반 감사 SHA256: `10724a395cf5d494bf6a67dddb10e84f37f0a181db60f61aeab1055f06133893`. 정정 README SHA256: `5f6bd2fe9091878204ec9b74960f1da63d70cb5e25c5a8865a968f2392e0aea5`. 검수자는 이 새 리뷰 파일만 작성했으며 추가 물리·학습 실행과 기존 파일 수정은 하지 않았습니다.
