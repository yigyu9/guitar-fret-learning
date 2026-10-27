# 새 손별 학습 실행 독립 검수

2026-10-20. 요약 판정: **소스 변경에서 추가 결함 없음. 전체 단일 프로세스 회귀 검증은 미완료**.

## 소스·실행 검토

- 작업 전 보관본을 기준으로 새 `train.py`·`training/start.py`와 `train_parallel.main(settings=...)` 변경을 검토했다. 기존 물리·보상·PPO·checkpoint 구현은 변경하지 않고 기존 worker와 선택한 손의 SpecialistPolicy를 연결한다. 과거 BC·전문가 모델·성공 gate 실행을 호출하지 않는다.
- 설정은 영구 출력 경로 `settings.json`에 먼저 저장한 뒤 실제 바이트를 pin한다. spawn에는 module-level worker factory를 전달하며, native 이전 Torch import를 피하는 CLI 순서와 예외 시 patch 복원을 확인했다. auto는 실제 장치를 저장하고 명시적 CUDA 요청은 실패 시 CPU로 대체하지 않는다.
- 최종 `source_manifest_final.json`의 Python385개가 현재 파일 집합·SHA와 정확히 일치했다. 추가·누락·변경 Python은 없다.
- 원자료 report/contract/persistent 감사에서 왼손420·오른손420·재개20전이가 모두 completed=true/failure=null이며 sampled/logged/durable/committed가 각각 일치함을 확인했다. 상태563과 persistent 감사 통과도 확인했다. 좌우 음악 성공은 각각0이며 실행 연결 검증을 음악 학습 성공으로 확대하지 않는다.
- checkpoint strict load와 optimizer/RNG 복원 경로는 기존 PPO 구현을 따른다. 재개 결과는 누적 업데이트1→2이며, checkpoint 계약 비교와 현재 실행 소스 SHA 감사를 구분해 문서화한다.
- 신규6검사의 초기화 요구 제거·장치 선택·help 의존성·비활성 손0행동·연결 복원·설정 pin을 검토했다. 역사 검사 변경은 새 train.py가 재사용하는 경로 대신 여전히 보관된 원본을 검사 대상으로 선택한 것이며 기존 evidence dict 검증은 유지된다.

## Warning — 전체 회귀 검증 제한

`full_tests_sigfpe.log` 및 `full_tests.log`에서 기존 `test_transition_capture.TransitionCaptureTests.setUpClass → transition/probe.py:92 → json.dumps → json.encoder`의 SIGFPE가 발생했다. 해당 전환 검사만 실행한 `transition_repro.log`에서도 재현되므로 새 검사 실행 순서가 원인이라는 근거는 없다. 원인은 아직 확정되지 않았다.

새 검사와 runner/capture를 함께 실행한 `order_repro.log`의17검사 통과와 읽기 전용 FPU 관측483회 정상 결과는 범위가 제한된 추가 증거다. 실패 순간의 상태나 근본 원인을 해명하지 않으며 **전체 단일 프로세스 회귀 통과를 주장할 수 없다**. mask·직렬화 backend를 변경해 실패를 숨기지 않았음을 확인했다.

최종 `remaining_tests.log`도 기존 `test_transition_refinement_serialization_v2.py:170`의 float 표현 비교에서 SIGFPE(exit136)로 종료한 것을 직접 확인했다. 따라서 전체 단일 프로세스와 분할 검사 전체 모두 통과를 주장할 수 없다.

최종 README와 verification.json을 다시 검토했다. 두 전체 실행과 나머지 검사에서 발생한 SIGFPE, 관련19검사·순서 재현17검사 통과, 원인 미해결을 구분해 기록했고 completed=false 및 implementation_verified=true로 실행 연결 검증과 전체 검증 제한을 분리했다. 이전 `running` 문구에 대한 기록 보완 권고는 해결됐다. 추가 소스 수정 사항은 발견되지 않았다.
