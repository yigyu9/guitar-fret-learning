# 누적 손가락 목표와 정책 입력 진단

검토 대상은 압현 개선 v4의 동결435소스와 기존 고정100회 정책·N4 대조 기록이다. **누적 목표·목표−실제 각도·직전 행동이 정책 입력에 없다는 가설은 이 구현과 맞지 않는다.** 실제로 정책에 전달된 저장 state에서도 해당 정보가 확인된다. 관측 누락을 이유로 PPO·표준편차·정책 구조를 바꿀 근거는 이번 검사에서 찾지 못했다. 이 문서는 분석이며 구현 변경이나 새 학습 결과가 아니다.

## 정책이 보는 관절 상태

[관측 생성](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:849)과 [필드·스케일 정의](/home/ajou/yigyu/3/guitar_learning/core/observations.py:22)의 순서는 다음과 같다. 아래 인덱스는 Python의 끝 제외 구간이다.

| state512 구간 | 실제 값 | 고정 나눗셈 스케일 |
| --- | --- | ---: |
| `0:105` | 전체 native105의 `q−reference` | 1rad |
| `105:210` | 전체 native105의 실제 `qd` | 10rad/s |
| `210:315` | 전체 native105의 `command_target−q` | 1rad |
| `315:354` | 직전 적용39축 행동 | 1 |
| 이후 | 기타 상대 자세·속도, 손목/손끝 body origin, 접촉·안전, 곡/음 이력·왼손 단계 | 계약 필드별 |

LH21은 native105에 모두 포함된다. 누적 목표105의 별도 raw 블록은 없지만, 고정 reference가 주어진 상태에서 `target = reference + (q−reference) + (target−q)`로 복원할 수 있다. ±10 정규화 clip이 걸리지 않는 범위라는 조건이 필요하다. 준비 reference와 native 한계는 고정 과제/행동 계약이며, 음별 목표와 혼동하면 안 된다.

현재 의사결정에서 아직 선택하지 않은 행동은 입력에 없고, 직전 적용 행동이 입력에 있다. [end_control](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:737)은 기존 직전 행동으로 변화 비용을 계산한 뒤 `previous_action = action.clone()`을 수행하고 다음 관측을 반환한다. [GpuPool](/home/ajou/yigyu/3/guitar_learning/training/gpu_pool.py:59)은 목표를 한 번 갱신하고 물리4회 진행 후 관측을 만든다. [scene](/home/ajou/yigyu/3/guitar_learning/gpu/scene.py:348)은 제출 목표를 snapshot에 보관한다. 따라서 관측의 target error는 초기 목표로 고정된 가짜 오차가 아니다.

[누적 제어](/home/ajou/yigyu/3/guitar_learning/gpu/control.py:379)는 LH21에 `clamp(previous_target + action×4/60, native_limits)`를 사용한다. 0은 목표 유지이고 반대 부호는 다음 tick 목표를 반전한다. 한계 밖 숨은 누적값은 남기지 않는다. 이 특정 제어기의 기억인 이전 목표는 위 관측으로 나타나므로, 이를 빠뜨려 비Markov가 됐다는 설명은 성립하지 않는다. 다만 이 점만으로 접촉 solver·모든 음별 누적 상태까지 포함한 전체 환경의 완전한 Markov성을 증명한 것은 아니다.

## 사건 토큰과 정책 연결

[24차원 사건 토큰](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:811)은 음 시작/끝/press까지 남은 시간, 현·프렛·지정 손가락, 현재/준비 여부, 순간 candidate/wrong, dwell/held/release를 포함한다. `16:19`는 현재 선택 손가락 표면점에서 압현면 목표까지의 오차, `19:22`는 물리 표면점의 상대 속도에 대응한다. 각각 .03m와 .5m/s로 나눈 뒤 ±10 clip한다. 즉 관절 목표−q뿐 아니라 **음의 공간 목표−실제 손가락 표면점**도 별도 입력이다. 두 오차는 다른 양이다.

현재·가까운 strict deadline의 우선 토큰2개와 lookahead 내 일반 토큰이 함께 제공된다. 유효 토큰은 24개 특징이 공유 MLP에 들어가고, state가 query인 attention context 및 우선 토큰과 합쳐진다. [Encoder](/home/ajou/yigyu/3/guitar_learning/training/policy.py:10)는 feedforward이며 LSTM/GRU의 숨은 상태는 없다. [SpecialistPolicy](/home/ajou/yigyu/3/guitar_learning/skills/specialist_policy.py:87)의 왼손 actor는 state512와 이 토큰을 실제 입력으로 사용한다. 왼손33축에는 팔/손목12축과 손가락21축이 포함된다. 전달된 정보가 있다는 사실은 정책이 그 정보를 충분히 사용하도록 학습됐다는 증거와는 다르다.

## 저장된 실제 입력 교차검산

기존 [N4 원자료](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_press_control_v1/policy_ablation_n4/capture_metadata.json)를 CPU로 읽었다. 각 행은 t0+1969개의60Hz endpoint, 총4×1970 state다. 정책/학습/물리를 새로 실행하지 않았다.

| 대조행 | 전체105 최대 abs(target−q), rad | 전체105 최대 abs(q−reference), rad |
| --- | ---: | ---: |
| 전체 정책 | 0.1146439314 | 1.7482384443 |
| LH21 행동만0 | 0.0531430244 | 0.0531430244 |
| 팔/손목12 행동만0 | 0.1139027476 | 1.7482960224 |
| 전체39 행동0 | 0.0531430244 | 0.0531430244 |

네 행 모두 아래 최대 절대 차이가 **0**이었다.

- 저장 state의 `210:315`와 실제 저장 `target−q`.
- t0를 제외한 endpoint state의 `315:354`와 그 endpoint를 만든 applied_action.
- 다음 행동에 사용된 `policy_input_state[t]`와 직전 endpoint `state[t−1]`.

이 기록의 관절각 오차 두 블록은 ±10 clip에 도달하지 않았다. 따라서 해당 실제 대조 기록에서는 목표 기억이 누락되거나 clip으로 소실됐다고 설명할 수 없다. 토큰 전체는 이 N4 도구가 저장하지 않았으므로 저장 state만으로 정책 추론 전체를 독립 재현했다는 뜻은 아니다.

## 추종 오차와 잘못된 목표 이동을 구분

[고정1024평가의 env0](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_press_control_v1/final_policy_diagnosis.md)에서 LH21 command−q pooled RMS는 이전 누적보상v3의 .082919rad에서 v4의 .031585rad로 작아졌지만, v4의8개 캡처는 모두0음이었다. 8개 모두18/21축이 전곡 내내 같은 비영 부호를 냈고 목표가 native 한계에서 잘리는 구간이 많았다. 작은 추종 오차는 **이동 중인 명령 목표를 잘 따라간다**는 지표이며, 그 목표가 적절한 음 위치라는 보장은 아니다. 실제 손가락 이동과 유효 음 창의 기하 부재가 동시에 기록됐다.

[N4 명령 차단 대조](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_press_control_v1/policy_ablation_analysis.md)는 전체 정책0음·LH21만0일 때5음·팔/손목12만0일 때0음·전체39가0일 때5음이었다. 보존된5음은 준비 자세 검지의 같은 현·프렛 목표 index41/52/62/63/64다. 네 손가락의 새로운 연주를 뜻하지 않는다. 이는 유효한 관측을 받은 정책의 지속 방향 명령이 준비 기하를 떠나는 현상과 일치한다. 각 조건은 한 환경ID의 폐루프이며 관측·차단하지 않은 행동도 갈라지므로, 학습 gradient의 원인을 확정하는 실험은 아니다.

[10월22일18환경 반전 검사](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_ring_pinky_probe_v1/README.md)는 비시험 목표 유지 오차0rad, 양 조건의 native 여유≥.05rad인12/12 방향에서 실제 요청 방향 이동을 확인했다. 약지2·소지3의 국소 반전은 가능했으며 소지 기저1_z에는 추종 잔차가 남았다. 따라서 손가락 전체가 움직일 수 없거나 모든0음이 position tracking 실패라는 설명은 과하다. 반대로 이 결과는 소지의 추종 문제를 부정하지 않는다. 해당 축의 PD/물리 원인과 개선은 별도 담당 범위이며 여기서는 중복 진단하지 않는다.

## 이번 수정에서의 판단과 확인 기준

관측 필드나 recurrent 메모리를 우선 추가하지 않는다. 현재 근거는 실제 목표 추종과 정책의 음별 접근·정지·반전 선택을 구분해 보는 쪽을 지지한다. 이번 소지 추종 보완은 정책·보상·PPO·표준편차를 유지해 효과를 분리할 수 있다.

후속 검증에서는 같은 사전 정의 pulse/hold/return에서 시작 오차를 포함한 실제 q−target 잔차·복귀 오차를 확인하고, 별도의 고정정책 평가에서는 지속 부호축 수·한계 바깥 요청·음별 기하/candidate/clean·달성을 확인한다. 앞 지표만 개선돼도 뒤 성과가 좋아졌다고 표현하지 않는다. 이미 존재하는 목표/이전 행동 정보에 대한 정책 민감도가 의심되면 동일 저장 상태에서 해당 블록만 바꾼 CPU 정책 출력 대조가 후보가 될 수 있으나, 이는 표현 민감도 검사일 뿐 물리적으로 가능한 상태·더 나은 정책·누락 원인의 증명이 아니다. 이번에는 수행하지 않았다.

모든 수치는 기존 기록의60Hz endpoint 또는 명시된 요약 범위다. 실제240Hz 극값·접촉쌍·압력·음향 성공으로 확대하지 않는다. 활성 소스·봉인 자료·기존 도구를 수정하지 않았으며 GPU/GL을 실행하지 않았다.
