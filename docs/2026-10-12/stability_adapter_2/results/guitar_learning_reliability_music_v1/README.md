# 장기 학습 중단·음악 목표 발견 개선 결과

메모리 감시·진행 출력·실패 복구를 구현하고 실제 중단과 재개를 검증했다. 음악 목표를 발견하도록 돕는 별도 `dense_v2` 보상을 추가했고, 서로 다른 단음을 선택했을 때 발생한 관측 정규화 불일치도 수정했다. **연주 성공이나 실제 목표 접근 개선은 아직 확인되지 않았다.** 이번 개선에서는 새 8시간 학습을 시작하지 않았다.

## 무엇이 문제였나

[이전 실행 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_16env_analysis_v1/README.md)에서 host global OOM과 별도 rg 프로세스의 약 7.86GiB RSS/OOM kill, worker0 IPC timeout을 확인했다. 학습 worker의 직접 OOM kill이나 학습 단독 무한 누수는 확정하지 않았다. 14업데이트 후 15번째 수집이 중단됐지만 종료 이유가 `updates_complete`로 남았고, 실패 저장이 없어 10업데이트 모델만 남았다. 완료 320에피소드에서 음악 매칭·목표 유지 0, 물리 실패 0이고 KL도 상한 이내였으므로 PPO 발산을 원인으로 판단하지 않았다.

기존 압현음 접근 보상은 압현 준비부터 타현까지 약 120ms에만 있었고, 오른손의 목표 현·시각·방향 접근 신호는 없었다. 이것을 유일한 정체 원인으로 확정하지 않고, 확인 가능한 보상 공백을 보완했다. 망 크기·PPO 수치·행동 범위·gain·초기 자세·충돌·안정성 한계·원 음악 성공 판정은 유지했다.

## 바꾼 내용

| 부분 | 변경 |
| --- | --- |
| RAM | 기본 8환경×256=2048 batch, MemAvailable 4GiB 보호, 5초마다 현재 RSS/PSS와 peak 기록 |
| 진행 | 10초 heartbeat: phase/update/tick/RAM/대기 worker, atomic status.json, 즉시 flush하는 events/resources JSONL |
| IPC | 0.5초 poll, 준비된 응답부터 수신하되 반환 순서는 유지. worker PID/exitcode 즉시 진단, 살아 있는 무응답은 300초 timeout |
| 복구 | 검증된 trainer만 failure_last_valid.pt 저장, 부분 rollout 폐기, 정확한 종료 이유·부분 전이 수·종료 진단. 정기 저장은 5업데이트마다 |
| 음악 신호 | 실제 240Hz·움직이는 기타 기준으로 왼손 초기 접근과 오른손 목표 현·깊이·시각·방향 가이드 보상 추가 |
| 목표 선택 | 기본 첫 음 고정 유지. 선택형 B 단음 pool의 균형 cycle, 공통 관측 계약, 실제 에피소드 목표 별도 보존 |

정책 출력 39축, 상태 관측 468, 이벤트 64×24, 우선 토큰 2×24, medium 망 1,931,600 parameters다. 하체는 외부 유한 유지 제어를 사용한다. Root 고정, 105입력/97비영범위/8영범위 구분, 자유 기타·중력 ON·스트랩 OFF·준비 2초를 유지한다. 새 보상·pool은 별도 계약으로 새 정책을 사용한다. 기존 legacy 고정 목표의 계약은 유지해 원 체크포인트를 실제로 재개했다.

## 실제 검증

최종 **CPU 127개 통과, 41.590초**. [최종 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reliability_music_v1/cpu_tests_pool_v2.log). 최초 개정과 거리 범위 개정의 126개 검사도 각각 통과했다. 검사 수를 중복 합산하지 않는다.

| 실제 실행 | 전이 | 업데이트 | 결과 |
| --- | ---: | ---: | --- |
| 기존 10업데이트 모델 → 수집 중 SIGINT |32, 미반영 |0 |interrupted, 유효 복구 저장 |
| 위 복구 모델 strict 재개 |8 |1 |정상 종료, 누적 10→11업데이트 |
| 가짜 저메모리 관측 주입 |5, 미반영 |0 |memory_guard, 유효 복구 저장 |
| N8/H256, 우손 거리 범위 20mm |4096 |2 |정상 종료, 40에피소드 |
| N8/H256, 우손 거리 범위 50mm |4096 |2 |정상 종료, 40에피소드 |
| 첫 N2 단음 pool |0 |0 |initial reset 계약 불일치, 원 실패 보존 |
| 수정 후 N2/H512 단음 pool |1024 |1 |정상 종료, 10에피소드·다섯 단음 모두 선택 |

총 로그 9261전이, 최적화에 반영한 전이 9224개/업데이트 6회다. 서로 다른 정책·계약의 짧은 실행을 합산한 수치이며, 한 모델의 연속 6업데이트가 아니다. 두 예정 중단과 첫 pool 실패를 정상 학습 완료로 집계하지 않았다. 37개 부분 수집 전이는 폐기했다.

중단 직전 모델과 복구 파일의 가중치·actor/value optimizer가 동일했고, 재개 직후에도 가중치·optimizer·저장 RNG가 정확히 일치했다. 복구 모델의 updates=10이 새 업데이트 후 11이 됐다. 저메모리 시험은 실제 host 압박을 만들지 않고 관측만 3GiB로 바꿨다. 그 3GiB는 실제 RAM 측정치가 아니다. OS SIGKILL·전원 차단 시 저장을 보장하는 검증도 아니다.

50mm N8 실행의 최소 실측 MemAvailable은 **18.470GiB**, 수집 속도는 16.413전이/초였다. 자식들의 현재 RSS 합 표본 최대는 5.614GiB, 현재 PSS 합 표본 최대는 4.021GiB였다. RSS 합은 공유 페이지를 중복 계산하며 두 값 모두 5초 표본이다. 실제 장기 누수 부재를 입증한 값은 아니다.

## 음악 신호를 어떻게 보완했나

왼손은 task 시작부터 press 전까지 `0.2 × exp(-(거리/30mm)^2)`를 초당 보상으로 추가했다. 말단 body 원점과 프렛 목표의 거리이며 실제 pad 간격·압력과 다르다. 기존 press~onset 접근 보상은 유지한다.

오른손은 현재 기타 좌표계의 유한한 목표 현, y=-0.32m, 현 아래 8mm를 지나는 가이드를 쓴다. onset 전후 80ms에 올바른 현 법선 방향으로 ±6mm 이동하고, 그 전에는 진입점을 제시한다. 거리 보상은 최대 초당 0.2, 올바른 방향 이동 추가 보상은 최대 초당 0.1이다. 제어 명령이나 기타 상태를 강제로 변경하지 않는다.

첫 실측에서 거리가 49.7397mm일 때 20mm Gaussian 범위의 우손 보상은 0.00000687128/tick으로, 왼손의 0.00222790/tick보다 매우 작았다. 원형을 보존한 후 거리 범위만 50mm로 넓혔다. 같은 초기 행동·같은 거리의 우손 보상이 0.00123921/tick으로 **180.35배** 커졌다. 최대 보상·경로·판정은 그대로다. 이는 보상 신호 증가이며 학습 성능 증가 배수가 아니다. 근접 위치·시간 분별력은 약해지는 절충이 있어 초기 도달 탐색용으로 해석한다.

20mm/50mm 실행의 평균 우손 거리 proxy는 각각 50.449/50.453mm, 실제 매칭·목표음 유지는 모두 0이었다. 에피소드 반환값 평균은 -0.36113→-0.27449지만 보상 정의가 달라진 결과이므로 성능 개선으로 해석하지 않는다. 두 실행의 평균 에피소드 비용은 0.002874/0.002823, 안정성 실패는 0이었다. 60Hz 끝점에서 양발 접촉과 최소 한 곳의 주요 지지는 모두 100%였다. 전체 240Hz 접촉 연속 100%를 주장하는 수치는 아니다.

Pool도 완료 10에피소드의 매칭·목표음 유지는 0이었다. 60Hz 접촉 후보가 1틱 있었지만 목표 발음 구간의 유지 성공은 아니다. event0~4가 두 worker에서 각각 한 cycle씩 모두 선택돼 에피소드가 끝났고, 다음 cycle에 진입했다. 종류는 2현7프렛/2현5프렛/3현7프렛/3현6프렛/3현4프렛이다. 기본 권장은 첫 음 고정이며 pool은 선택 옵션이다.

## 실제 시험과 검수에서 더 고친 경계

- terminal step 뒤 reset 실패 시 완료 전이 수가 한 틱 누락되던 문제: reset 전에 step 완료 진행을 반영하고 guard/timeout 회귀 검사를 추가했다.
- strict resume 실패 후 무작위·미검증 모델이 복구 파일로 저장되던 문제: load 성공 또는 fresh 초기화 완료 후에만 복구 저장 자격을 부여했다.
- 첫 pool의 개별 음 길이에 따른 시간 관측 scale 불일치: 실제 builder의 remaining/held_total/elapsed를 pool 최대 음 길이로 고정하고 spec/contract와 reset 반환 관측을 함께 재생성했다. 개별 종료 시각과 이벤트 토큰은 유지한다. FakeEnvironment만 검사하던 부분을 실제 RecordedSession+Training/Dense/ObservationBuilder 검사로 바꾸고 native 재시도에 성공했다.

## 코드·설정·근거

[현재 실행법과 복구](/home/ajou/yigyu/3/guitar_learning/PARALLEL_TRAINING.md) · [새 시작 권장 설정](/home/ajou/yigyu/3/guitar_learning/configs/long_B_8env_dense_v2.json) · [기존 모델 재개 설정](/home/ajou/yigyu/3/guitar_learning/configs/long_B_8env_safe_v1.json) · [선택 pool 설정](/home/ajou/yigyu/3/guitar_learning/configs/long_B_8env_pool_v2.json).

[실제 결과 집계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reliability_music_v1/native_summary_v1.json) · [입력·보존 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reliability_music_v1/preservation_check_v1.json) · [입력 버전 union](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reliability_music_v1/inputs_union_v1.json).

[사전 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reliability_music_v1/review_preflight.md) · [거리 범위 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reliability_music_v1/review_scale_v2.md) · [pool 정규화 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reliability_music_v1/review_pool_v2.md).

원본 52파일, 거리 범위 개정 전 3파일, pool 개정 전 3파일은 guitar_learning/archive의 날짜별 디렉토리에 보존했다. 실행 전 source_run_v1/v2/v3 및 중간 수정 전 보관본 총 282개 copy의 SHA가 일치했다. 실제 입력 1585경로/1588 SHA버전, 원 XML과 선언 mesh 106파일이 닫혔다. 코드 3경로의 소비 버전 차이를 보존본으로 구분했으며 이전 실행을 사후 수정하지 않았다. Reset 감사 113개, 첫 틱 원자료 111개/실제 240Hz 표본 444개를 확인했다. 나머지는 60Hz compact 로그이며 전체 240Hz 원자료를 저장했다고 설명하지 않는다.

남은 연구 검증은 실제 손가락 pad 접촉과 타현 도달성, 충분한 학습에서 거리·방향·접촉 유지·음악 성공의 개선, 더 긴 메모리 추적, 다중 이벤트·전체 곡이다. 실제 현 압력·진동·음향과 Root 자유 균형은 이번 검증 범위 밖이다.

[최종 독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_reliability_music_v1/review.md)는 문제없음 판정이다. 음악 성과와 장기 메모리 안전성을 인증한 판정은 아니다.
