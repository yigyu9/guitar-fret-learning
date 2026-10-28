# 독립 검수 결과

**요약 판정: 문제없음**

Critical·Suggestion: 발견된 항목 없음.

**Warning — 구형 고정 출처 검사의 호환성 제한**

`guitar_learning/tests/test_contact_recovery_checkpoint_provenance.py:67`의 기존 성공 검사는 이번 변경 뒤 실패한다. `tool/experiments/contact_recovery/checkpoint_provenance.py:25`의 고정 live SHA·bytes 5개는 작업 전 스냅샷과 모두 일치하고 현재 소스와는 모두 불일치하므로, 69행의 엄격 검사가 의도대로 거부한다. 고정 계약을 현재 SHA로 다시 정의하거나 검증·테스트를 완화하지 않는 처리가 적절하다. 결과 문서에 이 구형 일회성 이전 도구를 현재 트리에서 재실행할 수 없음과 추가 실패 1건을 명시해야 한다. 현행 기본 새 학습의 계산 회귀나 strict resume 실패와는 구분한다.

- 보관 원문 487개와 현재 소스를 대조했다. 지정한 40개만 변경되었으며, 33개는 설명용 docstring을 제외한 실행 AST가 동일하다. 나머지 7개에서 발생한 실행 AST 차이는 요청한 10개 중복 함수 제거와 기존 공용 구현의 별칭 연결뿐이다.
- 파일 SHA 별칭 7개를 빈 파일·1바이트·1MiB 경계 전후·2MiB의 6가지 크기로 검사하여 기존 SHA와 일치했다. `_sha`와 `_wrist_sha`의 모듈별 patch 대상도 독립적이다. `_rigid_body_row`는 기존과 동일한 자세·속도 순서를 반환한다.
- `training.recording`은 즉시 표준 라이브러리만 사용한다. `historical_inputs`와 `score.canonical`을 새 프로세스에서 불러와도 NumPy·Torch·Isaac을 불러오지 않으며, 새 순환 import나 Isaac/Torch 초기화 순서 문제를 발견하지 못했다.
- native 출처 목록의 차이는 정확히 4개 `internal_sha256`뿐이다. 원본 SHA·경로·나머지 필드는 동일하고, 현행 190개 출처 파일의 바이트 검증이 통과했다. 보관 원문의 SHA도 모두 유지된다.
- 정책 9조건에서 매개변수 순서·가중치·행동/가치/확률·난수 상태가 정확히 동일함을 확인한 검증 자료를 검토했다.
- 보상·제어·종료·자료 키·checkpoint 입력 검증은 바뀌지 않았다. 설명문 변경도 파일 SHA를 바꾸므로 기존 checkpoint의 strict 재개가 거절될 수 있다는 제한은 현행 README에 이미 명시되어 있다.

487개 파일의 구문 컴파일을 확인했다. 전체 CPU 188모듈·1318검사 중157모듈 통과·31모듈 실패다. 기존30개 실패는 동일하고, 위 구형 고정live source 검사1건이 추가로 실패했다. 실제 GPU 새 학습과 동일 소스의 strict 재개는 모두 통과했다. 이 검수는 변경의 정확성을 다루며 장기 학습 성능 개선을 증명하지 않는다.

추가 확인: 최종 결과 README에 위 호환성 제한·추가 실패·고정 pin 보존이 명시되었다. 검사 비교 JSON의 해당 `baseline_same`도 false로 교정되어 경고의 문서화 권고는 반영 완료다.
