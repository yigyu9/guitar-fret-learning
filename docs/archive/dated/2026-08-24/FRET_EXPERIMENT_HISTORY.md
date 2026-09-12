# Fret 학습 실험 이력

### FRET-017 — 문맥별 실패 진단과 checkpoint 평가 복원

- 시기: 2026-09-11
- 분류: METRIC / FORGETTING / TRANSITION
- 연결: FRET-012, FRET-015, FRET-016
- 기준: `20260911_0009_02_Jazz1-200-B_solo`, 32,080~33,070 기록 100행.
- 관측: 소지 rehearsal 99.62%, sequence 47.02%, 전체곡 표본 52.91%.
  sequence에서 전체곡을 뺀 짧은 구간은 약 40.55%. 분모는 목표 프레임이며
  독립 시도 수가 아니다. 복구 배정 15/15/30/40%는 정확하지만 목표 프레임 노출과 다르다.
- 문제: goal-pair의 실제 gate 실패 사유가 none으로 표시된다. 오프라인 도구는
  기본값으로 판정하고 sequence gate를 누락한다. 영상은 v2 block 모델을 일반
  ActorCritic으로 복원해 실패한 기록이 있다.
- 계획: `docs/plans/fret_diagnostics_20260911.md`.
- 성공 기준: run 설정과 실제 gate가 일치하는 진단, sequence/전체곡 분리,
  모델 구조를 보존한 평가 및 이벤트별 실패 기록. 학습 보상·승급 기준은 유지.
- 결과: CPU 회귀·별도 리뷰·실제 33,500 checkpoint의 두 시점 GPU 영상 생성 통과.
  동일 조건 재생의 이벤트 결과는 일치했다. 무보조 전체곡 F1 0.244861,
  압현 137/965프레임, sustain 2/35이벤트, 조기 종료 0. 소지 4/19프레임이며
  목표 시작 13프레임 뒤에 최초 압현했다. 엄지 지지는 48.55%였다.
- 판단: 평균 학습 F1이 무보조 전체곡 품질을 보장하지 않는다. 소지뿐 아니라
  초기화·성공 cache·행동 분포 차이를 비교해야 한다. teacher는 추가 loss이므로
  원인으로 확정하지 않는다. 보상/분포 변경과 장기 재학습은 아직 수행하지 않았다.
- 상세 결과: `docs/2026-09-11/FRET_DIAGNOSTICS_AND_EVALUATION.md`.
- 상태: 유지 — 진단·평가 보강 검증 완료. 학습 성능 개선은 후속 대조 실험 필요.

> **상태: APPEND-ONLY HISTORICAL RECORD.** 각 절의 수치와 “현재”는 해당 실험 시점 기준이다.

> 복구일: 2026-08-27
>
> 이 파일은 작업공간에서 누락된 뒤 현재 코드, run manifest, 학습 로그를 기준으로
> 복구했다. FRET-009 이전 상세 기록은 원본을 찾으면 이 문서에 다시 합친다.

## 중복 방지 표

| 실험 | 문제 | 변경 | 결과 |
|---|---|---|---|
| FRET-009 | 단일 손가락 집중 뒤 다른 손가락 망각 | 초기 단계 유지율 감시와 복구 focus | 단독 손가락 단계 통과에는 효과가 있었으나 순차 focus 망각이 통합 단계에서 재발 |
| FRET-010 | 통합 압현에서 약한 손가락을 고치면 다른 손가락이 무너짐 | 모든 손가락 최소 15%를 보장하는 적응형 다중 손가락 복구 | 구현·CPU 검사 완료. `20260825_1816`은 이전 `fine_reach`에서 막혀 장기 효과 미검증 |
| FRET-011 | 단일 focus 복구에서 매 iteration 전체 환경 reset | 샘플러 전환 멱등성, 복구 상한, evidence 고갈·reset watchdog | `20260827_1334`에서 episode 흐름과 `fine_reach` 통과 확인 |
| FRET-012 | `isolated_press`에서 약지만 엄격 성공률이 낮고 단일 focus 복구가 소진됨 | 판정 퍼널 진단, 최소 15% 보존 적응 표집, 선택적 stall 종료 | `20260828_0100`에서 표집 정확도와 약지 개선 확인. 복구 종료 뒤 약지 망각 재발 |
| FRET-013 | 약지 아치 부족과 12블록 뒤 균등 표집 복귀 | strict 경계 정렬 아치 보상, 24블록 복구, 소진 후 보존형 분포 유지 | 구현·CPU 회귀 검사 완료, fresh GPU 비교 필요 |
| FRET-014 | 높은 평균 보상이 접촉·위치·아치 중 한 조건 포기를 가림 | 기존 보상 70%와 접촉×위치×아치 결합 품질 30% 혼합, 최약 손가락 표시 | 구현·CPU 회귀 검사 완료, fresh GPU 비교 필요 |
| FRET-015 | 단일 focus가 평가 증거를 지우고 전체 환경을 반복 reset | 75/25 학습·평가 분리, 다중 손가락 가중 표집, 고정 승급 분포 | 구조 동작 확인. 두 비교 run에서 약지·소지 회복 실패 |
| FRET-016 | `frozen_context`에서 약지·소지 망각과 시간 기반 평가가 재발 | 성능 기반 복구, 순위 표집, 제한적 distal teacher, 무보조 안정화 뒤 평가 | CPU·GPU smoke 검증 완료. schema 57 장기 비교 필요 |

### FRET-010 — 적응형 다중 손가락 통합 복구

- 시기: 2026-08-25
- 분류: FORGETTING / TRANSITION / METRIC
- 문제와 관측 사실:
  - `integrated_press`에서 약한 손가락 하나에 75%를 집중하면 다른 손가락 성공률이 크게 하락했다.
- 개선 가설:
  - 모든 필요한 손가락에 최소 15%를 남기고, 나머지 표본을 성공률 부족과 최고점 대비 하락에 따라 배분한다.
- 구현:
  - `curriculum.py`: 400 iteration 적응 블록, 최대 12블록, 유지율과 최소 성공률 진단
  - `goals.py`: 비동기 reset에서도 목표 비율을 지키는 가중 손가락 표집
  - curriculum schema 51
- 검증:
  - CPU 회귀 검사 통과
  - 장기 GPU 검증 전
- 상태: 검증 전

### FRET-011 — 초기 복구 reset 무결성

- 시기: 2026-08-27
- 분류: TRANSITION / METRIC / FORGETTING
- 연결된 이전 실험: FRET-009, FRET-010
- 기준 run: `fret/training/runs/20260825_1816_02_Jazz1-200-B_solo`
- 문제와 관측 사실:
  - `coarse_reach`는 iteration 633에 통과했다.
  - `fine_reach`는 iteration 2140에 복구로 들어갔다.
  - 복구 직전 성공률은 검지 100.00%, 중지 78.54%, 약지 87.23%, 소지 100.00%였다.
  - 복구 뒤 매 iteration 1,024개 환경이 전부 다시 배정됐다.
  - 복구 전 완료 episode는 30,707개, 이후에는 8개뿐이며 모두 실패 종료였다.
  - 중지 성공률은 68개 복구 블록 동안 78.54%로 고정됐다.
- 원인 판단:
  - curriculum이 비적응 단계에서도 `set_practice_finger_weights(None)`을 먼저 호출했다.
  - 이 호출이 단일 focus를 지운 뒤 같은 focus를 다시 설정해 `changed=True`와 전체 reset을 매번 만들었다.
- 개선 가설:
  - 단일 focus와 가중치 모드를 한 경로에서만 적용하고 setter를 멱등하게 만들면 episode가 정상 완료된다.
  - 전체 복구 상한과 신규 evidence 감시를 두면 같은 종류의 오류가 장시간 계산을 낭비하지 않는다.
- 기존 시도와 다른 점:
  - 보상이나 80% 승급 기준은 바꾸지 않는다.
  - FRET-010의 통합 단계 적응 분포도 바꾸지 않는다.
- 구현:
  - 비적응 단계에서는 단일 focus setter만 호출한다.
  - 동일 설정 반복 적용은 상태를 바꾸거나 reset하지 않는다.
  - 초기 복구에 전체 블록 상한 12개를 둔다.
  - 손가락별 evidence age와 최근 episode 수를 기록한다.
  - 연속 focus reset 25회는 학습 파이프라인 오류로 중단한다.
  - 동일 focus 반복, 모드 전환, 복구 상한, evidence 고갈 회귀 검사를 추가한다.
  - 변경 파일:
    - `tab2body/learning/curriculum.py`
    - `tab2body/env/goals.py`
    - `tab2body/cfg.py`
    - `tab2body/learning/ppo.py`
    - `tab2body/tools/plot_fret_diagnostics.py`
    - `tab2body/tests/test_fret_curriculum_windows.py`
- checkpoint 호환성·재시작 위치:
  - curriculum schema를 52로 올린다.
  - schema 51 checkpoint는 진단용 로드는 가능하더라도 정식 대조 학습에는 사용하지 않는다.
  - 장기 검증은 fresh start로 수행한다.
- 사전 성공 기준:
  - 동일 focus 두 번째 적용부터 전체 reset 0회
  - 정상 복구에서 100 iteration 안에 신규 완료 episode 존재
  - 손가락별 evidence age가 연속 100 iteration 이상 증가하지 않음
  - 초기 복구 전체 블록 수가 12를 넘지 않음
  - `fine_reach` 이후 단계 진입 여부를 3,000~5,000 iteration run에서 확인
- 실제 결과:
  - Python 정적 컴파일 통과
  - `test_fret_curriculum_windows.py` 통과
  - `test_fingertip_approach_curriculum.py` 통과
  - `test_checkpoint_contract.py` 통과
  - `test_training_console.py` 통과
  - `test_goal_pair_preservation.py` 통과
  - `test_fret_precision_reward.py` 통과
  - 기존 `20260825_1816` 프로세스는 이전 코드를 메모리에 올린 상태라 결과 판정에 사용하지 않는다.
  - fresh run `20260827_1334_02_Jazz1-200-B_solo`는 schema 52로 시작했다.
  - `coarse_reach`는 586, `fine_reach`는 1765 iteration에 통과했다.
  - 손가락별 evidence는 4096 episode를 유지하고 age는 0이었다.
  - 반복 reset 없이 `isolated_press`까지 진입해 직접 목표를 만족했다.
- 상태: GPU 검증 완료

### FRET-012 — 약지 엄격 압현 진단과 보존형 초기 복구

- 시기: 2026-08-28
- 분류: METRIC / FORGETTING / PRECISION / TRANSITION
- 기준 run: `fret/training/runs/20260827_1334_02_Jazz1-200-B_solo`
- 문제와 관측 사실:
  - 14,790 iteration에도 `isolated_press`에 머물렀다.
  - 검지·중지·소지 누적 성공률은 86.8%, 90.0%, 88.1%였다.
  - 약지는 35.9%였고 승급 기준은 모든 손가락 80%다.
  - 약지 실제 압현 프레임은 89.3%, 목표 영역 내부 비율은 99.6%였다.
  - 엄격 손 모양 성공은 39.1%여서 접촉 뒤 위치·아치·유지 판정의 구분이 필요했다.
  - 초기 복구는 8,570 iteration에 12블록을 소진한 뒤에도 학습이 계속됐다.
- 기존 시도와 다른 점:
  - FRET-009의 순차 단일 focus 대신 네 손가락을 동시에 표집한다.
  - FRET-010의 보존형 적응 분포를 현재 병목인 `isolated_press`로 확장한다.
  - 80% 승급 기준, 압현 위치 범위, 엄지·안전 보상은 바꾸지 않는다.
- 구현:
  - 손가락별 접촉·위치·아치·결합 프레임 통과율을 기록한다.
  - 12프레임 연속 성공, 평가 구간 80% 유지, 최종 성공을 episode 단위로 기록한다.
  - `isolated_press` 복구에서 각 필요한 손가락의 표집 비율을 최소 15%로 보장한다.
  - 남은 표본은 80%까지의 부족분과 최고점 대비 하락량으로 배분한다.
  - 복구 소진 경고를 한 번 출력한다.
  - `--stop-on-curriculum-stall`을 지정하면 checkpoint를 저장하고 정상 종료한다.
  - 기본값은 기존처럼 계속 학습한다.
  - 진단 플롯에 약지 판정 단계와 손가락별 최종 성공률을 추가한다.
  - curriculum schema를 53으로 올린다.
- 변경 파일:
  - `tab2body/env/rewards/fret.py`
  - `tab2body/env/tasks/task_fret.py`
  - `tab2body/learning/curriculum.py`
  - `tab2body/learning/ppo.py`
  - `tab2body/cfg.py`
  - `tab2body/train_fret.py`
  - `tab2body/tools/plot_fret_diagnostics.py`
- 사전 성공 기준:
  - 약지의 접촉·위치·아치·연속·유지 실패가 각각 로그에 남음
  - 적응 복구 중 모든 필요한 손가락 표집 비율 15% 이상
  - 약지가 가장 약할 때 약지 표집 비율이 가장 높음
  - 복구 블록 사이에 evidence를 초기화하지 않음
  - 선택적 stall 종료 시 마지막 checkpoint 저장
  - fresh run에서 약지 strict episode 성공률이 상승하고 다른 손가락이 75% 이상 유지
- 검증:
  - Python 정적 컴파일 통과
  - 정밀 압현 판정·episode 집계 검사 통과
  - 커리큘럼·샘플러·checkpoint 복원 검사 통과
  - PPO 정상 종료 callback 검사 통과
  - 기존 schema 52 로그의 진단 플롯 호환성 확인
- 실제 결과:
  - fresh run `fret/training/runs/20260828_0100_02_Jazz1-200-B_solo`은 schema 53으로 실행됐다.
  - `coarse_reach`는 577, `fine_reach`는 1,441 iteration에 통과했다.
  - 적응 표집의 목표 비율과 실제 비율 오차는 반올림 수준이었다.
  - 약지 누적 성공률은 복구 시작 시 0%에서 8,000 iteration의 56.5%까지 상승했다.
  - 같은 시점 약지 아치 통과율은 75.3%, 엄격 프레임 성공률은 67.8%였다.
  - 12블록 소진 뒤 균등 표집으로 돌아가며 마지막 누적 약지 성공률은 39.5%로 하락했다.
  - 마지막 약지 판정은 접촉 71.0%, 위치 83.3%, 아치 50.0%, 결합 21.0%였다.
  - 연속 12프레임 획득률은 100%였으므로 주 병목은 시간 유지가 아니라 아치와 접촉의 동시 성립이다.
  - 엄지 지지 86.1%, 오압현 0%, 안전 종료 0%로 해당 항목은 병목이 아니다.
- 상태: GPU 검증 완료, FRET-013으로 후속

### FRET-013 — 엄격 아치 습득과 복구 후 망각 방지

- 시기: 2026-08-28
- 분류: PRECISION / FORGETTING / REWARD / TRANSITION
- 연결된 이전 실험: FRET-010, FRET-012
- 기준 run: `fret/training/runs/20260828_0100_02_Jazz1-200-B_solo`
- 문제와 관측 사실:
  - 위치·엄지·오압현이 아니라 약지 아치가 `isolated_press` 승급을 막았다.
  - 보존형 적응 표집은 효과가 있었지만 고정 12블록 종료 뒤 균등 표집으로 돌아가 효과가 유지되지 않았다.
- 변경:
  - 분리 압현 아치 보상을 25%에서 35%로 높인다.
  - 연속 아치 품질에 strict 판정 경계 0.65를 향하는 shaping을 추가한다.
  - 압현 core는 55%에서 45%가 되며 엄지 20%는 유지한다.
  - 적응 복구 상한을 12블록에서 24블록으로 늘린다.
  - 상한 소진 뒤에도 마지막 최소 15% 보존형 손가락 분포를 유지한다.
  - 손가락별 아치 품질과 MCP/PIP/DIP 각도를 로그에 추가한다.
  - curriculum schema를 54로 올린다.
- 성공 기준:
  - 약지 아치 통과율 80% 이상
  - 네 손가락 누적 엄격 성공률 모두 80% 이상
  - 접촉률 급락 없이 `integrated_press` 진입
  - 엄지 지지 75% 이상, 오압현과 안전 종료 악화 없음
- 검증:
  - Python 정적 컴파일과 diff 형식 검사 통과
  - 정밀 압현 보상, 커리큘럼 저장·복원, PPO 집계 검사 통과
  - 복구 소진 뒤 보존형 가중치 유지 검사 통과
  - Isaac Gym fret 진단 경로 검사 통과
- 상태: 구현·CPU 검증 완료, fresh GPU 비교 전

### FRET-014 — 단일 조건 우회 방지와 병목 가시화

- 시기: 2026-08-29
- 분류: REWARD / METRIC / PRECISION
- 연결된 이전 실험: FRET-012, FRET-013
- 기준 run: `fret/training/runs/20260828_0100_02_Jazz1-200-B_solo`
- 문제와 관측 사실:
  - 마지막 일반 압현 성공률은 94.6%, F1은 96.6%였지만 약지 strict 누적 성공률은 39.5%였다.
  - 접촉·위치·아치를 더한 보상에서는 한 조건을 포기하고 다른 조건으로 평균 점수를 얻을 수 있다.
  - `isolated_press`에서 네 손가락이 동시에 달성한 최고 최솟값은 64.1%로 승급 기준 80%에 못 미쳤다.
- 변경:
  - 접촉 진행도, 유효 압점 품질, strict 아치 품질의 곱을 결합 품질로 정의한다.
  - 기존 연속 보상 70%와 결합 품질 30%를 혼합해 접촉 전 기울기를 유지한다.
  - 엄지 20%와 오압현·안전 보상은 바꾸지 않는다.
  - curriculum state에 최약 손가락과 네 손가락 최소 누적 성공률을 추가한다.
  - `isolated_press` 터미널 출력에 `strict-min`과 접촉·위치·아치 중 최저 gate를 표시한다.
  - 결합 품질과 손가락별 결합 품질을 상세 로그에 기록한다.
  - curriculum schema를 55로 올린다.
- 실험 해석 주의:
  - FRET-013의 fresh GPU 검증 전에 추가되었으므로 다음 run은 FRET-013과 FRET-014의 결합 효과를 측정한다.
  - 특정 MCP/PIP/DIP 관절 보강은 새 관절별 로그를 확인하기 전까지 적용하지 않는다.
- 성공 기준:
  - 약지 strict 누적 성공률이 이전 최고 71.2%를 넘음
  - 네 손가락 최소 누적 성공률 80% 이상
  - 접촉 성공률과 엄지 지지가 각각 80%, 75% 아래로 급락하지 않음
  - `integrated_press` 진입
- 검증:
  - Python 정적 컴파일과 변경 파일 형식 검사 통과
  - 결합 품질의 단일 조건 우회 차단 검사 통과
  - curriculum 최약 손가락·최소 성공률 검사 통과
  - 터미널 strict 병목 표시 검사 통과
  - PPO·체크포인트·Isaac Gym fret 진단 회귀 검사 통과
- 상태: 구현·CPU 검증 완료, fresh GPU 비교 전

### OPS-001 — 장시간 학습 CUDA 장치 가드 오류 완화

- 시기: 2026-08-30
- 기준 run: `fret/training/runs/20260829_1540_02_Jazz1-200-B_solo`
- 발생:
  - 28,180 iteration의 `integrated_press`에서 PyTorch
    `CUDAGuardImpl d.is_cuda()` 내부 assertion으로 중단됐다.
  - 마지막 주기 checkpoint는 28,000 iteration이다.
  - 같은 시각의 NVIDIA Xid·커널 GPU 오류는 확인되지 않았다.
- 변경:
  - 같은 프렛의 다중 손가락 목표 계산에서 매 step 생성하던
    `full_like` 상수 텐서 세 개를 scalar-tensor 계산으로 치환했다.
  - 수학적 결과와 보상 의미는 바꾸지 않았다.
  - 이후 `RuntimeError`가 발생하면 마지막 완료 iteration의 checkpoint 저장을
    먼저 시도한 뒤 원래 오류를 다시 발생시킨다.
- 검증:
  - 이전 식과 새 식의 최대 절대 오차 0
  - CPU·CUDA 보상 회귀 검사 통과
  - 8환경 Isaac Gym GPU smoke 학습 통과
  - 28,000 checkpoint의 계약 마이그레이션과 1,024환경 1 iteration 재개 통과
- 재개:
  - 구현 fingerprint가 바뀌므로 28,000 checkpoint에는
    `--migrate-contract`이 필요하다.
  - 기존 로그 뒤에 더 낮은 iteration을 덧붙이지 않도록 새 run 이름을 사용한다.

### FRET-015 — frozen-context 망각 방지와 승급 평가 분리

- 시기: 2026-08-31
- 분류: FORGETTING / SAMPLING / TRANSITION / METRIC
- 연결된 이전 실험: FRET-009, FRET-010, FRET-011, FRET-012
- 기준 run: `fret/training/runs/20260830_1935_02_Jazz1-200-B_solo_resume`
- 문제와 관측 사실:
  - `frozen_context` 진입 뒤 약 17,500 iteration 동안 승급하지 못했다.
  - 단일 focus가 약 29 iteration마다 바뀌었다.
  - focus 변경 때마다 1,024개 환경 reset과 bridge evidence 삭제가 발생했다.
  - 마지막 균형 구간의 손가락별 압현률은 검지 35.6%, 중지 53.0%, 약지 0.7%, 소지 0.01%였다.
  - 이전 `static_chord`에서는 검지·중지·약지가 92% 이상이었으므로 망각이 주원인이다.
  - 엄지 지지와 안전 종료는 병목이 아니었다.
- 변경:
  - 환경의 75%는 적응형 학습, 25%는 고정 균형 평가 cohort로 사용한다.
  - 학습 cohort는 모든 손가락에 최소 20%를 남긴다.
  - 초기 비율은 검지/중지/약지/소지 `20/20/30/30%`다.
  - 학습 문맥은 단일 압현 60%, 안정 다중 압현 30%, 전체 문맥 coverage 10%로 구성한다.
  - 500 iteration 단위로 성공률 부족과 최고점 대비 하락을 반영해 가중치를 갱신한다.
  - 가중치 변경은 현재 episode를 끊지 않고 다음 자연 reset부터 적용한다.
  - 가중치 변경으로 전체 환경 reset, bridge 초기화, regression 초기화를 하지 않는다.
  - 승급 bridge는 고정 평가 cohort의 episode만 사용한다.
  - real-context 전환 뒤 200 iteration이 지난 시점에 평가 evidence를 한 번만 초기화한다.
  - 평가 window마다 필요한 손가락별 evidence가 충분한지도 확인한다.
  - recovery 구간에는 손가락 탐색 하한을 유지하고, 평가 시작 뒤 정밀화 schedule을 새로 시작한다.
  - `--stop-on-curriculum-stall`은 frozen-context 평가 실패도 정상 종료 사유로 처리한다.
  - curriculum schema를 56으로 올린다.
- 체크포인트 호환성:
  - schema 55 이하의 정책·optimizer·전체 iteration은 유지할 수 있다.
  - 기존 focus 편향 bridge와 frozen stage clock은 폐기하고 `frozen_context` 처음부터 다시 측정한다.
  - 권장 재시작 지점은 `fret_034500.pt`이며 `--migrate-contract`이 필요하다.
- 검증:
  - 적응 가중 quota, 25% 고정 cohort, 60/30/10 문맥 표집 검사 통과
  - 가중치 setter가 진행 중 frame과 episode를 바꾸지 않는 검사 통과
  - 평가/train episode 분리 및 raw 손가락 evidence 집계 검사 통과
  - 평가 시작 전 evidence 0, 시작 시 1회 초기화, 이후 평가 cohort만 누적하는 검사 통과
  - 가중치 변경 시 전체 환경 reset·bridge 삭제 0회 검사 통과
  - schema migration, PPO 집계, checkpoint 계약, 터미널 출력 회귀 검사 통과
  - `fret_034500.pt`를 schema 56으로 옮긴 8환경·1 iteration GPU smoke 학습 통과
  - `--migrate-contract`가 기존 run manifest를 재사용하던 문제를 발견해 새 run을 만들도록 수정
  - 장기 GPU 비교는 아직 수행하지 않았다.
- 성공 기준:
  - stage 전환 외 가중치 갱신에 따른 전체 환경 reset 0회
  - 모든 손가락 실제 학습 표본 비율 20% 이상
  - 고정 평가 cohort 비율 25%, 손가락별 표본 고갈 0회
  - 약지·소지가 1,000 iteration 뒤 10% 아래로 붕괴하지 않음
  - 2,000 iteration에서 약지·소지 각각 50% 이상
  - 최종 hard gate에서 네 손가락 모두 70% 이상, F1 75% 이상
- 상태: 구현·회귀·GPU smoke 검증 완료, 장기 GPU 비교 전

### FRET-016 — frozen-context 성능 기반 복구와 무보조 평가

- 시기: 2026-09-01
- 분류: FORGETTING / SAMPLING / TRANSITION / REWARD
- 연결된 이전 실험: FRET-015
- 기준 run:
  - `fret/training/runs/20260831_1646_02_Jazz1-200-B_solo`
  - `fret/training/runs/20260831_1649_02_Jazz1-200-B_solo`
- 문제와 관측 사실:
  - 두 run 모두 `fret_034500.pt`에서 시작해 38,500 iteration 부근의 `frozen_context`에서 정체됐다.
  - 대표 run `20260831_1646`은 F1 50.34%, 검지 92.48%, 중지 59.67%, 약지 0.19%, 소지 10.01%였다.
  - NP 정확도는 92.99%, 오압현률은 3.44%였지만 sustain 44.7%, event 성공 33.6%, dropout 11.1%, 실패 종료 0.49%였다.
  - `static_chord`에서 존재하던 teacher와 pose guide가 `frozen_context`에서 0이 됐다.
  - 적응 표집 갱신 횟수도 0이라 약지·소지 붕괴에 대응하지 못했다.
  - 평가는 성능 회복과 무관하게 시간으로 시작됐고, evidence 초기화 시점도 평가 계약과 정확히 맞지 않았다.
- 변경:
  - curriculum schema를 57로 올린다.
  - `frozen_context` 앞에 500 iteration 단위 성능 복구 블록을 최대 8개 둔다.
  - 손가락별 압현률 70% 이상, 목표 거리 25 mm 이하를 2블록 연속 만족해야 복구를 마친다.
  - 학습 75%·고정 평가 25% cohort 분리는 유지한다.
  - 학습 cohort 표집은 순위 기반으로 갱신하며 손가락별 최소 20%, 최대 40%를 적용한다.
  - distal 손가락 teacher와 pose cache는 학습 cohort에만 적용하고 회복률에 따라 점차 줄인다.
  - action teacher loss에도 보조 강도를 직접 곱해 실제 기울기를 함께 줄인다.
  - 성공 자세 RSI도 보조 cohort에만 적용해 강도와 함께 줄이고, 강도 0·안정화·평가에서는 모두 끈다.
  - 복구 뒤 200 iteration 동안 teacher 없이 안정화한 뒤 평가를 시작한다.
  - 평가 timeout은 stage 전체 시간이 아니라 실제 평가 시작 시점을 기준으로 계산한다.
  - 복구 거리 증거는 학습 cohort만, 승급 엄지 증거는 고정 평가 cohort만 사용한다.
  - frozen-context completion gate는 복구·안정화·평가 모든 phase에 유지한다.
  - 기존 승급·성공 threshold는 완화하지 않는다.
- 체크포인트 호환성·다음 실험:
  - 권장 재시작 지점은 `fret_034500.pt`다.
  - `--migrate-contract`로 schema 57에 맞춘 뒤 새 run에서 비교한다.
  - `20260831_1646`과 `20260831_1649`의 38,500 checkpoint는 재개 기준으로 사용하지 않는다.
- 검증:
  - 순위 표집의 20% 하한·40% 상한 검사
  - 복구 2블록 판정, 8블록 상한, 200 iteration 무보조 안정화 검사
  - 학습·평가 cohort 분리와 평가 상대 timeout 검사
  - distal teacher·pose guide의 학습 cohort 한정 적용 검사
  - pose-guide 마스크가 후속 보상의 활성 마스크를 바꾸지 않는 검사
  - 학습 거리·평가 엄지 raw evidence의 cohort별 pooled 집계 검사
  - schema 57 저장·복원·JSON 직렬화 검사
  - 실제 `fret_034500.pt`를 옮긴 8환경·1 iteration GPU smoke 학습 통과
  - 8환경·30 iteration GPU 검사에서 완료 episode가 학습 75%·평가 25%로 분리되고 거리·엄지 지표가 각각 기록됨
- 상태: 구현·CPU·GPU smoke 검증 완료, schema 57 장기 GPU 비교 전
