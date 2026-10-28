# 검지 낮은 effort 조건의 B: cost head 0 초기화 검토안

**상태: root가 이 최소 재사용안의 CPU 구현·검수를 승인했다. GPU/native 실행은 금지한다.** 원 position/antiwindup 대조와의 실제 실행 순서는 root가 정한다. cost head가 현재 실패의 주원인이라고 단정하지 않는다.

소유권은 이 새 폴더뿐이다. 원 `guitar_learning`·기존 진단 소스/문서·checkpoint·원자료·봉인을 수정하지 않는다. 이 계획은 기존 시간/credit ablation의 **B만** 현재 검지 조건에서 분리하는 안이며, A의 gamma 변경과 결합하지 않는다.

## 고정 조건과 유일한 개입

- 대조는 `../low_effort_index_learning_v1/`의 현재 검지 학습이다: private finger16 effort0.25Nm, thumb5/다른89축 불변, 원90 collision pairs, wrist teacher v3, fixed guitar, incremental selected4, large/128환경/H32/seed7/300업데이트/save50/원 std, PPO·PBRS gamma0.99·9보상·종료·준비 상태·원 teacher/reference 동일.
- 정상 `ShortPolicy` 생성이 끝난 직후 `torch.no_grad()`에서 **`cost_critic.weight`와 `cost_critic.bias`만0**으로 만든다. 이 현재 head는 마지막 `nn.Linear`이다. 나머지71개 state tensor·actor/R-critic/value encoder·log_std는 그대로이다. gradient를 끄지 않으며 실제 양의 cost가 발생하면 이 head도 학습한다.
- 평가·렌더의 정책 생성은 **fresh=False**이다. 이후 원 strict `trainer.load`가 학습된 cost head를 그대로 복원한다. 평가 때 다시0으로 만들거나 이전 Actor를 이식하지 않는다.
- 원 cost/termination 신호나 계수·할인·optimizer는 바꾸지 않는다. B는 초기 허위 cost-value 성분을 분리하기 위한 기존 계획의 대조이며, 성공/실패 원인·힘 제한 효과를 사전 확정하지 않는다.

## 구체적인 최소 재사용 연결

1. 원 B의 `04_ablation/time_credit_ablation/corrected_source_v3/support/variants.py`에서 `descriptor('B_zero_cost_head')`와 `policy_type(..., fresh=...)`를 그대로 import/pin하는 안을 우선한다. 이 함수는 정상 정책 생성 후 두 파라미터만0으로 만들므로 추가 난수를 소비하지 않는다. 과거 frozen-source 실행기·middle 설정·과거 checkpoint는 실행/재사용하지 않는다. `settings_for`로 새 settings를 바꿀 필요도 없다.
2. 현재 `low_effort_index_learning_v1/probe.py`의 `launch`, `effort_scope`, `verify128`, `train_args`, checkpoint/output 배치와 원 runner/train/load/evaluate/render를 재사용한다. 새 wrapper에서 해당 모듈의 `HERE`/gate 연결만 새 출력·봉인으로 한정하고 finally에 복원한다. 기존 precheck384를 새 실행처럼 복제하지 않는다.
3. 원 `effort_scope`가 만든 검증된 pool을 한 번 감싸, **정책 생성 전** `pool.contract['task']['short_learning']['ablation']`에 위 원 B descriptor를 추가한다. 원128 native 검사/scene 생성/제어/관찰을 복제하지 않는다. 실제 settings는 원 검지 설정과 exact이고 contract에만 초기화 정체성이 추가된다. `runner.ShortPolicy`와 렌더가 참조하는 `runtime.ShortPolicy`를 해당 B 생성자로 scoped 연결/복원한다. fresh 여부는 train에서만 True이다.
4. 그러면 원 `runner.run`이 tag가 있는 계약을 쓰고 정책 architecture/저장 identity에도 반영한다. baseline↔B 교차 strict load는 거부되어야 한다. 원 `_pins`·teacher 증거 검사·complete trainer load는 유지하고 새 wrapper·원 B helper·선행 실제 검수·새 선언을 추가 pin한다. 우회 loader나 전역 profile 변경을 만들지 않는다.
5. 위 연결에는 기존 module 경로/alias 복원 및 새 pre-native gate만 필요하다. 전체 학습기·평가기·PD verifier를 복제하거나 새 범용 framework/옵션을 만들지 않는다. 원 보고서는 보존하고 초기화 검사/alias 복원 근거가 필요하면 새 진단 보고서로 분리한다.

## 선행 gate와 CPU 검증 기준

후속 구현/실행을 선택하더라도 다음 두 실제 검수의 `PASS/findings[]`, `reviewed_sha256`, `verification.json`의 직접/검증 입력 SHA를 stdlib-only gate로 확인해야 한다. 검수 PASS는 음악 성능 전체 통과를 뜻하지 않는다.

- 원128 precheck: `../low_effort_index_learning_v1/precheck_analysis/results_v1/review.json` 및 기존 `precheck_gate()`의384개 첫 시도·수용 기준.
- 원300+7평가: `../low_effort_index_learning_v1/learning_analysis/results_v1/review.json` 및 실제 launcher/입력·원장. root가 실제 독립 PASS를 전달했으며, 후속 도구는 파일과 모든 SHA도 직접 확인한다.

후속 구현 승인 시 CPU 검사는 다음으로 제한한다.

- [ ] 현재 CPU `ShortEnvironment` 계약+private0.25Nm/128 선언에서 동일 seed7로 baseline/B 정책을 각각 생성. state key/shape73개 동일, 변경은 두 cost 파라미터뿐이며 나머지71개 exact. 원 실제 initial checkpoint의 model73 tensor도 CPU 비교하되, 이는 model-only 비교이고 과거 strict full-load 성공으로 부르지 않는다.
- [ ] Python/NumPy/Torch RNG 상태 exact, 동일 RNG 상태에서 actor mean/log_std·tanh latent/action·reward value exact, std/optimizer 설정·parameter grouping exact. 마지막 두 파라미터를0으로 만드는 연산 자체가 RNG를 소비하지 않음을 확인한다. CPU 증명을 CUDA 난수열 exact 증명으로 확대하지 않는다.
- [ ] 초기 cost prediction0, encoder/reward-value 업데이트만으로 허위 cost-value가 생기지 않음, 실제 양의 cost target에는 head gradient/학습 가능. `fresh=False` 생성+원 strict save/load 후 학습된 nonzero cost head 보존; baseline/B 교차 load 거부.
- [ ] 원128 verifier의105개 실제 속성·16 effort만0.25·90pairs·controller caps 일치 검사 재사용. 생성 실패/close 이중오류·alias/loader 복원·기존 출력/symlink pre-native 거부·장면종료·전후 pin 검사 유지.
- [ ] 원 settings/PPO/보상/종료·목표/시계와 차이를 재귀 비교하여 초기화 계약 tag 외 의미 변경0 확인. CPU 검수·dry plan·독립 change-reviewer PASS 후에만 root에 봉인을 인계.

CPU 실행 근거는 새 `cpu_verification.json`에 별도로 기록한다. 향후 실행을 선택하면 root가 한 GPU에서 원300+7평가 계획으로 순차 실행하며, 본 작업은 GPU 작업을 예약하거나 시작하지 않는다. 원 연속2회 음악 평가 기준·모든128 첫 시도/실패 분모를 유지한다.

추가 사전 지표인 **후반 유지**는 200/250/300 세 평가가 모두 달성≥90%·clean≥90%·wrong≤10%·물리/손목fail0일 때만 통과로 보고한다. 이 기준은 원 연속2회 기준을 대체하지 않는다. 각 평가에서 target 상계 체류·PIP target−actual gap·DIP 실제 굴곡도 함께 보고하며, env0/60Hz 상세와 전체128 음원장을 구분한다. 기준을 통과해도 자연스러움·자유 기타·전곡·생산채택은 미완료이다. source/자산/과거결과·기준을 바꾸지 않는다.
