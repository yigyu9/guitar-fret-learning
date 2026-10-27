# v4 보상 설계 감사 신호

이 자료는 보상 구조 자체의 장점과 계산 일관성을 실제 학습 유인으로 혼동하지 않도록, 사전에 준비된 반례와 수치 신호를 설명한다. 계산 그래프는 Isaac Gym 렌더가 아니다. 새 물리 실행은 0회, 학습 업데이트는 0회다.

![보상 감사 신호 세 패널](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/reward_design_audit_v4/audit_signals.png)

## 첫 패널: 같은 비율, 다른 dropout 모양

`counterexamples.json`의 두 합성 60-frame trace는 모두 54/60 정상 frame, 즉 `U=0.90`이다. 두 조건 모두 마지막 검사점 `O=1`, 가정한 `E=1`이며 파일에 기록된 조건부 보상값도 각각 `2.04`로 같다. v4의 해당 항을 풀어 쓰면 이 예시에서 `F=2(2·1−1)=2`, `U` 기여는 `0.10·0.90`, `E` 비용은 `0.05·1`이므로 `F + 0.10U − 0.05E = 2.04`다. 이 계산은 β=1, 단일 Fret event인 예시 조건이다.

첫 trace는 6개 단일-frame dropout이 띄엄띄엄 분포한다. source CPU sustain tracker는 longest dropout 1 frame, interruption 6개, event success 1로 기록한다. 둘째 trace는 6개 dropout이 연속된다. tracker는 longest dropout 6 frames, interruption 1개, event success 0으로 기록한다. 실제 `PressSustainTracker` 기본 후보 cutoff는 dropout 최대 3 control frames이며, event 성공에는 hold ratio 기준과 longest-dropout 기준을 함께 쓴다. 따라서 동일한 전체 hold ratio와 마지막 O가 dropout 배열의 모양을 구분하지 못한다.

이 tracker 계산은 주어진 Boolean trace를 source CPU tracker에 넣은 결과다. 런타임 detector, 현재 기타 좌표계 geometry, 실제 crossing 시각, 새 정책 연결을 검증하지 않는다. 합산 보상값이 같다는 산술 검사와 tracker의 별도 event-success 판정이 다를 수 있음을 보여준다.

## 둘째 패널: 기타 위치 비용의 cap

입력 field는 `pure_position_outside_mm`(허용 경계 바깥 위치 거리, mm), `rotation_outside_deg`(deg), `C_raw`(포화 전 무차원 비용), `C_g`(1에서 cap한 무차원 학습 비용)다. 그림의 모든 점은 순수 위치 이탈이며 회전 이탈은 0°로 둔다.

기록된 거리 0/10/20/30/40/100 mm에서 `C_raw`는 0/0.125/0.5/1/1.5/4.5, `C_g`는 0/0.125/0.5/1/1/1이다. 따라서 학습 비용은 30 mm부터 1에서 포화하지만 원시 비용은 계속 커진다. 실제 계측에는 포화 없는 거리와 raw 비용을 남긴다. 이는 제공된 수식 표본이며 기타 물리 이동, 허용범위 계산, SO(3) 회전집합 판정을 실행한 결과가 아니다.

## 셋째 패널: 할인 잔존 가중치

입력은 `gamma_per_step`(step당 γ), `synthetic_hz`(합성 가정 60 Hz), `half_life_seconds`(초), `weight_after_2s`와 `weight_after_5s`(해당 시간 뒤 잔존 가중치)다. log y축은 작은 잔존값도 함께 읽기 위한 표시다. 계산은 각 γ를 60 step/s로 환산한 합성 시간 가정에 따른 값이다.

표본의 2초 잔존값은 γ=.95/.99/.995 순으로 약 .00212/.29938/.54799이고, 5초 뒤에는 약 `2.08×10⁻⁷`/.04904/.22229다. 대응 half-life는 약 .225/1.149/2.305초다. 이는 할인 차이가 수초 horizon에서 장기 신호 비중을 크게 바꿀 수 있음을 보여주는 산술 비교다. γ를 추천하거나 adapter가 특정 γ를 사용한다고 주장하지 않는다. workspace PPO 설정의 `PPOConfig.gamma` 기본값은 .95지만, 그 사실만으로 새 adapter 실행 설정을 알 수 없다.

## 길이·이벤트 수에 따른 희석 신호

v4는 유지·접근 예산을 고정 분모 `N_F`로 나누고 β를 `6/m_max`로 정한다. 입력 counterexample에서 유지 event 최대 기여 `U_max_per_event`는 `N_F=1, β=1`일 때 .10, `N_F=16, β=1`일 때 .00625, `N_F=64, β=.25`일 때 .000390625다. 접근 최대 기여도 각각 .05/.003125/.0001953125로 줄어든다. 또한 episode 시간 평균인 자세 비용 `B`의 episode 총 예산은 해당 표본에서 .025/.025/.00625다. 그러므로 고정 예산 설계의 산술적 상한이 잘 지켜져도 긴 곡이나 많은 Fret event에서 개별 유지/접근 신호가 작아질 수 있다. 이는 자동으로 성능이 나쁘다는 증명이 아니라 학습 유인과 길이별 신호 크기를 실제 분포에서 검사해야 한다는 감사 포인트다.

## 해석 범위와 다음 확인 사항

[root 감사 보고서](/home/ajou/yigyu/3/stability_adapter_2/REWARD_DESIGN_AUDIT_V4.md)는 전체 학습 유인 감사와 우선순위를 정리한다. 이번 그림과 README는 이를 대신하지 않는다.

보상 구조가 잘 정리되어 있고 합성 산술 검사를 통과한 것과 학습 유인이 완성됐다는 것은 서로 다르다. dropout 배열에 대한 평가 불일치, 긴 음악에서의 event별 희석, 할인 시간척도, detector/crossing/dwell/geometry의 실제 신호 연결을 별도로 확인해야 한다. 가중치나 gamma를 새로 제안하지 않는다.

## 원자료와 코드 추적성

- 사용한 입력: [counterexamples.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/reward_design_audit_v4/counterexamples.json)
- v4 설계 기준: [UPPER_BODY_REWARD_DESIGN_V4.md](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:30)
- 감사 계획: [REWARD_DESIGN_AUDIT_V4_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/REWARD_DESIGN_AUDIT_V4_PLAN.md:5)
- CPU sustain tracker 기본 설정: [metrics.py](/home/ajou/yigyu/3/tab2body/env/metrics.py:285), event 판정 조건은 [metrics.py](/home/ajou/yigyu/3/tab2body/env/metrics.py:379)
- workspace PPO 설정의 gamma 기본값: [ppo.py](/home/ajou/yigyu/3/tab2body/learning/ppo.py:1131)
- root 감사 판단: [REWARD_DESIGN_AUDIT_V4.md](/home/ajou/yigyu/3/stability_adapter_2/REWARD_DESIGN_AUDIT_V4.md:33) (dropout), [62행](/home/ajou/yigyu/3/stability_adapter_2/REWARD_DESIGN_AUDIT_V4.md:62) (할인/지급 시각), [92행](/home/ajou/yigyu/3/stability_adapter_2/REWARD_DESIGN_AUDIT_V4.md:92) (길이별 신호 희석)

신호별 단위와 조건은 각 패널 및 설명에 적었다. producer 입력 SHA와 실행 전후 보존 대조는 [producer_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/reward_design_audit_v4/producer_manifest.json)에 기록한다.
