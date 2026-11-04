# V5 기준 정리 독립 검수

요약 판정: **문제없음**. 검토한 변경에서 수정이 필요한 정확성·계약 검증·보안 결함을 발견하지 못했다.

## 검수 범위

- 작업 시작 상태는 `before.json`의 활성 Python SHA와 기존 git 상태를 기준으로 구분했다. 이미 있던 타현·전신 구현을 이번 변경의 결함으로 평가하지 않았다.
- V5 환경의 구버전 상속 제거, 공용 MLP와 목표 결합의 `training/policy.py` 이동, 구형 FingerSkillPolicy 제거, 기본 학습·평가·영상의 V5 연결을 확인했다.
- C1 원본 압현 시계, checkpoint 입력 SHA와 전체 architecture/contract 검사, runtime 복원과 재귀 여부, 오른손 공용 코드와 그래픽·목표각 역변환 helper 보존을 확인했다.
- 문서는 `documents_changes.json`의 삭제·이동·대체 경계와 대표 README·코드 지도·실행 예시를 대조했다. 문서 전체의 편집 검토나 보존된 역사 원문 내부 경로의 복구는 범위에 포함하지 않는다.

## Critical

없음.

## Warning

없음.

## Suggestion

없음. V5 소스 정리 전 checkpoint를 새 소스에서 암묵 재개하지 않는 현재 정책을 유지한다.

## 확인한 연결과 검증

- `training/launch.py`의 기본 설정은 V5 builder를 사용하고, V5 builder는 공용 `build_settings`를 직접 호출한다. 서로의 facade를 다시 호출하는 재귀는 없다.
- 공개 영상 함수는 V5 reader를 거쳐 내부 `_render`로 연결한다. 내부 renderer를 다시 공개 함수로 호출하지 않으며 실제 환경에서 `DecisionPPOTrainer.load()`의 엄격한 identity 검사를 유지한다.
- V5 checkpoint reader는 입력 SHA와 전체 architecture/contract 비교를 수행한다. C번들은 등록 bundle과 `verify_checkpoint_clock()` 검사를 추가로 요구하며, 준비·실행 시 원본 압현 시계 adapter를 적용한다.
- V5 runtime의 환경·정책·schema·pin override는 `finally`에서 원래 값으로 복원한다. C번들 원본 clock adapter도 기존 설치를 인식해 중첩 설치를 피한다.
- 왼손 legacy CLI와 직접 legacy runner 호출은 거부한다. 오른손 경로가 공유하는 정책·설정·그래픽 helper와 직접 위치 행동 역변환은 남아 있다.
- 활성 내부 import 검사는 삭제된 전용 모듈을 요구하지 않는다. 구버전 이름이 남은 보상·진단 메타데이터를 실행 가능한 구버전 모듈 참조와 구분했다.

독립 실행한 CPU 검사:

```text
test_compact_press_v5_entry
test_compact_press_v5_environment
test_compact_press_v5_policy
test_main_tools
52 tests, OK (18.513 s)

test_compact_strike_policy
test_whole_body_policy
test_press_sequence_entry
test_press_acquisition
test_hand_contact_probe
31 tests, OK (1.139 s)
```

총 83개 검사가 통과했다. 검수자는 구현을 수정하지 않았고 GPU 실행·C1 runtime/감독/원시 자료 변경을 수행하지 않았다. CPU 검사는 물리 장면을 새로 실행한 GPU 검증이나 음악적 성능 향상의 증거가 아니다. 별도 PC 재부팅에 따른 기존 C1 재개 작업은 이번 코드 정리 검수와 구분한다.

## 부록: 재부팅 후 C1 복구 감독기 검수

요약 판정: **문제없음**. `tools/resume_c1_after_reboot.py`를 별도로 검토했으며 실제 학습은 시작하지 않았다.

- `--start`에서만 학습을 시작한다. 원래 감독기의 lock과 별도 복구 lock을 함께 획득하고, 기존 attempt02·복구 상태가 있으면 덮어쓰지 않는다. `/proc`의 명령·실행 경로와 GPU compute 프로세스를 검사하므로 PID 값만으로 이전 프로세스가 살아 있다고 판단하지 않는다.
- checkpoint250의 고정 SHA, 원래 manifest, 원본 strict reader·C1 clock, 커리큘럼과 구간/전곡 확정 노출을 대조한 뒤 원래 snapshot의 실행 명령에 추가1750회를 전달한다. 원래 runtime·감독기·분석기 파일은 수정하지 않는다.
- 확정 prefix의 실제1~250회 로그를 CPU로 읽어250개·8,192,000전이임을 재확인했다. attempt01의251회 이상 제외, 중복 업데이트와 잘못된 전역 update_index 거부도 별도 가짜 행으로 확인했다. 추가1750회는57,344,000전이이며 합계는2,000회·65,536,000전이다.
- 완료 분석은 확정 metrics가 참조한 `(update_index, episode_id)`만 읽고 누락·중복을 거부한다. 기존 분석기의 목표별·전곡 평가를 그대로 호출하며 합계 분모를 다시 검사한다. 기존 initial/1000/final 평가와 선정 모델 영상 순서를 유지한다.
- 기존 `old.execute()`의 원본 봉인·저장공간·진행 정체 감시를 사용하며, 복구 감독기 자체 SHA도 완료 시 확인한다. 학습·후처리 실패는 완료로 표시하지 않고 예외를 기록한다. 추가 장애를 임의로 다시 재개하는 기능은 없다.

이 검수는 코드와 현재 원본 prefix 및 기존 `reboot_cpu_check.json` 기록의 대조다. 실제 GPU 재개·평가·영상 완료는 아직 검증하지 않았다.

정리 전후 동등성의 별도 근거는 `equivalence.json`과 `tools/compare_v5_core.py`, `tools/compare_shared_policies.py`에 있다. 기록의144,609는 컨테이너·텐서 등을 포함한 **중첩 비교 항목 호출 수**이며 물리 샘플 수나 스칼라 원소 수를 의미하지 않는다.
