# Tensor effort API 사전 독립 검수

- 검수일: 2026-10-07
- 범위: `run_tensor_effort_api.py`, 승인된 `TENSOR_EFFORT_API_PROPOSAL.md`, fixture 및 CPU Tensor 소유권 계약.
- 검수 방식: 코드·로컬 API 근거·AST/XML 구조 읽기. Native 초기화·시뮬레이션은 실행하지 않았다.

요약 판정: **문제없음 — 승인된 6조건 실행의 사전 검수 통과. 남은 Critical/Warning 없음.**

## 확인 내용

- 원본 L_Shoulder_x hinge와 해당 형상을 별도 fixture로 복사한다. 원본 모델·메인 환경을 수정하지 않으며, fixed root·중력 0·기타/바닥/스트랩 없는 단일 관절 조건이다.
- EFFORT/POS × 0/+1/−1 Nm를 각각 fresh 환경에서 24 step 실행한다. stiffness 0, damping 50, effort 150 및 CPU solver 조건을 native readback으로 검사한다.
- 초기 q/속도는 한 번만 설정한다. 이후에는 force tensor만 제출하며 실제 pose/state를 다시 쓰지 않는다. 초기 1개와 완료 24개의 상태, 24개 제출을 기록한다.
- 연속 NumPy float32 버퍼의 주소·shape·device·dtype와 `own_data=False`를 검사한다. 버퍼와 descriptor는 sim을 파괴할 때까지 살아 있는 함수 지역 참조로 유지된다.
- API 거절, 비유한 상태, 예상하지 않은 접촉 및 계약 위반 시 중단하고 해당 partial JSON을 남긴다. 다른 모드/API로 자동 전환하지 않는다.
- 측정된 0/±1 Nm의 응답 차이는 관측값이다. 원본 GPU 모델의 구동 유효성, 전체 사람 모델의 actuator 등가성이나 기타 안정성으로 일반화하지 않는다.

## 지적 및 해소

- **Warning 해소:** `/home/ajou/yigyu/3/stability_adapter_2/run_tensor_effort_api.py:143`의 저장 후 정리 순서는 저장 예외 시 sim 정리를 건너뛸 수 있었다. 현재 :144–147의 중첩 `try/finally`로 저장 성공 여부와 무관하게 `destroy_sim` 호출을 보장하는 수정 확인.

## 최종 판정

문제없음. 승인된 단일 6조건 배치를 실행할 수 있다. 실제 API 수락·native 응답·실행 완료 여부는 후속 runtime 검수 대상이며 이번 사전 검수의 성공 주장에 포함하지 않는다.

이 사전 검수 기록은 동결한다. 다른 코드·원자료·기존 동결 검수 파일은 수정하지 않았다.
