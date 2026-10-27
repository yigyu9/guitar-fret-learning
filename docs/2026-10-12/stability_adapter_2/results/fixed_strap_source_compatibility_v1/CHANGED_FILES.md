# 변경 파일과 입력 근거

## 이번 산출물

- 한국어 결과와 범위 한계: [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/README.md:1)
- 6관절 signed minimum-change 그림: [fixed_strap_source_range_changes.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/artifacts/fixed_strap_source_range_changes.png)
- producer·wrapper·직접입력의 SHA 사본: [source_snapshot.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/artifacts/source_snapshot.json:1), [source_snapshot 디렉토리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/artifacts/source_snapshot)
- 그림 출력·14개 직접입력 전후 해시·48개 원분석 closure 수: [artifact_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/artifacts/artifact_manifest.json:1)
- 실제 명령·환경·exit·log SHA: [producer_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/artifacts/producer_execution.json:1), [producer.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/artifacts/producer.log:1), [실행 wrapper](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/artifacts/run_producer.sh:1), [보존 wrapper](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/artifacts/run_producer.sh.archived)

## 원분석·root 계획·코드

- 범위 요약·810개 행: [compatibility.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/compatibility.json:1), [joint_ranges.jsonl](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/joint_ranges.jsonl:1)
- 48개 입력 전후 hash와 실행 기록: [input_sha256_before.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/input_sha256_before.json:1), [execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/execution.json:1), [analysis.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/analysis.log:1)
- source 범위 계획·분석 판단·후속 손 배치 계획: [FIXED_STRAP_SOURCE_COMPATIBILITY_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SOURCE_COMPATIBILITY_PLAN.md:1), [FIXED_STRAP_SOURCE_COMPATIBILITY_DECISION.md](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SOURCE_COMPATIBILITY_DECISION.md:1), [FIXED_STRAP_SOURCE_HAND_INITIAL_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SOURCE_HAND_INITIAL_PLAN.md:1)
- 저장 분석기·artifact producer와 실행기: [audit_fixed_strap_source_compatibility.py](/home/ajou/yigyu/3/stability_adapter_2/audit_fixed_strap_source_compatibility.py:47), [run_fixed_strap_source_compatibility.py](/home/ajou/yigyu/3/stability_adapter_2/run_fixed_strap_source_compatibility.py:19), [make_fixed_strap_source_compatibility_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_fixed_strap_source_compatibility_artifacts.py:194)
- root 최종 감사 실행기: [/tmp/audit_fixed_strap_source_compatibility.py](/tmp/audit_fixed_strap_source_compatibility.py:1) (실행 결과는 phase 최종 검증 기록을 참조)
- root 검증 노트: [ROOT_VERIFICATION_NOTES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/ROOT_VERIFICATION_NOTES.md:1)
- root 누적 결과: [README.md 결과](/home/ajou/yigyu/3/stability_adapter_2/README.md:1100), [PLAN.md 결과](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1917), [VISUAL_REPORT §110](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2007)

기존 native t=0 프레임과 손 영상은 [앞선 initial-aligned trial](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/README.md:1)에서 재사용했다. 이번 작업에서 새 native·physics·actor·학습 실행은 없었다.
