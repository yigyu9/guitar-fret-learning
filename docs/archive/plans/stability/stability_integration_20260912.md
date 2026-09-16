> **HISTORICAL — 통합 이전 기록.** 본문의 수치·명령·검증 결과는 작성 당시 기준이다. [현재 StabilityAdapter 안내](../../../../stability_adapter/README.md)를 먼저 읽는다. 보관은 미완료 검증의 완료를 뜻하지 않는다.

# StabilityAdapter의 향후 연주 결합 준비

사용자 요청: 현재 독립 안정화 구조가 향후 Fret·Strike·Synchronizer에 연결되도록 설계.
현재 27D/107D 물리 사전학습은 유지하고, Full 105D 공통 관절 계약의 보정 모듈로 경계를 분리한다.

- [x] 현재 adapter 및 Full action/runtime/one-step 계약 확인
- [x] 관절 이름·radian residual proposal과 공통 합성 함수 구현
- [x] 독립 환경도 같은 합성 경로 사용
- [x] Full 105D pre-EMA bridge와 명시적 안전·Synchronizer 권한 제한 구현
- [x] 소유권/순서/단위/zero-residual 및 source 보존 CPU 검사
- [x] 독립 GPU 동작·짧은 PPO 재검증과 별도 변경 검수
- [x] 통합 순서·관측 확장·학습 단계·checkpoint 호환성 문서화

검증: 초기 hold를 기준으로 합성했을 때 현재 독립 task와 같은 target을 생성한다.
Full에서는 source 기준 target을 보존하며 허용된 27개 관절에만 제한된 residual을 적용한다.
손가락·손목·하체·시선의 source/hold 값을 그대로 보존하고, gate가 닫히거나 residual이 0이면
기존 source action과 동일해야 한다. bridge가 score clock·물리·EMA를 직접 실행하면 안 된다.

범위: 실제 source를 한 simulator로 연결하는 Full G1 구현·연주 보존 학습은 후속 단계다.
현재 107D actor는 source proposal/음악 상태를 학습하지 않았으므로 연주 결합 완료 정책으로
사용하지 않는다. Full용 관측 확장에는 별도 version과 fine-tuning/evaluation이 필요하다.

검증 결과: 새 CPU 합성 9개, 기존 adapter 13개 및 Full 계약/one-step 회귀 통과.
GPU audit의 두 환경 정착 값이 기존과 동일. 새 PPO 4회/1,024 transition에서 10회
optimizer update와 checkpoint 메타데이터 저장 확인. change-reviewer 검수 통과.
현재 완료는 연결 경계 준비이며 실제 Full G1 결합·연주 조건부 학습은 후속 단계다.
