# 변경 파일 색인

이 phase의 결과·실행·저장 자료는 아래에 있다. 경로는 절대 경로이며 각 링크는 실제 파일 줄을 가리킨다.

## 결과 및 산출물

- [한국어 결과·수치·실제 장면과 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/README.md:1)
- [저장 분석: 42개 검사, 두 완료 trial과 기준선 응답](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/analysis.json:1)
- [저장 시계열](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/series.json:1)
- [body9 실제 움직임 별도 진단](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/body_motion.json:1)
- [기타 오차·Wrist_y 실제각/PD 목표·기준 대비 위치 비교 도표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/artifacts/quiet_wrist_support_response.png), [실제 Gym 장면 프레임·영상은 결과 문서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/README.md:23)
- [그림 생성 실행·입력 SHA·로그 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/artifact_execution.json:1), [선택 입력 사본 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/artifact_source_manifest.json:1), [그림 생성 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/artifact.log:1), [그림 SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/artifacts/manifest.json:1)
- [분석 실행 metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/analysis_execution.json:1), [분석 입력 사본 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/analysis_source_manifest.json:1), [영상 수집 실행 metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/collection_execution.json:1), [수집 입력 사본 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/collection_source_manifest.json:1)
- [Root 보존 확인 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/ROOT_VERIFICATION_NOTES.md:1), [phase 최종 감사 실행기 source](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/root_final_audit_producer.py:1)
- [영상 모음 v15, 162개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v15.md:1), [v14 수집 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/video_collection_update_v14.json:1)
- [누적 과학 도표 설명 §119](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2116)

## 계획·실행·후처리 코드

- [L_Wrist_y 실험 계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_SUPPORT_AUTHORITY_PLAN.md:1), [실행 leaf](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_SUPPORT_EXECUTION.md:1), [다음 Wrist_z 계획(미실행)](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_Z_SUPPORT_AUTHORITY_PLAN.md:1)
- [조건 runner](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_wrist_support.py:19), [초기화·입력 봉인 wrapper](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_wrist_support_phase.py:23)
- [저장자료 analyzer](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_wrist_support.py:9), [body9 저장자료 진단기](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_wrist_body_motion.py:8)
- [분석·영상 수집 postprocess](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_wrist_postprocess.py:15), [4개 영상 수집기](/home/ajou/yigyu/3/stability_adapter_2/collect_quiet_wrist_videos.py:1)
- [그림 producer](/home/ajou/yigyu/3/stability_adapter_2/make_quiet_wrist_artifacts.py:1), [그림 실행 wrapper](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/artifacts/run_producer.sh:1)
- [phase 분석 log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/analysis.log:1), [영상 수집 log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/collection.log:1)
