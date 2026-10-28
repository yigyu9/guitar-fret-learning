# B 비용 head 초기화 대조: CPU 분석 준비

소유는 이 analysis/ 아래뿐이다. root의 parent PLAN은 읽기만 한다. producer·CPU준비는 live worker 소유이며 기존 baseline/precheck/regression/source/봉인/원자료는 변경하지 않는다. GPU 실행 권한은 root에게만 있다.

## 결과 전 고정한 분석 범위

- [x] 원 baseline과 같은 large/128/H32/seed7/300 및 7고정평가(0/50/100/150/200/250/300), 원9보상·gamma/PPO·종료·cap0.25·wristv3·검지112의 단일 대조로 한정한다.
- [x] 인접2 음악기준과 후반 유지기준을 아래처럼 분리하고, best/latest 사전순위를 유지한다.
- [x] 실제 전체 완료 전 raw/model 읽기와 결과 생성을 차단하는 stdlib-only 가드 및 기준 경계 CPU 검사를 준비한다.
- [x] producer와 jobs/출력/launcher/계약/초기화 증거 인터페이스를 메시지로 합의했다. 정확한 실제 JSON 키는 producer 구현 완료 통보 후 대조한다. 이 단계에는 실제 B 자료/모델을 읽지 않는다.
- [x] root의 학습중 사전구현 지시에 따라 분석 actual main을 완성했다. 합성dict/미완료launcher 가드만 CPU 검사한다.
- [x] 완성 main의 별도 독립 준비검수 PASS를 받았다(이전 골격 검수와 구분).
- [x] root의 session71599 전체8child exit0 통보(1676.633288111초) 후 actual main을 CPU 실행했다.
- [ ] 최종 실제 결과의 독립 수치/문서/그림 검수는 별도review에 기록한다(요청 뒤 이 계획 동결).

B는 정상 정책 생성 직후 cost_critic.weight/bias 두 tensor만0으로 만든 fresh 초기화 대조다. actor/Rcritic/encoder/std 등 나머지71개 exact와 Python/NumPy/Torch RNG·optimizer 설정 동일성을 producer CPU 증거와 실제 initial에서 각각 구분해 확인한다. B의 실제73개가 B expected와 같다는 검사를 baseline의73개 default exact로 오표기하지 않는다. 기존 baseline initial 대비는71개 exact+두 cost0이다. CPU model-only 비교는 native strict full-load 검증과 별개다.

## 정확한 분모·검증

전체300 metrics/1,228,800 raw전이, 완료/실패 episode와 남은 open 전이를 구분한다. 7×128=896 고정평가 첫시도는 실패·random에 유리한 제외 없이 모두 보존한다. 기존 precheck384는 새 실행처럼 합산하지 않으며 noNN random31/128과 NN initial의 차이를 그대로 둔다.

실제 완료 가드는 parent8child 순서/rc0/completed와 child launcher를 확인한다. 실행 전후 입력·source·scene닫기/native128×105/16cap/90pairs·alias복원·설정/contract·실제 checkpoint identity/strict load 경로를 원 검수 자료와 새 자료에서 대조한다. B의 source pin 추가와 ablation tag는 명시하고 원 physics/target/reward/PPO 의미 변경이 없는지 확인한다. baseline↔B strict 교차 load를 우회하지 않는다.

동결 baseline `learning_analysis/analyze.py`의 passed/rank 산술, prelearning trace_audit, precheck arm_audit를 함수 단위로 재사용한다. 전체 main을 monkeypatch해 초기화 검사를 바꾸지 않는다. 그래프는 baseline에 독립 함수가 없어 필요한 짧은 plotting만 새로 작성한다. 전체7 결과와 원9보상/300metrics를 공개하고 selected4의 상한 도달·PIP/DIP actual/target·몸체1/2/3 합력·wrist·armbounds를 동일 env0/60Hz 범위로 비교한다. source SHA가 다른 옛 자료는 당시 source mapping을 검증하고 현재 판정 helper와 의미가 같은지 확인한다.

실제 실패비용과 cost GAE·critic(value/target/MSE/EV), entropy/ratio/KL/LR를 분리한다. 비용 초기화 B가 후퇴 원인을 해결한다거나 자연스러움을 보장한다고 결과 전에 단정하지 않는다. 목표 상한과 실제 추종차이는 별도 관찰이다. 나머지127의 힘·기하를 env0에서 추정하지 않는다. nearest와 any-sample witness, 60Hz 합력과240Hz 극값/압력/접촉쌍을 구분한다.

## 사전 고정 수용·영상 선정

단일 평가 통과: 달성률≥0.9, 평균clean≥0.9, 평균audiblewrong≤0.1, 물리실패율=0, 손목실패율=0. trained 평가50~300 중 인접 두 시점 모두 통과하면 기존 연속 음악기준 통과다(초기0 제외).

추가 후반 유지기준: 200/250/300 **세 평가가 모두** 위 단일기준을 만족해야 한다. 연속 통과와 따로 보고하며 새 자연성 기준으로 바꾸지 않는다.

best는 전체7평가를 (달성률, 평균clean, −평균audiblewrong, −물리OR손목실패시도율, update큰순)으로 정렬한다. latest300은 별도다. 같으면1모델, 다르면2모델의 동일128장면 env0 손/전신 영상 후보를 분석 후 선정한다. 영상 실행은 root의 별도 strict/native 검수·스케줄을 따른다.

## producer와 합의한 인터페이스

새 probe.HERE는 B 폴더이며 output(phase, control=None, update=0), checkpoint(update), gate(phase='train', require_review=True)를 제공한다. 출력은 train/evaluation_000000..300, parent02_train_eval_launcher.json은기존8children형식이다. 새precheck384를실행하지않는다.

contract.task.short_learning.ablation은원variants의 B_zero_cost_head descriptor이며 settings는baseline exact다. cpu_verification.json.initialization과 실제 train/initial_model_comparison.json을구분한다. 확정키는 state_tensor_count=73, equal_original_state_tensors=71, changed_state_names=[cost_critic.bias,cost_critic.weight](정렬), cost_parameters_exact_zero이며 CPU initialization에는 RNG_and_actor_reward_exact도 있다. 실제 source probe.py의 기록식을 읽어 확인했다. 실제 initial비교에는 baseline/B initial경로·SHA를남긴다. 각output의zero_cost_diagnostic.json과pool생성시initialization_declaration.json은원diagnostic_report에추가되는증거다. 평가/렌더는fresh=False로학습된head를재초기화하지않는다.

analyze.py는 실제 main 구현을 포함하되 noarg는 실제파일을 읽지 않는다. --self-test는 합성dict/미완료launcher만 검사하며 Torch/NumPy/Isaac를 import하지 않는다. --root-completed는 먼저 stdlib로 parent8stage 완료/rc0/순서를 검사하고 실패하면 producer import·로그/모델읽기·출력쓰기 전에 중단한다. 이 옵션은 root 전체완료통보 뒤에만 실행한다. 사전검수 당시 actual 실행/결과생성은0이었고, root의 전체완료 통보 후 실제결과를 생성했다. 실제 producer JSON 키는 사전에는 구현 원문만 읽어 확인했고 완료 후 실제JSON을 검산했다.

## 완성 main의 사전 검수 범위

- root의 전체8child exit0 gate를 통과한 뒤에만1267 producer핀/선행3검수·source를 검증하고 numerical dependency를 import한다. CPU에서는 불완전launcher를 합성 주입해 그전에 중단함을 검사한다.
- B8scene 원settings/native/contract/Bfresh선언/strict저장identity를 확인하고 baselinecontract의유일차이가Bdescriptor인지검사한다. initialB expected73·baseline71/2를실제모델과source기록JSON에서각각검산한다. 평가fresh=False를검사하며학습된costhead의0지속을가정하지않는다.
- 원 trace_audit/arm_audit/passed/rank를 직접 호출한다. 수치불일치·nearest잔차는보존하며전체음원장을CPU60Hz로대체하지않는다. 실패/cost episode는제외하지않고원9보상·열린전이·costsignal/GAE/critic표와후반PIP/DIP/상한을함께기록한다.
- output은새results_v1만허용한다. 사전검수에서는 B실제로그/모델읽기/결과생성0을 확인했다. 이후 root 전체완료 통보를 받아 이 main을 CPU 실행했고 결과에 대한 별도 실제검수를 요청한다.

## 실제 분석 기록

전체8stage 완료/닫기·입력핀·B73expected/기존71+cost2zero 및896평가·300metrics를검산했다. 결과에맞춰cost critic value/target/MSE·EV None과MCPz하한체류를보고하는요약만추가했다. producer/준비1267핀/source/기존결과/GPU는변경하지않았다. 성과·후반유지·target추종/힘을분리하고최종raw수치검수는새results_v1/review.json·REVIEW.md만허용한다.
