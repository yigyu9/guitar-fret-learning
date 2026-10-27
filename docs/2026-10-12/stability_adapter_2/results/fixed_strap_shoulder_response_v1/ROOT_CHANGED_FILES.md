# Root 변경 파일·실제 줄 번호

산출물 담당자의 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/CHANGED_FILES.md:1)에 구현/실행 입력 경로를 보완한다. 기존 frozen native runner와 공용 모델은 수정하지 않았다.

| 파일 | 이번 역할 |
|---|---|
| [FIXED_STRAP_SHOULDER_RESPONSE_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SHOULDER_RESPONSE_PLAN.md:12) | 두 목표 응답 비교·불변 조건·검증 계획 |
| [prepare_fixed_strap_shoulder_response.py](/home/ajou/yigyu/3/stability_adapter_2/prepare_fixed_strap_shoulder_response.py:10) | 두 trial과 float32 목표·기존 입력 closure 준비 |
| [run_fixed_strap_shoulder_phase.py](/home/ajou/yigyu/3/stability_adapter_2/run_fixed_strap_shoulder_phase.py:6) | 실행 전 원문/R상대경로 복사·SHA·명령/로그/exit 기록 |
| [analyze_fixed_strap_shoulder_response.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_fixed_strap_shoulder_response.py:14) | world6D 오차·signed 응답·29검사 |
| [collect_fixed_strap_shoulder_videos.py](/home/ajou/yigyu/3/stability_adapter_2/collect_fixed_strap_shoulder_videos.py:6) | 네 새 영상 SHA exact 복사·134개 신규 색인 |
| [minus008.json](/home/ajou/yigyu/3/stability_adapter_2/trials/fixed_strap_shoulder_response_v1/minus008.json:1) | −0.008rad 목표 입력 |
| [plus008.json](/home/ajou/yigyu/3/stability_adapter_2/trials/fixed_strap_shoulder_response_v1/plus008.json:1) | +0.008rad 목표 입력 |
| [FIXED_STRAP_SHOULDER_RESPONSE_DECISION.md](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SHOULDER_RESPONSE_DECISION.md:19) | 결과 채택 판단과 다음 Wrist_y 단위 |
| [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:1008) / [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1806) | 준비 기록 append |
| [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:1013) / [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1811) | 실제 결과 append |
| [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1877) | §102 그림/이미지/영상과 설명 append |
| [VIDEO_INDEX_v7.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v7.md:1) / [video_collection_update_v6.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/video_collection_update_v6.json:1) | 이전 색인/원본 유지·네 영상 추가 |
| [ROOT_VERIFICATION_NOTES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/ROOT_VERIFICATION_NOTES.md:1) | 실제 QA·실행 집계·보존 범위 |

계획은 소비 당시 원문으로 동결했다. 결과 체크리스트와 최종 봉인 여부는 이 phase의 [검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/review.md:1)와 final_verification.json(최종 생성 경로)에서 확인한다.
