# 입력·검증 파일 색인

## 감사와 독립 hull 검증

- [HAND_HAND_COLLISION_AUDIT.md:1](/home/ajou/yigyu/3/stability_adapter_2/HAND_HAND_COLLISION_AUDIT.md:1): 질문과 감사 범위·대표 시점 검증 계획.
- [audit_hand_hand_collision.py:24](/home/ajou/yigyu/3/stability_adapter_2/audit_hand_hand_collision.py:24): 저장된 241 pose의 17×17 source shape signed query와 native filter/contact summary.
- [verify_hand_hand_hulls.py:16](/home/ajou/yigyu/3/stability_adapter_2/verify_hand_hand_hulls.py:16): 대표 5개 저장 시점의 independent convex-hull intersection LP.
- [environment.py:122](/home/ajou/yigyu/3/stability_adapter_2/environment.py:122): humanoid actor의 native collision filter 설정.
- [initial_overlap.py:59](/home/ajou/yigyu/3/stability_adapter_2/initial_overlap.py:59), [replay_contact_geometry.py:10](/home/ajou/yigyu/3/stability_adapter_2/replay_contact_geometry.py:10): 기존 source geometry query/probe 경로.
- [report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_hand_collision_audit_v1/report.json:1), [samples.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_hand_collision_audit_v1/samples.json:1): 241상태 query와 native contact/filter 결과.
- [hull_frames.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_hand_collision_audit_v1/hull_frames.json:1), [hull_verification.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_hand_collision_audit_v1/hull_verification.json:1), [hulls_execution.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_hand_collision_audit_v1/hulls_execution.log): 대표 pair 결과, LP 증거, 검증 실행 로그.
- [interrupted_full_hull_scan/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_hand_collision_audit_v1/interrupted_full_hull_scan/): 중단된 전체 LP scan의 코드·실행 기록·상태 보존.

## 측정 대상과 표시 이미지

- source run [report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/full_1s/report.json:1), [states.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/full_1s/states.json:1), [contacts.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/full_1s/contacts.json:1).
- 기존 0.5초 source-geometry preview: [preview_step_120.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/images/preview_step_120.png). 새 이미지나 영상은 만들지 않았다.
- [README.md:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_hand_collision_audit_v1/README.md:1), [VISUAL_REPORT.md §51:948](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:948): 사용자 질문에 대한 요약과 범위.

이 문서화 단계에서는 물리 실행이나 설정 변경이 없었다. [최종 독립 검수](review.md:7)는 완료했고 남은 finding이 없다.


[메인 계획의 추가 기록](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1065), [결과 메인 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:300), [검수](review.md:7), [실행 소스·문서 사본](source_final_manifest.json), [마감 검증](verification.json)을 함께 보존한다.
