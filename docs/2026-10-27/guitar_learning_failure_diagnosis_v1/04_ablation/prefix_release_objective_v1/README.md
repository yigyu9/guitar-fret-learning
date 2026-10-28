# 3음 목적·해제 보상 감사

**이번 지정 시간표에서 원 핵심5항의 full3-clean 경우는 비교한 두 부분성공보다 높다. 그러나 A 종료 뒤의 해제 자체는 이5항에서 지급하지 않는다.** 다음 음의 성공·오압현 회피와 약한 대기 권고가 간접 유인이므로 “해제 유인이 없다”도 틀리다. 이 둘을 구분한다. 아래는 CPU 보상 산술이며 보상만이 실제 전환 실패의 원인이라는 결론이 아니다. 활성 소스·모델·설정·원자료 변경과 GPU 실행은 없다.

## 원 시간표와 보상

원67목표 중 검지4/7/8만 진단 평가하며 다른 손가락 기회는 이 subset에서 제외된다. 원 target ID·press/onset/end와 공유 압현을 바꾸지 않는다. score time=local+2.4497초, 354tick/5.9초다. 표의 score는 task의 원3초 pre-roll을 포함한다. 원 오디오 onset/end는 표의 score에서3초를 빼며 source JSON에도 보존돼 있다.

| 원 source index/target ID | physical 현·fret | 원 score press | audible score | local audible | 원 연속clean 달성문턱 |
|---|---|---:|---|---|---:|
| 4 / event-000004/string-3/note-4 | 3현4프렛 | 5.3297 | 5.4497–5.6200 | 3.0000–3.1703 | .06812초 |
| 7 / event-000007/string-2/note-7 | 2현5프렛 | 6.2817 | 6.4017–7.1796 | 3.9520–4.7299 | .31116초 |
| 8 / event-000008/string-2/note-8 | 2현5프렛 | **6.2817** | 7.8065–8.1548 | 5.3568–5.7051 | .13932초 |

균형계수는 선택3/(존재손가락1×검지3)=각 b=1이다. 각음의 핵심5항은 다음과 같다. 실제 구현은240Hz 두 끝점의 clean·wrong/missing 적분,60Hz 정산을 사용한다.

`r5 = .25·Δcontact_progress + Δclean/D + .25·new_achieved − .15·Δwrong/D − Δperformance_paid`

`contact_progress=min(best_press_clean_streak/min(.05,end−press),1)`이고 반복접촉 때 예산을 충전하지 않는다. `achieved`는 원 `min(D,max(.05,.4D))` 연속clean 문턱의 1회 latch다. performance는 missing/D를 단조 지급하다 end에 `max(missing/D,1−best_clean_streak/required)`로 정산하며 최대.10이다. 단음당 양성 최대1.50, wrong 최대−.15, deficit 최대−.10이다. A가 끝난 뒤에는 A의 이5항에 직접적인 접촉잔류 감점·해제 보상이 없다. 잔류가 B wrong/missing을 유발하면 **B의** 원 감점과 놓친 보상이 적용된다.

원 native `released`는 `previous_candidate & ~candidate & ever & end≤score≤end+.10`의 1회 진단 latch다. A의 원해제창은 local3.1703–3.2703초다. 이것을 실제 전 피부 분리·안정된 무접촉·압력0으로 확대하지 않는다. 평가의 music_passed·release_passed·AND stage_ready는 분리돼 있고 reward에 all3/AND 보너스는 없다.

## 최소 CPU 대조와 할인

`audit.py`는 현재 `PrefixLearningEnvironment`를 CPU fixture에서 생성해 원 `substep/end_control/performance_settlement`를 호출한다. candidate/wrong만 미리 지정하고 safety·PBRS를 차단했다. q/접촉기하·힘·동역학을 재현한 실험이 아니다. 다음 표는 **원9항 중5항만**이다. 처음 보상에 γ⁰, 이후 control마다 γ=.99를 적용한다. 소수 끝점·float32 누적 때문에 예산 이론값과 약간 차이 난다.

| 지정한 라벨 시간표 | 5항 비할인 합 | reset 기준 할인합 | A/7/8 achieved | A released |
|---|---:|---:|---|---|
| A clean→해제, B7/8 공유clean | 4.500004 | .426641 | 모두True | True |
| 위 clean/wrong/달성 지급은 같고 A종료 뒤 candidate만 잔류 | 4.500004 | .426641 | 모두True | False |
| A clean 계속유지, B7/8 wrong | 1.000811 | .213810 | A만True | False |
| A wrong, B7/8 clean | 2.751599 | .149310 | B7/8만True | False |

첫 두 행의 **5항은 모든 tick에서 exact 동일**하다. 실제 같은 q 궤적으로 두 candidate 라벨을 만들 수 있다는 주장이 아니다. full3는 두 부분성공보다 비할인·할인 모두 높다. 반면 두 부분성공끼리는 비할인 순위(2.752>1.001)와 할인 순위(.149<.214)가 바뀐다. 이는 지정한 시간표의 산술이며 실제 정책의 선호·수렴 원인을 확정하지 않는다.

| A end에서 다음 시점까지 | 지연 | γ^(60·지연) | (γλ)^(60·지연), λ=.98 |
|---|---:|---:|---:|
| A 원해제 마감 | .1000초 | .9415 | .8340 |
| B7/8 공유 press | .6617초 | .6710 | .3009 |
| B7 audible 시작 | .7817초 | .6241 | .2420 |
| B8 audible 시작 | 2.1865초 | .2675 | .0189 |

A 유지+Bwrong에서 A clean→해제+B성공으로 바꾸는 지정 라벨 대조의 추가5항 보상은 비할인 약+3.49919, reset 할인+0.212831, Aend 기준 미래할인+1.439791이다. 해제에 직접 붙은 점수는 아니지만, 다음 음을 성공시키는 유인은 이미 상당하다. B8은 B7과 press가 같아 최초접촉 진행 최대.25도 B7의 준비 시기에 함께 벌 수 있다. H32=.533초가 이후 보상을 완전히 자르는 것은 아니다. 표의 GAE 열은 직접 TD잔차 전파 가중치이며 가치 bootstrap·학습·전체 return을 대체하지 않는다.

## 원9항과 실제 관측의 범위

원9항은 위5항에 PBRS·standby·thumb·action_change를 더한다. 표를 원9항 총보상이나 실제 q 궤적의 완전한 반사실 비교로 부르지 않는다.

- PBRS는 `γΦ(next)−Φ(current)`다. 같은 초기Φ와 원 terminal nextΦ=0을 갖는 완전 할인합은 망원합으로 `−Φ(initial)`이다. 접근 credit 배분을 돕지만 이 가정하의 총 목적에 별도 해제 보너스가 생기지는 않는다. **비할인** episode PBRS합은 궤적별로 다를 수 있다.
- standby는 접촉해제 보상이 아니라 B자세 품질×원 score-only idle gate다. rate≤.02/s·고정4손가락 평균이므로 검지 한 개의 차이는≤.005/s다. A→B press .6617초 전체를 모두 써도 비할인≤.00331이고 실제 gate 창은 더 좁다. CPU 원 helper에서 Aend+.10의 검지 gate=.5, gap중간=0, B7/8 무음gap=0이었다. angle quality·native 도달은 이 검산에서 평가하지 않았다.
- thumb는 별도 지지 후보/기하이고 선택F4의 해제 목적과 같지 않다. 선택 LH21 움직임 비용0, 전체 native범위·4rad/s·cap.25·90쌍·손목v3/엄지035/비선택B를 유지했다. 움직임·관절자세/힘 감점으로 문제를 바꾸지 않았다.
- 실제250 env0의5항 합은2.749999,300은1.000000이다. 실제9항에는 각각 approach−1.675385/−1.433862, standby+.086643/+.087965, thumb+.107733/+.053956과 작은 기존 action_change가 따로 있다. 이 episode 원장은 비할인 누적이며 저장60Hz trace로 미저장240Hz 보상을 복원했다고 주장하지 않는다.

독립검수된 실제학습은 확률적 완료3456episode 중 all3 4건이며 **4건 모두 A released=False**다. 저장평가896회는 all3/release0,200/300은 A128·B0,100/150/250은 A0·B각128이다. 250처럼 A 자체가 clean0인 평가를 “A압현 성공 후 해제만 실패”로 부르지 않는다. 원 cost/GAE/critic은300행0이었다. 추가 carry의 자세개선과 전환실패가 함께 관찰됐다는 root 통보는 원인 분리에 유용하지만 이 감사가 carry 원장을 재검산한 것은 아니다. 이 자료만으로 보상만의 원인·정책 표현 한계·탐색 부족 중 하나를 확정하지 않는다.

## 단 하나의 최소 개선안 — 보류된 설계

**A의 기존 `song_left_success` .25b만 원 A 해제창까지 유보(escrow)한다.** A의 원 achieved latch가 True이고 원 released가 유효창에서 True가 된 control에, 실패가 없을 때 그 .25b를 한 번 지급한다. 해제하지 못하면 지급하지 않고 소멸한다. A의 contact.25/clean1/원감점과 B7/B8의 전체예산은 그대로다. 새10번째항·새총예산·해제감점·움직임비용·pose/force 문턱을 추가하는 안이 아니라 **기존9항 내 A달성 지급시점·조건 변경**이다. 새로운 reward 계약·엄격저장본 정체성은 필요하다. achieved·music_passed·release_passed의 정의는 바꾸지 않는다.

A를 skip하거나 음 전 접촉만 하고 떨어뜨려서는 원 achieved latch가 없어 받을 수 없다. 원 문턱을 만족했더라도 end 전 해제·deadline 뒤 해제는 받을 수 없다. 원 musical 달성문턱/clean비율을 새로 강화하지 않는다. 원 native falling-edge의 짧은 재접촉 한계는 이 최소안도 그대로 가진다. 따라서 실제 피부 분리 목적을 완전히 해결한다고 부르지 않는다.

**B7/8은 같은 press의 연결 그룹이므로 B7 해제를 요구하지 않는다. 마지막 B8에도 escrow를 추가하지 않는다.** 기존 `release_required` 배열은 현재 지급에 사용되지 않으며 공유 press 그룹과 같은 정의가 아니다. 이 배열만 새 지급 eligibility로 쓰지 않는다. 이번 제안 eligibility는 명시적 A4→다른 위치 B그룹 하나에만 한정한다.

이 설계는 root 판단으로 **보류**다. supervised warmstart/NN-only 재현·RL 유지 검증과 동시에 바꾸지 않는다. 이번 지정 시간표의 핵심5항에서 full3-clean이 비교한 두 부분성공보다 높고 참고동작으로도 도달한 전제가 있으므로, 학습 가능성 대조와 보상 목적 정렬은 별도 실험이어야 한다. root 승인 전 구현·새학습은 없다.

재현: `audit.py`를 rl38 CPU 환경에서 실행하면 새 `results.json`을 만든다(기존 출력 거부). 원입력과 함수 SHA·각항 지급시각·원7평가의 env0 9항은 JSON에 있다. 기존 reward_objective_audit는 중지 단음의 역사적 산술 근거로 재사용했고 이번 검지3음 결과와 혼합하지 않았다. 통합독립검수는 root가 carry 실제검수 뒤 별도 위임한다.

근거 함수: `guitar_learning/gpu/environment.py:992–1067` 원시간 적분/achieved/released/contact, `simplified_finger_environment.py:18–27,227–234` deficit/최종9항, `finger_skill_environment.py:109–113` 균형계수, `finger_reward.py:238–278` score-only 회복gate, `training/decision_ppo.py:9–36` γ와GAE. 제안은 이 활성 파일을 변경한 것이 아니다.
