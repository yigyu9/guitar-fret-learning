# 구현 및 데이터 경로

## 신규 실행 세 개

- 입력: [−Shoulder Y](</home/ajou/yigyu/3/stability_adapter_2/trials/seed2_response_locality_v1/negative_shoulder_y.json>), [−Wrist Z](</home/ajou/yigyu/3/stability_adapter_2/trials/seed2_response_locality_v1/negative_wrist_z.json>), [half heldout](</home/ajou/yigyu/3/stability_adapter_2/trials/seed2_response_locality_v1/half_heldout.json>)
- 초기값/raw/capture: [native run 자료](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/native>)
- 준비·실행·분석: [trial 준비기](</home/ajou/yigyu/3/stability_adapter_2/prepare_seed2_locality_trials.py:18>), [runner](</home/ajou/yigyu/3/stability_adapter_2/run_seed2_response_locality.py:18>), [analysis producer](</home/ajou/yigyu/3/stability_adapter_2/analyze_seed2_response_locality.py:24>)
- 저장 분석: [analysis.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/analysis.json>) — 8 checks, 3 init, 3600 physics steps

## 저장 참조와 그림

- 과거 7개 probe 중 재사용한 baseline/positive Shoulder Y/positive Wrist Z: [probe_analysis.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/probe_analysis.json>)
- 과거 full heldout: [heldout_analysis.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/heldout_analysis.json>)
- 새 그림 생성기: [make_seed2_locality_artifacts.py:82](/home/ajou/yigyu/3/stability_adapter_2/make_seed2_locality_artifacts.py:82)
- [canonical artifacts](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifacts>), [manifest](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifacts/artifact_manifest.json>), [execution metadata](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifact_execution.json>), [execution log](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifact_execution.log>)
- 후처리 이력은 세 번이다. [v1 archive](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifacts_attempt_v1>)는 필드명 오류로 렌더 전에 종료했다(0 native/0 physics step). [v2 archive](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifacts_attempt_v2>)는 첫 성공 출력이지만 step 0–24 exactness boolean을 true여야 하는 그림 통과조건으로 사용했다. [preservation record](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifacts_attempt_v2/preservation_verified_before_edit.json>)는 v2 편집 전 producer·출력 SHA와 입력 closure를 확인한다. 현재 canonical은 세 번째 후처리 실행으로 boolean 형식만 검사해 false도 허용하며 PNG 두 개는 v2와 byte-identical이다. 최종 기록은 [검증](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/final_verification.json>), [artifact inventory](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifact_inventory.json>), [source final manifest](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/source_final_manifest.json>)를 참고한다.

## 계획·검수 경로

- [이 단계 계획과 결과](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1401)
- [현재 결과 인계](/home/ajou/yigyu/3/stability_adapter_2/README.md:760)
- [후속 Shoulder Y feedback 계획](</home/ajou/yigyu/3/stability_adapter_2/SEED2_SHOULDER_GUITAR_FEEDBACK_PLAN.md>)은 아직 실행되지 않았다.
- 독립 검수 완료 기록은 [review.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/review.md>)에 있다.
