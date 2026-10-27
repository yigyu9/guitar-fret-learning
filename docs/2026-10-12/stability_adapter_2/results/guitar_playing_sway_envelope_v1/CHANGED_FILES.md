# 변경 파일 색인

이 phase는 정적 native 끝점 13개를 촬영했고 물리 스텝은 0이었다. contact sheet 6장은 저장된 PNG를 모은 후처리 산출물이며 별도 물리 실행이 아니다.

| 파일 | 역할 |
|---|---|
| [Phase 계획](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_PLAYING_SWAY_ENVELOPE_PLAN.md:1) | 중심 및 6축 최소·최대 후보 계획. |
| [사전 검수 보완](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_PLAYING_SWAY_ENVELOPE_PREFLIGHT_V2.md:1) | 실제 렌더 v2에 앞선 보완 기록. |
| [최종 시각 제안](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_PLAYING_SWAY_ENVELOPE_DECISION.md:1) | 13개 이미지 검토 후 정한 범위와 제한. |
| [기본 endpoint 입력](/home/ajou/yigyu/3/stability_adapter_2/trials/guitar_playing_sway_envelope_v1/endpoints.json:1) | 중심 및 12개 단독 끝점 입력. |
| [원 v1 렌더 producer 사전검사 main](/home/ajou/yigyu/3/stability_adapter_2/render_guitar_playing_envelope.py:48) | pure math/preflight에 사용; 실제 촬영은 v2 source가 수행했다. |
| [실제 v2 native renderer main](/home/ajou/yigyu/3/stability_adapter_2/render_guitar_playing_envelope_v2.py:48) | native 13개 캡처 실행. |
| [native comparison 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/comparison.json:1) | 13개 case, native paths, 실제 semantic 각과 aggregate checks. |
| [native execution log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native_execution.log:1) | 실제 렌더 실행 출력. |
| [원 기본 contact-sheet producer main](/home/ajou/yigyu/3/stability_adapter_2/build_guitar_sway_endpoint_sheets.py:55) | 최초 시트 생성 producer; 첫 producer/output 버전은 별도 보존되지 않았다. |
| [재검증 contact-sheet producer v2 main](/home/ajou/yigyu/3/stability_adapter_2/build_guitar_sway_endpoint_sheets_v2.py:55) | 저장된 native PNG에서 `artifacts_v2` 6장을 생성. |
| [v2 case mapping](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifacts_v2/case_mapping.json:1) | 시트 셀, case ID, 원본 경로와 이미지 SHA-256. |
| [v2 artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifacts_v2/artifact_manifest.json:1) | bounded inputs와 outputs SHA-256. |
| [translation front sheet](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifacts_v2/contact_sheet_translation_front.png) | X/Y/Z 이동 최소·중심·최대의 정면 시점. |
| [translation side sheet](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifacts_v2/contact_sheet_translation_side.png) | X/Y/Z 이동의 측면 시점. |
| [translation hands sheet](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifacts_v2/contact_sheet_translation_hands.png) | 이동 끝점의 손 시점. |
| [rotation front sheet](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifacts_v2/contact_sheet_rotation_front.png) | 넥·방위 절대각과 앞판 baseline correction의 정면 시점. |
| [rotation side sheet](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifacts_v2/contact_sheet_rotation_side.png) | 회전 끝점의 측면 시점. |
| [rotation hands sheet](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifacts_v2/contact_sheet_rotation_hands.png) | 회전 끝점의 손 시점. |
| [결과 설명 및 개별 native 링크](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/README.md:1) | 제안과 제한, 6개 시트, 13개 case별 pose/front/side 링크. |
| [artifact 보존 전 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifact_preservation_before_v2.json:1) | 현재 artifacts 재검증 전 producer/manifest/mapping 보존 목록. |

누적 문서 완료 섹션: [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:1368), [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:2201), [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2204).
