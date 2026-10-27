# 변경 파일·절대 경로·실제 줄 번호

2026-10-06. 이 소단계의 신규 구현/입력/산출물과 갱신한 메인 안내를 정리한다.
기존 stability_adapter·공용 자산·2026-08-19 자료는 수정하지 않았다.

## 메인 계획과 구현

- [HAND_SUPPORT_INITIAL_POSE.md](/home/ajou/yigyu/3/stability_adapter_2/HAND_SUPPORT_INITIAL_POSE.md:1)
- [search_hand_support.py](/home/ajou/yigyu/3/stability_adapter_2/search_hand_support.py:1)
- [compare_hand_support.py](/home/ajou/yigyu/3/stability_adapter_2/compare_hand_support.py:1)
- [plot_hand_support.py](/home/ajou/yigyu/3/stability_adapter_2/plot_hand_support.py:1)
- [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:10)
- [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:603)

## 초기 설정 입력

- [candidate_01.json](/home/ajou/yigyu/3/stability_adapter_2/trials/hand_support_v1/candidate_01.json:1) — 원거리 query 순위 문제로 제외, native 미실행
- [candidate_02.json](/home/ajou/yigyu/3/stability_adapter_2/trials/hand_support_v1/candidate_02.json:1) — 원거리 query 순위 문제로 제외, native 미실행
- [candidate_03.json](/home/ajou/yigyu/3/stability_adapter_2/trials/hand_support_v1/candidate_03.json:1) — 원거리 query 순위 문제로 제외, native 미실행
- [reference.json](/home/ajou/yigyu/3/stability_adapter_2/trials/hand_support_v1/reference.json:1) — 원거리 query 순위 문제로 제외, native 미실행
- [candidate_01.json](/home/ajou/yigyu/3/stability_adapter_2/trials/hand_support_v2/candidate_01.json:1)
- [candidate_02.json](/home/ajou/yigyu/3/stability_adapter_2/trials/hand_support_v2/candidate_02.json:1)
- [candidate_03.json](/home/ajou/yigyu/3/stability_adapter_2/trials/hand_support_v2/candidate_03.json:1)
- [reference.json](/home/ajou/yigyu/3/stability_adapter_2/trials/hand_support_v2/reference.json:1)
- [p08_load00.json](/home/ajou/yigyu/3/stability_adapter_2/trials/hand_coupled_v1/p08_load00.json:1)
- [p3_load00.json](/home/ajou/yigyu/3/stability_adapter_2/trials/hand_coupled_v1/p3_load00.json:1)
- [p3_load10.json](/home/ajou/yigyu/3/stability_adapter_2/trials/hand_coupled_v1/p3_load10.json:1)
- [p3_load20.json](/home/ajou/yigyu/3/stability_adapter_2/trials/hand_coupled_v1/p3_load20.json:1)

## 결과·그림 설명·검수

- [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_support_v1/README.md:1)
- [comparison.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_support_v1/comparison.json:1)
- [coupling_inputs.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_support_v1/coupling_inputs.json:1)
- [search.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_support_v1/search_v2/search.json:1)
- [plot_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_support_v1/plot_manifest.json:1)
- [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_support_v1/review.md:1)
- [source_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_support_v1/source_manifest.json:1)
- [source_manifest_final.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_support_v1/source_manifest_final.json:1)
- [source_snapshot_validation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_support_v1/source_snapshot_validation.json:1)
- [protected_validation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_support_v1/protected_validation.json:1)
- [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:530)
- [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:264)

PNG는 이 결과 폴더 images에, 원자료 report/trace/states/contacts 및 실행 로그는 각 run에 있다.
그림은 저장 native pose의 source 형상 재구성이며 Isaac/PhysX renderer·clearance 인증이 아니다.
기존 원자료를 보존하고 새 경로로 후처리한 이력을 함께 남겼다.
