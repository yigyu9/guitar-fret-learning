# 기타·자세 자료 정리 독립 검수

판정: **문제없음 — 최종 v2 자료 정리 범위 승인**. 미해결 Critical 0 / Warning 1 / Suggestion 0. 검수는 문서 사실·단위·링크·원본/사본 대응과 SHA에 한정했다. 새 native 실행·학습·광범위 물리 재검증이나 다른 담당 파일 수정은 하지 않았다.

## 발견과 정정 확인

최초 video/manifest_v1은22행의 destination이4개뿐이어서 진단 영상18개가 후보 파일로 잘못 연결됐다. 실제61개 사본은 원본과 일치했으며 오류는 metadata에 있었다. [manifest v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/manifest_v2.json:1)는22개 고유 source/destination, label/view, 실제 source·copy SHA를 모두 대조해 통과했다. 후보4개와 진단18개를 구분하며 원 v1은 이력으로 보존됐다.

최초 자세 문서의60Hz 표기 역시 정정됐다. [자세 v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/posture/README_v2.md:31)는1200개 접촉을240Hz physics 끝점, RHfinger 추가 관측을60Hz의299개 query로 구분한다. 연속 시간 또는 전기간 RHfinger 무접촉으로 확대하지 않는다. 두 정정 사항은 최종 승인 시점에 해결됐다.

## 확인 범위

- [기타 v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/guitar/README_v2.md:7): 바디491.957×380.632mm, 중심선 국소 두께 약85~107.198mm·꼬리104mm와 전체 mesh bbox 폭108.476mm를 구분한다.63 collision hull·기존 넥/물리 영역·물리 없는6현 표시·기존 질량4.648716kg 설명과 복사 원자료가 일치한다. 실제 중공 목재/음향/사진 제품 재현이나 새 법률 판단을 주장하지 않으며 기존 attribution을 연결한다.
- 현재 후보는 동일 초기조건 native11/12의5초 결과다. 바디 bbox 중심40.207mm≠actor-root53.017mm, SO(3)11.071°, 후기2→5초 .073932mm/.028843° 및 상완1187/1200·왼팔/Head0/1200을 원 검증 자료와 대조했다. 물리5.0초와 MP45.033333초를 구분한다. force/moment 기여 미측정·raw lambda≠N·큰 초기각/손목 한계 접근·연주 미검증을 명시한다.
- R_Hip의 상부 다리 capsule 설명은 [fixed_lower XML:73](/home/ajou/yigyu/3/stability_adapter_2/assets/humanoid_fixed_lower.xml:73)과 맞는다. source mesh/depth PNG와 추가 기타 초점 이미지를 실제로 열었다. 과거 초점 이미지는 현재 후보 초기 자세가 아니라는 주석이 있어 장면을 혼동하지 않는다.
- 기존61개와 추가 focus 이미지/설명2개, 총63개 사본의 현재 source/copy SHA를 대조했다. v2 출력8개·direct input·helper SHA도 일치했다. active 문서75개 링크 목적지와 지정 행을 확인했다. 복사 JSON 내부 원경로는 추적용이며 새 실행 config가 아니다.
- [root 탐색 append 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/root_navigation_append_v1.json:1)의 before snapshot SHA와 현재 after SHA/prefix를 확인했다. 옛71개 출력 중 이 root-owned README만 snapshot으로 해석하고 나머지70개는 현재 SHA가 그대로다. v2 stage의 역사적 보존 기록과 후속 root 탐색 append를 구분한다.
- [검증기:10](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/verify_archive_v1.py:10)의 좁은 snapshot 예외, source별 영상 대응/label/view/실제 SHA 및 배타 inventory 생성 논리를 검토했다. 기존 source60개·inventory SHA와22개 ffprobe151frame/30fps는 root의 읽기 전용 전단 검사 통과를 전달받았다. 최종 inventory/verification 생성은 root 후속 작업이다.

## 주의

Warning 1 — [최초 copier:143](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/tools/archive_oct19_materials.py:143)는 기존 destination을 덮어쓸 수 있다. 소비된 현재 보관본에 재실행하지 말아야 한다. 이번 정정은 원61개/영상 재복사 없이 새 metadata·문서로 완료됐으며, 향후 새 보관 작업은 별도 경로나 배타 복사를 사용해야 한다. 원 v1 영상 metadata는 현재 색인으로 사용하지 않는다.

핵심 SHA-256:

| 파일 | SHA-256 |
|---|---|
| video/manifest_v2.json | 611d154c7e5b6cb877400b1b3b84b4c6b44ae91d551d3b9a540fb0f3a44f2adc |
| provenance_v2.json | 20a82d98fd8a2afa277ae7edd0e0484d57f5f09e26f26a57b10204eab5043d0c |
| root_navigation_append_v1.json | 35988600c33917f66131ccff262d807bd308556c4292ebeb8a3c1d658274dae6 |
| verify_archive_v1.py | c27713f8dfcef0371662e514328d027d555080037fabc24f2737780d7b53da38 |

완료를 막는 사항은 발견하지 않았다.10-19는 사용자 지정 자료 정리 경로이며 이전 실험 날짜를 바꾸거나 새 시험 성공을 선언하는 작업이 아니다. 지정한 이 새 검수 파일만 작성했다.
