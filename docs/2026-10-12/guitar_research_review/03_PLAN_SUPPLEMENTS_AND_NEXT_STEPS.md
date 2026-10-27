# 계획서 보충 내역과 다음 순서

> 작업일: 2026-10-09. 기존 계획의 환경·행동·보상 기본값은 수정하지 않았다.

## 기존 계획서 검토

[LEAN_STABILITY_ADAPTER_EXECUTION_PLAN.md](../plans/LEAN_STABILITY_ADAPTER_EXECUTION_PLAN.md)는 환경, 초기화, 접점, 제어 action, 관측, 단계, 힘 기반 grip 판정, 보상·종료, PPO와 구현 순서를 상세히 담고 있다. 계획에 나열된 미확정 물리값을 이번 문서 검토만으로 숫자화하는 것은 적절하지 않다. 실제 물리 측정 후 정하도록 한 기존 원칙을 유지했다.

처음 계획을 읽었을 때 확인한 보완점은 다음과 같다.

1. **lean 계획은 PPO 단일 경로를 기본으로 고정하고 있었다.** 단일 policy를 첫 baseline으로 삼는 것은 가능하지만, 단계 분리·기하/IK controller·residual RL·demonstration warm start를 언제 비교하고 어떤 지표로 채택할지 적혀 있지 않았다.
2. **최근 연구 흐름을 함께 설명하지 않았다.** 별도 `stability_adapter_2/`에는 2026-10-08까지의 저수준 물리 feedback 및 정적 배치 선택 결과가 있고, 같은 날짜에 물리 trial을 멈춘 사용자 요청도 있다. 기존 StabilityAdapter 상태 문서에는 이 분기와 pause가 반영되지 않았다.
3. **독립 복원 과제와 전체 연주 연구의 연결 순서가 부족했다.** StabilityAdapter가 해결할 과제와 물리 G0의 현 상태를 함께 표시해, 독립 환경 성공을 전신 기타 연주 완료로 오해하지 않도록 해야 했다.

## 이번에 보충한 내용

- 전체 연구 흐름을 Stage1 입력부터 FullBodyPlayer까지 한 경로로 요약했다.
- 각 단계에 현재 계약, 구현/검증 근거, 미완료 경계를 한 표에서 구분했다.
- 한 가지 방법에 고정되지 않도록 오디오, 운지, skill 학습, StabilityAdapter, Synchronizer, Full 결합의 후보와 trade-off를 기록했다.
- 후보 기법의 채택을 smoke 결과가 아니라 동일 입력·초기조건, 단계별 성공·안전·기술 보존 비교에 연결했다.
- 전체 연주 증명 우선 경로와 자유 기타 복원 우선 경로를 나란히 제시했다.
- 과거 계획·checkpoint가 현재 결과를 증명하지 않는다는 증거 해석 기준을 명시했다.

이 보충은 기존 학습 구조를 폐기하거나 PPO·33 action·목표 허용 오차를 변경하는 승인으로 해석하지 않는다. 실행 단계별 비교 제안이다.

## 다음 작업 체크리스트

- [x] 프로젝트·모듈 기준 문서와 현재 StabilityAdapter 계획 확인
- [x] 시작부터 최종 물리 실행까지 연구 흐름 및 근거/미검증 상태 정리
- [x] 미흡점 우선순위와 복수 접근법·장단점·비교 신호 정리
- [x] 기존 실행 계획에 대안 비교 및 공통 비교 게이트 보충
- [x] lean 경로와 `stability_adapter_2/`의 목표·action 차이 및 2026-10-08 pause 구분
- [x] `docs/2026-10-12/README.md`에서 새 검토 자료를 찾을 수 있게 연결
- [ ] Fret·Strike full-song 승급에 쓸 현행 checkpoint와 실행 폴더 identity 대조
- [ ] G0 물리 backend의 API·step 경계·source checkpoint 선행조건을 구현 계획에 쪼개 기록
- [ ] 우선 연구 질문(물리 연주 G0 또는 자유 기타 복원)을 논문 실험 순서와 일치시킴
- [ ] StabilityAdapter 두 경로를 분리 유지할지, 새로 맞춘 공통 계약으로 통합할지 결정
- [ ] `stability_adapter_2/` 물리 실험은 사용자의 재개 요청이 오기 전까지 중단 상태 유지

## 다음 단계의 완료 조건 제안

| 다음 단계 | 완료로 부를 최소 결과 |
|---|---|
| Source 준비 | Fret·Strike 각각 현재 계약과 일치하는 checkpoint, 입력 bundle hash, full-song 평가 report가 재현 가능하게 연결됨 |
| Physical G0 | 한 simulator의 고정 기타 rollout에서 event별 Fret readiness·Strike crossing·Synchronizer outcome을 같은 clock으로 기록하고 무결성 검사 통과 |
| G0 성능 근거 | 대표 구간과 곡 전체 평가에서 source 대비 성능 보존/퇴행, miss/delay, 안전 실패를 함께 보고 |
| lean Stability 단계 2 | lean 경로의 접촉면·법선·힘·상대 미끄럼 및 33 action 이동을 실제 PhysX에서 측정하고, API와 집계 경계가 관측·전환과 일치함을 보고. 이는 S2 기존 66관절 quiet 진단을 재분류한 결과가 아니다. |
| G1 통합 | G0 대비 기타 pose 안정성 향상과 Fret/Strike retention을 별도 지표로 동시 제시 |

위 완료 조건은 권고안이며 이미 승인된 성능 수치가 아니다. 수치 gate는 baseline 분포와 실제 물리 편차를 확보한 뒤 각 계획에서 정한다.
