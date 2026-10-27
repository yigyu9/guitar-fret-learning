# 수동 기타 초기 배치 편집기 v1 — 파일 색인

이번 도구 구현과 입력 조건 기록은 아래 소스에 있다. 줄 번호는 작성 시점 파일의 실제 줄에서 확인했다.

| 파일 | 목적·참조 |
|---|---|
| [interactive_guitar_pose.py](/home/ajou/yigyu/3/stability_adapter_2/interactive_guitar_pose.py:19) | 키 도움말(19–24), candidate 입력 검증 및 session 출처(73–92), 저장 payload(159–170), 후보 저장(175–180), preview/state guard/report(184–243), 키 이벤트(267–289), CLI/DISPLAY 조건(331–342) |
| [guitar_pose_edit.py](/home/ajou/yigyu/3/stability_adapter_2/guitar_pose_edit.py:6) | 유한 pose 검증·quaternion 정규화(6–12), world/local 위치·회전 조작(15–26), 기준 대비 pose delta(29–35) |
| [tests/test_guitar_pose_edit.py](/home/ajou/yigyu/3/stability_adapter_2/tests/test_guitar_pose_edit.py:1) | world/local 이동, rotation composition/pivot, 잘못된 pose 및 quaternion-sign 테스트 |
| [verify_interactive_guitar_pose.py](/home/ajou/yigyu/3/stability_adapter_2/verify_interactive_guitar_pose.py:1) | 원 native harness 실행 소스 참조. 종료 시 `numpy.bool_` summary 직렬화 오류와 exit 1은 원 log/verification 기록에 그대로 보존 |
| [open_guitar_pose_editor.sh](/home/ajou/yigyu/3/stability_adapter_2/open_guitar_pose_editor.sh:1) | rl38 runtime/PYTHONPATH 설정 및 실행 진입점(3–9) |
| [INTERACTIVE_GUITAR_POSE_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/INTERACTIVE_GUITAR_POSE_PLAN.md:1) | 도구 범위, 키, 검증 계획, 후보 해석 한계 |
| [GUITAR_POSE_EDITOR_GUIDE.md](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_POSE_EDITOR_GUIDE.md:1) | 사용자 실행 가이드와 키 조작(현재 파일 57행) |
| [verify_guitar_pose_editor_static_v2.py](/home/ajou/yigyu/3/stability_adapter_2/verify_guitar_pose_editor_static_v2.py:20) | 새 native static scene에서 입력·pose·불변조건·기존 preview를 확인하는 검증 진입점 |
| [static_v2 verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/static_verification_v2/verification.json:1) | 27 checks all true, 신규 물리 0, 저장 preview read-only 대조 |
| [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/README.md:1) | 실행법, 보존 조건, 저장 후보, 실제 preview와 harness 실패 구분 |
| [VIDEO_INDEX_v18.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v18.md:1) | 이전 v17 170개 + 이번 preview 영상 2개 = 172개 목록 |

## 이번 문서 작업 산출물

- [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/README.md:1) — 후보 및 preview에 관한 확정 brief 사실만 기록했다. 정적 장면을 contact/clearance 인증으로, 5초를 평형으로, 편집 후보를 자연스러운 채택 결과로 해석하지 않는다.
- [VIDEO_INDEX_v18.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v18.md:1) — v17의 기존 170개를 보존 참조하고 새 whole-body/hands 영상 두 개를 추가해 합계 172개로 표시한다.
- [preview_000 whole-body video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos/interactive_guitar_pose_v1__preview_000__whole_body.mp4) 및 [hands video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos/interactive_guitar_pose_v1__preview_000__hands.mp4) — 원본 preview MP4를 재인코딩 없이 복사했다. 원본과 복사본의 SHA-256은 README에 기록했다.

기존 원 harness exit 1의 truncated JSON은 static_v2 PASS와 구분해 보존했다. strap OFF 5초 physics는 실행하지 않았고 정적 OFF 표시/raw recorder 분기만 검사했다. Root가 추가한 main references는 [stability_adapter_2 README](/home/ajou/yigyu/3/stability_adapter_2/README.md) 1346행, [PLAN](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md) 2167행, [VISUAL_REPORT](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md) 2165행에 기록했다. 최종 보존 감사는 root 담당이며 이 색인은 완료를 선취하지 않는다.
