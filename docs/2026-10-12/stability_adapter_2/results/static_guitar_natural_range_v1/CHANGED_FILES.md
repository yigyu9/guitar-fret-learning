# 변경 파일 색인

native 촬영 30개(단일 변화 25개와 작은 조합 5개)는 모두 물리 스텝 0이다. 이 파일들은 촬영 단계와, 저장된 native 이미지에서 contact sheet를 만드는 후처리 단계를 구분해 색인한다.

| 파일 | 역할 |
|---|---|
| [실행 계획](/home/ajou/yigyu/3/stability_adapter_2/STATIC_GUITAR_NATURAL_RANGE_PLAN.md:1) | 물리 없는 native 위치·회전 비교 절차. |
| [렌더 실행기](/home/ajou/yigyu/3/stability_adapter_2/render_static_guitar_range.py:30) | bounded 입력/보존 사전 검사; [실제 main](/home/ajou/yigyu/3/stability_adapter_2/render_static_guitar_range.py:57)에서 native 캡처 실행. |
| [결과 제안](/home/ajou/yigyu/3/stability_adapter_2/STATIC_GUITAR_NATURAL_RANGE_PROPOSAL.md:16) | native30개를 보고 정한 시각적 중심·탐색 범위와 한계. |
| [작은 조합 결정](/home/ajou/yigyu/3/stability_adapter_2/trials/static_guitar_natural_range_v1/DECISION.md:1) | 5개 추가 조합 촬영 범위 결정. |
| [조합 입력](/home/ajou/yigyu/3/stability_adapter_2/trials/static_guitar_natural_range_v1/combined.json:1) | combined 5개 native 입력. |
| [native 25개 비교 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/native/comparison.json:1) | 단일 변화 25개 캡처 결과와 검사. |
| [combined 5개 비교 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/combined/comparison.json:1) | 추가 조합 5개 캡처 결과와 검사. |
| [25개 시트 producer](/home/ajou/yigyu/3/stability_adapter_2/build_static_guitar_range_artifacts.py:208) | 저장된 이미지의 기본 contact sheets 생성 `main`; native 실행은 하지 않는다. |
| [25개 case mapping](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts/case_mapping.json:1) | 셀-케이스 대응 및 원본 이미지 SHA-256. |
| [25개 artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts/artifact_manifest.json:1) | producer·bounded input·산출물 SHA-256. |
| [Translation front sheet](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts/contact_sheet_translation_front.png) | 위치 단일 변화의 정면 시점. |
| [Translation side sheet](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts/contact_sheet_translation_side.png) | 위치 단일 변화의 측면 시점. |
| [Translation hands sheet](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts/contact_sheet_translation_hands.png) | 위치 단일 변화의 손 시점. |
| [Rotation front sheet](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts/contact_sheet_rotation_front.png) | semantic 회전 단일 변화의 정면 시점. |
| [Rotation side sheet](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts/contact_sheet_rotation_side.png) | semantic 회전 단일 변화의 측면 시점. |
| [Rotation hands sheet](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts/contact_sheet_rotation_hands.png) | semantic 회전 단일 변화의 손 시점. |
| [Combined sheet producer](/home/ajou/yigyu/3/stability_adapter_2/build_static_guitar_range_combined.py:49) | 저장된 5개 combined 비교 입력을 검증하고 front/side/hands 시트를 만드는 후처리 `main`. |
| [Combined front/side/hands sheet](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts_combined/contact_sheet_combined_front_side_hands.png) | 5개 조합의 세 native 시점. |
| [Combined case mapping](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts_combined/case_mapping.json:1) | 셀-케이스 대응 및 원본 이미지 SHA-256. |
| [Combined artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts_combined/artifact_manifest.json:1) | producer·bounded input·산출물 SHA-256. |
| [결과·이미지 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/README.md:1) | 비교 결과의 시각적 설명과 제한. |

누적 문서의 해당 완료 섹션: [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:1362), [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:2192), [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2195).
