# 접근 shaping·단계·손목 종료의 실제 보상 감사

2026-10-31. 기존 native 완료 평가와 봉인 소스를 CPU로 읽었다. GPU 실행·학습/보상/종료 구현 변경 없음.

결론: 전체 실패 정책과 성공 정책의 **할인하지 않은 episode 보상 합계가 비슷한 현상은 실제**다. 그러나 원인은 phase0에서 접근 벌점을 끄는 마스크가 아니다. 접근 항은 potential shaping이며, 이를 단순 합산하면 목표에 오래 가까운 정책에서 더 음수가 될 수 있다. 현재 자료만으로 보상 허점이나 PPO 목적함수의 성공/실패 동등성을 입증하지 못한다. 손목 종료도 단계와 무관하며 기록된 이탈이 실제 종료 문턱보다 작다.

## 실제 32환경 반례와 합계의 분해

두 평가는 각 최초32개 완료 episode, 모두6초/360제어 tick이다. 실패도 분모에 포함한다. 원본 full33 seed7 100회 정책은32/32 성공, no-prior100 평균 정책은0/32이며 clean0·missing2.5초다. 동일한 목표·physics/reward 소스지만 실제 초기 q/hold가 paired 동일하다는 별도 로그 증거는 아직 없으므로 paired 실험이라고 부르지 않는다.

| 항 | 성공 full100 평균 | 무접촉 no-prior100 평균 |
|---|---:|---:|
| song_left_approach | -1.673308831 | -0.128130465 |
| song_left_contact | 0.250000000 | 0.000000000 |
| song_clean_hold | 0.999999225 | 0.000000000 |
| song_left_success | 0.250000000 | 0.000000000 |
| song_wrong_press | 0.000000000 | 0.000000000 |
| song_performance_deficit | 0.000000000 | -0.099999800 |
| song_finger_standby | 0.102555824 | 0.102841662 |
| song_thumb_support | 0.003993956 | 0.055922399 |
| action_change | -0.000004668 | -0.000000001 |
| reward 합계 | -0.066763675 | -0.069366259 |
| cost 합계 | 0 | 0 |
| approach 제외 합계 | 1.606545156 | 0.058764206 |

성공 정책은 approach 외 항에서 약1.60655를, 실패 정책은 약0.05876을 받는다. 성공의 나머지 보상 우위 약1.54778가 approach 단순합 차이 약−1.54518에 가려져 총합 차이가 약0.00260으로 작아진다. 평가 총보상을 곧바로 음악 성과 점수로 해석하면 잘못된 결론이 나오는 실제 사례다.

## 접근 항에 phase/readiness 마스크가 있는가

없다. gpu/finger_skill_environment.py:283~294의 Φ는 다음 요소만 사용한다.

- 시간표 기준 목표 선택(valid), 선택 손가락 균형 가중치, 시간표 기준 tracking weight.
- exp(−패드거리/0.03m)와 근접 방향 품질.
- motion_phase나 readiness 또는 clean 성공 여부로 Φ를 켜고 끄는 조건은 없다.

목표 valid는 press−2초부터 end 전까지이고(finger_reward.py:23~52), tracking은 score-only per-finger idle의 반대값이다(:238~279). 준비→press 시점은 근접 성공과 무관하다. 해당 목표 press=3초이므로 t0에는 valid=false/Φ0=0이며 준비 exposure는4.5초다. 실제 두 정책의 exposure도 모두4.5초, 목표 손가락 tracking의 반대인 gate_weighted standby는3초로 같다. 나머지 세 손가락 standby gate는 각각6초로 같다. 실패 정책이 phase0에 머물러 접근/대기 분모를 유리하게 바꾼 증거는 없다.

실제 단계 시간은 성공 [move0.20,align0.15,press5.65]초, 실패 [move5.9167,align0.0833,press0]초다. 이 차이는 진단 관측이지 접근 항의 보상 마스크가 아니다. StructuredPool.step은 free_v9에서 phase 기반 팔 hold/clamp도 적용하지 않는다(structured_press.py:450~467).

## 왜 가까운 성공 정책이 더 음수인가

각60Hz tick에서 rΦ,t=γΦ(t+1)−Φ(t), γ=.99다(gpu/environment.py:882,:1253~1254). 정상 timeline과 물리 실패 모두 마지막 다음 potential을0으로 만들며 정상 종료도 terminated다(:1310). 따라서 다음 두 식을 구분해야 한다.

`할인하지 않은 합 = −Φ0 − (1−γ) × Σ중간 Φ + γΦT`

`γ로 할인한 합 = −Φ0 + γ^T ΦT`

현재 Φ0=ΦT=0이라 이상적인 전체 episode의 할인된 shaping 합은0이다. 반면 로그가 보여주는 비할인 합은 −.01×Σ중간Φ다. 성공의 approach−1.67331는 중간Φ 합 약167.33, 무접촉의−.12813는 약12.81에 해당한다. 목표에 가깝게 머무른 성공이 더 큰 Φ를 가지므로 비할인 접근합이 더 음수인 것은 식과 일치한다. 이는 거리 벌점 회피의 증명이 아니다. 해당 Φ 합은 총합에서 역산한 값이며 원시 시점별 Φ를 직접 측정한 결과와 구분한다.

PPO 설정 γ와 shaping γ는 모두.99로 일치한다. 다만 finite H32, 가치망 오차·GAE·clipping·학습 중 상태 분포 때문에 이 등식만으로 실제 학습이 아무 영향도 받지 않는다고 보장하지는 않는다. 현재 episode 총합만으로 실제 할인된 총보상이나 각 보상항의 시점별 할인 기여를 복원할 수 없다.

## γ=.99의 실제 시간척도

60Hz 기준3초 뒤 가중치는 .99^180=**0.163808**다. 할인 반감기는 약68.97 tick=**1.14946초**다. 4초 뒤는약0.089629,5.5초뒤는약0.036276다. 3초 준비 이후의 음악 성과는 episode 시작에서 크게 할인되고, 초기 대기·엄지 안내는 더 이른 시점부터 누적된다. 이는 장기 credit와 약한 실패 비용을 별도로 조사할 이유지만, 실제 순서를 기록하지 않고 어느 정책의 할인 반환이 높은지는 단정할 수 없다.

## 손목이 영역 밖인데 종료되지 않은 이유

손목 안내 delta는 기준점까지 거리가 아니라 **허용 box의 초과 거리**다. 준비 판정은 각축 초과≤10mm, 정상 종료 진입은3초 이후 초과>30mm다. 20~30mm에서는 recovery timer를 감소시키고20mm이하에서는 reset한다. 초과가30mm보다 큰 누적 순시간1.5초면 종료한다. 별도의 심각 종료는초과≥100mm가0.1초 연속일 때다. 정상 조건의3초 enable 외 phase/readiness/성공 마스크는없고 severe 조건은3초 enable도없다(finger_skill_environment.py:296~310).

| 진단 | 성공 full100 | no-prior100 |
|---|---:|---:|
| 전체 physics 표본 중 box 내부 비율 평균 | 0.55556% | 0.00000% |
| 32환경 전체 기록 최대 box 초과 | 13.416mm | 16.096mm |
| 마지막 box 초과 범위 | 6.477~6.746mm | 10.474~10.780mm |

실패 정책은 box 밖이지만 최대16.10mm로30mm종료 문턱 미만이다. 준비 readiness10mm를 넘으면 phase0일 수 있지만 그것이 종료 대상이라는 뜻은 아니다. 목표 패드 최소거리는약73.87mm여도 손목 box 초과는약10~16mm일 수 있다. 서로 다른 점·영역을 측정하므로 모순이 아니다. 정상 종료0은 현재 계약과일치한다. 학습 중706 episode 중314개 guitar_displacement 실패가 있었던 것은 확률 정책·진행 중 가중치의 결과이며 이 평균 정책 평가0실패와 분포가다르다.

## 대기/엄지 안내와 수행 부족

대기 보상은 두 조건에서 약.1026/.1028로 거의같다. 비목표 손가락3개는 항상 대기 대상이고 목표 손가락도 시간표상 대기 구간만 점수를 받는다. 실패했다고 목표 손가락에 음 구간 대기 보상이 추가되는 phase 허점은 확인되지 않았다.

실패 no-prior의 엄지 guidance 품질은약.9307, 성공은약.0666이다. 따라서 no-prior가 엄지 안내를 더 받는것은 실제 기하 차이와일치한다. no-prior의 rear candidate 시간 평균도약.00794초에 불과하므로 .05592보상을 지지접촉 성공으로 읽으면안된다. 음 수행 부족은 약−.10으로 올바르게 전액 정산됐다. 음악과 무관한 보조항만으로 실패를 충분히 구분하는지와 시간할인의 영향은 정량 후속 대상이지만 아직 reward loophole이라고 확정할 증거는없다.

## 최소 후속 계측안 — 미구현·미실행

동일 actual 초기q/hold에서 성공full100과 no-prior100 평균 정책의 시점별9항 및 할인합을 기록하는 짧은 native 진단이 필요하다. 원본 체크포인트는 각각 해당 봉인 runtime에서 먼저 strict load하고 native physics/reward/종료를 그대로 실행한다. 새로운 진단 helper를입력 SHA에추가하고 provenance를분리한다. 기존 free/full source를바꾸거나 체크포인트identity를위조하지않는다.

가장 작은 read-only hook은 StructuredEnvironment._reward_components의 원본 반환 dict를 그대로 반환하면서, strict load완료후부터 각60Hz component tensor를 clone해 기록하는 wrapper다. 이 위치는 최종9항을이미만들고 실패비용도계산된뒤이며 episode누계/reset 전에있어 초기화로말단보상을잃지않는다. 원본 method의 반환값을변형하거나 추가호출로reward를두번적용하지않는다. 비용은같은경계 tick_cost를읽고 원본reward와9항합을매tick 대조한다. 초기reset q/hold캡처는 별도의pool.reset 읽기hook으로한다.

필수 열: env/episode/tick/localtime/scoretime,9항,Φbefore/Φafter(terminal0반영),cost,terminated,phase/readiness,box초과,timers,최초접촉/clean/wrong/missing. first32 episode만집계하고실패포함;평균정책·가중치전후동일·optimizer0을확인한다. 원시합은기존episode누계와맞춰야하고 Σγ^t rΦ와telescoping항차이가허용수치이내인지확인한다. γ=.99 기준전체9항의시점별할인합을표시하고shape제외음악/보조항도분리한다.

기존 fixed_reset_evaluate의 load/reset/pins context를참고할수있으나 현재그helper는 B전용이며 실제free의원본설정을그대로지원하는별도얇은wrapper검수가필요하다. A→free변환을다시할것이아니라현재검증된평가체크포인트의저장조건으로검사한다. 먼저 baseline재현과실제초기q대응증명후비교한다. 이번감사에서는hook을구현하거나실행하지않았다.

## 보존과 근거

모든평가경로,원시episodes/settings/report/metadata와양쪽reward소스SHA는 REWARD_PHASE_AUDIT.json에기록했다. 제안한추가계측이끝나기전보상계수·종료문턱·γ를이번자료만으로바꾸지않는다.
