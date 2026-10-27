# 왼손 초기 철수 방향 변경 보완 검수 v2

요약 판정: **문제없음 — 철수 목표 한 줄 변경의 사전 범위.** 미결 Critical은 없습니다. 실제 native 왼팔 비접촉·기타 유지 성공은 아직 인증하지 않습니다.

[새 검색:19](/home/ajou/yigyu/3/stability_adapter_2/search_rounded_spine_no_left_v2.py:19)을 v1과 직접 diff 대조했습니다. 유일한 소스 변경은 `withdraw=원palm−worldZ 0.03m+Pelvis앞 0.08m`입니다. Pelvis 앞 방향은 수평 투영 후 정규화되어 있으므로 새 목표는 앞8cm·아래3cm이며 [v2 계획:3](/home/ajou/yigyu/3/stability_adapter_2/ROUNDED_SPINE_NO_LEFT_PLAN_V2.md:3)과 일치합니다. v1의 위8cm·뒤3cm 목표를 최신 조건으로 사용하지 않습니다.

몸통 분산9°/12°·scalar±5°, 오른팔±0.3rad/왼팔±0.6rad·모델 한계·palm 방향 목표·source 겹침/IK 오차 수용 조건·기타 초기 p/q·finger/head 초기각·prep2/horizon5 및 기존 fixed q_ref runner는 변경되지 않았습니다. 처음부터 손이 빠진 조건이며 실제시간 release나 strapOFF 시험이 아닙니다.

[사전 소스 핀](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/source_before_search_v2.json:1)의 v1/v2 소스·계획4개 현재 SHA를 대조해 일치했습니다. v1 검색의 선택은9°왼손 지지 조건 한 개이며3개 비지지 후보 거절을 보존하고 있습니다. 새 검색 SHA256은 `efe571e6dc74ac8a53d7439e1d6abcda7b6e1b525187583cdc8508ee702166d8`, 새 계획 SHA256은 `d4b6217c4cec013b71f17caa5b98ecdf199542f6fecd229a84191c6572292c66`입니다.

## Warning

[v1 사전 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/review_preflight_v1.md:1)의 source gap/cooked 접촉 구분은 그대로 적용합니다. 새 방향은 source 관통 거절을 피하려는 후보이며, native에서 모든 L_팔/LH:–기타 접촉과 동적 재접촉을 확인하기 전에는 전구간 왼손 비지지로 설명할 수 없습니다. 실제5초 이동·영상·접촉 결과는 후속 검수 대상입니다.

검수자는 이 새 파일만 작성했습니다. 기존 v1 계획·검색·리뷰 수정 및 추가 물리·학습 실행은 하지 않았습니다.
