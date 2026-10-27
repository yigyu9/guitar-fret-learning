# 지지 우선 재검사 v2 — 기존 최종검수 문서 봉인 순서 문제 분리

v1 producer/계획/log/입력 map은 그대로 보존한다. v1은 전체 이전 inventory 검사에서 review_final_v1.md 하나의 SHA 불일치를 발견해 정상 중단했다. 이전 목록과 현재 문서를 덮어쓰지 않는다.

나머지3582개 기존 phase 파일과 closed-input3235개는 모두 원래SHA에 일치함을 별도 전수확인했다. 기존최종검수 문서 mtime은 inventory보다 약1.64초 늦으며 이번 작업의 before anchor보다 약12분 이르다. 이전 마무리에서 root가 reviewer 마지막 저장 완료보다 먼저 봉인한 순서 문제와 정합한다. 예외는 새 prior_review_manifest_mismatch_v1.json에 기록한 **원inventory SHA·정확한절대경로·expected/currentSHA·bytes** 1건으로만 제한한다. 다른 물리/입력/코드/문서 변경은 허용하지 않는다. 과거전체inventory pass는False로 남긴다.

새 v2는 이 사전명시된 메타데이터 불일치의 unchanged 여부와 나머지파일 원SHA 일치를 검사한다. 핵심 물리 판정과 문서봉인 오류를 분리하고 전체옛자료무변경이라는주장은하지않는다. 원 기대검수문서를 별도 복구한다면 SHA exact 대조 후 새경로에만 보존하며 원경로를 복원/덮어쓰지 않는다.

하체가동16축·원zero8·유한K/D/effort·원asset/금지API, 가슴+오른상완+허벅지 동시95%유지, 자유기타 안정성, Pelvis기준 whole/hold 좌우/전방각 및인접부위 방향차 검사는 v1계획과동일하다. 입력증거검사(existing25/raw4exact/SHA)와 사용자 필수물리항목은결과에서분리한다. 발정면/척추세부정렬은관측선호항목이며강제로바꿀조건으로해석하지않는다. rawlambda는체중분담률/N으로환산하지않는다.

v2에새물리/자세변경/PPO없음. 기존자료계속보존. 새code audit_v2.py/analysis_v2로만진행하고독립검수뒤최종문서/봉인한다. 최종봉인은이번에는reviewer가문서마지막저장완료및더수정없음을통지한뒤에만수행한다.
