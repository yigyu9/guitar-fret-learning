# 최종 검수 — 덜 숙이고 넥 쪽으로 더 회전한 자세

요약 판정: **문제없음.** Critical 0 / Warning 2 / Suggestion 0. 19° 초기 후보의 한정된5초 정지·팔꿈치 scalar 목표 ±5° 한 주기와 자료 보존 절차를 승인한다. 연주·장시간·반복 성공이나 해부학적 겨드랑이 지지 인증으로 확대하지 않는다.

- [native 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/review_native_v1.md:1)의7회 원자료·수식·동일초기 비교 결론과 [결과 README:13](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/README.md:13)의5개 gate 실패·2개 추천 진단 구분이 일치한다. 기존 임계값을 완화하지 않았다. 선택조건은 원world고정 인간 상완점 cap10N이며 follow/cap20 실패를 추천으로 바꾸지 않았다.
- [완료 기록:7](/home/ajou/yigyu/3/stability_adapter_2/UPRIGHT_NECKWARD_POSE_COMPLETION_V1.md:7)의 실제 앞기울기 −8.500774°/heading +5.787953°, 정지BB9.548665mm/SO3 2.995398° 및 실제동작 비교 최대 .077660mm/.042115°가 원자료와 맞다. [정식 artifact:23](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/artifacts_v1/README_V2.md:23)는 절대 moving q 왕복과 incremental 응답·RMSE를 구분한다. 지정근위35%+기타상부영역1117/1200은 native 공간분류 결과로 source30% 최소gap과 다르다.
- 두 최종 PNG를 실제로 열어 이전12°/새19°의 초기·5초와 정지/동작0·2·5초 패널, 글자·캡션·배치를 확인했다. [artifact:13](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/artifacts_v1/README_V2.md:13)은 같은 기타 **초기** quaternion 이후 물리에서는 자유롭게 회전한다고 정확히 설명한다. V1 문서·그림 보존과 V2 canonical routing을 확인했다.
- provenance1/2/3의 실제 flat producer·입력 before/after·출력 SHA를 대조했다. 최종 video manifest2의 서로 다른 목적지16개는 원본/사본 SHA exact이고 실제 ffprobe도 각151frames/30fps다. 파생 side-by-side 재인코딩과 원영상 byte-copy를 구분한다. physics5.0초와 영상5.033333초는 다른 기간이며, 컨테이너 검사는 전 프레임 재생 인증이 아니다.
- [navigation 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/navigation_update_v1.json:1)의 main3 원prefix·before/after SHA와 실제 추가 heading PLAN1157/A README2249/D README82를 대조했다. 검토 문서108개 절대링크/줄도 존재한다. [결과 README:34](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/README.md:34)는 원attempt PLAN1/search1과 후속PLAN4/5 실행 맥락 차이를 명시한다.
- [봉인:51](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/seal_outputs_v1.py:51)은 flat producer 및 입력 before/after SHA·출력 map을 실제 provenance schema대로 검사하고, [봉인:67](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/seal_outputs_v1.py:67)은 최종 manifest2의 source/copy SHA·151frames/30fps를 처리한다. syntax 및 review 존재 gate·현재/역사적 navigation SHA 해결·exclusive final 출력 순서를 읽기 검토했고 Critical은 없다. 이 스크립트는 실행하지 않았다.

Warning 1 — [결과 README:23](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/README.md:23): final 회전 임계 여유는 .004602°이며 실행중 최대BB10.380810mm/SO3 3.313974°는 최종 gate와 다르다. 기존12° 정지의 BB3.944391mm/SO3 1.472679°보다 새 자세의 이탈이 증가했다. 자세 요구의 충족을 기타 안정성이 전반적으로 개선됐다는 주장으로 확대하지 않아야 한다. 반복 강건성은 미검증이다.

Warning 2 — [정식 artifact:25](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/artifacts_v1/README_V2.md:25): 240Hz endpoint 접촉 및 양의 raw lambda는 연속시간 접촉·N단위 지지력·힘/모멘트 분담 또는 해부학적 조직 인증이 아니다. 현재 제한 문구가 이를 명시하며 한 초기값·한 소동작만 검증했다.

추가 native/학습/소스·기존자료 수정0. 이전 전체 inventory의 전수 재감사 및 최종 source_final/inventory/final_verification 생성은 root 후속 봉인 범위다. 현재 그 예정 출력의 부재를 완료 인증으로 대신하지 않는다.

검수 SHA256:

- root README: `cab10538241ccfe3a56614c4ad10613ab4b4c803baf88f18b0af49f38c3afa49`
- canonical artifact README_V2: `d5b3ae2864ddf768937c9d9a456afcfa21c64f96c8510c2c21321a79e2686aea`
- 변경 색인: `77550a871b940cc1aafe895effbc9b5267917b207e6a655957ac19e870ef084a`
- 결과 summary: `8ec0709830033549d07ed95dbeb622a722f2116713dd8d3ef51756e1b26ca67c`
- 봉인 source: `94114b29aafc10f325b8a27fcfe69296a2b34543658d04a6277d0add3fe92b78`
- 초기/5초 비교 PNG: `7c36e5c67f271ac6ecf4641cf0cda780114ed1dee61786414fe7ca87b872ed72`
- 정지/동작 timeline PNG: `219a05175ff40134a157cc6f72b107197d481e64aab6bec88fb9dfd507ec5cde`
