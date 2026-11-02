# 자율 개선 구현 변경 검수

요약 판정: **문제없음**. 지적 사항 수정 후 재검수 완료. GPU 실행 없이 CPU 검수만 수행했다.

## Critical / Warning

남아 있는 항목 없음.

## 수정·재검수

- 실패 원장의 마지막 유효 체크포인트가 항상 null이던 문제: `protected_kl(..., previous)`로 이전 경로와 SHA를 직접 기록하도록 수정 확인.
- 최고 모델만 렌더하던 문제: 조건별 최고와 동일 seed의 마지막 체크포인트가 다르면 두 모델을 구분하여 렌더·출판하도록 수정 확인.
- 새 조건을 제외한 빈 중간 그래프 문제: 원본 plot을 새 실행 프로세스에서만 no-op 처리하고 최종 summarize가 실제 조건으로 그래프를 생성하도록 확인.
- 수정 도중 생긴 summarize의 미정의 selection_kind 참조: 제거 확인. 실제 128환경 analysis fixture로 요약 생성과 추가 회귀 검사를 통과했다.
- model-only 이전은 원본 입력 핀·정책/PPO identity·가중치 유한성과 SHA를 검사한다. 새 정책 계약에 원본 SHA와 LR 조건을 포함하며 strict resume/평가에서는 재이전하지 않는다.
- LR 초기값·회복 상한 외 KL 보호·재시도 하한·보상·행동·관측 변경은 발견하지 못했다. 유한 KL만 독립 군 진행, 비유한·입력/정리 오류는 전체 중단 조건으로 분리되어 있다.
- 최종 비교는 두 seed·4군 추가100회 이상과 보호 실패 없음이 전제다. 실패 군을 제외한 우세 판정이나 환경128개를 독립 학습128회로 해석하는 통계 문구는 없다.

## 검증 근거

- `test_stability_runtime.py`: 11개 통과. 실제800회 체크포인트 strict identity/가중치 이전, CPU RNG 보존, 잘못된 SHA/identity 거부, LR 상한·원래 재시도 하한, finite/nonfinite KL 기록, factory 복원 포함.
- `test_run_study.py`: 최종 수정 후8개 통과. 오류 경계 6개와 실제 평가 fixture의 요약·실패 시 채택 차단·그래프 생성, 4군 각각 동일50/100블록 orchestration 검사 포함.
- 실제 원본800회 블록 learning_metrics 100줄을 읽어 추가 diagnostics를 생성했다. LR/KL/entropy/critic EV 및 9보상 집계가 오류 없이 생성됨을 확인했다.
- 기존 `study_v1`의 488개 source_seal과 실행 중 `continuation_v1`의491개 source_seal을 실제 SHA 대조했다. 변경0개.
- wrapper GPU 새 학습/strict resume/평가/렌더 검증은 이 검수 범위에서 실행하지 않았으며 root 작업의 preflight로 확인한다.

## 해석 범위

통과는 실행 계약·기록의 정합성과 CPU 검증에 대한 판정이다. 낮은 LR의 학습 성능 개선이나 자연스러운 압현 성공을 입증하지 않는다. 실제 GPU 비교 결과가 필요하다.

## 최종 추가 범위

- native preflight는 실제 7개 operation 정상 종료·완료, 원본 불변, 기존 감독 재개 확인을 모두 요구한다. 이후 기존 비교 완료와 GPU 비움을 기다리므로 기존 실행과 새 GPU 계산이 겹치지 않도록 순서가 연결되어 있다.
- ANALYSIS.md는 새4군의 마지막128평가와 기존 H/I/T의 `_last_saved` 평가를 구분한다. thumb 지표의 실제 키·단위 변환과 기존조건 필터가 일치한다. 가설의 다음 방향을 조건부로 기술하며 생산 기본값의 자동 교체를 주장하지 않는다.
- 총 CPU19검사(wrapper11 + coordinator8)를 통과했다. GPU preflight 결과는 별도 기록으로 확인하며 이 검수자가 GPU를 실행하지 않았다.

## tools_v2 이전 계약 수정 재검수

판정: **문제없음**. 원 v1 GPU preflight가 학습 시작 전 예산 계약 차이를 거부한 기록은 보존한다.

- 새 버전의 `transfer_architecture()`는 deepcopy에만 적용하며 top/core 두 contract의 `task.finger_skill.planned_transitions`와 `full_song_after`만 비교에서 제외한다. 원 settings·checkpoint identity 및 strict resume 검증은 그대로 유지한다.
- 제외 범위·이유를 새 실험 계약에 명시했다. 원본 정책/PPO identity·입력 핀·SHA 검사는 우회하지 않는다. 다른 scope/action 계약 변조는 여전히 거부한다.
- 기존 TransitionEnvironment._reset_scope는 evaluation/full_song을 일시 True로 강제하여 전체 AB를 선택한다. 이 실험에서 위 두 예산 필드 제외가 학습 목표 범위를 변경하지 않는 근거를 코드와 회귀 검사로 확인했다.
- coordinator 차이는 `TOOLS=__file__.parent`와 validation_v2 경로다. 이전 코드/실패 증거를 덮어쓰지 않는다.
- tools_v2의 wrapper13 + coordinator8 = **21 CPU 검사 독립 통과**. 실제 실패 training_contract로 모델 이전과 저장 architecture 불변, 비승인 변경 거부를 검사했다.
- GPU 7-operation preflight는 root 작업에서 진행하며 이 검수자는 GPU를 실행하지 않았다.
