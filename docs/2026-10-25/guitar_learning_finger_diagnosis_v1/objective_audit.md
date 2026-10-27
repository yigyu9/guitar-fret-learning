# v19 손가락 목적함수·제어의 읽기 전용 점검

2026-10-25. 현재 v19 구현을 읽고 CPU helper·기존 검사를 대조했다. 학습/보상/제어/과거 실행 파일은 수정하지 않았다. 아래 수치는 실제 재학습 효과가 아니라 코드의 보상식과 작은 측정 fixture를 검산한 것이다.

검증: `test_gpu_preparation_B`, `test_gpu_tracking_contact_independence`, `test_gpu_control`, `test_gpu_finger_actor`, `test_gpu_surface_learning`의 CPU 검사 55개 통과(11.205초). 별도 scalar 대조로 B/관측 gate 표·극단 자세 품질·거리 보상 비율·할인을 재계산했다. 이번 점검의 환경·B·패드·제어·정책·PPO·수집·양 커리큘럼·episode 진단 10개 모듈은 실제 v19 장기 학습 동결본과 SHA가 모두 같았다. 새 GPU/native 실행은 이 점검에서 수행하지 않았다.

## 확인된 구조

**끝관절만 굽힌 자세를 직접 고치는 항은 현재 압현 구간에 없다.** 환경은 `finger_preparation_reward`의 B 대기 항만 누적하고 `song_finger_coordination`은 0으로 남긴다. 예전 `finger_posture_reward` 안에 관절 분담 품질식이 남아 있어도, 그 함수의 coordination_rate가 실제 보상에 사용되는 것은 아니다. [환경](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:923), [기존 분담 측정식](/home/ajou/yigyu/3/guitar_learning/gpu/finger_reward.py:138).

손가락 추종은 각 손가락의 **말단 패드 표본과 목표 사이 거리**를 보상한다. 같은 거리·선택 목표·normal_cos라면 MCP/PIP/DIP 분담과 관계없이 추종 보상도 같다. candidate, 속도, 행동은 이 추종 항을 바꾸지 않는다. 방향은 2cm 안에서 최대 20%만 감액하며, 반대 방향이라도 추종 보상은 남는다. 이것은 접촉 성공 자체가 필요 없다는 의미가 아니다. 실제 candidate는 별도의 위치·방향·말단 하중 판정을 통과해야 한다. [추종](/home/ajou/yigyu/3/guitar_learning/gpu/fingertip_pad.py:263), [접촉 기하](/home/ajou/yigyu/3/guitar_learning/gpu/fingertip_pad.py:246).

현재 곡처럼 4개 손가락이 모두 등장하면, 선택 목표가 있는 손가락 하나의 추종 보상률은 정렬계수 전 `0.5×(1+d/0.04)^−2 /초`다. B는 손가락 하나 최대 `0.0025 /초`다. 둘 다 approach 단계 가중치 1을 받는다.

| 패드 거리 | 추종 보상/초/손가락 | 완벽한 B의 최대 보상 대비 |
| --- | ---: | ---: |
| 0cm | 0.5000 | 200배 |
| 1cm | 0.3200 | 128배 |
| 2cm | 0.2222 | 88.9배 |
| 3cm | 0.1633 | 65.3배 |
| 4cm | 0.1250 | 50배 |
| 10cm | 0.04082 | 16.3배 |

이는 같은 상태에서 둘 중 하나를 반드시 포기해야 한다는 뜻이 아니다. 실제 복귀 동작에서 패드 거리가 얼마나 변하는지가 필요하다. 다만 B 권고와 추종의 상대적 크기는 명확하다.

**대기 시간이 짧은가와 별개로, 가까운 준비 손가락은 B 대상에서 빠진다.** 본인 목표가 press−2..end에 있고 거리가 4cm 이하이면 B gate는 0이다. 같은 구간에서도 추종은 계속 보상한다. 따라서 “당장 압현하지 않고 3cm 근처에 머무르는 손가락”은 추종을 받으면서 B 신호는 전혀 받지 않을 수 있다. [B gate](/home/ajou/yigyu/3/guitar_learning/gpu/finger_reward.py:207), [추종 선택창](/home/ajou/yigyu/3/guitar_learning/gpu/finger_reward.py:29).

## 짧은 대기 창의 정확한 조건

본인 음의 `press−0.35..end`는 B 시간 gate가 0이다. 앞뒤 0.15초 선형 fade를 쓰므로, 이전 음의 end와 다음 음의 press 사이 간격을 G라 하면 다음과 같다. 이는 시간만 본 조건이며 실제 근접·접촉 veto를 곱하기 전이다.

- G≤0.35초: 두 음 사이 B 시간 gate가 양수가 되는 구간이 없다.
- 0.35<G<0.65초: B 시간 gate가 부분적으로 열리지만 1까지 도달하지 못한다.
- G≥0.65초: 완전한 시간 gate 구간 길이는 `max(G−0.65,0)`초다.
- 다음 본인 목표가 2초 이내이고 패드가 4cm 이내이면 이 기회도 근접 veto로 사라진다.

따라서 연속 B 자격 구간의 실제 길이와 복귀 성공률을 봐야 한다. 에피소드 합계 10초가 있어도 50ms짜리 조각들인지 3초짜리 구간인지 알 수 없다. 반대로 충분히 긴 자격 구간에서도 계속 펴는 명령이면 창 길이만 늘리는 것으로 원인을 다 설명할 수 없다. [시간 계산](/home/ajou/yigyu/3/guitar_learning/gpu/finger_reward.py:213).

## 관측 idle과 실제 B gate는 서로 다르다

관측에 들어가는 `finger_posture.*.idle_weight`는 기존 press−2..end 및 0.25초 fade다. 실제 B 보상은 press−0.35..end 및 0.15초 fade에 근접·접촉 veto까지 곱한다. 따라서 정책에 “B 자격 gate” 자체가 직접 입력되지는 않는다. 손가락 전용 head의 20개 직접 입력에도 기존 idle이 들어간다. 정책은 각도·관절·목표 토큰과 전체 문맥으로 실제 자격을 간접 추론해야 한다. [관측](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1204), [전용 head 입력](/home/ajou/yigyu/3/guitar_learning/skills/specialist_policy.py:68), [전용 head 사용](/home/ajou/yigyu/3/guitar_learning/skills/specialist_policy.py:164).

이것은 문서에 명시된 의도된 호환 설계다. 관측 idle을 실제 B gate라고 해석하면 잘못되지만, **두 값이 다르다는 사실만으로 구현 버그 또는 현상 원인을 확정할 수는 없다.** 같은 학습에서 맞춘 관측을 비교하지 않았다.

CPU helper 검산: press=3초/end=5초인 검지 목표, 접촉 없음, B 자세.

| 시각 | 목표 거리 | 관측 idle | B 시간 idle | 실제 B gate |
| --- | ---: | ---: | ---: | ---: |
| 2초 | 3cm | 0 | 1 | 0 |
| 2초 | 4cm | 0 | 1 | 0 |
| 2초 | 4.0001cm | 0 | 1 | 1 |
| 2초 | 10cm | 0 | 1 | 1 |
| 5.075초 | 3cm | 0.3 | 0.5 | 0.5 |

마지막 행에서는 이전 목표가 이미 끝났으므로 그 목표의 근접은 veto하지 않는다. 구형 2초 전체 차단이 B에 실수로 남은 것은 아니다.

## 극단 자세에서 권고가 주는 신호

검지의 기하 각도가 MCP=0°/PIP=0°/DIP=90°이고 실제 B gate=1이면, B 품질은 **0.00689675**, 손가락 하나의 보상률은 **0.0000172419/초**다. B 기준은 약25.49°/35°/12°, ±15° 평탄대역, 외부 30° 척도의 지수 품질이다. 완벽한 B에서는 같은 손가락 0.0025/초다. [품질식](/home/ajou/yigyu/3/guitar_learning/gpu/finger_reward.py:202).

이 자세가 “좋은 자세라 판정된다”는 의미는 아니다. 품질은 매우 낮지만 패널티가 없고, 극단 영역에서는 작은 각도 개선의 보상 차이도 작다. 완전히 B로 돌아올 때 얻는 **추가 보상**과, 돌아오는 동안 변하는 추종·접촉·곡 보상의 손익을 비교해야 한다. 단순히 현재 받는 0.000017이라는 작은 값을 복귀의 총 이득으로 오해하면 안 된다.

## 누적 제어와 학습 시간

LH21은 `target_next=clamp(target_previous+action×4/60)`다. 행동 0은 B 복귀가 아니라 현재 목표 유지다. 예를 들어 지속 행동 +0.1은 약22.9°/초로 목표를 증가시킨다. 작은 한 방향 명령도 한계에 도달할 수 있으며, tanh 행동이 ±1에 가까운지 측정하는 action saturation과 관절 목표가 native limit에 붙었는지는 다른 지표다. clamp 전 요청은 버리고 clamped 목표만 저장하므로 누적기 windup은 없다. 반대 명령은 바로 다음 tick에 목표를 되돌릴 수 있다. [제어](/home/ajou/yigyu/3/guitar_learning/gpu/control.py:382), [관련 검사](/home/ajou/yigyu/3/guitar_learning/tests/test_gpu_control.py:158).

현재 실행 설정은 H32=0.5333초, gamma=0.99/60Hz, GAE lambda=0.98이다. 1초 후 보상의 현재 할인 가중치는0.5472, 2초 후는0.2994이며 H32에서 직접 GAE 잔차 전달 계수는 약0.3798이다. 다음 상태 가치 bootstrap은 유지하므로 **0.533초보다 긴 대기를 못 학습한다는 절단은 아니다.** 하지만 작은 지연된 B 복귀 신호의 학습 어려움을 키울 가능성은 있으며, 단독 원인으로 확정하려면 비교가 필요하다. [실행 설정](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_long_training_v19_3000/train3000/settings.json), [GAE](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:33), [수집 bootstrap](/home/ajou/yigyu/3/guitar_learning/training/gpu_pool.py:119).

접근 PBRS는 `gamma×Phi(next)−Phi(now)`이고 실제 episode 종료에서 Phi를0으로 둔다. stationary hover는 양의 PBRS를 계속 얻는 구조가 아니다. 따로 존재하는 양성 거리 추종률과 구분해야 한다. 현재 코드에서는 압현/달성의 양성 단계와 오압현/누락/미달성의 음성 단계 가중치도 서로 다른 계약을 쓴다. 이는 보존된 설계이며, 손가락 자세만으로 오압현·누락 감점이 붙는 것은 아니다. [PBRS](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1021), [가중치](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1052).

## 필요한 추가 진단

기존 episode 진단은 실제240Hz B 자격 초·품질·보상·차단 원인과 idle/press 각도 통계를 이미 기록한다. 다만 **연속 구간, 관절 명령과 그 순간 보상 관계**는 집계값으로 복구할 수 없다. 원인 분리를 위해 기존 보상을 건드리지 않는 observer에 아래 값을 모으면 된다.

1. 손가락별 실제/목표 MCP·PIP·DIP, 행동, 목표 한계까지 거리, clamp 전 요청·한계 밖 명령·한계 탈출 tick.
2. 관측 idle, 실제 B 시간 idle, 실제 gate와 근접/접촉/비유한/시간 차단 비트, 다음 press까지 시간, 지난 end 후 시간.
3. 손가락별 연속 gate>0 구간과 gate≈1 구간의 길이 분포, B band 진입/이탈·첫 진입 지연, 극단 DIP−PIP 차이 지속 시간.
4. 같은 구간의 선택 목표, pad 거리·normal_cos·surface sample id, candidate/wrong, 현재/최장 contact 및 clean streak, 실제 받은 추종/B/접촉/달성/감점.
5. “긴 B 자격+계속 한계 밖 명령”과 “B 자격 없음+근거리 추종 수령”, “명령은 B 방향인데 실제 관절 불응”을 각각 집계한다. 마지막 경우만 별도로 충돌·하중·PD 추종 문제를 의심할 근거가 된다.

관측과 gate 불일치는 입력·보상 뜻의 차이, 극단 자세는 목적함수와 정책의 관계다. 별도 observer로 확인한 실제 시간 패턴과 이 코드 점검을 합쳐야 “대기 창 부족”, “복귀 신호가 약함”, “관절 분담 신호 부재”, “물리적 걸림”의 기여를 구분할 수 있다. 물리 재학습이나 보상 변경은 이번 점검에 포함하지 않는다.
