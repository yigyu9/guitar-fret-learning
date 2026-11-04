# 압현 v4 실행·정책·PPO 구조 감사

2026-11-04. 활성 코드와 원문 결과는 수정하지 않았다. GPU 실험이나 새 학습 없이 실제 체크포인트·설정·로그를 읽고 CPU 합성 예제로 확인했다. 재현 도구는 [audit.py](audit.py), 수치·입력 SHA·검사 결과는 [audit.json](audit.json)에 있다.

## 결론과 우선순위

**가장 먼저 보정해야 할 확정 불일치는 탐색 초기값이다.** v4 기본 실행은 33축 모두 약0.0498이며, 이전7시간 실험은 팔·엄지0.15/검지~소지0.35였다. 단순히 같은 구조라고 간주하고 다음 장기 학습을 실행하면 탐색 조건이 바뀐다. 단, 현재 v4 native 결과는 작동 검사이므로 이 차이가 v4 학습 성능을 낮췄다는 인과 결과는 아직 없다.

장기 학습의 어려움을 신경망 입력 단절이나 PPO reset 오류로 설명할 근거는 찾지 못했다. 목표 인코더·상태 인코더는 연결되어 있고, 무효 목표 마스크는 정상이다. 그 다음 우선 검토 대상은 짧은 직접 GAE 구간, 학습률의 영구 감소, 실패 비용과 음악 보상 우위의 규모 차이, 평가 기반 최상 모델 선정 부재다. 이들은 작동 오류가 아니라 설계·실험 운영 위험으로 구분해야 한다.

| 구분 | 발견 | 판단 |
| --- | --- | --- |
| 확정 설정 불일치 | v4 탐색0.0498, 과거 팔/엄지0.15·손가락0.35 | 장기 비교 전에 조건을 명시·일치시켜야 함 |
| 설계 위험 | H32 직접 자료0.533초, 나머지는 가치 예측으로 연결 | 수 초 준비·전환의 신용 할당이 느릴 가능성 |
| 설계 위험 | KL 재시도 후 actor LR 복구·하한 없음 | 정체 후에도 작은 학습률을 계속 사용할 수 있음 |
| 실로그 상관 | 마지막100회 비용 우위 표준편차가 음악 보상 우위보다 평균5.50배 | 안전·비용 예측 신호가 정책 갱신을 강하게 좌우할 가능성 |
| 운영상 한계 | 공용 실행기는 best를 선정하지 않고 마지막 모델을 반환 | 마지막 모델이 최고 음악 성능이라는 보장 없음 |
| 정상 확인 | actor/critic 분리, 목표 경로·마스크, H 경계 지속, strict resume | 전체 구조 재작성의 근거는 아님 |

## 1. 탐색값의 실제 실행 불일치

다음 저장본은 각각의 `checkpoint_manifest.jsonl`에 기록된 SHA256과 일치하는 것을 확인한 뒤 CPU로 읽었다.

| 실제 checkpoint | 팔12축 | 엄지5축 | 검지~소지16축 |
| --- | ---: | ---: | ---: |
| v4 native 최초 모델 | 0.0497871 | 0.0497871 | 0.0497871 |
| v4 native4회 모델 | 약0.0498 | 약0.0498 | 약0.0498 |
| 기존7시간 v2 최초 모델 | 0.1500000 | 0.1500000 | 0.3500000 |
| 기존7시간 v2 최종1427회 모델 | 0.14846 부근 | 0.14965 부근 | 0.34866 부근 |

정확한 평균·최솟값·최댓값과 SHA는 `audit.json.checkpoints`를 따른다. 비교 결과 손가락은 약7.03배, 팔·엄지는 약3.01배의 초기 탐색 차이가 있다. 이 값은 관절각 표준편차가 아니라 **tanh 이전 정규분포의 표준편차**다.

원인은 과거 연구용 `도구/run.py`가 정책 factory에서 `support_log_std=log(0.15)`, `finger_log_std=log(0.35)`로 별도 초기화했기 때문이다. 설정의 `initial_std`만 읽으면 과거도0.0498로 오해할 수 있다. 과거 설정에는 실제 초기화를 `song_run_initialization`에 추가 기록했고 모델에도 그 값이 들어 있다. 신규 v4에는 이 별도 초기화가 없다.

근거: [공용 초기화](/home/ajou/yigyu/3/guitar_learning/training/finger_skill_runner.py:261), [v3 정책의 초기 log_std](/home/ajou/yigyu/3/guitar_learning/training/compact_press_v3.py:61), [과거 별도 초기화](/home/ajou/yigyu/3/docs/2026-11-09/압현_상태443_목표16/전곡학습_7시간_결합512_v2/도구/run.py:38).

확정된 것은 조건 차이다. 높은 탐색이 모든 과제에서 우월하다는 뜻은 아니다. 보상 profile을 비교할 때는 이 값을 함께 고정하고 실제 최초 checkpoint의 축별 분산까지 검사해야 한다.

## 2. 시간 범위와 신용 할당

실제 v4 설정은 정책60Hz, H32, reward gamma0.99, cost gamma1.0, GAE lambda0.98이다. H는 **초가 아니라 정책 tick 수**다. 1024환경이면32768개 표본이지만 한 환경에서 직접 이어진 자료는 약0.533초다.

| 미래 시간 | 보상 할인 gamma^tick | TD 잔차의 GAE 가중치 (gamma×lambda)^tick |
| --- | ---: | ---: |
| 0.5초 | 0.73970 | 0.40349 |
| 1초 | 0.54716 | 0.16281 |
| 2초 | 0.29938 | 0.02651 |
| 3초 | 0.16381 | 0.00432 |

위 GAE 열은 같은 궤적 자료가 충분히 길 때의 이론상 가중치다. 실제 H32 밖의 미래 잔차를 지금 buffer에서 직접 계산하는 것은 아니며, 마지막 상태의 critic bootstrap이 대신한다. 보상 할인 시간상수는 약1.658초, GAE 잔차 시간상수는 약0.551초다.

CPU 최소 재현에서120tick 뒤에 보상1을 놓고 critic을 모두0으로 두면,180tick GAE의 최초 우위는0.0265065지만 첫32tick만 계산한 최초 우위는0이다. 이는 **장기 보상 전달이 불가능하다는 증거가 아니라, critic이 아직 정확하지 않은 초반에는 H 밖의 성공을 준비 행동과 연결하기 어렵다는 예시**다. 접근 잠재처럼 즉시 들어오는 보상은 이 예시와 달리 단기 신호를 제공한다.

근거: [결정 단위 GAE](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:389), [매 tick 수집](/home/ajou/yigyu/3/guitar_learning/training/rollout.py:201), [실제 설정](/home/ajou/yigyu/3/docs/2026-11-09/압현_보상개선_v4/검증/native_train/J/settings.json).

따라서 H를 늘리는 비교가 타당하지만, sample 수·갱신 수·실제 시간을 함께 맞춰야 한다. gamma를 바꾸면 접근 잠재의 gamma도 반드시 같이 바꿔야 하며 실행기는 두 값 불일치를 거부한다. 곡 전체가 길다는 이유만으로30초 뒤 보상이 최초 행동에 강하게 전해져야 한다는 뜻도 아니다. 각 음의 준비·유지에 필요한 시간 범위와 비교해야 한다.

## 3. 학습률과 탐색 조절

actor loss는 PPO clipped surrogate이며 entropy 보너스가 없다. 표준편차는 학습되는33개 파라미터이고 log_std의 출력 범위는[-5,2]다. 정체 감지 후 탐색 회복·그룹별 최저 탐색값은 없다. entropy를 로그에 남기는 것과 보너스로 최적화하는 것은 다르다.

KL 제한을 초과하면 가중치·Adam을 해당 minibatch 이전으로 복원하고 학습률을 낮춘다. 같은 minibatch에서 최초 학습률3e-5에 대한 재시도 값은7.5e-6,1.875e-6,4.6875e-7이다. 채택된 감소율은 다음 업데이트에도 남으며 복구 하한은 없다. 마지막 재시도까지 실패하면 조용히 진행하지 않고 전체 업데이트를 복원하고 오류를 보고한다.

근거: [KL 재시도](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:427), [actor loss](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:488), [표준편차 출력 제한](/home/ajou/yigyu/3/guitar_learning/training/compact_press.py:116).

다만 과거1427회 로그는 LR이0에 가까워진 사례가 아니다. 재시도는 전체에서 단1번이며574회에3e-5→7.5e-6으로 줄고 끝까지 유지됐다. 최종 accepted KL0.00545, clip 비율5.33%로 실제 갱신이 계속됐다. 최종 손가락 탐색도 약0.35를 유지했다. **이번 실패 전체를 LR·탐색 붕괴로 설명하면 실제 로그와 맞지 않는다.**

## 4. 상태·목표 인코더와 gradient

v4는 v3 정책을 그대로 사용한다.

```text
상태452 또는461 → 256 → 256
목표26 ×8 → 각 슬롯이 공유하는64 →64 →512
연결768 → actor512 →256 →33
연결768 → 별도 critic256 →256 →reward value1 / cost value1
```

actor는 약721,218개, critic은450,818개 파라미터다(상태452 기준). `--size large`는 이 고정 폭을 확대하지 않는다. actor와 critic의 인코더는 서로 독립이며, 두 value head는 하나의 critic 인코더를 공유한다. 현재 실행은 왼손33축 정책이고 오른손6개는 공용 전달 형식의0이며, 전신은 기존의 유한한 지지 제어를 사용한다. 전신·타현 정책3개를 함께 학습하는 실행은 아니다.

CPU 확인 결과:

- 초기 actor 최종층이0이므로 최초 표본 수집의 평균 행동은0이며, 첫 head 갱신 이전 actor 인코더 gradient는0이다. 첫 head 학습 이후 경로가 열리는 정상적인 초기화 특성이다.
- head를 비영점으로 둔 검사에서 유효 목표 입력 gradient는 비영점이고, 무효 목표 입력 gradient는 정확히0이다.
- 무효 슬롯에 NaN을 넣어도 정책의 모든 출력은 원래와 정확히 같다. 마스크 처리 누락을 발견하지 못했다.
- actor/value 파라미터 집합은 겹치지 않는다.

근거: [특징 조립·마스크](/home/ajou/yigyu/3/guitar_learning/training/compact_press.py:32), [v3 고정 폭과 초기 head](/home/ajou/yigyu/3/guitar_learning/training/compact_press_v3.py:49), [actor/value 파라미터](/home/ajou/yigyu/3/guitar_learning/training/compact_press.py:104).

이는 경로 연결 검사다. 학습된 정책이 손가락별 목표를 충분히 이용한다는 증명은 아니다. 출력33개를 한 head로 만드는 구조에서 특정 손가락의 쉬운 해법이 다른 손가락 학습과 간섭할 수 있다는 것은 여전히 미검증 가설이다. 손가락별 head나 순환망을 바로 도입할 근거로 쓰지 않는다.

## 5. 비용 우위와 음악 보상 우위의 규모

현재 actor는 reward advantage−cost advantage를 한 번에 정규화한다. cost weight는1, cost gamma는1로 고정이며 적응 승수는 사용하지 않는다.

과거7시간 v2의 마지막100회에서:

- reward advantage 표준편차의 업데이트별 평균:0.21793.
- cost advantage 표준편차의 업데이트별 평균:1.19930, 약5.50배.
- 모든100회에서 cost advantage 표준편차가 더 큼.
- 완결1843개 stochastic episode 중 물리 실패304개,16.49%.
- 전체1427회에서는 물리 실패4911/57205개,8.58%.

이 수치는 최종 deterministic 평가의 물리 실패0과 양립한다. 학습 중 탐색 정책과 평균 정책 평가를 혼동하지 않아야 한다. 비용 신호가 큰 것은 안전을 강조한 설계와 관련될 수 있고, critic 오차가 섞여 있을 수도 있다. 위 표준편차만으로 정책 gradient의 방향·원인을 확정할 수는 없다. 다만 음악적 개선이 늦을 때 비용을 포함한 joint advantage를 함께 추적해야 한다는 실로그 근거다.

최종 reward critic MSE0.06309, cost critic MSE2.54610으로 약40.36배 차이가 있다. 두 head가 critic 인코더를 공유하고 loss는 두 MSE를 같은 계수로 더하므로 비용 예측이 공유 특징 학습에 더 강하게 작용할 가능성이 있으나, MSE 비율만으로 실제 gradient 비율을 단정할 수는 없다. 최종 reward critic explained variance0.9218, cost critic0.8807이지만, 이는 H32의 고정 lambda-return에 대한 적합도다. 곡 전체의 음악 성과나 먼 목표의 정확한 가치 예측을 보증하지 않는다.

근거: [결합 우위](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:167), [Decision PPO 우위 처리](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:466), [원문 학습 로그](/home/ajou/yigyu/3/docs/2026-11-09/압현_상태443_목표16/전곡학습_7시간_결합512_v2/학습/J/learning_metrics.jsonl).

## 6. 수집·구간/전곡 일정·종료

H32 경계에서는 buffer만 새로 만들고 물리 상태·곡 시계·원장을 유지한다. CPU collector를16tick씩 두 번 진행해 시계가16→32로 이어지고 reset이 없음을 확인했다. duration은 모든 결정에서1이다. 정상 곡 종료와 물리 실패 모두 환경에서 `terminated=True`이며, bootstrap은0이 된다. collector 주석의 일반적인 truncation 설명과 달리 현재 finite song은 진짜 terminal로 구현되어 있다.

최초 계획 전이의25%를 넘으면 **그 이후 다음 episode reset부터** 전곡을 고른다. 숙련도 판정은 없다. 이는 정해진 데이터 노출 일정이지 압현 단계별 행동 잠금이나 전곡 성공 확인이 아니다.

v4 native4회 검사는 update1 이후 다음 reset scope가 전곡이지만, 전체128tick=2.13초라 reset까지 도달하지 않아 실제 전곡 노출은0이다. 이것은 정상 동작이며, 해당 검사로 전곡 학습 효과를 판단할 수 없다. 과거 장기는 실제 구간11,868,755개·전곡34,891,181개 전이가 누적됐다.

근거: [일정](/home/ajou/yigyu/3/guitar_learning/training/finger_skill_runner.py:43), [reset에서 범위 적용](/home/ajou/yigyu/3/guitar_learning/gpu/finger_skill_environment.py:219), [terminal 정의](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1310).

## 7. 저장·재개·평가와 최상 모델

소스·자산·설정 SHA, v4 설정/profile snapshot, 전체 architecture/contract, PPO config, optimizer, RNG, 누적 노출과 sampler 복원을 확인하는 경로가 유지된다. v4가 v2/v3 저장본을 암묵 변환하지 않는 것도 정상이다. 재개는 물리 중간 상태 재현이 아니라 **fresh prepared episode**에서 이어 가는 계약이다. H32 동안의 정책 갱신은 episode를 유지하지만, 프로세스 재개의 의미는 다르다.

공용 학습기는 initial/periodic/final/recovery 저장만 한다. 평가 점수를 비교해 best를 선정하지 않는다. 반환 checkpoint도 언제나final이며, 과거7시간 driver도 final을 평가·영상화했다. 따라서 파일 이름이final이거나 반환 모델이라는 이유로 최고 모델이라고 부르면 안 된다.

평가는 기본적으로 평균 행동을 실행하고, 설정한 각 환경의 첫 완결 episode만 고정 분모로 반영한다. 원문 SHA와 실제 trainer identity 검사를 통과해야 한다. 확률 정책의 접촉·실패와 평균 정책의 연주 성능은 둘 다 따로 봐야 한다.

근거: [재개 계약](/home/ajou/yigyu/3/guitar_learning/training/finger_skill_runner.py:98), [strict PPO 복원](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:365), [v4 보상 계약 검사](/home/ajou/yigyu/3/guitar_learning/tool/experiments/compact_press_v4.py:54), [주기·최종 저장](/home/ajou/yigyu/3/guitar_learning/training/finger_skill_runner.py:353), [평가](/home/ajou/yigyu/3/guitar_learning/training/finger_skill_runner.py:456).

후속 best 기준은 raw 합산 보상보다 완결·안전·압현/동시 유지·오압현·타이밍을 우선한 명시적 평가 순서가 적절하다. 이 감사에서 평가·저장 동작 자체는 변경하지 않았다.

## 재현과 한계

```bash
/home/ajou/miniconda3/envs/rl38/bin/python \
  docs/2026-11-09/압현_보상개선_v4/구조점검_20261104_1128/training/audit.py
```

적용 소스13개의 SHA를 v4 native 입력 봉인과 비교했고 체크포인트4개의 SHA를 각 출력 manifest와 비교했다. 모든 CPU assertion이 통과했다. 새 학습/물리 실험은 없다. 활성 코드·기존 검사·원문 결과는 읽기만 했으며 `training/` 아래 도구·JSON·문서만 새로 저장했다.

장기 실로그는 v2이고 현재 v4는 보상·추가 관측·동시 유지 조건도 다르다. 따라서 v2에서 확인된 위험이 v4의 실패 원인이라고 단정하지 않는다. 다음 실행에서는 탐색 조건부터 명확히 맞추고, 그 이후 H/할인·학습률 복구·비용 우위·평가 best를 각각 독립 비교하는 편이 원인 분리에 적절하다.
