# 독립 검수

요약 판정: **문제없음**. 검수 시점의 필수 수정 사항은 없다. 새 GPU 실행 없이 코드와 기존 원시 증거를 읽고 CPU 검사를 수행했다.

## 범위

`tools/runtime.py`, `prepare_targets.py`, `test_runtime.py`, `run_study.py`, `test_study.py`, `audit_action_space.py`, 네 조건의 생성 번들 및 `validation/action_space/report.json`·`분석.md`를 확인했다. 기존 6→8 runtime과 변경 부분을 비교했다. 별도 worker가 추가 중인 `test_analysis.py`는 이 검수 범위에 포함하지 않았다.

## 확인 결과

- CPU runtime 계약 검사 8개, study 검사 5개, 행동 codec·실제 제어기 CPU 검사 7개가 통과했다.
- 보상·제어·관측 선택·압현 판정과 A6 초기 catalog/provenance가 보존됐다. 단독 B의 역할은 index0/B이며 목표 수에 맞게 배열을 만든다. 엄지 활성화는 거절한다.
- gap150 시간표는 A3~4.5초/B6~7.5초, 전체8초다. gap075의 기존 기준 대비 실제 training 목표는 같고 차이는 생성 metadata다.
- 재개는 조건·schema·초기 자세·번들·source SHA를 엄격히 검사한다. 조건 간 모델 재개를 사용하지 않는다.
- orchestrator는 기존 helper의 실행 전후 source 봉인, GPU 점유 검사, 유한 시간 제한과 자기 child 정리를 사용한다. 조건별 19+19+26 updates와 seed7/17 경험 예산이 기존 기준과 맞는다.
- mean128 반복·sampled32는 분리된다. 실패를 평가 분모에 남기고 두 seed의 두 mean128 평가가 모두 통과해야 다음 조건으로 간다. 공개 영상은 조건별 대표 모델의 손/전신 한 쌍이다.
- 행동 범위 보고서의 모든 입력 SHA가 현재 파일과 일치하고 기존 native evidence의 accepted=true를 확인했다. 요청각과 적용각 비교 오차는 둘 다0이다. 발 IK 생략과 정책 학습 성공을 보장하지 않는 한계를 문서에 구분했다.
- 초기 Thorax_y의 latent 포화 설명은 고정 bias의 수치 비교이며 실제 network mean이나 유일한 정답 경로로 단정하지 않았다.

## 검증의 한계

본 검수는 GPU 물리 장면, 실제 학습·저장·strict 재개·렌더의 신규 실행 통과를 대신하지 않는다. 본 실험 전 orchestrator의 smoke를 실제로 완료하고 기술 검증과 성과 기준의 실패를 구분해야 한다. 검수 뒤 소스 변경이 있으면 최종 봉인 전에 해당 변경을 다시 확인해야 한다.

## 추가 확인: 실제 smoke 완료

추가된 `tools/test_analysis.py`를 읽고 CPU 8개 검사를 재실행해 모두 통과했다. M1/B index0, M2의 동적 시간표, 실패 포함 분모, 나중 episode 배제, trace episode/time window, 거절 사유의 우선순위, 보상 합계와 trace identity 거절을 확인했다. 위 최초 검수 범위의 제외 항목은 이 추가 확인으로 해소됐다.

2026-11-01 23:29 KST 무렵 `research_v1`의 다음 실제 실행 보고서를 독립 확인했다. 검수자는 GPU 실행을 추가하지 않았다.

| 실행 | 확인한 결과 |
| --- | --- |
| `jobs/smoke_train2/J/report.json` | completed/lifecycle_verified=true, large·1024환경·GPU PhysX/CUDA pipeline, 2 updates·65,536 committed 경험, failure 및 changed_inputs/missing_import_pins/cleanup_errors 없음 |
| `jobs/smoke_resume1/J/report.json` | 동일 b_only·seed7·1024환경으로 원래 final.pt strict 재개, initial manifest의 optimizer_updates=2에서 final=3으로 진행, 이번32,768·누적98,304 경험, completed/lifecycle_verified=true, 입력·종료 오류 없음 |
| `jobs/b_only_s7_t98304_smoke_mean32/report.json` | completed/lifecycle_verified=true, GPU32환경, 32개 최초 episode와 실패 포함 분모 계약 true, 입력변경·정리 오류 없음 |
| `jobs/smoke_render/report.json` | completed/lifecycle_verified=true, source_pins_unchanged/source_checkpoint_pins_validated/native_pixels=true, 150프레임, training_updates=0, 입력변경·정리 오류 없음 |

진행상태의 source_seal 508개를 실제 파일 SHA와 직접 대조해 변경 없음도 확인했다. 본학습 `b_only_s7_t622592_train` 진입을 확인했으며, **본학습 완료나 압현 성과 통과를 의미하지 않는다.** 이후 source 봉인과 각 조건의 성과 gate는 계속 별도로 확인해야 한다.
