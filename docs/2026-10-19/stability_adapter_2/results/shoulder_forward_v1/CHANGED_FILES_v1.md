# 이번 단계 변경·추가 파일

절대경로와실제1기반줄을기록한다. main3문서는기존prefix를스냅샷으로보존하고추가만했다. consumed source1/2·실패·기존실험/원자산은변경하지않았다. native영상/원사진수백개는manifest/원자료와묶어색인한다.

## 구현·계획

- [SHOULDER_FORWARD_COMPLETION_V1.md](/home/ajou/yigyu/3/stability_adapter_2/SHOULDER_FORWARD_COMPLETION_V1.md:1)
- [SHOULDER_FORWARD_PLAN_V1.md](/home/ajou/yigyu/3/stability_adapter_2/SHOULDER_FORWARD_PLAN_V1.md:1)
- [SHOULDER_FORWARD_PLAN_V2.md](/home/ajou/yigyu/3/stability_adapter_2/SHOULDER_FORWARD_PLAN_V2.md:1)
- [analyze_shoulder_forward_v1.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_shoulder_forward_v1.py:1)
- [run_shoulder_forward_v1.py](/home/ajou/yigyu/3/stability_adapter_2/run_shoulder_forward_v1.py:1)
- [run_shoulder_forward_v2.py](/home/ajou/yigyu/3/stability_adapter_2/run_shoulder_forward_v2.py:1)
- [search_shoulder_forward_v1.py](/home/ajou/yigyu/3/stability_adapter_2/search_shoulder_forward_v1.py:1)
- [search_shoulder_forward_v2.py](/home/ajou/yigyu/3/stability_adapter_2/search_shoulder_forward_v2.py:1)

전방투영목표와직교이동선호는 [search_shoulder_forward_v2.py](/home/ajou/yigyu/3/stability_adapter_2/search_shoulder_forward_v2.py:25),수락조건은 [동일소스](/home/ajou/yigyu/3/stability_adapter_2/search_shoulder_forward_v2.py:26)다. 실제새runner의상완점합산은 [run_shoulder_forward_v2.py](/home/ajou/yigyu/3/stability_adapter_2/run_shoulder_forward_v2.py:117)이며기존과같은제어이다.

## 기존본문을 보존한 추가

- [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1164) · [기존본문](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/A_PLAN_before_append_v1.md:1)
- [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:2256) · [기존본문](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/A_README_before_append_v1.md:1)
- [README.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/README.md:89) · [기존본문](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/D_README_before_append_v1.md:1)

## 원자료·검증·산출물

- [analyze_contact_region_v1.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/analyze_contact_region_v1.py:1)
- [analyze_contact_region_v2.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/analyze_contact_region_v2.py:1)
- [seal_outputs_v1.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/seal_outputs_v1.py:1)
- [summarize_results_v1.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/summarize_results_v1.py:1)
- [summarize_results_v2.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/summarize_results_v2.py:1)
- [A_PLAN_before_append_v1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/A_PLAN_before_append_v1.md:1)
- [A_README_before_append_v1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/A_README_before_append_v1.md:1)
- [D_README_before_append_v1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/D_README_before_append_v1.md:1)
- [README.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/README.md:1)
- [review_native_v1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/review_native_v1.md:1)
- [review_preflight_v1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/review_preflight_v1.md:1)
- [contact_region_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/contact_region_v1.json:1)
- [contact_region_v2.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/contact_region_v2.json:1)
- [navigation_update_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/navigation_update_v1.json:1)
- [result_summary_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/result_summary_v1.json:1)
- [result_summary_v2.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/result_summary_v2.json:1)
- [artifacts_v1/build_archive_v1.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1/build_archive_v1.py:1)
- [artifacts_v1/build_archive_v2.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1/build_archive_v2.py:1)
- [artifacts_v1/build_archive_v3.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1/build_archive_v3.py:1)
- [artifacts_v1/README_V1.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1/README_V1.md:1)
- [artifacts_v1/README_V2.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1/README_V2.md:1)
- [artifacts_v1/README_V3.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1/README_V3.md:1)
- [artifacts_v1/provenance_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1/provenance_v1.json:1)
- [artifacts_v1/provenance_v2.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1/provenance_v2.json:1)
- [artifacts_v1/provenance_v3.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1/provenance_v3.json:1)
- [정식결과사진/설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1/README_V3.md:1)
- [원본영상6개색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/shoulder_forward_v1/INDEX_V1.md:1)
- [영상source/copySHA·151frames](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/shoulder_forward_v1/manifest_v1.json:1)

최종review_final_v1.md 및source_final_v1.json/artifact_inventory_v1.json/final_verification_v1.json은독립검수·봉인후생성되는예정감사결과이다. 아직없는파일의링크는만들지않는다.
