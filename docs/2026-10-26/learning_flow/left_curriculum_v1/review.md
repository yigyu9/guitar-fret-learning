# 독립 변경 검수

요약 판정: **문제없음**

Critical / Warning / Suggestion: 현재 검수 범위에서 미해결 사항 없음.

## 검수 범위

2026-10-20 현재의 왼손 성능 기반 단계 변경과 관련 회귀 검사, 상위 `learning_flow/README.md` 및 이 결과 디렉토리의 `README.md`를 실제 구현과 비교했다. 기존의 다른 작업 변경은 검수 대상에 포함하지 않았다. 검수자는 production 파일을 수정하거나 native 학습·무거운 테스트를 새로 실행하지 않았다. 이 파일만 검수 기록으로 작성했다.

- `song/left_curriculum.py`: 최근 8회 완료 이력, 실패의 0점 반영, 최소 4회·안전/도달/접촉 기준, 새 안전 전곡이 있는 업데이트의 최대 0.1 진행, 27개 상태의 의미 검증과 선형 보간.
- `song/wrist_guide.py`, `song/left_environment.py`: manifest로 확인한 anchor만 사용한 기타 좌표계 손목 가이드, 실제 240Hz 표본쌍의 도달/clean 접촉 적분, 512개 관측, 실패 tick의 양성 보상 억제, 공유 감점·비용 및 원곡 성공 판정 유지.
- `song/curriculum_runtime.py`, `training/launch.py`, `runner.py`, `parallel.py`: 부모 집계, rollout 동안 고정된 비중, PPO 이후 worker 관측 재동기화, 에피소드 reset 없는 단계 적용, 정책 buffer의 float64 상태 저장/복원, 복원 검증 후 broadcast, 오른손 기존 500상태 분기.
- 새 단위 검사 및 `tests/test_training_runner_logging.py`의 실패 주입 회귀: 상태·시간·비중·저장/복원·IPC와 실패 회계의 검증 내용 확인.

## 지적 사항의 해결

초기 검수에서 `training/runner.py`가 PPO 갱신 성공과 journal commit 사이에 실패 가능한 curriculum worker 통신을 수행하는 문제를 지적했다. 이 순서에서는 통신 실패 시 이미 모델 갱신에 사용한 전이를 discarded로 기록하면서 갱신된 optimizer/count를 복구 checkpoint에 저장할 수 있었다.

현재 `runner.py:260` 이후 순서는 **PPO 갱신 성공 → journal commit → curriculum 집계/worker 동기화**다. 해당 문제는 해결됐다. `tests/test_training_runner_logging.py:117`의 회귀는 실제 runner 제어 흐름과 journal을 사용하고 trainer/pool/coordinator를 대역으로 바꿔 통신 `TimeoutError`를 주입한다. 다음을 명시적으로 검사한다.

- committed 전이 2, discarded 전이 0.
- optimizer 업데이트 1, committed 업데이트 1.
- 후속 기록이 완료되지 않은 recorded 업데이트 0.
- 복구 checkpoint의 optimizer 업데이트 1.

`failure_injection_tests.log`에서 이 검사를 포함한 3개 검사의 `OK`를 확인했다. 이 실패 검사는 실제 native 통신이나 실제 tensor optimizer 복구를 실행한 검사는 아니다. 실제 PPO checkpoint 상태의 별도 검증은 `test_left_curriculum_runtime.py`가 담당한다.

## 직접 확인한 근거와 한계

- `source_manifest.json`의 활성 Python 파일 **404개 SHA를 다시 계산해 모두 일치**함을 확인했다.
- 모듈별 원시 로그를 직접 읽은 시점에는 **108개 모듈 / 612개 검사**에서 `Ran … tests?`와 최종 `OK`를 확인했다. 당시 2개 로그는 실행 중이었으며 전체 126개 모듈 검사는 아직 완료되지 않았다. 이 수치는 최종 전체 검사 결과가 아니다.
- 문서의 단계 비중, 진행 기준, 512/500상태 구분, 준비/곡 시간축 유지, 원곡 clean 성공과 보조 성공의 구분, strict resume 범위를 구현과 대조했다. 검증 진행 중인 문서는 완료·수렴을 주장하지 않는다.
- 진행 중인 native 실행, 새 모델 재개, 최종 전체 검사와 보존 감사의 완료 여부는 이 기록에서 판정하지 않았다. 최종 결과는 완료 후 실제 결과 파일로 별도 확인해야 한다.

이번 변경으로 기존 단일 프로세스 전체 검사에서 보고된 JSON/float SIGFPE 원인이 해결됐다고 판단하지 않는다. 단기 물리 실행이나 보조 보상 증가를 전곡 연주 학습 수렴으로 판단하지 않는다.

## 추가 확인: 완료된 단기 native 실행

이후 완료된 세 실행의 원시 `report.json`, `training_contract.json`, `song_report.json`, `persistent_audit.json`, `inputs_before.json`과 gzip 전이 전체를 직접 읽었다. 이 추가 확인 시점에도 `source_manifest.json`의 404개 SHA는 모두 현재 파일과 일치했다.

| 실행 | 직접 확인한 결과 |
| --- | --- |
| `native_left` | 2환경, 512전이, PPO 2회, 512상태. 환경별 256tick의 마지막 곡 시계 4.2666667초. |
| `native_resume` | 2환경, 40전이, 누적 PPO 3회, 512상태. 새 에피소드 첫 tick 1/60초, 마지막 20/60초. |
| `native_right` | 1환경, 20전이, PPO 1회, 기존 500상태. |

세 실행 모두 `report.completed=true`, 입력 변경·import pin 누락·과거 원문 불일치·금지 호출·worker 실패·물리 flag 오류 목록이 비어 있었다. persistent 감사도 모두 `completed=true`, `errors=[]`였다. 각 실행에서 봉인한 입력 548/549/548개의 현재 SHA를 재계산해 변경이 없음을 확인했다.

각 gzip 로그의 모든 tick에서 episode index 0, 순차 control tick, `(tick+1)/60`의 실제 곡 시계를 확인했다. 왼손의 PPO 경계 128→129tick은 2.1333333→2.15초로 이어져 reset이 없었다. 실제 적용된 왼손 `song_left_contact` 보상의 전이 합은 0.07875로 양수였다.

세 실행 모두 완료 에피소드·안전 전곡·전곡 음악 성공은 0회이며, 왼손 진행도와 최근 완료 이력은 0이었다. 따라서 이 추가 검수는 native에서 새 관측·보상이 작동하고 짧은 수집/PPO/저장이 수행됐다는 근거다. native 단계 진급이나 전곡 학습 수렴의 근거가 아니다. 실제 저장 tensor·optimizer·난수 payload 전체의 resume 동등성은 이 추가 확인에서 비교하지 않았다.

전체 126개 모듈 검사와 최종 `verification.json`의 완료 판정은 이 추가 기록에도 포함하지 않았다.
