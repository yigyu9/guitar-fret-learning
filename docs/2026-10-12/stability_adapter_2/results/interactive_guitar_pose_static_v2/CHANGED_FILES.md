# 정적 기타 초기 배치 편집기 v2 — 파일 색인

새 물리 없는 static 도구의 최종 권장 실행 entry와 결과를 정리한다. 이전 v1 physical preview와 기존 frozen static core/launcher/이미지는 수정하지 않았다. 현재 확인한 파일의 실제 줄 번호를 연결했다.

| 파일 | 내용 |
|---|---|
| [interactive_guitar_pose_static.py](/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose_static.py:1) | 보존된 frozen static core: zero-gravity와 차단 API, 정적 edit/candidate 입력 저장의 기본 구현. 같은-batch 캡처 선 정리는 후속 entry에 추가 |
| [guitar_pose_static.py](/home/ajou/yigyu/3/stability_adapter_2/guitar_pose_static.py:1) | 최종 entry; candidate capture 직전 viewer line clear, capture 뒤 화면 draw 복원(6–20), wrapper 실행(23–32) |
| [open_guitar_pose_static.sh](/home/ajou/yigyu/3/stability_adapter_2/open_guitar_pose_static.sh:1) | 사용자용 최종 권장 rl38 launcher(1–9) |
| [GUITAR_POSE_STATIC_ENTRY.md](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_POSE_STATIC_ENTRY.md:1) | 최종 launcher와 same-batch T/S capture 처리 안내 |
| [verify_guitar_pose_static_snapshot.py](/home/ajou/yigyu/3/stability_adapter_2/verify_guitar_pose_static_snapshot.py:1) | draw 사이 없는 T/S native 입력과 whole-body/hands orange pixel, state 불변, 시간0 검사(10–35) |
| [open_guitar_pose_editor_static.sh](/home/ajou/yigyu/3/stability_adapter_2/open_guitar_pose_editor_static.sh:1) | 이전 static-core launcher. 과거 재현 및 정적 core 보존용이며 최종 권장 진입점은 아님(1–9) |
| [GUITAR_POSE_STATIC_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_POSE_STATIC_PLAN.md:1) | 사용자 정정, 금지 물리 동작, 정적 검증 범위와 새 진입점 |
| [GUITAR_POSE_STATIC_GUIDE.md](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_POSE_STATIC_GUIDE.md:1) | 사용자 조작법, 실행·후보 재사용, 정적 도구의 해석 범위 |
| [verify_guitar_pose_static.py](/home/ajou/yigyu/3/stability_adapter_2/verify_guitar_pose_static.py:1) | native static X11 입력과 no-physics barrier 검증(9–61); 18 checks와 0 physics steps/trials를 결과 JSON에 기록 |
| [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/README.md:1) | 실제 검증·이미지 캡션, 실행법 및 후보 해석 범위 |
| [verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/native/verification.json:1) | 18/18 checks true, `physics_steps=0`, `physics_trials=0`, X11 입력 F3/L/SPACE/E |
| [candidate_000](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/native/session/candidate_000/pose.json:1) / [candidate_001](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/native/session/candidate_001/pose.json:1) | 같은 기능검증용 편집 pose의 route display ON/OFF 저장 값; 둘 다 물리 비활성 |
| [snapshot verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/snapshot_verified/verification.json:1) | 4/4 checks true; same-batch T/S에서 두 native PNG의 orange debug pixel 0, 전체상태 불변, physics step 0 |
| [snapshot-verified OFF image](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/snapshot_verified/candidate_000/images/frames/whole_body/00000.png) | README에 표시한 최종 권장 entry의 native camera 캡처 |
| [clean_capture_check.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/clean_capture_check.json:1) / [clean_static_capture OFF image](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/clean_static_capture/candidate_000/images/frames/whole_body/00000.png) | 앞선 보정용 정적 캡처·기록도 보존. 최종 T/S event-batch 검증에는 snapshot_verified를 사용 |

ON 실제 이미지는 native/session/candidate_000 아래의 whole_body/hands PNG다. OFF 원본 candidate_001과 앞선 clean_static_capture는 보존하며 README의 최종 OFF 이미지는 snapshot_verified 캡처다. 영상은 생성하지 않았다. 최종 root README·PLAN·VISUAL_REPORT append는 완료됐으며 각 참조 줄은 추가 직후 다시 확정한다. 검수·감사 파일은 해당 담당자가 관리한다.
