# Persistent reset 독립 사전 검수

판정: **문제없음 — 제한된 native 연결·반복 reset 검증 진행 가능.**

검수 시점에는 신규 native 실행 전이다. 이 판정은 구현과 CPU 증거에 대한 사전 검수이며, 반복 reset의 물리적 동등성이나 장기 학습 성능의 인증은 아니다. 검수자는 물리·학습·전체 검사를 추가 실행하지 않았고, 이 문서만 작성했다.

## 검수 범위와 확인 내용

- 새 persistent session/environment/pool/entry 및 lifecycle audit와 해당 검사, 호출되는 기존 prepared reset·finite controller·guard 경로를 확인했다. 기존 실행 중인 학습의 코드나 원자료는 수정하지 않았다.
- reset에서 human DOF 위치·속도와 기타 body 상태 및 target을 복원한다. 인체 articulated rigid-body setter를 다시 사용하지 않는다. 초기화 권한은 기존 `_restore_once`의 `finally`로 복구하며, 일반 step의 state write 금지는 기존 guard가 유지한다.
- Scene, Controller, FK와 anchor/reference는 유지하고 episode별 target/history와 policy/reward/measurement 상태를 초기화한다. scene의 실제 episode step은 0부터 진행하고 기존 mature feedback phase view는 그대로 유지한다. scene 생성과 asset load는 반복 reset 경로에 없다.
- 첫 entry-close만 억제하며 reset 실패·구성 변경·닫힌 session 재사용·진행 중 physics 상태는 실제 close 또는 거부로 끝난다. factory 및 Pool binding은 예외에서도 복원한다.
- 종료 감사는 worker별 reset 및 lifecycle의 native identity, create/env/load/destroy 횟수, guard, reset clock/history, readback과 state write 수를 확인한다. 최종 state write 총계와 마지막 reset 기록의 일치도 검사한다. 감사 누락이나 실패는 canonical `report.json`의 완료 판정에 반영되며 원 runner report는 `core_report.json`으로 보존된다. 기존 출력 폴더를 대상으로 실패한 재실행은 기존 report를 재감사하거나 수정하지 않는다.

## 검수 중 발견 후 수정 확인

1. Human effort 초기화 배열을 명시적 float32로 맞췄고 검사에서 dtype을 확인한다. 원 guard는 배열을 자동으로 float32 변환하지 않으므로 이 수정은 native 호출 계약에 필요했다.
2. Lifecycle 파일 저장 실패가 원 runner의 완료 판정에 반영되지 않던 경로에 종료 감사와 회귀 검사가 추가됐다. 원 예외는 보존하고, 정상 core 결과에 대한 감사 실패는 실패로 승격한다.
3. 마지막 reset 이후 state setter 호출 누락을 잡도록 최종 누적 계수 검사가 추가됐고 asset load의 양수 증거도 확인한다.

남은 Critical/Warning 발견: 없음.

## 증거와 후속 검증 범위

- `cpu_tests_v1.log`: 수정 전 전체 142개, 67.207초, OK.
- `cpu_review_fixes_v1.log`: 관련 12개, 0.059초, OK.
- **`cpu_tests_v2.log`: 최종 전체 146개, 67.278초, OK.** 로그를 확인했으며 검수자가 중복 실행하지 않았다.
- Module binding patch는 별도 CLI parent/worker 프로세스 사용을 전제로 한다. `train_persistent`의 Pool patch는 core 실행 전체 동안 유지되므로 같은 프로세스의 임의 동시 Pool/native construction용 embedding API로 해석하지 않는다.
- `status.json`은 원 core 단계 상태이고, lifecycle 감사까지 반영한 최종 판정은 `report.json`이다.
- 저장한 articulated state를 복원해도 숨은 PhysX solver/contact cache까지 이전 초기값으로 복원했다는 주장은 하지 않는다. 실제 fresh/persistent 비교와 여러 episode reset에서 접촉·기타 편차·관절 상태·lifecycle 계수를 확인해야 한다. 현재 사전 검수만으로 reset 물리 동등성이나 음악 학습 성과를 주장할 수 없다.

## 검수한 소스 SHA-256

| 파일 | SHA-256 |
| --- | --- |
| `guitar_learning/persistent_session.py` | `b7a4d4860985376477a7c0d10efdb62c7508bfe39095e44bd6ad24a0f329b705` |
| `guitar_learning/persistent_environment.py` | `533d52333a822604155228998392229bd0f878b8191b50f768585e9320374e55` |
| `guitar_learning/persistent_parallel.py` | `717849e889635a3b39f00bcb8cd03d610f528afb315666dd1f6edc8510c6e7ef` |
| `guitar_learning/persistent_audit.py` | `c9cd72ec1dac6d541f49b8bb3f22f2c45158766038029b033334d2f724c1a0ec` |
| `guitar_learning/train_persistent.py` | `5c7d06bf540fd4acbb44299b7de419b462e7c6a823f25f14b4dbab29381f3c04` |
