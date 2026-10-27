# 손별 전문정책 구조 검수

상태: 최종 코드·CPU·제한 native 실행·문서 검수 완료. 검수자는 구현 소스와 실행 원자료를 수정하지 않았다.

## 요약 판정

**문제없음.** 검수 범위에서 미해결 정확성·품질·보안 문제를 발견하지 않았다. 실제 손별 연주 기능 성공은 0회이며, 아래 검증은 역할 분리·전달·실행·저장과 안정성 회귀 확인이다.

## Critical

없음. 초기 Pool 부분 적용 객체의 상속 불가 문제는 구현자가 `train_specialists.py:80`의 `ConfiguredPool` 클래스로 수정했다. 실제 상속 정의와 예외 후 바인딩 복원을 검사하는 회귀 테스트가 통과했다.

## Warning

없음. 아래 성공 정의와 검증 한계를 문서에 명시한 것을 확인했다.

## Suggestion

없음.

## 코드 확인 근거

- `specialist_policy.py:68`: 비학습 Actor encoder/head는 optimizer 대상에서 제외된다. 활성 채널만 탐색·log probability·entropy에 참여한다. 비활성 std는 상수이며 동결 Actor 출력은 PPO 갱신 동안 같아 기존 39D analytic KL의 비활성 항은 0이다.
- `specialist_policy.py:136`: 전체 encoder/head와 해당 std를 전달한다. 계약·shape·dtype·유한성 확인 뒤 변경하며, 새 Critic/optimizer를 사용하는 warm-start와 기존 엄격한 resume를 구분한다.
- `specialist_environment.py:224`: 기존 환경의 실제 240 Hz 접촉·기하·안정성 비용과 실패 종료를 계속 사용한다. 기존 통합 음악 이력을 조작하지 않으며, 실패 tick의 양수 손별 보상과 단계 성공을 무효화한다.
- `specialist_settings.py:38`: 손별 실행에서 유한한 양의 안정성 비용 가중치를 요구한다.
- `train_specialists.py:58`: expert checkpoint를 기존 입력 SHA 감사에 추가한다. CLI 바인딩은 context manager 종료 시 복원한다. worker의 compact 교체는 독립 spawn 프로세스 내부다.

## 별도 CPU 확인

- 검수자가 policy/environment/runner의 specialist 검사 22개를 별도로 실행해 모두 통과했다.
- 최종 비용 가중치 검사가 추가된 뒤 runner 검사 5개를 다시 별도로 실행해 모두 통과했다.
- 구현자가 기록한 전체 CPU 168개 검사 로그와 최종 runner 5개 검사 로그의 성공 종료도 확인했다. 합성 접촉·기하 fixture 검사는 native 성공 증거와 구분했다.

## Native 원자료 독립 대조

검수자는 `analyze_native.py`를 다시 호출해 결론을 받아들이는 대신, 별도 읽기 전용 코드로 각 `report.json`, `transitions.jsonl.gz`, `rollout_first.pt`, `initial.pt`, `final.pt`, `persistent_audit.json`을 직접 대조했다.

| 실행 | 전이 | 완료 episode | 단계 성공 | 물리 실패 | 초기→최종 PPO 업데이트 |
| --- | ---: | ---: | ---: | ---: | ---: |
| left | 88 | 1 | 0 | 0 | 0→1 |
| right | 88 | 1 | 0 | 0 | 0→1 |
| right_with_left | 88 | 1 | 0 | 0 | 0→1 |
| joint, 2 workers | 176 | 2 | 0 | 0 | 0→1 |
| left_resume | 4 | 0 | 0 | 0 | 1→2 |
| 합계 | 444 | 5 | 0 | 0 | 5회 업데이트 |

- 전이 수와 H×N, 실제 로그 행동과 rollout latent의 tanh 출력이 일치했다. 정책 물리 표본은 444×4=1,776개이며 준비 표본은 별도다.
- 모든 실행에서 최종 모델이 유한하고 PPO KL 한계 이내였다. 원 실행 보고서의 입력·모델 parity·guard·물리 flag·worker·정리 오류가 비어 있었다.
- 단독 실행의 반대 손 행동은 정확히 0이었다. 모든 단일 손 실행에서 반대 Actor encoder/head와 해당 std가 업데이트 전후 정확히 동일했다.
- 적응/joint 초기 모델의 양손 encoder/head와 std가 각각 원 specialist의 최종 checkpoint와 정확히 동일했다.
- `right_with_left` 전체 88개 rollout 관측을 원 왼손 모델과 적응 후 모델에 직접 넣어 결정적 왼손 출력이 정확히 같은 것을 확인했다.
- `left_resume`의 초기 model·두 optimizer·identity·cost weight·업데이트 수·Python/NumPy/Torch/CUDA RNG를 source 최종 checkpoint와 재귀 비교해 정확히 같은 것을 확인했다.
- 각 worker의 persistent lifecycle에 create_sim/create_env/destroy_sim 각 1회, load_asset 2회, guard 위반 0, 최종 close가 기록돼 있었다.
- 60 Hz 말단 444개 표본에서 전체 지지와 양발 접촉이 모두 관측됐고 모든 tick의 실패 사유 합집합은 비어 있었다. 삼중 지지의 지속 100%나 전체 240 Hz 원자료 보존을 주장하지 않는다.

## 보존과 문서 범위

- 실행 소스 manifest의 현재 파일·보관본 69개 SHA가 모두 일치했다. 이전 버전 보관 manifest 68개도 온전했고, 그중 이전 Python 60개 원 경로가 보관 SHA와 동일했다.
- 결과 README와 `guitar_learning/SPECIALIST_TRAINING.md`는 왼손 성공을 `[press,end]` 내 기본 50 ms 연속 접촉 후보로 명시한다. onset/end까지 유지·해제 완수를 뜻하지 않는다. joint 성공도 타현 시점의 접촉 조건을 포함한 strict 매칭이며 전체 음 유지·해제 인증과 구분한다.
- 결합 입력 checkpoint는 기능 성공이 없는 1업데이트 fixture임을 명시했다. 실제 압력·음향·Root 자유 균형·105축 신경망 학습·장기 수렴·기능을 학습한 전문가의 결합 성능을 주장하지 않는다. 기존 `validate.py`가 새 specialist 모델을 지원하지 않는다는 제한도 명시했다.
- 최종 전체 산출물 봉인 `final_verification.json`은 구현 담당자가 이 검수 이후 작성한다.
