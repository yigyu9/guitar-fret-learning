# 그림 보완 및 후속 기록

## 보존된 v1과 범례 수정

v1 producer는 실행 시 source SHA `5d4c36a158b41528d8babd19c4b4d73c376c8122403200fc815f7792bc2d77c5`와 일치했다. v1 그림과 manifest는 보존되어 있으며 재작성하지 않는다. Root의 PNG 확인에서 세 subplot의 범례를 모두 합쳐 같은 조건 이름이 9회 나타나는 것을 확인했다. 보완 producer는 새 파일 [make_body9_strap_minus4mm_artifacts_v2.py](/home/ajou/yigyu/3/stability_adapter_2/make_body9_strap_minus4mm_artifacts_v2.py)이며, figure legend 입력은 첫 axes의 handles/labels만 사용하고 캡션을 캔버스 안의 명시적 두 줄로 배치한다.

v1 결과: [PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/artifacts/body9_strap_minus4mm_comparison.png), [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/artifacts/artifact_manifest.json). v1 PNG SHA-256은 `69afefd2d710b3eddbeeceb633c902c83c46f2629d381ab3f051c72738d6a48a`다. v2는 새 경로 `artifacts/body9_strap_minus4mm_comparison_v2.png` 및 `artifacts/artifact_manifest_v2.json`을 사용한다. v2 producer는 이 문서 작성 시 실행하지 않았으며 root가 실행·PNG QA 후 상태를 확정한다.

## 후속 방향과 영상 모음

Root가 확정한 [후속 결정](/home/ajou/yigyu/3/stability_adapter_2/STRAP_MINUS4MM_DECISION.md)은 −4 mm의 회전 개선을 보존하면서 −2 mm를 후기 유지 비교 기준으로 유지한다. strap을 더 줄이는 대신 −2 mm actual 저장 상태에서 기존 팔 12 + finger 6 연동 source 계획의 첫 형상 검증을 진행한다. 상세 bounds와 물리 판단은 해당 결정 문서를 따른다.

영상 모음은 126개이며 [VIDEO_INDEX_v4.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v4.md)와 [video_collection_update_v3.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/video_collection_update_v3.json)에 기록됐다.

## 독립 검수 상태

독립 검수에서 Critical/Warning은 0건으로 보고됐다. Root의 최종 보존·검수 기록은 [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/review.md) 예정 경로이며 아직 생성되지 않았다. 이 addendum은 기존 phase README와 원 실행 산출물을 수정하지 않는다.
