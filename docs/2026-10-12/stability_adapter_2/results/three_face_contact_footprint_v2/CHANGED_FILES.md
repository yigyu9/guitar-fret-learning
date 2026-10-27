# 변경 파일과 실제 줄 번호

모든 경로는 절대 경로이며, 줄 번호는 현재 파일에서 확인했다. 소비된 첫 variant도 보존했다.

| 파일 | 내용 |
|---|---|
| [search_contact_footprint.py](/home/ajou/yigyu/3/stability_adapter_2/search_contact_footprint.py:28) | V1 source 검색; 소비된 원본 보존 |
| [search_contact_footprint_v2.py](/home/ajou/yigyu/3/stability_adapter_2/search_contact_footprint_v2.py:28) | V2 유한 패치/전체 hull 검사 |
| [analyze_contact_footprint_search.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_contact_footprint_search.py:15) | 보존된 첫 분석; 자기stdout 입력 문제 기록 |
| [analyze_contact_footprint_search_v2.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_contact_footprint_search_v2.py:15) | Canonical 네 후보 요약 |
| [make_contact_footprint_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_contact_footprint_artifacts.py:27) | 보존된 첫 그림 producer; 입력검증에서 중단 |
| [make_contact_footprint_artifacts_v2.py](/home/ajou/yigyu/3/stability_adapter_2/make_contact_footprint_artifacts_v2.py:27) | Canonical source 비교 그림 |
| [THREE_FACE_REAR_FACET_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_REAR_FACET_PLAN.md:13) | 다음 미실행 후보 계획 |
| [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1561) | 현재 단계 계획/진행 |
| [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:867) | 단계 인계 |
| [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1605) | 누적 보고서 §84 |
| [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md) | 산출물 인덱스 |
| [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/README.md:30) | 실행/검수/실패 보존 설명 |
| [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v1/review.md:1) | V1 및 직전 단계 독립검수 |
| [review_v2.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/review_v2.md:1) | V2 독립검수 |
| [review_status.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/review_status.json:1) | 새 후처리 검수 보류 범위 |
| [analysis_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/analysis_v2.json:1) | Canonical 수치/입력 SHA |
| [proposal.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/proposal.json:1) | V2 후보/거절 원자료 |
| [artifact_manifest_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/artifact_manifest_v2.json:1) | 그림 전후입력/출력 SHA |

그림: ![source 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/artifacts_v2/source_candidate_comparison.png)

최종 보존 감사·source_final·artifact_inventory는 root가 생성하며, source 검수와 새 요약/PNG의 독립 최종 검수 보류 범위를 구별해 기록한다.
