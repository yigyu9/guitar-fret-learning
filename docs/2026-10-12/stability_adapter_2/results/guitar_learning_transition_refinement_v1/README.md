# 단음 학습 보완 구현과 검증

사용자가 승인한 준비 보상·성공 기준·탐색·성공자료 재사용 개선을 새 경로에 구현했다. **CPU 검사43개는 통과했다. 실제 native 실행2회는 SIGFPE로 중단되어 새 초기 정책 성공 평가와 PPO 연결 검증은 미완료다.** 새 학습 성과나 전환 성공을 확인한 결과가 아니다.

## 구현한 것

| 내용 | 새 코드 | 동작 |
|---|---|---|
| 준비·유지·해제 보상 | `guitar_learning/transition_refinement/reward.py`, `environment.py` | press_s=0인 첫2초에도 접근 보상. 단음 성공 보너스는 평가와 같은90% 실제 clean 유지 기준. 기존40% 보너스 제거. |
| 작은 탐색량 | `policy.py`, `settings.py` | 실제 초기std0.003·하한0.0001 적용. 기존exp(-5) 하한과±0.0002 평균 제한을 상속하지 않음. |
| PPO와 성공 행동 보존 | `ppo.py` | Actor PPO 손실에 새 native 성공 행동의 BC MSE 추가. log_std 별도 학습률. 기존 KL·Adam·RNG 원자적 복원과 strict resume 유지. |
| 실행·증거·재검증 | `run.py`, `worker.py`, `evidence.py`, `capture.py` | 원 BC 증거를 검증한 뒤 Actor만 이전. 새 계약의 독립4회 성공을 요구하며 원 native 관측·물리 검사와 새 보상 재계산을 모두 수행. |
| 탐색량 비교 | `sweep.py` | 같은 BC·seed 집합으로 잡음 없는 평가와 여러 std 비교. 음악 실패·물리 실패·수치 오류를 분리. 설정·모델·소스 변경 검사. |

코드 설명·실행 명령은 [새 패키지 안내](/home/ajou/yigyu/3/guitar_learning/transition_refinement/README.md)에 있다. 예시 BC 가중치100·Actor LR1e-7·std LR1e-5는 시작 설정이며 최적값이나 학습 개선을 검증한 값이 아니다. 새 정책·학습기는 현재 왼손 단계 전용이다. Pair 보너스는 원래40%·최소50ms 기준을 보존하며 단음90%와 구분한다.

Root고정·하체유한제어·105/97/8·자유 기타·중력ON·strapOFF·원 gain/제한/속도/안전 종료는 유지했다. 기타 직접 보조 힘·강제 부착·매step 상태 덮어쓰기는 추가하지 않았다. 기존500상태의 SongLedger 이력은 BC 호환을 위해 유지하며, 그40% 진행 marker는 현재 성공 판정이 아니다.

## 완료한 검증

- 새 보상12+학습9+연결7+탐색 비교9+기존 공용PPO6=43개 검사 통과. `rl38` CPU 전용 환경이며 `CUDA_VISIBLE_DEVICES=''`로 실행했다. 예외 억제나 FPU 마스크 변경은 하지 않았다. [로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_v1/cpu_verification_v1/transition_refinement_43_cpu_isolation_v1.log), [실행 조건](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_v1/cpu_verification_result_v1.json).
- 별도 change-reviewer가 보상·학습·이전·증거·spawn·탐색 비교를 검수했다. 미해결 코드 지적0개, 원본33개 및 동결53파일 SHA 일치. 독립 핵심21검사도 통과했다. [검수 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_v1/independent_review_v1.json).
- 과거 checkpoint20 실패의 실제 접촉 기록을 새 보상으로 재계산했다. 압현 유지81.6667%에서 과거 성공 보너스1은 새 보상0으로 바뀌고, 첫2초 접근 진전 보상은 발생했다. 이는 기존 기록의 오프라인 검증이며 새 정책 성과가 아니다. [재계산](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_v1/old_checkpoint20_reward_replay_v1.json).
- 중단된 새 native trace의 완전한311개 행·1244개240Hz 표본에서 신규 보상 항목과 실제 reward 조합을 독립 재계산해 일치했다. 잘린 원자료는 복구·변경하지 않았다. 전체 capture 감사나 성공 gate를 대신하지 않는다. [부분 재계산](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_v1/partial_native_reward_replay_v1.json).

## 실제 실행의 한계와 남은 것

| 실행 | 마지막 완전 기록 | 상태 |
|---|---|---|
| native_init_v1 | 213정책행, task3.55초 | Python float formatter에서SIGFPE, 종료136. 전체 성공 증거 아님. |
| native_init_v2 | 98정책행, task1.633333초 | 같은 함수에서SIGFPE, 종료136. 전체 성공 증거 아님. |

두 실행 모두 동일한 동결 코드·설정을 사용했다. `format_float_short`의 `fldcw`에서 `FPE_FLTRES`를 관찰했다. 근본 원인은 미확정이다. 첫 실행에서 보였던 부분 유지율100%를 완료 성공으로 집계하지 않았다. `native_init_v1.log`, `native_init_v2.log`에 GDB 최초 오류 상태를 남겼으며 같은 오류 뒤 계속 실행하지 않았다. 초기 통합 CPU 검사의 SIGFPE 실패 기록도 보존했다. 이후 CPU43개 통과가 native/CUDA 오류의 해결을 뜻하지 않는다.

새 성공 gate는0개다. 새 PPO를 시작하지 않았으며 새 checkpoint나 학습 개선 결과는 없다. 이번 작업에서 실행한 프로세스는 모두 종료됐다.

다음 순서로 이어간다.

1. 간헐적 float formatter SIGFPE의 원인을 규명한다. 실패를 숨기거나 원자료 검사를 생략하지 않는다.
2. 새 경로에서 독립4회 완주 및 `transition_refinement.capture.audit_capture`를 통과한다. 기존 두 중단 실행과 과거 보상 계약의 성공은 gate로 사용하지 않는다.
3. 통과한4개 실제 case 경로를 넣은 **새 버전의 학습 설정**을 만든다. 동결된 `configs/training*.json`은 현재 `native_init_v1..v4`를 가리키는 시작 템플릿이므로 지금 그대로 PPO를 시작하면 gate 검사에서 거절되어야 한다.
4. 1환경·1업데이트와 저장 checkpoint 재로드를 확인한다.
5. 고정 BC 탐색량 비교 후 짧은 PPO로 확장한다. 성과를 확인한 뒤 장기 학습·두 음 전환으로 진행한다.

## 보존 위치

- 구현 전33파일: `guitar_learning/archive/20261019_before_transition_refinement/manifest.json`.
- 원본33개+새 코드·검사·설정·설명53파일: 이 결과 디렉토리의 `source_snapshot_v1/`, `source_pins_v1.json`. 최종 재계산에서도 불일치0개다.
- 기계 판독 요약: [implementation_result_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_v1/implementation_result_v1.json).
- 기존 transition 실행·BC·checkpoint4/8·checkpoint20 실패·중단 학습 기록은 변경하지 않았다. 이후 코드 변경도 새 버전으로 진행한다.
