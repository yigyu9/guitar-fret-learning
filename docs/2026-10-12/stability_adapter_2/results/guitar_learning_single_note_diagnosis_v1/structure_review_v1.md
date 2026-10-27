# 단음 학습 정체의 구조 진단

이 문서는 실행 중인 학습을 바꾸지 않고 읽기 전용으로 작성했다. **안전하게 압현·타현하는 기존 동작은 유지되고 있지만, LH 해제와 RH 추가 타현 억제를 새로 발견하는 경험이 부족한 상태**라는 설명이 현재 근거와 가장 잘 맞는다. 보상과 탐색·할인 구조가 이 정체를 설명할 수 있지만, 특정 항목을 단독 원인으로 확정할 실험은 아직 없다. 네트워크 규모 확대나 목표 풀 확대를 먼저 시행할 근거도 부족하다.

## 1. 관측 범위와 확정할 수 있는 사실

진행 중 수치의 기준은 [고정 evidence manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_single_note_diagnosis_v1/evidence_v1/manifest.json)와 그 안의 `left/right` 스냅샷이다. 양손 각각 update 파일21개·완료 에피소드96개 시점이며 최종 결과가 아니다. 현재 실행·평가·프로세스·생산 소스에는 손대지 않았다.

- LH: timing-only95/96, 새 quality0/96, 물리 실패0. 첫 완료 에피소드는 clean audible fraction1.0이지만 release_complete=False, release_late_s=2.5478이고 reward는 약2.18039다.
- RH: timing-only93/96, 새 quality0/96, 물리 실패0. 첫 완료 에피소드는 extra_count1, recovered=True, quality=False이고 reward는 약1.76572다.
- 양손 모두16환경/H120·60Hz 정책·240Hz 물리·정책7초·native 준비0초·stage1이다. `gamma=.99`, `gae_lambda=.95`, cost_gamma1, minibatch240, epochs2를 유지한다.
- 고정21개 update에서 KL retry는 양손 모두0이다. 실효 actor LR은 LH1.5625e−7, RH6.25e−7로 처음부터 일정하다. JSON의 초기 actor_lr1e−5와 다르다. long은 `pilot_dual16_{role}_v1/final.pt`를 strict resume했으므로 optimizer의 실효 LR을 상속했다. **현재 long 도중 KL guard가 새로 LR을 계속 줄였다는 근거는 없다.**
- update20의 accepted KL은 LH약0.000908, RH약0.003442다. 표준편차는 양손 약0.02를 유지한다. LH의 tanh 행동 포화율(abs≥.98)은 약15.15%, RH는0이다. 이 집계값만으로 어느 관절이 해제를 막는지는 알 수 없다. 아래의 별도 저장 관측 probe와 구분한다.

위 숫자는 각 [LH update20](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_single_note_diagnosis_v1/evidence_v1/left/update_000020.json), [RH update20](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_single_note_diagnosis_v1/evidence_v1/right/update_000020.json), 손별 `learning_status.json`과 `episodes.jsonl`에 근거한다. 자세한 분포·추세 집계는 별도 정량 분석과 구분한다.

## 2. 보상과 성공 판정이 요구하는 행동

### LH: 해제 벌점은 연결되어 있으나, 실패 동작도 양의 보상을 얻는다

[QualityLedger.update](/home/ajou/yigyu/3/guitar_learning/musical_quality.py:81)는 잘못 누르는 점유시간을 음 종료까지−1/s, 음 구간의 missing을−0.5/s로 계산한다. 해제는 지정 손가락 후보가 False인 것만으로 충분하지 않다. **목표 현의 적격 손가락 접촉 증거가 모두 사라진 상태**가 연속50ms 필요하며, 음 종료+100ms 이후 남은 접촉에는−0.5/s를 적용한다. 해제 보너스+0.25는 사전 clean audible 접촉이 `min(50ms, 음 길이)` 이상인 경우에 한 번만 지급한다. 무접촉으로 기다리기만 해서는 이 보너스를 받지 못한다.

[품질 성공 조건](/home/ajou/yigyu/3/guitar_learning/musical_quality.py:149)은 timing 성취와 stage1 clean audible fraction≥0.4, 마지막의 release_complete를 함께 요구한다. 따라서 전체 음을 잘 누르더라도 끝까지 잡고 있으면 실패다. 실제 실패는 이 판정과 일치한다.

[품질 환경](/home/ajou/yigyu/3/guitar_learning/musical_quality_environment.py:65)은 음 종료 뒤 timing_hold를 상쇄하고, 기존 timing_success를 상쇄한 뒤 audible clean 성취에 +1을 지급한다. 따라서 **음 이후 계속 누르기에 +2/s를 주는 과거 보상이 그대로 남아 있는 오류는 아니다.** 다만 stage1의 음 이전 확장창에는 +2/s hold가 남는다. 첫 목표의 press4.0, onset4.12, end4.3522에 대해 창 시작은3.5초다. 넓은 창을 일찍 획득하고 이후 계속 잡는 기존 전략도 많은 보상을 얻을 수 있다.

다음은 native 행동 실험이 아닌, 현재 ledger의 가정된 사건을 연속시간으로 계산한 비교다. 안정성 비용·행동 변화·240Hz 경계 오차를 제외한다.

| 가정한 접촉 이력 | 할인 전 task reward 근사 | 품질 성공 |
| --- | ---: | --- |
| 음 전체를 놓치고 계속 무접촉 | −0.6161 = missing−0.1161 + missed−0.5 | 실패 |
| 3.5초부터 올바르게 누르고7초까지 유지 | +2.1805 = hold1.7044 + acquisition0.25 + precision0.5 + audible1 − late1.2739 | 실패 |
| 같은 압현 뒤 음 종료에 접촉을 제거하고 해제 유지 | +3.7044 = 위 양성항3.4544 + release0.25 | 성공 가능한 이력 |

즉, **해제 성공은 같은 나머지 조건에서 더 유리하지만, 해제 실패도 양의 수익을 얻는다.** 현재 보상이 무조건 무행동을 최선으로 만든다는 결론은 틀리다. 반대로 보상이 양수이거나 증가한다고 해제를 학습했다고 판단해서도 안 된다. 원본 첫 에피소드의 약2.18039는 위 유지 실패 근사와도 가깝다. 실제 zero-action의 접촉·기타 움직임·비용은 측정하지 않았으므로 이 표를 zero-action 실행 결과로 해석하면 안 된다.

### RH: 성공 통과 뒤의 잘못된 반복은 작은 벌점으로 남는다

[TimingLedger](/home/ajou/yigyu/3/guitar_learning/timing_curriculum.py:173)는 첫 창 내 적격 통과에 +1, 시간 정밀도에 최대+0.5를 준다. [QualityLedger](/home/ajou/yigyu/3/guitar_learning/musical_quality.py:114)는 추가 matching 통과−0.1, unprepared−0.1, 별도 blocked−0.1, 회복 달성+0.1을 지급한다. 잘못된 현·방향의 적격 통과는 기존 timing에서−0.1로 한 번 감점한다. matching extra는 detector가 기존 timing event에서 차단하므로 중복 감점하지 않는다.

하지만 새 품질 판정은 accepted 존재·현재 recovered·unprepared/extra/other_blocked/wrong 모두0을 요구한다. 첫 통과 보너스는 이후 extra/wrong이 생겼다고 회수되지 않는다. 회복 보너스도 한 번 받은 뒤 다시 접근하면 회수되지 않는다. 마지막 recovered는 별도 비래치 판정으로 정확히 False로 돌아갈 수 있다. [검출과 회복의 정의](/home/ajou/yigyu/3/guitar_learning/strike_quality.py:82)는 현재 구현에 명시돼 있다.

따라서 첫 통과+회복을 유지하면서 왕복하는 기존 전략은 품질 실패여도 높은 수익을 유지한다. 같은 나머지 조건에서 extra를 없애면 수익은 올라가므로 추가 타현을 직접 장려하는 식은 아니다. 다만 기존 동작을 바꿔야 하는 신호가 성공 보너스에 비해 작고, 이미 회복하는 정책에 recovery 보너스만 크게 올리는 것은 원인과 맞지 않을 수 있다.

RH guide는 [pick_guide_evidence](/home/ajou/yigyu/3/guitar_learning/dense_environment.py:56)에 의해 onset+0.08초까지만 존재한다. 기준점은 앞쪽−8mm에서 뒤쪽+8mm로 이동하고 거리 scale은50mm다. [TimingLedger:196](/home/ajou/yigyu/3/guitar_learning/timing_curriculum.py:196)의 guide 항은0.2/s이다. 첫 목표에서 최대 기간4.2초이므로 이 항의 할인 전 상한은0.84다. 전혀 타현하지 않더라도 가정상 guide를 잘 따라 높은 근접 보상을 얻으면 missed−0.5 후 양의 수익이 남을 여지는 있다. 실제 정지 피크가 그 근접도를 유지하는지는 별도 측정해야 한다. 준비 위치와 뒤쪽 위치의16mm 차이는50mm scale에 비해 작으므로 근접 보상만으로 정확한 통과·회복 경로를 강하게 구분하기 어렵다는 추론은 가능하다.

## 3. gamma·GAE·H120: 재시작 오류와 긴 신호 전달 문제를 구분

할인은 **정책 tick60Hz마다** 적용된다. 240Hz마다 .99가 곱해지는 구현이 아니다. [compute_gae](/home/ajou/yigyu/3/guitar_learning/ppo.py:32)의 TD 잔차와 재귀는 다음과 같다.

`delta_t = r_t + gamma * (not terminated_t) * V(next_t) - V(t)`

`A_t = delta_t + gamma * lambda * (not done_t) * A_(t+1)`

| 시간 차이 | reward 할인 계수 .99^(60s) | 같은 buffer 내 TD 잔차의 직접 GAE 계수 (.99×.95)^(60s) |
| --- | ---: | ---: |
| 0.5초 | 0.73970 | 0.15877 |
| 1초 | 0.54716 | 0.02521 |
| 2초 | 0.29938 | 0.000635 |
| reset→onset4.12초 | 0.08337 | 0.000000260 |

reward 할인 반감기는 약1.149초, 직접 GAE 계수 반감기는 약0.188초다. 원래 .99라는 숫자만 보고7초 작업의 장기 보상이 충분히 보존된다고 볼 수 없다. 특히 먼저 준비해 나중에 정확히 해제하는 동작의 인과가 여러 초에 걸치면 value 추정에 크게 의존한다. **이 계수는 모든 학습 신호의 실제 크기나 신경망 gradient 자체가 아니다.** critic bootstrap과 반복 업데이트를 통해 더 긴 결과를 학습할 수 있으므로 먼 신호가 완전히 사라진다고 단정하지 않는다.

[Collector](/home/ajou/yigyu/3/guitar_learning/parallel.py:365)는 H120 끝에 환경을 reset하지 않는다. 실제 종료·time-limit인 worker만 reset하며, 다음 collect 호출은 그 관측을 이어 받는다. 다음 상태의 value를 저장하고 실제 terminated에서만 bootstrap을0으로 만든다. H120 경계는 GAE의 carry가0에서 끝나는 수집 경계이고, 마지막 TD 잔차의 `gamma*V(next)`는 남는다. 따라서 **H120은 잘못된 terminal 처리라는 증거가 없다.**

현재7초 에피소드와2초 수집창은 정렬되지 않는다. 첫 에피소드의 획득/음/해제는 대략4~6초 buffer에, 마지막 해제 유지 비용은6~8초 buffer에 나뉜다. 다음 에피소드는7초에서 시작하므로 경계 위치도 돌아간다. 올바른 bootstrap이 있어도 해제 전후의 critic 오차와 짧은 직접 GAE 범위가 함께 작용할 수 있다. H420으로 한 에피소드 전체를 담는 비교는 유용하지만, **lambda를 그대로 두면 긴 직접 GAE 감쇠가 해결되지는 않는다.** H420은 rollout 크기와 update당 minibatch 수까지 바꾸므로 같은 전이 수·accepted KL·critic 오차를 함께 비교해야 한다.

gamma를 .999로 바꾸면7초 뒤 reward 계수는 약0.657로 늘지만 lambda .95가 그대로라면 직접 GAE 전파는 여전히 짧다. 할인·lambda·H를 한 번에 모두 바꿔 원인을 잃기보다, 성공 가능한 행동 데이터를 확보한 뒤 별도 새 버전에서 통제 비교하는 것이 낫다. 현재 strict resume 중 JSON 값만 바꾸는 방식은 계약 위반이다.

## 4. 입력과 행동 권한: 정보가 없다는 진단도, 해제가 불가능하다는 진단도 아직 이르다

시간·음 종료 정보는 이미 제공된다. [ScoreTask/SkillScoreTask tokens](/home/ajou/yigyu/3/guitar_learning/skill_environment.py:57)는 목표를 에피소드 전체에 노출하며 onset/end/press delta와 string/fret/finger/direction을 포함한다. [기본 관측](/home/ajou/yigyu/3/guitar_learning/observations.py:22)은 관절 위치·속도·목표 오차·이전 행동·손/피크의 기타 상대 위치·접촉을 포함한다. 품질 history에는 target_string_contact, release_clear_dwell_s, release_complete, release_late_s와 strike accepted/extra/recovered가 있다.

따라서 음 종료를 전혀 알 수 없어서 해제하지 못한다는 주장은 맞지 않는다. 다만 현재 입력에 **별도의 release 목표 위치·손가락 표면 clearance 벡터나, 실제 지지 안전을 만족하는 검증된 해제 경로**가 있는 것은 아니다. 몸체 원점과 접촉 유무로부터 스스로 방향을 찾아야 한다. phase flag 추가만으로 해결될지는 미검증이며, 이미 시간 정보가 있으므로 먼저 필수 변경으로 취급하지 않는다.

[JointTargetContract](/home/ajou/yigyu/3/guitar_learning/control.py:107)는 증분 행동이 아니라 reset reference에 대한 유계 위치 offset을 사용한다. LH 손가락은 기본±0.5rad, 왼팔은±0.35rad, 오른팔꿈치/손목은±0.25rad이며 원 관절 제한으로 비대칭 clipping한다. smoothing alpha0.2, 손가락 target rate1.5rad/s, 팔3rad/s도 적용한다. [기본 범위](/home/ajou/yigyu/3/guitar_learning/training_environment.py:26)와 [rate](/home/ajou/yigyu/3/guitar_learning/native_session.py:8)에 근거한다.

기존 고정 action 계약의 예시는 다음과 같다. 출처는 [기존563 native 계약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/left_native_train_v2/training_contract.json)의 `action.target_contract`이다.

| 축 | reference(rad) | 유효 target 범위(rad) | 의미 |
| --- | ---: | --- | --- |
| LH:ring2 | 1.55903 | [1.05903, 1.57080] | 이 축 하나로 완전히 펴는0rad까지 갈 수 없음 |
| LH:ring3 | −0.0872646 | [−0.0872665, 0.412735] | 음의 방향 target 여유는 약1.9e−6rad뿐 |
| LH:index2 | 0.905778 | [0.405778, 1.405778] | 해당 손가락도 굽힘 범위 일부만 사용 |
| L_Shoulder_x | 0.264733 | [−0.085267, 0.614733] | 팔을 이용한 전체 손 이탈 권한은 존재 |
| L_Wrist_x | 0.0001755 | [−0.349824, 0.350176] | 손목도 고정되어 있지 않음 |

이는 **일부 손가락을 완전히 펴는 방식에는 제한이 있다**는 근거다. 현재 포화 관절을 추정한 표는 아니다. 목표 현 접촉을 없애는 데 완전 펴기가 필요한지, 팔·손목의 작은 이동으로 충분한지는 모른다. 초기 자세 검증에서 손을 넥에서 뗀 성공과 현재 정책의 좁은39축 범위에서 해제하는 성공도 같은 조건으로 취급하면 안 된다. 범위를 먼저 늘리기보다 현재 범위 안의 실제 해제 가능한 궤적을 확인하는 것이 가장 작은 확인이다.

LH 포화율15.15%는33채널 중 약5채널 비율에 해당한다. [별도 저장 관측 probe](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_single_note_diagnosis_v1/policy_change_v1.md)는 접촉 발생2.83초 관측에서 L_Thorax_x/y, L_Shoulder_z, L_Wrist_y, LH:ring2가 포화했고 초기 Actor에도 같은 포화가 있었음을 확인했다. ring2 행동 평균은 약+0.99393, 국소 tanh std는 약0.000242 normalized다. **해제 이후의 관측은 이 sparse probe에 없어 해제 시점 포화를 확인한 결과는 아니다.**

tanh에 가까운 평균에서 latent std0.02는 행동 공간의 이동량을 훨씬 작게 만든다. 예를 들어 평균 행동0.99 부근의 국소 std는 `(1−.99²)×.02 ≈ .000398`이다. 여기에 offset 배율·비대칭 native limit·smoothing이 추가된다. 이것은 포화가 탐색을 좁힐 수 있다는 수학적 근거이며, 현재5개 포화축이 해제 실패의 원인이라는 증거는 아니다. 후속 결정적 평가에서는 음 종료 전후4.2~6초의 관절별 평균/표준편차·실제 target·원 접촉 evidence를 함께 남겨야 한다.

## 5. 상속 LR/std/KL과 업데이트: 완전 정지는 아니지만 새 행동 탐색은 보수적이다

[PPO strict load](/home/ajou/yigyu/3/guitar_learning/ppo.py:233)는 모델·actor/value Adam·cost weight·update counter·RNG를 복원한다. 시작 설정의 initial_std0.02나 초기 actor_lr1e−5를 다시 적용하는 새 학습이 아니다. [KL guard](/home/ajou/yigyu/3/guitar_learning/ppo.py:158)는 초과 minibatch를 되돌리고 LR을 줄이며, 통과했다고 LR을 다시 키우는 단계는 없다. 이전 pilot의 축소가 장기 실행에도 남는 것은 구현대로다.

현재 accepted KL이 비영이고 actor가 업데이트되므로 학습이 완전히 멈췄다는 설명은 부정확하다. 위 별도 offline 분석에서도 initial→checkpoint19의 active Actor relative L2 변화는 LH0.005817%·RH0.022456%, 같은 저장 관측에서 평균 절대 행동 변화는 약0.000585·0.001307로 측정됐다. 이는 작은 변화가 누적된 근거이며 전체 native 궤적이나 해제 능력의 대조 실험은 아니다. 해당 문서의 누적20업데이트 KL과 매 update의 accepted KL도 서로 다른 지표다.

반대로 많은 전이를 수집했다고 기존 hold/왕복 동작에서 멀리 벗어나는 탐색이 보장되지도 않는다. std는 상태 독립인 채널별 Gaussian이며 [SpecialistPolicy.act](/home/ajou/yigyu/3/guitar_learning/specialist_policy.py:117)에서 active 채널만 샘플링한다. [PPO actor loss](/home/ajou/yigyu/3/guitar_learning/ppo.py:164)에는 별도 entropy 증가 항이 없다. std는 학습 가능하지만 더 넓은 탐색을 강제하지 않는다.

critic의 현재 λ-return 적합도나 설명 분산은 수집한 행동 근처의 값이다. LH가 해제하지 않는 데이터만으로 critic이 잘 맞는다고, 아직 보지 못한 release 행동의 이득을 정확히 예측한다고 볼 수 없다. 동일 초기 상태·목표에 작은 잡음을 더한16개 환경은 처리량을 늘리지만 행동 종류의 다양성을 자동으로 늘리지 않는다.

## 6. 개선 우선순위와 검증할 항목

### 우선1 — 현재 기록을 끝까지 보존하고, 성공 가능한 국소 동작을 확인

현재 실행의 설정은 그대로 둔다. checkpoint0/중간/최종을 같은 판정으로 비교하고 LH의 clean 유지와 release, RH의 첫 통과와 extra/wrong/최종 recovered를 나눠 본다. reward 상승과 quality 성공을 분리한다. 새 풀은 기존 단음 quality gate를 통과할 때만 시작하는 현재 계획을 유지한다.

후속으로 가장 먼저 필요한 별도 native 확인은 다음 세 가지다. 이 문서에서는 실행하지 않았다.

1. **zero-action/현재 정책 기준선**: 실제 무행동의 reward 각 항·비용·접촉·기하 결과를 측정한다. 위 사건 수준 계산을 실제 무행동 수익으로 대체한다.
2. **LH 현재 범위 내 해제 가능성**: 음 구간 clean을 보존한 뒤 현 접촉을 없애는 짧은 관절 목표 경로를 찾고, 접촉 feature·관절별 target bounds·실제 clearance·지지/접지를 확인한다. assigned candidate만False인지, 목표현의 다른 손가락 증거까지 사라졌는지 구분한다.
3. **RH 타현 후 경로**: 첫 accepted 뒤 추가 matching과 잘못된 현/방향이 각각 어디서 발생하는지 실제240Hz 피크 경로와 확인한다. 기존6축 범위 안에서 재통과 없이 최종 회복을 유지할 수 있는 짧은 경로와 대조한다. 깊이/영역 탈락 진단을 오타현으로 재분류하지 않는다.

여기서 유효한 경로가 확인되면 그 짧은 해제/타현 후 구간을 교사 데이터에 포함해 Actor를 재초기화하거나 구간별로 학습하는 것이, 성공 예시가0인 상태에서 벌점만 키우는 것보다 먼저 검토할 개선이다. 이 경우에도 새563 계약과 inactive hand0, 원 물리·안전·행동 범위를 검증한다. **교사/수동 경로 가능성이 확인되기 전에는 해제 불가능이나 정책 구조 실패를 결론내리지 않는다.**

### 우선2 — 작은 새 실험에서 보상과 탐색을 한 항목씩 비교

가능한 행동이 확인된 후 새 버전에서 다음을 순차 비교한다. 현재 실행에는 적용하지 않는다.

- LH: 해제 성공 이력을 먼저 공급하고 현재+0.25/−0.5s에서 release 확률이 변하는지 확인한다. 해제를 한 번도 못 본 상태에서 보너스만 키우는 방식은 양성 신호를 만들지 못할 수 있다. 필요하면 사전 audible 성취를 조건으로 실제 contact-clear 진행을 보조하되, 불명확한 distal 원점 거리를 성공 기준으로 복원하지 않는다.
- RH: 현재 이미 나타나는 recovery를 더 크게 보상하기보다 **오류 없는 한 번의 통과와 마지막 회복**에 대한 보상 정렬을 시험한다. 예를 들어 기존 첫 통과 timing 보너스 일부를 완전 품질 달성 보너스로 옮기는 비교가 가능하다. terminal 보너스만 추가하면 신호가 더 늦어지므로, 검증된 타현 후 경로의 국소 학습과 함께 비교한다. 성공 임계값을 낮춰 기존 반복 타현을 통과시키지는 않는다.
- LR/std: 같은 Actor에서 명시적 새 초기화로 작은 LR 후보 또는 탐색 후보 하나만 비교한다. 기존 Adam/RNG를 보존하는 strict resume와 새 초기화를 혼동하지 않는다. accepted/attempted KL·retry·관절별 mean/std·실제 action/target 변화량·해제/extra의 경험 수를 함께 기록한다. 현 KL 여유만으로 LR을 임의로 크게 늘리지 않는다.

### 우선3 — 시간 신호와 수집 경계를 통제 비교

위 동작이 실제로 가능한데도 근접 구간 밖으로 보상이 전달되지 않는다면 H120 대 H420, gamma/λ 후보를 별도로 비교한다. 완료 에피소드·단계별 advantage·bootstrap 값/오차·λ-return critic 적합·총 전이 수·실제 optimizer step 수를 맞춰 해석한다. gamma 변경과 horizon 변경을 동시에 학습 개선의 단일 원인으로 설명하지 않는다.

후순위는 더 큰 네트워크, 고급 분산 구조, 여러 음·sequence/chord 확장이다. 지금은 단일 목표 자체의 마지막 행동이 성공 경험으로 나타나지 않았다. 현재 증거는 모델 용량 부족을 보여주지 않으며, 단음 pool 구현은 준비돼 있어도 이 실패를 해결한 것으로 간주하지 않는다.

## 판단의 한계

보상 식·입력·행동 제한·bootstrap 연결은 소스로 확인했다. 현재 소규모 탐색이 해제 발견을 어렵게 할 수 있다는 설명과 보상/품질 불일치가 정체를 강화한다는 설명은 추론이다. 현재 범위의 실제 release 가능성, zero-action 수익, 벌점/LR/시간 설정을 바꾼 효과는 아직 검증하지 않았다. 압현 후보와 타현 기하를 실제 압력·진동·음향의 성공으로 확대하지 않는다.
