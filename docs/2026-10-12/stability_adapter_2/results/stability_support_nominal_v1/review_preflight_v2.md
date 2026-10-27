# 지지 nominal readiness 수정 사전 독립 검수

요약 판정: **문제없음 — 최종 native v7/runner v8의 readiness 수정에 남은 실행 차단 오류 없음.** 원래 Q 사전 검수에서 collect가 readiness를 직접 호출하는 경로의 profile context를 놓쳤다. 기존 검수·소스·실패 실행은 보존하고 이 새 기록으로 판정을 보완한다. 이번 판정은 수정 경로의 정적·CPU 검수이며 실제 재시도 학습 성공이나 물리 안정성을 인증하지 않는다.

## Critical

최종 버전에서 없음. 보존된 [첫 실행 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/smoke_on_v1/report.json)의 stack는 collect→bounded.require_training_ready→native v5 readiness에서 실패했음을 보여준다. updates/transitions/학습 physics는0이었다. 별도 초기 평가 child는982control/3928physics를 완료했다. 실제 원인은 학습 장면의 종료 플래그가 아니라 support metadata와 부모 module PROFILE 이름의 불일치다.

## 확인 사항

- [native v7](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v7.py:8)은 readiness의 직접 호출 동안 native v5의 PROFILE을 해당 support profile로 적용한다. collect 진입과 기존 step 내부 모두 이 override를 사용한다. 정상/예외 반환 뒤 context가 원래 module 값을 복원한다. 종료·미준비·다른 metadata profile 거부 조건은 부모에서 그대로 검사하며 이를 우회하지 않는다.
- [readiness 회귀](/home/ajou/yigyu/3/stability_adapter_2/test_deadline_support_readiness_v1.py:14)는 올바른 profile의 직접 호출과 patch 복원, finished/unready/wrong-profile 거절을 검사한다. 검수자가 `PYTHONDONTWRITEBYTECODE=1 python -m unittest stability_adapter_2.test_deadline_support_readiness_v1 -v`를 독립 실행해2개 모두 통과했다. `__new__` 기반 상태 fixture여서 native 장면·물리 실행·정책 추론·학습·파일 출력은 없다.
- [runner v8](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v8.py:103)의 v7 대비 diff는 native import와 평가 child module 진입점뿐이다. [launcher v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/launch_run_v2.py:18)도 runner v8로 변경했다. 기존 codec·teacher 후처리/관측/기록·실제 PD history·한 물리 제출자·RMS-only 초기화·PPO v3·보상·안전/마감 계약은 수정하지 않는다.
- [계획 v2](/home/ajou/yigyu/3/stability_adapter_2/STABILITY_SUPPORT_NOMINAL_V2.md:5)는 첫 실패의 profile 원인과 초기 평가/갱신 전 실패를 구분하며 새 경로 재시도를 명시한다. 기존 leaf v1 및 첫 실행을 정상 학습 완료로 다시 해석하지 않는다.
- [새 사전 봉인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/source_before_native_v2/manifest.json)의9개 현재 원본·사본·예상 SHA를 독립 대조해 전부 같았다. 기존 v1 봉인의8개도 현재 원본·보존 사본·SHA가 그대로였다. native v7 SHA는 `c2e89a2ff961dc356107396a060db17c5d2be826ed9f1e7a486e0983936a2197`, runner v8 SHA는 `30b31afa2b7edca852f071e8582bf51259e4edb822ff53c5b5158b25ab2797d5`다.

## Warning

새 수정 요구 없음. readiness 수정은 실제 optimizer 갱신을 가능하게 하는 계약 오류 수정이다. 초기 평가 완주, 실제 학습 갱신, 기타 안정화·음악 성공은 별도로 판정해야 한다. 기존 Q 사전 검수의 성공 보장 없는 요청 공간·teacher 후처리 한계와 비선점 마감 제한은 유지한다.

## Suggestion

추가 변경 제안 없음. 실제 smoke_on_v2의 collect 진입·승인 optimizer step·KL/RMS·teacher/nominal/final PD·입력 불변·실제 종료 영상으로 재시도 결과를 확인해야 한다. 검수자는 이 새 보고서만 작성했고 기존 파일을 수정하지 않았다.
