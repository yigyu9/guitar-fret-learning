# 변경 파일과 실제 줄 번호

이번 변경은 보상 설계 감사·계산용 코드·문서와 그림뿐이다. 실제 환경/학습 코드·가중치·기존 v4는 변경하지 않았다. 기존 main4개는 추가 기록만 남겼다.

| 파일 | 실제 줄 | 내용 |
|---|---:|---|
|[REWARD_DESIGN_AUDIT_V4_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/REWARD_DESIGN_AUDIT_V4_PLAN.md:1)|1|감사 계획/분담/검증 기준|
|[REWARD_DESIGN_AUDIT_V4.md](/home/ajou/yigyu/3/stability_adapter_2/REWARD_DESIGN_AUDIT_V4.md:7)|7|전체 판단|
|[REWARD_DESIGN_AUDIT_V4.md](/home/ajou/yigyu/3/stability_adapter_2/REWARD_DESIGN_AUDIT_V4.md:22)|22|핵심 감사 항목|
|[REWARD_DESIGN_AUDIT_V4.md](/home/ajou/yigyu/3/stability_adapter_2/REWARD_DESIGN_AUDIT_V4.md:33)|33|실제 CPU tracker 반례|
|[REWARD_DESIGN_AUDIT_V4.md](/home/ajou/yigyu/3/stability_adapter_2/REWARD_DESIGN_AUDIT_V4.md:112)|112|다음 소단계|
|[audit_reward_design_v4_v2.py](/home/ajou/yigyu/3/stability_adapter_2/audit_reward_design_v4_v2.py:16)|16|성공한 합성 계산/원본 CPU tracker 호출|
|[audit_reward_design_v4.py](/home/ajou/yigyu/3/stability_adapter_2/audit_reward_design_v4.py:16)|16|첫 실패 계산기; 실행 후 보존, 재실행 진입점 아님|
|[README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/reward_design_audit_v4/README.md:1)|1|결과 설명/원자료/그림|
|[generate_audit_signals.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/reward_design_audit_v4/generate_audit_signals.py:1)|1|그림 producer|
|[PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:809)|809|main 원문 뒤 감사 요약 추가|
|[README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:1934)|1934|main 원문 뒤 감사 요약 추가|
|[README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:619)|619|main 원문 뒤 감사 요약 추가|
|[VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2389)|2389|main 원문 뒤 감사 요약 추가|

이미지: [세 패널 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/reward_design_audit_v4/audit_signals.png). 계산 기록: [counterexamples.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/reward_design_audit_v4/counterexamples.json), [execution_record.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/reward_design_audit_v4/execution_record.json). 첫 실패 및 그림 보완 전 원본은 attempt_1/before_visual_fix/before_caption_move 아래 보존했다. 독립 검수/최종 보존 검증/봉인 snapshot은 이 phase의 review.md/final_verification.json/source_final/artifact_inventory.json을 따른다.
