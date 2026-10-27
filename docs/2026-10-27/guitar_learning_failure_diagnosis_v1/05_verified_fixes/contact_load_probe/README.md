# 128환경 실제 240Hz 하중 관찰 준비

목표는 기존 env0/60Hz 감사의 표본 한계를 보완하고, 목표 preload 및 계속 안쪽으로 향하는 명령의 국소 선형 성분을 후속 분석할 자료를 남기는 것이다. GPU 실행·학습·보상/종료/힘/재료/PD/관절 범위/controller 수정은 이 준비에 포함하지 않는다. 현재 baseline 학습과 활성517 Python·기존 orchestrator·docs04 감시20개·INTERVENTION_PLAN의 동결을 유지한다. 이 폴더의 새 도구만 작성한다.

`probe.py`는 원래 `runner.run`→strict checkpoint validation→`trainer.load`→`runner._evaluate`→`ShortPool.step`을 재사용한다. `--checkpoint`, `--control policy|zero|reference`, `--out`만 받으며 사전에 지정한 아래 네 조합만 허용한다. 현재 교정 thumb support v3 / diagnostics v6의 fresh 원래 gamma baseline 저장본만 사용한다. 과거 source pin 우회·actor 이전·새로운 학습은 없다.

| 조건 | checkpoint | control | 원래 업데이트 |
|---|---|---|---:|
| initial_zero | initial.pt | zero | 0 |
| initial_reference | initial.pt | reference | 0 |
| cp50_policy | evaluation_000050.pt | policy | 50 |
| final300_policy | final.pt | policy | 300 |

모든 checkpoint는 `04_ablation/time_credit_ablation/corrected_source_v3/baseline_original_gamma_seed7/train/` 아래다. reference는 원래 `03_short_learning/reference_middle_row8_v2.json`이다. 첫 시도 quota는 원래 각 환경1개/총128개이며 실패도 분모에 포함한다. 원래 218 control/872 physics endpoint 상한과 60/240Hz를 유지한다. 이미 종료된 환경이 원래 evaluator에 의해 reset되더라도 추가 시도는 보관하지 않으며, 저장 배열의 해당 행은 `first_attempt=false`와 0으로 마스킹한다.

## 관찰 자료와 의미

원래 `environment.substep`이 기하·원장·실패를 갱신한 직후 원본 snapshot을 관찰한다. 추가 scene.step·policy.act·critic forward·난수 추출은 없다. `ShortPool.step`에는 행동을 그대로 전달하고 결과를 그대로 반환한다. 성공/보상/종료 판정은 원래 runner가 수행한다. 추가 보고서 completed는 수집·원래 평가·불변성·종료 감사의 완료이며 음악 성공률을 뜻하지 않는다.

`physics240.npz`에는 clock/source/local time, first-attempt와 물리/손목 실패, candidate/wrong/positive 및 any-sample position/facing, 원래 최근접 reward-pad 표본 index/거리/높이/cosine/실제 world 점·법선, LH21 actual/target, 선택4 qd, thumb/index/middle/ring/pinky3의 native force W, guitar/선택 distal/thumb3의 pose13, 해당 최근접 점의 world point Jacobian3×4, 실제 점 속도와 전체105 DOF로 예측한 점 속도를 저장한다. full-body 상태·힘·전체 Jacobian·정책 가중치를 복제해 저장하지 않는다. 원래 evaluator가 쓰는 기존 env0 trace는 그대로 남긴다.

최근접 reward point는 `surface_sample`이 지정하는 거리 기반 표본이다. candidate/positive는 다른 유효 표본이 만들 수 있다. 최근접 점 자체의 position/facing은 원래 pad_target_geometry에 그 점 하나만 넣어 별도로 관찰하며 환경 판정에 다시 쓰지 않는다. 따라서 최근접 점의 cosine과 any-sample candidate를 결합해 같은 점의 접촉을 인증하지 않는다. Jacobian은 원래 `thumb_contact_probe.point_jacobian`의 COM→point 공식을 그대로 호출한다. 실제 점 속도는 body COM 선속도 + 각속도×COM→point이며, 전체 DOF Jacobian×qd 잔차의 first-attempt 전체/실패 전 RMS·최대를 보고한다. 잔차가 크면 법선 Jacobian 해석을 보류한다. CPU 합성 fixture 통과가 실제 native Jacobian의 정확도를 보장하지 않는다.

`control60.npz`에는 선택4 policy/executed 요청, reward/cost, 원래 9개 보상의 control increment 및 episode cumulative, 선택음 ledger9필드를 보관한다. cumulative 값을 시계열로 합산하지 않는다. `first_attempt_notes.json`에는 환경별 종료 이유·물리/손목 종료·최종 ledger9필드·원래 reward components를 남긴다. 배열의 항 순서는 protocol/report에 명시한다.

`tick_physical_failure`는 같은 control에서 이미 발생한 native tick_failure와 직전 control failure를 포함한다. `tick_wrist_failure`는 원래 normal/severe wrist latch다. 둘 다 원래 substep **후** 읽으므로 최초 실패 endpoint 자체가 표시된다. 추가 `failure_latched`는 그 endpoint와 이후 첫 시도 표본을 모두 표시한다. 후속 정상/성공 통계는 `first_attempt & ~failure_latched`를 사용하되 모든128시도와 실패는 전체 분모에 남겨야 한다.

후속 분석에서는 실제 guitar pose로 press/rear plane 법선을 world로 변환한다. 선택4의 `j_n = n_W·J_point_W`와 `j_n·(target-q)` 및 `j_n·(4×executed_action)`을 계산할 수 있다(원래 incremental 속도 단위 rad/s). 이는 국소 선형 투영이며 실제 penetration·접촉쌍 압력·정책 단독 인과효과·힘 cap이 아니다. thumb035와 teacher 손목이 함께 작동하므로 정책만의 하중 원인으로 귀속하지 않는다. native force W는 body resultant이며 pair/압력 인증으로 확대하지 않는다.

고정 크기 배열을 사전 할당하고 최대872×128 물리/218×128 control 표본만 받는다. 추가 선택 필드의 비압축 자료+작은 원장/보고서는 조건당100MB 미만으로 제한한다. float32 기하·힘·관절/J, float64 원래 시각/보상·원장, 정수 clock/index·bool mask를 사용한다. 해당 예산의 CPU 근거는 `cpu_verification.json`에 있다.

## 출력·소스·모델 보호와 실행

기존 out은 native import 및 base runner 호출 전에 거부한다. base runner가 exclusive mkdir를 마친 뒤 `_pins` callback에서 dev/inode를 기록하고, 동일 소유 디렉토리에만 새 NPZ/원장/`load_probe_report.json`을 작성한다. 기존 report/evaluation/settings/trace는 수정하지 않는다. 원래 runner `_pins`의 활성517·자산·준비 입력과 자체 wrapper/helper/README/precommit/원래 teacher/reference evidence를 함께 pin한다. 원래 strict checkpoint 검사와 사전 source seal을 모두 유지한다. 원래 `_evaluate` 전후 모델 tensor 해시·trainer updates·Python/NumPy/Torch CPU/CUDA RNG 해시를 확인한다. 가중치는 보고서에 복제하지 않는다. 오류와 부분 자료는 신규 output에 보존한다.

CPU 준비 순서는 `CUDA_VISIBLE_DEVICES='' PYTHONPATH=. python .../contact_load_probe/self_test.py` 뒤 `prepare.py`다. 준비 검사에서는 CUDA checkpoint의 RNG topology를 우회해 trainer.load하지 않는다. 현재 저장본 input pin/teacher/reference와 업데이트·설정은 CPU에서 확인하며, 전체 architecture/config/optimizer/RNG strict load는 원래 GPU runner에 그대로 맡긴다. 미완성 final은 미확보로 표시하고 나중에 runtime이 원래 strict 검사를 수행한다.

네 checkpoint/원래 baseline 평가가 모두 완료되고 root가 GPU를 직렬 인계한 뒤만 실행한다. GPU 인계는 내부 자원 조정이며 추가 사용자 승인 요청을 뜻하지 않는다. root의 기존 rl38/Isaac 환경에서 조건별 새 out을 사용한다.

```bash
taskset -c 0-13 /home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/contact_load_probe/probe.py --checkpoint docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/time_credit_ablation/corrected_source_v3/baseline_original_gamma_seed7/train/initial.pt --control zero --out docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/contact_load_probe/run_initial_zero
```

나머지는 표의 checkpoint/control과 `run_initial_reference`, `run_cp50_policy`, `run_final300_policy`로 바꾼다. 기존 native baseline/evaluation 원자료를 덮어쓰지 않는다. 추가 관찰의 실제 결과는 실행 뒤 별도로 분석·검수한다.
