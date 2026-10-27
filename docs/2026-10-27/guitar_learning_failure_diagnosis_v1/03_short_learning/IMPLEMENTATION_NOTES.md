# 3단계 짧은 과제 PPO 비교 연결안

작성일: 2026-10-27. **읽기 설계이며 구현·GPU 실행·학습 결과가 아니다.** 현재 활성 Python 510개를 사용하는 2단계 진단이 종료되고 입력 검증을 마친 뒤에만 소스를 변경한다. 이 문서는 기본 학습 변경안이 아니라, 같은 측정·보상 아래 incremental/position의 짧은 학습 가능성을 비교하는 진단 경로 제안이다.

현재 24목표 DLS에서 네 손가락의 positive 사례가 확보되었다는 진행 보고를 전제로 한다. 약지의 손목 안내 초과 약 30.3mm를 19mm 이내로 줄이는 6D teacher 검사는 대기 중이다. positive 후보가 있다는 사실만으로 현재 종료 조건 아래 반복 학습 가능한 초기 배치가 검증된 것은 아니다.

## 1. 재사용 범위와 최소 변경

기본 `guitar_learning.train`, launch 설정의 incremental 제한, 561상태·v2/J·K1 정책, 보상 9개·오압현 v2·손목/물리 종료·035 reset은 그대로 둔다. 기존 runner 전체를 복사하지 않고 진단 진입점에서 아래 네 클래스를 조립한다.

| 구성 | 재사용 방식 | 필요한 진단 차이 |
|---|---|---|
| `FingerSkillPolicy` | 작은 subclass | 고정 학습 축 마스크, teacher 축 동결, 진단 architecture 계약 |
| `DecisionCollector` | 수정 없이 사용 | K1, 모든 행을 매 tick 수집; teacher는 pool 내부에서 비학습 축에만 합성 |
| `DecisionPPOTrainer` | 수정 없이 사용 | 기존 GAE·ratio·KL·critic·atomic save/strict load |
| `GpuPool` | 작은 subclass | 고정 기타 scene 선택, 진단 environment 선택, teacher 비학습 축 합성 |
| `SimplifiedFingerEnvironment` | 작은 subclass | 지정 원곡 1~4음만 반복, position 허용, 노출 25% 전곡 전환 비활성 |

활성 공용 코드의 예상 수정은 다음 두 곳이다. 나머지는 `tool/experiments/` 아래 진단 모듈과 관련 tests에 둔다. 승인된 실행 구현 단계에서 실제 파일 이름을 확정한다.

1. `FingerSkillEnvironment`에 `allowed_finger_action_modes = ('incremental',)` 하나를 두고 기존 생성자 비교를 이 속성의 membership 검사로 치환한다. 진단 subclass만 `('incremental', 'position')`을 선언한다. `SimplifiedFingerEnvironment`와 기본 CLI는 position을 계속 거부해야 한다.
2. `GpuPool`의 장면 생성과 환경 선택에 두 개의 작은 확장 지점을 만든다. 예: `_create_scene(settings, out)`와 `environment_class_override = None`. 기본 구현의 인수와 선택 분기는 현재와 같고, 진단 subclass만 `diagnostic_guitar_mode='fixed'` 및 진단 환경을 지정한다. reset/step/4회 substep/인증/close 처리는 복사하지 않는다.

진단 설정 생성은 기존 `settings_document`로 정상 incremental 설정을 만든 뒤, 진단 검증기가 허용하는 `song.finger_action_mode`와 별도 진단 계약만 추가한다. 기본 설정 검증기의 position 제한을 없애지 않는다. 런타임 import monkeypatch로 환경·제어를 바꾸는 방식은 학습 runner에 가져오지 않는다.

## 2. 원곡 1~4음 선택과 시간 정합

첫 pilot은 **손목 조건이 검증된 중지 등의 고정 1음**을 두 모드로 비교한다. 이 연결이 검증된 뒤 네 손가락을 별도 조건으로 돌리고, 통과 후 같은 손가락의 원래 인접 2~4음, 그다음 여러 손가락 구간으로 확장한다. 처음부터 네 손가락을 한 배치에서 서로 다른 학습 마스크로 섞지 않는다. 모드 간 동일한 source target ID·시간·teacher 입력을 사용한다.

원곡 task와 전체 M개 원장은 유지한다. 별도 축약 악보를 다시 compile하거나 임의 음 길이를 만들지 않는다. 기존 `FingerPhrase`/`FingerPhraseCatalog`/`BalancedPhraseSampler`를 재사용하되, 진단용 catalog는 지정한 단일 view만 가진다. 전체 source_targets/provenance와 기존 closed_groups는 보존하고, 선택 부분집합이라는 사실을 새 계약에 적는다. 기존 `build_phrase_catalog`는 singleton을 인접음과 합치므로 그대로 호출해 1음 과제라고 부르면 안 된다.

선택한 집합 S에 대해 다음을 고정한다.

- `focus_mask`: 원곡 인덱스 S만 True. 목표 ID·string/fret/finger·press/onset/end는 원곡 그대로다.
- `start = min(press[S])`, `first_onset = min(onset[S])`, `end = max(end[S])`, **`score_offset = first_onset - 3.0`**.
- 원곡 시간은 항상 `native local clock / 240 + score_offset`. 첫 audible onset은 local 3초다. 첫 press는 `3 - (first_onset - start)`이고, 원래의 press→onset 간격·audible 길이를 보존한다. 음 하나의 view는 60Hz 올림을 포함해 `3 + 원래 음 길이 D + 0.5초`다. local press가 음수가 되는 목표는 첫 pilot에서 제외한다.
- 기존 phrase의 `press - 3` offset과는 다른 **onset 정렬 진단 조건**이다. `view_first`는 원곡 press를 유지한다. 진단 catalog의 preparation_s는 실제 local 첫 press까지 시간으로 적고, 별도로 teacher 준비/첫 audible 시각 3초를 기록한다. 여러 view를 섞을 때 이 간격이 다르면 view별 기록이 필요하므로 첫 구현은 단일 view로 제한한다.
- 종료 tick은 기존 규칙처럼 마지막 end를 지난 60Hz 경계 이후이며, 원 tail 0.5초를 적용한다. 인접 구간 확장에서는 다음 원곡 press보다 말미가 길어지지 않도록 기존 경계 규칙을 적용한다. 유효 경계가 없으면 겹치는 음을 임의로 자르지 않고 구간을 다시 선택한다. 단일 손가락 격리 과제에서는 제외된 다른 음이 view를 조기 종료시키지 않도록 그 제외 조건도 적는다.
- 1음이 원곡 동시음 집합 일부라면 명확히 **다른 음을 제외한 단일 손가락 진단**으로 표기한다. 원래 화음/구간을 성공했다고 표현하지 않는다. 여러 음 단계에서는 가능하면 overlap-closed 구간을 선택한다.

진단 `_reset_scope`는 `FingerSkillEnvironment._reset_scope`의 phrases 경로를 재사용하고, `SimplifiedFingerEnvironment`가 reset하는 wrist/failure 타이머들도 같은 항목으로 초기화한다. 전곡 전환을 피하려고 committed 값을 거짓으로 유지하거나 `evaluation=True`를 학습 때 켜지 않는다. 진단 계약에는 `scope=fixed_source_subset`, `schedule=disabled`를 명시하고, v2 schema/J/independent/K1/561 기반은 유지한다. 변경된 reset의 타이머 동등성은 검사한다.

기존 scope 경로가 다음을 함께 결정하므로 별도 가짜 목표 관측을 만들지 않는다.

- `_events`의 valid mask와 `_finger_targets`의 8개 tracking/next priority slot.
- approach/contact/hold/achievement, wrong/performance 원장의 대상 및 손가락 균형 가중치.
- `_preparation_scope`의 선택 음과 손가락별 다음 원곡 준비 경계. 제외한 음을 missing으로 평가하지 않되, tail을 가짜 긴 대기로 바꾸지 않는다.
- `left_note_ledger.focus_mask`, `selected_target_ids`, 에피소드 분모.

CPU 검증에서는 동일 물리 상태와 동일 원곡 시각의 full task/view를 비교해 선택 음의 목표 좌표·방향·positive/wrong 조건이 같은지 확인한다. 보상 총합은 선택 범위와 가중치 때문에 달라질 수 있으므로 무조건 같다고 검사하지 않는다.

## 3. 035 reset, teacher와 정책 기여의 경계

최소 구현은 **정책이 첫 tick부터 선택 손가락을 제어하고, local 0~3초 동안 팔과 비학습 손가락만 teacher로 배치**하는 방식이다. onset 정렬에서는 원래 press가 3초보다 이르므로 teacher 준비 중에도 목표 접근·최초 접촉 구간이 시작될 수 있다. 접촉 보상을 시작 전에 차단하거나 시각을 임의 이동하지 않는다. 전이를 버리거나 시간축을 되감지 않는다. 3초 안에 이 배치가 실제 도달 가능한지는 짧은 GPU 사전검사에서 확인해야 한다.

- 매 episode 경계에서 기존 035/v14 reset을 한 번 수행한다.
- 왼팔 12축에는 단계2로 검증한 유한 ramp와 hold 목표를 적용한다. 선택 손가락 관절 4축은 teacher가 건드리지 않는다.
- 나머지 비학습 손가락은 B 목표를 같은 유한 제어로 유지한다. 엄지 5축은 명시된 준비 기준을 유지하고, 오른쪽 비활성 6축은 0이다. 어느 축을 B로 두는지 이름으로 저장한다.
- 학습 중에는 pad 오차를 보고 선택 손가락까지 수정하는 단계2 DLS를 실행하지 않는다. 현재 DLS는 **팔12+해당 손가락4**를 움직여 접촉을 만든다. 그 결과를 그대로 teacher에 넣으면 정책이 해결할 과제를 teacher가 수행한다.
- 가능하면 teacher 팔은 준비가 끝난 뒤 고정 joint target을 유지한다. 움직이는 기타를 쫓거나 pad 위치를 따라 팔을 재배치하는 피드백은 추가 보조 조건이므로 별도 비교가 필요하다.
- teacher 동작도 native PD/속도/힘 상한·충돌·중력·물리/손목 실패를 통과한다. 강체 위치·관절 상태의 중간 덮어쓰기와 기타 직접 보조 힘을 쓰지 않는다.
- 행동 변화 항에는 실제 환경에 제출한 합성 행동을 전달한다. teacher 팔 동작의 비용도 현재 수식대로 포함하고, 정책이 직접 조절하지 못하는 조건임을 기록한다. 선택 손가락의 움직임 비용 0은 유지한다.

**부분 reset 안에서 teacher 물리 준비를 추가 실행하면 안 된다.** `GpuPool`은 한 simulator이고 `DecisionCollector`는 매 tick N개 모두를 기록한다. 일부 완료 행을 reset하는 동안 전체 simulator를 여러 번 step하면 아직 진행 중인 행의 시계·보상·관측과 수집 전이가 불일치한다. 또한 environment.clock은 scene.physics_steps와 매 substep 일치를 검증하므로 측정 시계만 되감는 방식도 불가하다.

단계2 teacher는 기본 6초 ramp 뒤 추가 보정을 사용한다. 따라서 3초 준비가 된다고 가정하지 않는다. 위의 축소 teacher가 3초 안에 손목·팔 위치를 확보하지 못하면 학습을 바로 시작하지 않고, 별도 준비 단계와 전이 유효 마스크/GAE 경계를 설계하거나 더 가까운 검증 목표를 선택한다. 준비 시간을 몰래 늘리면서 `pre_roll_s=3` 또는 같은 과제라고 기록하지 않는다. 먼저 손가락별 1음에서 문제를 줄이는 편이 코드가 작다.

성과 명칭은 **고정 기타·teacher 팔·비학습 B 조건의 정책 수행**이다. 평가에는 동일 teacher와 선택 손가락 출력 0 대조를 포함한다. teacher가 팔을 옮겨 수동 접촉을 만든 성공과 정책 학습으로 늘어난 성과를 나누며, 출력 0에서도 이미 달성된다면 그것만으로 손가락 압현을 배웠다고 결론내리지 않는다. 모드별 출력 0의 뜻도 서로 다르므로 실제 target/q 궤적을 함께 제시한다.

## 4. 학습 축 마스크와 likelihood

기존 policy는 v2에서 phase J만 허용한다. 이를 F로 속여 사용하거나 561을 557로 줄이지 않는다. 진단 policy subclass의 `_active_mask()`만 고정 선택 축을 반환하게 한다. 단일 손가락은 17:33 중 해당 4축, 여러 손가락은 해당 4축들의 합집합이다. 한 실행의 모든 행과 시간에 동일한 마스크를 쓴다.

기존 `act`, `log_probability`, `evaluate` entropy, `analytic_kl`은 모두 `_active_mask()`를 사용하므로 이 경로를 재사용한다. `DecisionPPOTrainer`는 그대로 39차원 mean/logstd/latent와 활성 축의 scalar logp를 저장·학습한다. support encoder/head와 support std, 비선택 finger head는 동결한다. 선택 finger encoder는 공동이라 학습할 수 있다. finger std는 16개가 한 Parameter이므로 부분 requires_grad를 기대하지 않고, 비선택 항의 gradient 0·값 불변을 검사한다.

pool의 `step(action)`에서는 `executed = where(learn_mask, policy_action, teacher_action)`으로 합성한다. 선택 축은 **policy가 샘플링한 tanh(latent)와 정확히 같아야 한다.** 이후 학습 축을 teacher로 교정하거나, 교정한 행동을 원래 latent/logp로 학습하지 않는다. native controller의 기존 target clamp/rate limit은 환경 전이의 일부이며 별도 logp 보정을 하지 않는다.

현재 collector는 phase J에서 `held`를 그대로 pool로 전달하고 K1을 사용하므로 수정이 필요 없다. teacher는 결정론적 환경 입력으로 취급한다. raw policy action, 합성 action, native target, actual q를 지정된 소수 행의 trace에 나눠 기록한다. 비학습 축의 policy mean이 0이 아니어도 실제 실행에는 teacher 값이 들어가고 likelihood에서는 제외된다.

필수 검사는 다음과 같다.

- 수집 직후 동일 모델의 재평가 logp가 old logp와 일치하고 PPO ratio가 1이다.
- 비활성 latent/mean/logstd를 바꿔도 logp·entropy·KL이 바뀌지 않는다.
- 활성 4축만 변경할 때 logp가 변하고 업데이트 후 teacher/비선택 파라미터는 불변이다.
- partial reset을 포함해 scene/environment clocks, decision duration 1, reset된 행만 episode ID 증가가 유지된다.
- active mask 합성 전후 선택 축의 값이 정확히 같다. 출력 0 대조에서도 합성 로그가 남는다.

## 5. 새 계약과 strict fresh

진단 최상위 계약을 `guitar_learning.short_finger_learning.v1` 등 별도 이름으로 둔다. 기반 training contract와 task.finger_skill.v2는 보존하되 `task.short_learning` 및 policy architecture에 아래를 추가한다.

- 고정/자유 기타, 선택 원곡 ID/인덱스/시각, subset catalog SHA, scope/종료 길이.
- 제어 mode와 native action codec 전체, 학습 축 마스크, teacher/B/reference 각도와 ramp/hold 규칙·입력 SHA.
- source/task/assets SHA, 준비 시간·정책 관여 범위, 평가 대조 조건, std/초기 mean 설정.

constructor에서 계약의 마스크·모드와 실제 scene/controller/policy 값을 상호 확인한 뒤 첫 reset을 수행한다. `GpuPool.__init__`가 `self.reset()`을 호출하므로 subclass의 teacher 설정은 `super().__init__` 전에 준비해야 한다. runtime teacher가 참조하는 controller/scene은 첫 reset 시점에는 생성되어 있다.

새 학습 CLI에는 resume/transfer 경로를 두지 않고 fresh 정책/optimizer/RNG로만 시작한다. 저장된 모델의 평가 로드는 `DecisionPPOTrainer.load`의 architecture/config 완전 일치와 기존 source 검사를 모두 통과해야 한다. trainer.load만으로 소스 SHA 검사가 되는 것은 아니므로 runner에서 현재 source/input 검증도 재사용한다. 기본 학습 checkpoint나 incremental checkpoint를 position에 억지로 읽지 않는다. 새 진단 policy subclass의 정확한 architecture와 state_dict를 평가 진입점에서도 동일하게 구성한다.

두 모드는 한 봉인 소스에서 mode만 달라야 한다. teacher 파일도 SHA 입력에 포함한다. 실행 중인 이전 510개 소스 봉인이 끝난 뒤 공용 hook을 수정하고, 변경 후 입력 목록을 새 버전으로 봉인한다. 구형 결과의 input manifest는 갱신하지 않는다.

## 6. 비교 예산과 입력 강도

계획의 시작안 large·128환경·H32·300업데이트(1,228,800전이), seed 7/17 뒤 27, 평가 간격 50을 따른다. 실제 실행 전에 조건·과제 ID·평가 에피소드 수·중간 중단 기준을 확정한다. 같은 초기 네트워크 난수·동일 teacher 물리 목표·동일 native 속도/힘/각도 제한을 사용한다.

**같은 action std가 같은 물리 탐색 강도는 아니다.** incremental은 `a×4/60`을 target에 누적하고 0은 이전 target 유지다. position은 준비 기준과 상/하한 사이의 절대 target 요청이며 0은 준비 기준 복귀다. 따라서 이 비교는 제어 표현 비교이며 동일 힘 실험이라고 표현하지 않는다.

PPO 전에 지정 초기 상태에서 짧은 open-loop 난수 입력을 사용해 1tick 및 일정 시간의 target 변화 RMS·actual q 변화·한계 체류를 모드별 측정한다. 가능한 범위에서 초기 std를 사전에 맞추고, 그 선택값과 남는 장기 누적 차이를 계약에 기록한다. actual q나 성공률을 보며 학습 중 std/teacher를 임의 조정하지 않는다. 초기 mean 0의 물리 차이는 그대로 보고하며 B mean bias를 한쪽에만 주지 않는다.

동일 teacher 팔 목표가 1~4음 전체에서 가능한지도 확인한다. 불가능한 여러 음은 먼저 가까운 구간을 선택한다. 시간에 따른 팔 경로를 추가하는 경우에는 원곡 phase에 따른 teacher라는 새 조건으로 명시하고, 해당 기여를 단일 고정 팔 과제와 구분한다.

## 7. 큰 원장 없이 남길 로그

현행 runner는 raw transition/decision journal을 항상 만든다. 이를 그대로 호출해 대용량 원장을 만든 뒤 삭제하지 않고, 작은 진단 runner에서 기존 collector/trainer/검증·저장 helper를 직접 조립한다. 메모리의 원곡 M개 음 원장은 유지하되 디스크에 매 tick 전체 원장을 덤프하지 않는다.

- `settings.json`, `training_contract.json`, subset/teacher 조건, `inputs_before/after.json`, 실행 명령과 환경 정보.
- `metrics.jsonl`: 업데이트마다 9개 `reward_component_means`, 별도 failure cost, reward/cost 총합, PPO KL/ratio/grad/critic 지표, 누적 전이와 시간. `reset_reward_window()`와 `reward_window_means(H×N)`를 그대로 사용하며 분모는 raw control transitions로 표기한다.
- 작은 에피소드 요약: 선택 target IDs/count, 달성/clean/audible wrong/수행 부족, 종료 사유, 실제 관측한 노트 시간과 예정 시간, teacher 준비 완료 여부. 실패 에피소드를 원래 시도 수 분모에서 제외하지 않는다.
- 각도 모니터: 손가락별 실제 MCP/PIP/DIP 범위, target−q p95, 명령/실제 native 한계 체류를 별도로, B 오차 4축 RMS/max, 손목 초과·타이머. 16축 통합 RMS를 손가락별 RMS처럼 표기하지 않는다.
- 지정 env 0~3의 사전 지정 평가 에피소드만 압축 trace: source time/target IDs, policy/executed action, target/q, candidate/clean/wrong, wrist와 종료. 영상은 같은 평가의 전신/왼손 각 1개를 우선한다.
- checkpoint는 initial/final과 사전 지정 평가 시점만 보존한다. best 선정은 달성·clean·wrong·실패 기준으로 정의하고 총보상만으로 선택하지 않는다. 같은 경로를 덮어쓰지 않는 기존 save 방식을 유지한다.

teacher 통과 후의 에피소드만 골라 성공률을 내지 않는다. 준비 실패도 시도 수와 물리/손목 실패에 포함하고, 조건부 준비 완료 후 음악 성과는 보조 표로만 병기한다. 출력 0 대조와 PPO 정책 성과를 같은 표에 둔다.

## 8. 구현 후 검증 순서와 시작 게이트

1. CPU: 기본 클래스/CLI의 position 거부 유지, 진단만 허용, 561/J/K1과 full contract/mask 검사, source subset 시간·관측·원장, partial reset 타이머, likelihood/gradient/strict mismatch 검사.
2. GPU 소규모: 각 손가락 1음·두 모드에서 035 reset→teacher 팔/B 유한 배치→원래 손목 종료 아래 실제 원곡 시각의 판정. 현재 약지 6D teacher 결과부터 확인한다. 준비 3초가 부족하면 별도 설계 없이 본 학습에 진입하지 않는다.
3. PPO smoke: 수집 1회→업데이트 1회→fresh 진단 checkpoint 저장→동일 계약 재평가, 출력 0 대조와 active 축 일치 검증.
4. 정해진 300업데이트 비교. 연속 두 평가에서 손가락별 달성 ≥80%, 평균 clean ≥70%, audible wrong ≤10%, 물리 실패 ≤5%의 계획 기준을 적용한다. 손목 실패도 별도 수와 합산 실패율을 보고한다. 준비 실패·조기 종료를 성공 분모에서 삭제하지 않는다.
5. 통과 후에만 원곡 2~4음과 자유 기타로 확장한다. 고정/teacher 조건의 성공을 자유 기타 J33 성공으로 확대하지 않는다.

구현 시작 전 해결할 핵심은 새로운 PPO가 아니라 **teacher가 선택 손가락을 대신 움직이지 않으면서 3초 안에 팔을 배치할 수 있는가**, 그리고 **position과 incremental에서 같은 학습 축의 likelihood가 정확히 유지되는가**이다.
