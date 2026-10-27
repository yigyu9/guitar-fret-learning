# 변경 파일 색인

`three_face_half_strap_slack_v1`의 실제 소스·결과 경로다. 소스 링크는 현재 1-based 줄 번호를 가리킨다. native 실행 runner는 수정하지 않았으며 기존 `main`은 [run_seed2_support_warmstart.py:18](/home/ajou/yigyu/3/stability_adapter_2/run_seed2_support_warmstart.py:18)이다.

## 실험 소스와 계획

- [prepare_three_face_half_slack.py:19](/home/ajou/yigyu/3/stability_adapter_2/prepare_three_face_half_slack.py:19) — 두 LA-only 입력과 출처 준비.
- [analyze_three_face_half_slack.py:20](/home/ajou/yigyu/3/stability_adapter_2/analyze_three_face_half_slack.py:20) — 새 두 실행과 저장 기준 분석.
- [half_slack.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/three_face_half_strap_slack_v1/half_slack.json:1), [zero_slack.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/three_face_half_strap_slack_v1/zero_slack.json:1) — 두 trial 입력.
- [THREE_FACE_HALF_STRAP_SLACK_PLAN.md:1](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_HALF_STRAP_SLACK_PLAN.md:1) — 비교 조건과 체크.
- [THREE_FACE_NATIVE_FEATURE_MAP_PLAN.md:1](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_NATIVE_FEATURE_MAP_PLAN.md:1) — 다음 saved-data feature 진단 계획, 아직 미실행.
- [PLAN.md:1533](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1533), [stability_adapter_2/README.md:853](/home/ajou/yigyu/3/stability_adapter_2/README.md:853) — 메인 계획 및 handoff 업데이트.
- [dated stability_adapter_2 index:517](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:517) — 날짜별 결과 색인.

## 산출물 producer와 보존본

- [make_three_face_half_slack_artifacts.py:10](/home/ajou/yigyu/3/stability_adapter_2/make_three_face_half_slack_artifacts.py:10) — v1 producer의 phase/hash 설정. v1 실행 소스는 보존됐고, timeline legend 겹침은 기록했다.
- [make_three_face_half_slack_artifacts_v2.py:10](/home/ajou/yigyu/3/stability_adapter_2/make_three_face_half_slack_artifacts_v2.py:10) — v2 producer의 phase/hash 설정. [그림 함수:90](/home/ajou/yigyu/3/stability_adapter_2/make_three_face_half_slack_artifacts_v2.py:90), [실행 함수:166](/home/ajou/yigyu/3/stability_adapter_2/make_three_face_half_slack_artifacts_v2.py:166)에서 그래프와 fresh 출력 경로를 만든다.
- [v1 실행 소스](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/artifact_layout_v1/artifact_source.py>), [v2 실행 소스](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/artifact_source_v2.py>)와 실행 wrapper/log를 보존했다. 원 producer template·manifest·복사 영수증은 [producer_template_snapshot](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/producer_template_snapshot/>)에 있다.

## 결과와 검증 근거

- [README.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/README.md>) — 한국어 초기값, 공통 목표, 측정 비교, 한계, 그림과 실제 영상.
- [VISUAL_REPORT.md:1551](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1551) — 누적 보고서 §82, 그림 118/119.
- [analysis.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/analysis.json>) — 결과 파일 SHA-256 `35e2054f93c863d299437842a79addcadafa40b6ec24f9dfceeaa232c87746e8`; 11321개 분석 입력 SHA closure와 7개 분석 계약은 plot closure와 별도다.
- [artifact_execution_v2.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/artifact_execution_v2.json>), [artifacts_v2/artifact_manifest.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/artifacts_v2/artifact_manifest.json>) — v2 산출물 실행 및 별도 14입력/2출력 hash closure, `native_calls: 0`.
- [review.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/review.md>) — 독립 검수 상태를 기록한다.
- [final_verification.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/final_verification.json>) — 최종 보존 대조와 입력·소스 봉인 기록 경로다.
- [artifact_layout_v1 archive](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/artifact_layout_v1/>) — v2 수정 전 성공한 첫 레이아웃과 실행 evidence.


## 담당 범위와 임시 문서 보존

- [추가 지침 AGENTS.md:1](/home/ajou/yigyu/3/stability_adapter_2/AGENTS.md:1) — 산출물 담당자의 검수/감사 placeholder 생성 금지, 파일 소유권·한국어 문서·절대 미디어 링크와 소비 소스 보존 규칙을 기록했다.
- [임시 검수·감사 초안 보존](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/artifact_document_drafts/preservation.json:1) — 산출물 담당자가 담당 범위 밖에 생성한 pending placeholder 두 파일을 실제 검수·감사 전에 SHA exact로 별도 보존했다. 최종 review는 독립 검수 담당자, final_verification은 root의 실제 감사 결과다.
